#!/usr/bin/env python3
"""
Database setup script for disaster management system
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import Base
from src.api.database import init_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_if_not_exists(database_url: str):
    """Create database if it doesn't exist"""
    try:
        # Parse database URL to get database name
        if 'postgresql' in database_url:
            # Extract database name from URL
            db_name = database_url.split('/')[-1]
            base_url = database_url.rsplit('/', 1)[0]
            
            # Connect to postgres database to create our database
            postgres_url = f"{base_url}/postgres"
            engine = create_engine(postgres_url)
            
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                    {"db_name": db_name}
                )
                
                if not result.fetchone():
                    # Create database
                    conn.execute(text("COMMIT"))  # End any transaction
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    logger.info(f"Database '{db_name}' created successfully")
                else:
                    logger.info(f"Database '{db_name}' already exists")
            
            engine.dispose()
            
        elif 'sqlite' in database_url:
            # SQLite databases are created automatically
            logger.info("Using SQLite database (will be created automatically)")
            
    except SQLAlchemyError as e:
        logger.error(f"Error creating database: {e}")
        raise


def setup_extensions(database_url: str):
    """Setup PostgreSQL extensions"""
    try:
        if 'postgresql' in database_url:
            engine = create_engine(database_url)
            
            with engine.connect() as conn:
                # Enable PostGIS extension for spatial data
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                    logger.info("PostGIS extension enabled")
                except SQLAlchemyError as e:
                    logger.warning(f"Could not enable PostGIS extension: {e}")
                
                # Enable other useful extensions
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_stat_statements"))
                    logger.info("pg_stat_statements extension enabled")
                except SQLAlchemyError as e:
                    logger.warning(f"Could not enable pg_stat_statements extension: {e}")
                
                conn.commit()
            
            engine.dispose()
            
    except SQLAlchemyError as e:
        logger.error(f"Error setting up extensions: {e}")
        raise


def create_indexes(database_url: str):
    """Create additional database indexes for performance"""
    try:
        engine = create_engine(database_url)
        
        indexes = [
            # Weather data indexes
            "CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_weather_created_at ON weather_data(created_at)",
            
            # Seismic data indexes
            "CREATE INDEX IF NOT EXISTS idx_seismic_timestamp ON seismic_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_seismic_location ON seismic_data(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_seismic_magnitude ON seismic_data(magnitude)",
            "CREATE INDEX IF NOT EXISTS idx_seismic_event_id ON seismic_data(event_id)",
            
            # River gauge data indexes
            "CREATE INDEX IF NOT EXISTS idx_gauge_timestamp ON river_gauge_data(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_gauge_location ON river_gauge_data(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_gauge_id ON river_gauge_data(gauge_id)",
            
            # Prediction indexes
            "CREATE INDEX IF NOT EXISTS idx_flood_pred_time ON flood_predictions(prediction_time)",
            "CREATE INDEX IF NOT EXISTS idx_flood_pred_location ON flood_predictions(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_earthquake_pred_time ON earthquake_predictions(prediction_time)",
            "CREATE INDEX IF NOT EXISTS idx_earthquake_pred_location ON earthquake_predictions(latitude, longitude)",
            
            # Alert indexes
            "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(alert_type)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_location ON alerts(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at)",
            
            # Historical disaster indexes
            "CREATE INDEX IF NOT EXISTS idx_historical_type ON historical_disasters(disaster_type)",
            "CREATE INDEX IF NOT EXISTS idx_historical_date ON historical_disasters(event_date)",
            "CREATE INDEX IF NOT EXISTS idx_historical_location ON historical_disasters(latitude, longitude)"
        ]
        
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Index created: {index_sql.split('idx_')[1].split(' ')[0]}")
                except SQLAlchemyError as e:
                    logger.warning(f"Could not create index: {e}")
            
            conn.commit()
        
        engine.dispose()
        logger.info("Database indexes created successfully")
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating indexes: {e}")
        raise


def insert_sample_data(database_url: str):
    """Insert sample data for testing"""
    try:
        from datetime import datetime, timedelta
        from src.models.database import (
            WeatherData, SeismicData, RiverGaugeData, 
            HistoricalDisaster, Alert
        )
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as db:
            # Sample weather data
            sample_weather = [
                WeatherData(
                    latitude=37.7749,
                    longitude=-122.4194,
                    temperature=20.5,
                    humidity=65.0,
                    pressure=1013.25,
                    precipitation=0.0,
                    wind_speed=5.2,
                    source="sample_data"
                ),
                WeatherData(
                    latitude=34.0522,
                    longitude=-118.2437,
                    temperature=25.0,
                    humidity=55.0,
                    pressure=1015.0,
                    precipitation=2.5,
                    wind_speed=8.1,
                    source="sample_data"
                )
            ]
            
            # Sample seismic data
            sample_seismic = [
                SeismicData(
                    event_id="sample_eq_001",
                    timestamp=datetime.utcnow() - timedelta(hours=2),
                    latitude=37.7749,
                    longitude=-122.4194,
                    magnitude=3.2,
                    depth=8.5,
                    magnitude_type="Mw",
                    place="San Francisco Bay Area",
                    source="sample_data"
                ),
                SeismicData(
                    event_id="sample_eq_002",
                    timestamp=datetime.utcnow() - timedelta(days=1),
                    latitude=34.0522,
                    longitude=-118.2437,
                    magnitude=4.1,
                    depth=12.3,
                    magnitude_type="Mw",
                    place="Los Angeles Area",
                    source="sample_data"
                )
            ]
            
            # Sample historical disasters
            sample_disasters = [
                HistoricalDisaster(
                    disaster_type="FLOOD",
                    event_date=datetime(2023, 1, 15),
                    latitude=37.7749,
                    longitude=-122.4194,
                    severity="HIGH",
                    affected_area=150.5,
                    casualties=0,
                    economic_damage=5000000.0,
                    description="Heavy rainfall caused flooding in downtown area",
                    source="sample_data"
                ),
                HistoricalDisaster(
                    disaster_type="EARTHQUAKE",
                    event_date=datetime(2022, 8, 20),
                    latitude=34.0522,
                    longitude=-118.2437,
                    magnitude=5.8,
                    severity="MEDIUM",
                    affected_area=500.0,
                    casualties=12,
                    economic_damage=25000000.0,
                    description="Moderate earthquake with minor structural damage",
                    source="sample_data"
                )
            ]
            
            # Add all sample data
            for data_list in [sample_weather, sample_seismic, sample_disasters]:
                db.add_all(data_list)
            
            db.commit()
            logger.info("Sample data inserted successfully")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise


def main():
    """Main setup function"""
    print("🗄️  Setting up Disaster Management Database...")
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    
    try:
        # Step 1: Create database if it doesn't exist
        logger.info("Step 1: Creating database...")
        create_database_if_not_exists(database_url)
        
        # Step 2: Setup extensions
        logger.info("Step 2: Setting up database extensions...")
        setup_extensions(database_url)
        
        # Step 3: Create tables
        logger.info("Step 3: Creating database tables...")
        init_database()
        
        # Step 4: Create indexes
        logger.info("Step 4: Creating database indexes...")
        create_indexes(database_url)
        
        # Step 5: Insert sample data (optional)
        if "--sample-data" in sys.argv:
            logger.info("Step 5: Inserting sample data...")
            insert_sample_data(database_url)
        
        print("✅ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the application: python -m src.main")
        print("2. Access the API docs: http://localhost:8000/docs")
        print("3. Access the dashboard: http://localhost:8000/dashboard/")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
