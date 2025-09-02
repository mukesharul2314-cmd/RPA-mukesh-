"""
Data API endpoints for weather, seismic, and river gauge data
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ...models.schemas import (
    WeatherDataCreate, WeatherDataResponse,
    SeismicDataCreate, SeismicDataResponse,
    RiverGaugeDataCreate, RiverGaugeDataResponse,
    HistoricalDisasterCreate, HistoricalDisasterResponse
)
from ...models.database import WeatherData, SeismicData, RiverGaugeData, HistoricalDisaster

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/weather", response_model=WeatherDataResponse)
async def create_weather_data(
    weather_data: WeatherDataCreate,
    db: Session = Depends(get_db)
):
    """Add new weather data record"""
    try:
        db_weather = WeatherData(**weather_data.dict())
        db.add(db_weather)
        db.commit()
        db.refresh(db_weather)
        return db_weather
    except Exception as e:
        logger.error(f"Error creating weather data: {e}")
        raise HTTPException(status_code=500, detail="Error creating weather data")


@router.get("/weather", response_model=List[WeatherDataResponse])
async def get_weather_data(
    latitude: Optional[float] = Query(None, description="Latitude for location filter"),
    longitude: Optional[float] = Query(None, description="Longitude for location filter"),
    radius_km: Optional[float] = Query(50, description="Radius in kilometers for location filter"),
    hours: Optional[int] = Query(24, description="Hours of historical data to retrieve"),
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get weather data with optional location and time filters"""
    try:
        query = db.query(WeatherData)
        
        # Time filter
        if hours:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(WeatherData.timestamp >= start_time)
        
        # Location filter (simplified bounding box)
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0  # Approximate km to degrees
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                WeatherData.latitude.between(latitude - lat_range, latitude + lat_range),
                WeatherData.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        weather_data = query.order_by(WeatherData.timestamp.desc()).limit(limit).all()
        return weather_data
        
    except Exception as e:
        logger.error(f"Error retrieving weather data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving weather data")


@router.post("/seismic", response_model=SeismicDataResponse)
async def create_seismic_data(
    seismic_data: SeismicDataCreate,
    db: Session = Depends(get_db)
):
    """Add new seismic data record"""
    try:
        db_seismic = SeismicData(**seismic_data.dict())
        db.add(db_seismic)
        db.commit()
        db.refresh(db_seismic)
        return db_seismic
    except Exception as e:
        logger.error(f"Error creating seismic data: {e}")
        raise HTTPException(status_code=500, detail="Error creating seismic data")


@router.get("/seismic", response_model=List[SeismicDataResponse])
async def get_seismic_data(
    latitude: Optional[float] = Query(None, description="Latitude for location filter"),
    longitude: Optional[float] = Query(None, description="Longitude for location filter"),
    radius_km: Optional[float] = Query(500, description="Radius in kilometers for location filter"),
    days: Optional[int] = Query(30, description="Days of historical data to retrieve"),
    min_magnitude: Optional[float] = Query(2.0, description="Minimum earthquake magnitude"),
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get seismic data with optional filters"""
    try:
        query = db.query(SeismicData)
        
        # Time filter
        if days:
            start_time = datetime.utcnow() - timedelta(days=days)
            query = query.filter(SeismicData.timestamp >= start_time)
        
        # Magnitude filter
        if min_magnitude:
            query = query.filter(SeismicData.magnitude >= min_magnitude)
        
        # Location filter
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                SeismicData.latitude.between(latitude - lat_range, latitude + lat_range),
                SeismicData.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        seismic_data = query.order_by(SeismicData.timestamp.desc()).limit(limit).all()
        return seismic_data
        
    except Exception as e:
        logger.error(f"Error retrieving seismic data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving seismic data")


@router.post("/river-gauge", response_model=RiverGaugeDataResponse)
async def create_river_gauge_data(
    gauge_data: RiverGaugeDataCreate,
    db: Session = Depends(get_db)
):
    """Add new river gauge data record"""
    try:
        db_gauge = RiverGaugeData(**gauge_data.dict())
        db.add(db_gauge)
        db.commit()
        db.refresh(db_gauge)
        return db_gauge
    except Exception as e:
        logger.error(f"Error creating river gauge data: {e}")
        raise HTTPException(status_code=500, detail="Error creating river gauge data")


@router.get("/river-gauge", response_model=List[RiverGaugeDataResponse])
async def get_river_gauge_data(
    gauge_id: Optional[str] = Query(None, description="Specific gauge ID"),
    latitude: Optional[float] = Query(None, description="Latitude for location filter"),
    longitude: Optional[float] = Query(None, description="Longitude for location filter"),
    radius_km: Optional[float] = Query(100, description="Radius in kilometers for location filter"),
    hours: Optional[int] = Query(24, description="Hours of historical data to retrieve"),
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get river gauge data with optional filters"""
    try:
        query = db.query(RiverGaugeData)
        
        # Gauge ID filter
        if gauge_id:
            query = query.filter(RiverGaugeData.gauge_id == gauge_id)
        
        # Time filter
        if hours:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(RiverGaugeData.timestamp >= start_time)
        
        # Location filter
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                RiverGaugeData.latitude.between(latitude - lat_range, latitude + lat_range),
                RiverGaugeData.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        gauge_data = query.order_by(RiverGaugeData.timestamp.desc()).limit(limit).all()
        return gauge_data
        
    except Exception as e:
        logger.error(f"Error retrieving river gauge data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving river gauge data")


@router.post("/historical-disasters", response_model=HistoricalDisasterResponse)
async def create_historical_disaster(
    disaster_data: HistoricalDisasterCreate,
    db: Session = Depends(get_db)
):
    """Add new historical disaster record"""
    try:
        db_disaster = HistoricalDisaster(**disaster_data.dict())
        db.add(db_disaster)
        db.commit()
        db.refresh(db_disaster)
        return db_disaster
    except Exception as e:
        logger.error(f"Error creating historical disaster record: {e}")
        raise HTTPException(status_code=500, detail="Error creating historical disaster record")


@router.get("/historical-disasters", response_model=List[HistoricalDisasterResponse])
async def get_historical_disasters(
    disaster_type: Optional[str] = Query(None, description="Type of disaster (FLOOD, EARTHQUAKE)"),
    latitude: Optional[float] = Query(None, description="Latitude for location filter"),
    longitude: Optional[float] = Query(None, description="Longitude for location filter"),
    radius_km: Optional[float] = Query(200, description="Radius in kilometers for location filter"),
    years: Optional[int] = Query(10, description="Years of historical data to retrieve"),
    limit: Optional[int] = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get historical disaster data with optional filters"""
    try:
        query = db.query(HistoricalDisaster)
        
        # Disaster type filter
        if disaster_type:
            query = query.filter(HistoricalDisaster.disaster_type == disaster_type.upper())
        
        # Time filter
        if years:
            start_time = datetime.utcnow() - timedelta(days=years * 365)
            query = query.filter(HistoricalDisaster.event_date >= start_time)
        
        # Location filter
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                HistoricalDisaster.latitude.between(latitude - lat_range, latitude + lat_range),
                HistoricalDisaster.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        disasters = query.order_by(HistoricalDisaster.event_date.desc()).limit(limit).all()
        return disasters
        
    except Exception as e:
        logger.error(f"Error retrieving historical disasters: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving historical disasters")


@router.get("/statistics")
async def get_data_statistics(db: Session = Depends(get_db)):
    """Get data statistics and summary"""
    try:
        # Count records by type
        weather_count = db.query(WeatherData).count()
        seismic_count = db.query(SeismicData).count()
        gauge_count = db.query(RiverGaugeData).count()
        disaster_count = db.query(HistoricalDisaster).count()
        
        # Recent activity (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_weather = db.query(WeatherData).filter(WeatherData.created_at >= last_24h).count()
        recent_seismic = db.query(SeismicData).filter(SeismicData.created_at >= last_24h).count()
        recent_gauge = db.query(RiverGaugeData).filter(RiverGaugeData.created_at >= last_24h).count()
        
        # Latest records
        latest_weather = db.query(WeatherData).order_by(WeatherData.timestamp.desc()).first()
        latest_seismic = db.query(SeismicData).order_by(SeismicData.timestamp.desc()).first()
        latest_gauge = db.query(RiverGaugeData).order_by(RiverGaugeData.timestamp.desc()).first()
        
        return {
            "total_records": {
                "weather": weather_count,
                "seismic": seismic_count,
                "river_gauge": gauge_count,
                "historical_disasters": disaster_count
            },
            "recent_activity_24h": {
                "weather": recent_weather,
                "seismic": recent_seismic,
                "river_gauge": recent_gauge
            },
            "latest_data": {
                "weather": latest_weather.timestamp if latest_weather else None,
                "seismic": latest_seismic.timestamp if latest_seismic else None,
                "river_gauge": latest_gauge.timestamp if latest_gauge else None
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving data statistics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving data statistics")
