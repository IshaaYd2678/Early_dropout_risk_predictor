"""
Production-ready FastAPI application with monitoring, logging, and error handling.
"""
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import uuid
import logging
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.production_config import settings
from src.core.logging_config import setup_logging, get_logger, RequestLogger
from src.api.v1.datasource import router as datasource_router
from ml.predict import DropoutRiskPredictor

# Setup logging
setup_logging(
    log_level=settings.log_level,
    log_file=settings.log_file,
    max_bytes=settings.log_max_bytes,
    backup_count=settings.log_backup_count,
    json_format=True
)

logger = get_logger(__name__)

# Global predictor instance
predictor: Optional[DropoutRiskPredictor] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Early Warning System API...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Load ML model
    global predictor
    try:
        if settings.enable_predictions:
            logger.info("Loading ML model...")
            predictor = DropoutRiskPredictor()
            logger.info("✅ ML model loaded successfully")
        else:
            logger.warning("Predictions disabled by feature flag")
    except Exception as e:
        logger.error(f"❌ Failed to load ML model: {e}", exc_info=True)
        if settings.app_env == "production":
            raise  # Fail fast in production
    
    logger.info("✅ Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Early Warning System API...")
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-ready Early Warning System for Student Dropout Risk",
    version="2.0.0",
    docs_url="/api/docs",   # always on so you can use the interactive UI
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Middleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host (security)
if settings.app_env == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domains
    )


# Request ID and logging middleware
@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    """Add request ID and log all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log request
        RequestLogger.log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id
        )
        
        return response
    
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "duration_ms": duration_ms,
                "error": str(e)
            },
            exc_info=True
        )
        raise


# Exception handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": request_id,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={"request_id": request_id, "path": request.url.path},
        exc_info=True
    )
    
    # Don't expose internal errors in production
    error_message = str(exc) if settings.debug else "Internal server error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": error_message,
            "request_id": request_id,
            "status_code": 500
        }
    )


# Health check endpoints

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "2.0.0",
        "model_loaded": predictor is not None,
        "features_enabled": {
            "predictions": settings.enable_predictions,
            "interventions": settings.enable_interventions,
            "analytics": settings.enable_analytics,
            "fairness_monitoring": settings.enable_fairness_monitoring
        }
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes."""
    if predictor is None and settings.enable_predictions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded"
        )
    
    return {
        "status": "ready",
        "model_loaded": predictor is not None
    }


@app.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}


# Metrics endpoint (Prometheus compatible)
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.prometheus_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    # TODO: Implement actual Prometheus metrics
    return {
        "message": "Metrics endpoint - integrate with prometheus_client library"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "environment": settings.app_env,
        "status": "operational",
        "docs": "/api/docs" if settings.debug else "disabled",
        "health": "/health"
    }


# Import and include routers
app.include_router(datasource_router)

# Uncomment when other routers are ready:
# from src.api.v1 import students, predictions, interventions, analytics
# app.include_router(students.router, prefix="/api/v1", tags=["Students"])
# app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
# app.include_router(interventions.router, prefix="/api/v1", tags=["Interventions"])
# app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.production_main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers if not settings.debug else 1,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )
