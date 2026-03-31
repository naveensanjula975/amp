from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum
from datetime import datetime

class ActionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
    CLOSE_ALL = "close_all"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class WebhookPayload(BaseModel):
    secret: str = Field(..., description="Webhook verification secret")
    action: ActionType = Field(..., description="Trade action to perform")
    symbol: str = Field(..., description="Ticker symbol to trade")
    quantity: int = Field(..., gt=0, description="Number of contracts")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Type of order")
    
    price: Optional[float] = Field(None, description="Limit price (if order_type is limit)")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    
    strategy: Optional[str] = Field("Futures Automated Strategy MVP", description="Strategy identifier")
    timestamp: datetime = Field(..., description="Timestamp of the alert")
    
    # Validation logic for limit and stop orders
    @validator("price", always=True)
    def check_price(cls, v, values):
        if values.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("Limit orders require a 'price' field.")
        return v
    
    @validator("stop_loss", always=True)
    def check_stop_loss_if_stop_order(cls, v, values):
        # We also use stop_loss when placing bracket orders (SL/TP) but
        # if the main order_type is 'stop', it requires a stop price (we can map stop_loss or add stop_price).
        # In this schema, we map stop_loss to the stop_price if this is a dedicated 'stop' order type.
        if values.get("order_type") == OrderType.STOP and v is None:
            raise ValueError("Stop orders require a 'stop_loss' functioning as the stop price.")
        return v
