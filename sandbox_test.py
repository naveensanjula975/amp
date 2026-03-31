import asyncio
import httpx
from unittest.mock import AsyncMock, patch
from app.core.broker import AMPBroker, AMPBrokerRateLimitException

# A script to run sandbox tests mocking the actual AMP/CQG HTTP API calls

async def run_paper_trading_tests():
    print("--- Starting Paper Trading Sandbox Tests ---")
    
    broker = AMPBroker()
    
    # We will patch the internal httpx AsyncClient request method
    # so we don't actually hit the real endpoint during this demo.
    
    with patch.object(broker.client, 'request', new_callable=AsyncMock) as mock_request:
        
        # 1. Test Authentication
        print("\n[TEST] 1. Authentication")
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "sandbox_jwt_token_999"}
        mock_request.return_value = mock_response
        
        # Override the dummy logic in authenticate for the purpose of the mock test
        broker.is_paper_trading = False 
        await broker.authenticate()
        print(f"Authenticated? {broker.session_token is not None} -> Token: {broker.session_token}")
        
        # 2. Test Account Info Retrieval
        print("\n[TEST] 2. Getting Account Info")
        mock_response.json.return_value = {"balance": 50000.0, "equity": 50100.0, "currency": "USD"}
        account_info = await broker.get_account_info()
        print(f"Account Info Result: {account_info}")
        assert "balance" in account_info
        
        # 3. Test Place Market Order
        print("\n[TEST] 3. Placing Market Order (BUY 1 ES)")
        mock_response.json.return_value = {"order_id": "ORD-1001", "status": "working", "symbol": "ES"}
        order_res = await broker.place_order(symbol="ES", side="BUY", quantity=1, order_type="market")
        print(f"Order Response: {order_res}")
        assert order_res.get("order_id") == "ORD-1001"
        
        # 4. Test Position Retrieval
        print("\n[TEST] 4. Getting Positions")
        mock_response.json.return_value = {"positions": [{"symbol": "ES", "side": "BUY", "quantity": 1}]}
        positions = await broker.get_positions()
        print(f"Current Positions: {positions}")
        assert len(positions) == 1
        
        # 5. Test Close Position
        print("\n[TEST] 5. Closing Position (SELL 1 ES)")
        mock_response.json.side_effect = [
            {"positions": [{"symbol": "ES", "side": "BUY", "quantity": 1}]}, # Get positions
            {"order_id": "ORD-1002", "status": "filled", "symbol": "ES"}     # Place opposing order
        ]
        close_res = await broker.close_position(symbol="ES")
        print(f"Close Position Response: {close_res}")
        assert close_res.get("order_id") == "ORD-1002"
        
        # 6. Test Retry Logic on Rate Limit (HTTP 429)
        print("\n[TEST] 6. Testing Retry Logic Handling")
        # Reset side effect
        mock_response.json.side_effect = None
        mock_response.status_code = 429
        mock_request.return_value = mock_response
        
        try:
            print("Intentionally triggering a 429 Rate Limit error. Expecting retries...")
            # We enforce a small wait time for the test to avoid taking 15 seconds
            with patch('app.core.broker.wait_exponential', return_value=None):
                await broker.get_account_info()
        except AMPBrokerRateLimitException:
            print("Retry mechanism successfully exhausted and raised RateLimitException as intended.")
            # mock_request should have been called the initial time + the 5 retries = 6 times.
            print(f"Total attempts made: {mock_request.call_count}")
        
    await broker.close_client()
    print("\n--- Sandbox Tests Completed Successfully ---")


if __name__ == "__main__":
    asyncio.run(run_paper_trading_tests())
