"""
FastAPI application factory and setup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.core.config import get_config
from src.core.logger import get_logger, setup_logging
from src.api.routes import router

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    config = get_config()

    # Setup logging
    setup_logging(
        log_level=config.logging.level,
        log_file=config.logging.file,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan context manager."""
        logger.info("Starting Deep Research Agent API")
        yield
        logger.info("Shutting down Deep Research Agent API")

    # Create app instance
    app = FastAPI(
        title="Deep Research Agent API",
        description="Production-grade autonomous research platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Add middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router)

    # Add startup/shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Startup event."""
        logger.info("API startup complete")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event."""
        logger.info("API shutdown complete")

    return app


# Create default app instance
app = create_app()
