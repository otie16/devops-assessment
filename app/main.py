import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.config import settings
from app.logging_config import setup_logging
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, metrics_response
from app.routes.sample import router as sample_router

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)

APP_START_TIME = time.time()
APP_READY = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global APP_READY
    logger.info("Starting application")
    APP_READY = True
    yield
    APP_READY = False
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.middleware("http")
async def add_metrics_and_logging(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    path = request.url.path
    method = request.method

    logger.info(
        "Incoming request",
        extra={"request_id": request_id},
    )

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        status_code = 500
        logger.exception(
            "Unhandled exception during request",
            extra={"request_id": request_id},
        )
        REQUEST_COUNT.labels(
            method=method,
            endpoint=path,
            status_code=str(status_code),
        ).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=path).observe(time.time() - start_time)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
            },
        )

    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=method,
        endpoint=path,
        status_code=str(status_code),
    ).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=path).observe(duration)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        f"Request completed: {method} {path} {status_code} in {duration:.4f}s",
        extra={"request_id": request_id},
    )
    return response


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    if not APP_READY:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.get("/metrics")
def metrics():
    data, content_type = metrics_response()
    return Response(content=data, media_type=content_type)


@app.get("/info")
def info():
    uptime_seconds = int(time.time() - APP_START_TIME)
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": uptime_seconds,
    }


app.include_router(sample_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Global exception handler caught an error")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unexpected server error",
            "path": str(request.url.path),
        },
    )