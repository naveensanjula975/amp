from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logger import logger

def validate_webhook_secret(payload_secret: str) -> bool:
    """
    Validates the secret sent in the JSON payload from the webhook.
    Raises HTTPException if invalid.
    """
    if payload_secret != settings.WEBHOOK_SECRET:
        logger.warning("Unauthorized webhook attempt with invalid secret.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret",
        )
    return True
