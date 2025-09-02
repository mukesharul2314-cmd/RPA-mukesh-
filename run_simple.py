#!/usr/bin/env python3
"""
Simple startup script for disaster management system
"""
import os
import sys
import logging
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Also add current directory
current_path = str(Path(__file__).parent)
if current_path not in sys.path:
    sys.path.insert(0, current_path)

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables"""
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not installed, using system environment")
    
    # Set default values
    os.environ.setdefault("DATABASE_URL", "sqlite:///./disaster_analytics.db")
    os.environ.setdefault("DEBUG", "True")
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "8000")

def setup_database():
    """Initialize database"""
    try:
        from src.api.database import init_database
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.info("Continuing with in-memory database...")

def main():
    """Main function"""
    logger.info("🌊 Starting Disaster Management System (Simple Mode)...")
    
    # Setup environment
    setup_environment()
    
    # Setup database
    setup_database()
    
    # Import and run the FastAPI app
    try:
        import uvicorn
        from src.api.main import app
        
        host = os.getenv("API_HOST", "0.0.0.0")
        port = int(os.getenv("API_PORT", 8000))
        debug = os.getenv("DEBUG", "true").lower() == "true"
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info("Dashboard will be available at: http://localhost:8000/dashboard/")
        logger.info("API documentation at: http://localhost:8000/docs")
        
        # Run the application
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
