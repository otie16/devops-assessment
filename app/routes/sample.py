import logging
from fastapi import APIRouter, HTTPException
from app.metrics import BUSINESS_EVENT_COUNT

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/v1/sample")
def sample_endpoint():
    BUSINESS_EVENT_COUNT.labels(event_type="sample_hit").inc()
    logger.info("Sample endpoint called")
    return {
        "message": "Sample endpoint is working",
        "status": "success",
    }


@router.get("/api/v1/error")
def error_endpoint():
    logger.warning("Intentional error endpoint called")
    raise HTTPException(status_code=400, detail="Intentional test error")