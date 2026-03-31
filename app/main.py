from fastapi import FastAPI
from datetime import datetime
from app.api.webhooks import router as webhook_router
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(webhook_router, tags=["Webhooks"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting up the {settings.PROJECT_NAME} Server")

@app.get("/health", tags=["System"])
async def health_check():
    """
    Basic health check for the server uptime.
    """
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/status", tags=["System"])
async def system_status():
    """
    Shows status of the last trade and general server stats (stub for MVP Phase 1).
    """
    return {
        "status": "active",
        "last_trade_time": None, # Will be updated in later phases
        "server_time": datetime.utcnow().isoformat(),
        "project": settings.PROJECT_NAME
    }
