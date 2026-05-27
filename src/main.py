"""
FastAPI application factory and main entry point

Creates and configures the FastAPI application with all middleware,
error handlers, and route dependencies.
"""

from fastapi import FastAPI, APIRouter, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from typing import Optional
import logging

from src.core.config import get_settings
from src.core.logger import setup_logging, get_logger
from src.core.exceptions import ResearchAgentException
from src.data.database import init_database, close_database, get_async_session
from src.integration.chromadb_client import init_chromadb, close_chromadb
from src.integration.neo4j_client import init_neo4j, close_neo4j
from src.integration.redis_client import init_redis_cache, close_redis_cache
from src.integration.ollama_client import init_ollama, close_ollama
from schemas import ErrorResponse, ValidationErrorResponse, HealthResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management
    
    Startup: Initialize services and databases
    Shutdown: Cleanup resources
    """
    
    # =========== STARTUP ===========
    logger.info("🚀 Application starting up...")
    
    try:
        # Setup logging
        setup_logging(
            level=settings.logging.log_level,
            format_type=settings.logging.log_format,
            log_file=settings.logging.log_file,
        )
        logger.info("✓ Logging initialized")
        
        # Initialize database
        await init_database(
            database_url=settings.database.db_url,
            pool_size=settings.database.db_pool_size,
        )
        logger.info("✓ Database initialized")
        
        # Initialize ChromaDB
        await init_chromadb(
            host="localhost",
            port=8000,
            collection_name=settings.vector_store.collection_name,
            embedding_dim=settings.vector_store.dimension,
        )
        logger.info("✓ ChromaDB initialized")
        
        # Initialize Neo4j
        await init_neo4j(
            uri=settings.knowledge_graph.neo4j_uri or "bolt://localhost:7687",
            username=settings.knowledge_graph.neo4j_username or "neo4j",
            password=settings.knowledge_graph.neo4j_password or "neo4j",
            database=settings.knowledge_graph.database or "neo4j",
        )
        logger.info("✓ Neo4j initialized")
        
        # Initialize Redis
        await init_redis_cache(
            url="redis://localhost:6379/0",
            default_ttl=86400,
        )
        logger.info("✓ Redis initialized")
        
        # Initialize Ollama LLM
        await init_ollama(
            base_url=settings.ollama.base_url,
            model=settings.ollama.model,
            timeout=settings.ollama.timeout,
        )
        logger.info("✓ Ollama LLM initialized")
        
        logger.info("✅ Application startup complete")
    
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        raise
    
    yield  # Application runs here
    
    # =========== SHUTDOWN ===========
    logger.info("🛑 Application shutting down...")
    
    try:
        # Close Ollama connection
        await close_ollama()
        logger.info("✓ Ollama connection closed")
        
        # Close Redis connection
        await close_redis_cache()
        logger.info("✓ Redis connection closed")
        
        # Close Neo4j connection
        await close_neo4j()
        logger.info("✓ Neo4j connection closed")
        
        # Close ChromaDB connection
        await close_chromadb()
        logger.info("✓ ChromaDB connection closed")
        
        # Close database connections
        await close_database()
        logger.info("✓ Database connections closed")
        
        logger.info("✅ Application shutdown complete")
    
    except Exception as e:
        logger.error(f"✗ Shutdown failed: {e}", exc_info=True)


# =============================================================================
# ERROR HANDLERS
# =============================================================================

def setup_error_handlers(app: FastAPI) -> None:
    """Setup global error handlers"""
    
    @app.exception_handler(ResearchAgentException)
    async def research_agent_exception_handler(
        request: Request, exc: ResearchAgentException
    ):
        """Handle custom application exceptions"""
        logger.warning(
            f"Application error: {exc.code} - {exc.message}",
            extra={"path": request.url.path}
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": exc.message,
                "status_code": exc.status_code,
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """Handle Pydantic validation errors"""
        logger.warning(
            f"Validation error: {exc}",
            extra={"path": request.url.path}
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "status_code": 422,
                "errors": exc.errors(),
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(
            f"Unexpected error: {exc}",
            extra={"path": request.url.path},
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "status_code": 500,
            }
        )


# =============================================================================
# MIDDLEWARE SETUP
# =============================================================================

def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware"""
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins or ["*"],
        allow_credentials=settings.api.cors_credentials,
        allow_methods=settings.api.cors_methods,
        allow_headers=settings.api.cors_headers,
        expose_headers=["X-Total-Count", "X-Page", "X-Process-Time"],
        max_age=600,
    )
    
    # GZip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log incoming requests"""
        import time
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "client": request.client.host if request.client else None,
            }
        )
        
        return response


# =============================================================================
# ROUTES SETUP
# =============================================================================

def setup_routes(app: FastAPI) -> None:
    """Setup API routes"""
    
    # Health check endpoint (no auth required)
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            status="healthy",
            version=settings.api.api_version,
            environment=settings.environment,
        )
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint"""
        return {
            "message": "Deep Research Agent API",
            "version": settings.api.api_version,
            "docs": "/docs",
            "health": "/health",
        }
    
    # Include all API routes
    from src.api.routes import router as api_router
    app.include_router(api_router)


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI application
    """
    
    app = FastAPI(
        title=settings.api.api_title,
        description=settings.api.api_description,
        version=settings.api.api_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup error handlers
    setup_error_handlers(app)
    
    # Setup routes
    setup_routes(app)
    
    logger.info(f"✓ FastAPI application created for {settings.environment} environment")
    
    return app


# =============================================================================
# APPLICATION INSTANCE
# =============================================================================

app = create_app()


# =============================================================================
# UVICORN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.api.api_host,
        port=settings.api.api_port,
        workers=settings.api.api_workers,
        log_level=settings.logging.log_level.lower(),
        reload=settings.api.api_reload,
    )
