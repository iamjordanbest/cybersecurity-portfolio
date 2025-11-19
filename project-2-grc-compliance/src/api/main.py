"""
GRC Analytics Platform API - Main Application

FastAPI application providing REST API access to GRC analytics.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import logging

from src.api.routers import frameworks, controls, compliance, risk, mappings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GRC Analytics API",
    description="REST API for GRC Analytics Platform - Multi-Framework Compliance Management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
from src.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(frameworks.router, prefix="/api/v1/frameworks", tags=["Frameworks"])
app.include_router(controls.router, prefix="/api/v1/controls", tags=["Controls"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["Compliance"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["Risk"])
app.include_router(mappings.router, prefix="/api/v1/mappings", tags=["Mappings"])


@app.get("/")
def root():
    """Root endpoint - API information."""
    return {
        "name": "GRC Analytics API",
        "version": "1.0.0",
        "description": "Multi-Framework Compliance Management API",
        "documentation": "/api/docs",
        "frameworks_supported": ["NIST-800-53", "ISO-27001", "CIS", "PCI-DSS", "SOC2"]
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "timestamp": "2025-01-01T00:00:00Z"
    }


@app.get("/api/v1/info")
def api_info():
    """Get API information and statistics."""
    # TODO: Get from database
    return {
        "frameworks": 5,
        "total_controls": 1359,
        "total_mappings": 139,
        "api_endpoints": 30,
        "status": "operational"
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
