"""
FastAPI Main Application
Compliant with all mandatory requirements
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import yaml
from pathlib import Path

from src.api.routes import visa_application, approval_workflow, session_management
from src.utils.logger import setup_logging, get_logger
from src.vector_store.milvus_client import MilvusClient
from src.api.routes.rag_routes import router as rag_router
 

# Load configuration
with open("config/api_config.yaml", 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Global resources
milvus_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global milvus_client
    
    # Startup
    logger.info("Starting Travel Visa Desk API")
    
    # Initialize Milvus connection
    try:
        milvus_client = MilvusClient()
        milvus_client.connect()
        logger.info("Connected to Milvus vector store")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {str(e)}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Travel Visa Desk API")
    if milvus_client:
        milvus_client.disconnect()
        logger.info("Disconnected from Milvus")


# Create FastAPI application
app = FastAPI(
    title=config['api']['title'],
    description=config['api']['description'],
    version=config['api']['version'],
    contact=config['api']['contact'],
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors']['allow_origins'],
    allow_credentials=config['cors']['allow_credentials'],
    allow_methods=config['cors']['allow_methods'],
    allow_headers=config['cors']['allow_headers'],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Travel Visa Desk API",
        "version": config['api']['version']
    }


# Include routers
app.include_router(visa_application.router)
app.include_router(approval_workflow.router)
app.include_router(session_management.router)
app.include_router(rag_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": config['api']['title'],
        "version": config['api']['version'],
        "description": config['api']['description'],
        "docs_url": "/docs",
        "health_check": "/health",
        "rag_knowledge_base": "/api/rag",
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=os.getenv("API_RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info")
    )
