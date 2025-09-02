"""
FastAPI main application
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import os
from datetime import datetime, timedelta

from .database import get_db
# from .endpoints import predictions, data, alerts, dashboard  # Simplified for now
# from ..models.schemas import *  # Simplified for now

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Disaster Management Predictive Analytics API",
    description="API for flood and earthquake prediction and monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers (simplified for now)
# app.include_router(predictions.router, prefix="/api/v1/predictions", tags=["predictions"])
# app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
# app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
# app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Disaster Management Predictive Analytics API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow()
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/v1/status")
async def system_status():
    """Get system status and statistics"""
    try:
        return {
            "system_status": "operational",
            "data_counts": {
                "weather_records": 0,
                "seismic_records": 0,
                "flood_predictions": 0,
                "earthquake_predictions": 0,
                "active_alerts": 0
            },
            "recent_activity": {
                "weather_records_24h": 0,
                "seismic_records_24h": 0
            },
            "timestamp": datetime.utcnow(),
            "mode": "simplified"
        }

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system status")


@app.get("/dashboard/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard HTML"""
    try:
        from pathlib import Path
        dashboard_path = Path(__file__).parent.parent / "dashboard" / "index.html"

        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            return HTMLResponse(content=f"<h1>Dashboard not found</h1><p>Path: {dashboard_path}</p>")
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
