from fastapi import APIRouter, status, HTTPException
from typing import Dict
from datetime import datetime, timedelta
import hashlib
from app.schemas.payload import WebhookPayload
from app.core.security import validate_webhook_secret
from app.core.logger import logger
from app.core.broker import broker_client

router = APIRouter()

# In-memory deduplication cache: {hash_key: timestamp}
_dedup_cache: Dict[str, datetime] = {}
DEDUP_WINDOW_SECONDS = 5

def is_duplicate_alert(payload: WebhookPayload) -> bool:
    """
    Check if the exact same alert was received within the DEDUP_WINDOW_SECONDS.
    This prevents double-execution if TradingView fires the webhook twice accidentally.
    """
    global _dedup_cache
    
    # We create a unique hash for this specific signal
    # If TradingView sends the exact same alert, the payload dict will be identical
    # Note: we use symbol, action, and strategy to form the key
    raw_key = f"{payload.strategy}-{payload.symbol}-{payload.action.value}-{payload.quantity}"
    alert_hash = hashlib.md5(raw_key.encode()).hexdigest()
    
    now = datetime.utcnow()
    
    # Cleanup old entries to prevent memory leaks over time
    expired_keys = [k for k, v in _dedup_cache.items() if (now - v).total_seconds() > DEDUP_WINDOW_SECONDS]
    for k in expired_keys:
        del _dedup_cache[k]
        
    last_seen = _dedup_cache.get(alert_hash)
    if last_seen and (now - last_seen).total_seconds() < DEDUP_WINDOW_SECONDS:
        return True
        
    # Not a duplicate, add to cache
    _dedup_cache[alert_hash] = now
    return False


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def process_webhook(payload: WebhookPayload):
    """
    Endpoint to receive TradingView webhook alerts.
    Validates, deduplicates, and dispatches to the AMP broker client.
    """
    # 1. Validate the secret
    try:
        validate_webhook_secret(payload.secret)
    except Exception as e:
        logger.error(f"Webhook validation failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
        
    # 2. Duplicate Deduplication Logic
    if is_duplicate_alert(payload):
        logger.warning(f"DUPLICATE ALERT DETECTED. Ignoring {payload.action.value} for {payload.symbol}")
        return {"message": "Duplicate alert ignored", "status": "ignored"}

    logger.info(f"Processing new alert: {payload.action.value} {payload.quantity} {payload.symbol}")
    logger.debug(f"Payload specifics: {payload.model_dump()}")

    # 3. Dispatch to Broker API
    try:
        # Route to the appropriate broker command
        if payload.action.value == "close":
            broker_resp = await broker_client.close_position(payload.symbol)
        elif payload.action.value == "close_all":
            # For MVP: Simplification just attempting to close the symbol requested 
            # (assuming 1 instrument traded at a time)
            broker_resp = await broker_client.close_position(payload.symbol)
        else:
            # It's a buy/sell order
            broker_resp = await broker_client.place_order(
                symbol=payload.symbol,
                side=payload.action.value,
                quantity=payload.quantity,
                order_type=payload.order_type.value,
                price=payload.price,
                stop_price=payload.stop_loss  # We map stop_loss to the limit/stop system
            )
            
        logger.info(f"Broker command successful: {broker_resp}")
        return {
            "message": "Order executed successfully", 
            "status": "success", 
            "broker_response": broker_resp
        }
    except Exception as e:
        logger.error(f"Broker Execution Failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Broker integration error: {str(e)}")
