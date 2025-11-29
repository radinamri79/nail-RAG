"""
FastAPI main application for Nail RAG Service
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.startup_service import startup_service
from app.routes.chat_routes import router as chat_router
from app.routes.websocket_routes import router as websocket_router
from app.config import settings
from app.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application startup and shutdown.
    """
    # Startup
    logger.info("🚀 Starting Nail RAG Service application...")
    
    try:
        # Run comprehensive startup sequence
        logger.info("Running comprehensive startup sequence...")
        startup_results = await startup_service.run_startup_sequence()
        
        if startup_results.get("system_ready"):
            logger.info("✅ Nail RAG Service application started successfully")
            logger.info(f"⏱️ Startup completed in {startup_results.get('total_time', 0):.2f}s")
        else:
            logger.warning("⚠️ Nail RAG Service started in degraded mode")
            logger.warning(f"Startup results: {startup_results}")
            # Don't raise exception - allow app to start in degraded mode
            # Health check endpoint will show the status
        
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Nail RAG Service application...")
    
    try:
        # Close Weaviate client
        from app.models.weaviate_client import close_weaviate_client
        await close_weaviate_client()
        logger.info("✅ Weaviate client closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title="Nail RAG Service",
        description="RAG-based nail design advice service with GPT-5.1 and Weaviate",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Health check endpoint
    @app.get("/", tags=["health"])
    async def root() -> dict:
        """Health check endpoint"""
        return {
            "status": "ok",
            "service": "Nail RAG Service",
            "version": "1.0.0"
        }
    
    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Detailed health check"""
        system_status = startup_service.get_system_status()
        return {
            "status": "ok" if system_status["system_ready"] else "degraded",
            "system_ready": system_status["system_ready"],
            "components": system_status["components"]
        }
    
    # Include routers
    app.include_router(chat_router)
    app.include_router(websocket_router)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

