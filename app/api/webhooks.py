from fastapi import APIRouter, status
from app.schemas.payload import WebhookPayload
from app.core.security import validate_webhook_secret
from app.core.logger import logger

router = APIRouter()

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def process_webhook(payload: WebhookPayload):
    """
    Endpoint to receive TradingView webhook alerts.
    """
    # 1. Validate the secret
    validate_webhook_secret(payload.secret)
    
    # 2. Log exactly what we received
    logger.info(f"Received valid webhook payload for action: {payload.action.value} on {payload.symbol}")
    logger.debug(f"Payload details: {payload.model_dump()}")

    # 3. TODO: In Phase 2, this section will dispatch the order to the broker.py module

    return {"message": "Webhook received successfully", "status": "success"}
