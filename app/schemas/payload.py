from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class ActionEnum(str, Enum):
    buy = "buy"
    sell = "sell"
    close = "close"
    close_all = "close_all"

class OrderTypeEnum(str, Enum):
    market = "market"
    limit = "limit"
    stop = "stop"

class WebhookPayload(BaseModel):
    secret: str = Field(..., description="Webhook secret token for validation")
    action: ActionEnum = Field(..., description="Trading action")
    symbol: str = Field(..., description="Futures symbol, e.g., ES or NQ")
    quantity: int = Field(default=1, description="Number of contracts")
    order_type: OrderTypeEnum = Field(default=OrderTypeEnum.market, description="Market, limit, or stop")
    price: Optional[float] = Field(default=None, description="Limit/Stop price")
    stop_loss: Optional[float] = Field(default=None, description="Stop loss price")
    take_profit: Optional[float] = Field(default=None, description="Take profit price")
    strategy: Optional[str] = Field(default=None, description="Strategy name for logging purposes")
    timestamp: Optional[datetime] = Field(default=None, description="Time the alert was fired")
