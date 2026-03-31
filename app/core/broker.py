import httpx
from typing import Dict, Any, Optional
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.core.config import settings
from app.core.logger import logger

class AMPBrokerAPIException(Exception):
    """Custom exception for Broker API errors."""
    pass

class AMPBrokerRateLimitException(AMPBrokerAPIException):
    """Custom exception for rate limiting."""
    pass


class AMPBroker:
    """
    Client for interacting with the AMP Futures Broker via a REST API.
    (Often this leverages gateways like CQG, Rithmic, or CTS REST connectors).
    """

    def __init__(self):
        self.base_url = settings.AMP_API_URL
        self.api_key = settings.AMP_API_KEY
        self.account_id = settings.AMP_ACCOUNT_ID
        self.is_paper_trading = settings.IS_PAPER_TRADING
        
        # In a real setting you would need to fetch/rotate session tokens.
        self.session_token = None
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=10.0,
            headers={"Content-Type": "application/json"}
        )

    # Retry logic: Wait 2^x * 1 second between each retry starting with 1s, up to 10s max, and 5 retries max.
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type((httpx.RequestError, AMPBrokerRateLimitException)),
        reraise=True
    )
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Base request method with exponential backoff retry logic."""
        
        # Ensure we are authenticated (pseudo-logic for session tokens)
        if not self.session_token and endpoint != "/auth/login":
            await self.authenticate()
            
        headers = {}
        if self.session_token:
            headers["Authorization"] = f"Bearer {self.session_token}"

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Broker API Request: {method} {url} Payload: {data}")

        try:
            response = await self.client.request(
                method, 
                url, 
                json=data, 
                headers=headers
            )
            
            # Handle rate limiting specifically
            if response.status_code == 429:
                logger.warning("Broker API Rate Limit Exceeded. Retrying...")
                raise AMPBrokerRateLimitException("Rate Limit Exceeded")

            # Raise for other bad HTTP statuses
            response.raise_for_status()
            
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Broker API Error: {e.response.status_code} - {e.response.text}")
            raise AMPBrokerAPIException(f"API Error: {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Broker API Network Error: {str(e)}")
            raise e


    async def authenticate(self) -> bool:
        """Authenticate with the broker API and obtain session token."""
        logger.info("Authenticating with AMP Futures Broker API...")
        
        # Sandbox / Dummy auth logic
        if self.is_paper_trading and "sandbox" in self.base_url:
            self.session_token = "mock_sandbox_token_12345"
            logger.info("Authenticated successfully (Sandbox Mode).")
            return True
            
        payload = {
            "api_key": self.api_key,
            "account_id": self.account_id
        }
        
        try:
            res = await self._request("POST", "/auth/login", data=payload)
            self.session_token = res.get("token")
            logger.info("Authenticated successfully.")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise

    async def get_account_info(self) -> Dict[str, Any]:
        """Retrieve account balance and equity information."""
        logger.info(f"Fetching account info for {self.account_id}")
        endpoint = f"/accounts/{self.account_id}/balance"
        return await self._request("GET", endpoint)

    async def get_positions(self) -> list:
        """Retrieve current open positions."""
        logger.info(f"Fetching open positions for {self.account_id}")
        endpoint = f"/accounts/{self.account_id}/positions"
        res = await self._request("GET", endpoint)
        return res.get("positions", [])

    async def place_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        order_type: str = "market",
        price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        :param symbol: Ticker symbol (e.g., 'ESM4' or 'NQ')
        :param side: 'BUY' or 'SELL'
        :param quantity: Number of contracts
        :param order_type: 'market', 'limit', or 'stop'
        :param price: Limit price if order_type == 'limit'
        :param stop_price: Stop price if order_type == 'stop'
        """
        side = side.upper()
        order_type = order_type.lower()
        
        logger.info(f"Placing {order_type} ORDER: {side} {quantity} {symbol}")
        
        # Validate order parameters
        if order_type == "limit" and price is None:
            raise ValueError("Limit orders require a 'price' parameter.")
        if order_type == "stop" and stop_price is None:
            raise ValueError("Stop orders require a 'stop_price' parameter.")

        payload = {
            "account_id": self.account_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "time_in_force": "DAY", # Configurable as needed
        }
        
        if price:
            payload["limit_price"] = price
        if stop_price:
            payload["stop_price"] = stop_price

        # Endpoint for submitting orders
        endpoint = f"/accounts/{self.account_id}/orders"
        
        try:
            response = await self._request("POST", endpoint, data=payload)
            order_id = response.get("order_id", "UNKNOWN_ID")
            logger.info(f"Order successfully placed. Order ID: {order_id}")
            return response
        except AMPBrokerAPIException as e:
            logger.error(f"Failed to place order: {str(e)}")
            raise

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close an open position for a specific symbol by sending an opposing market order."""
        logger.info(f"Attempting to close open position for {symbol}")
        
        positions = await self.get_positions()
        pos = next((p for p in positions if p.get("symbol") == symbol), None)
        
        if not pos:
            logger.warning(f"No open position found for {symbol} to close.")
            return {"status": "ignored", "reason": "No position"}
            
        quantity = pos.get("quantity", 0)
        if quantity == 0:
            return {"status": "ignored", "reason": "Zero position"}
            
        # Determine opposite side
        current_side = pos.get("side", "").upper()
        close_side = "SELL" if current_side == "BUY" or current_side == "LONG" else "BUY"
        close_quantity = abs(quantity)
        
        logger.info(f"Closing position: Generating {close_side} order for {close_quantity} {symbol}")
        return await self.place_order(symbol, close_side, close_quantity, "market")

    async def close_client(self):
        """Clean up the httpx client."""
        await self.client.aclose()


# Singleton instance to be injected or imported where needed
# Normally this could be a FastAPI Dependency `Depends(get_broker)`
broker_client = AMPBroker()
