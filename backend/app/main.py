"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.database import Base, async_engine
from app.core.redis import close_redis, get_redis
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    print("🚀 Starting SEO SaaS application...")

    # Initialize database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Test Redis connection
    redis = await get_redis()
    await redis.ping()
    print("✓ Redis connected")

    print(f"✓ Application started (Environment: {settings.ENVIRONMENT})")

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_redis()
    await async_engine.dispose()
    print("✓ Application stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SEO SaaS Tool - Complete SEO analysis and optimization platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Prometheus metrics endpoint
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check with dependencies."""
    health_status = {
        "status": "healthy",
        "api": "operational",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        health_status["redis"] = "operational"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Database
    try:
        from sqlalchemy import text

        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["database"] = "operational"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
    )
