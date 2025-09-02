"""
Prediction API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ...models.schemas import (
    PredictionRequest, FloodPredictionResponse, EarthquakePredictionResponse,
    FloodPredictionCreate, EarthquakePredictionCreate
)
from ...models.database import FloodPrediction, EarthquakePrediction, WeatherData, SeismicData, RiverGaugeData
from ...models.flood_predictor import FloodPredictor
from ...models.earthquake_predictor import EarthquakePredictor

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize predictors (in production, these would be loaded from saved models)
flood_predictor = FloodPredictor()
earthquake_predictor = EarthquakePredictor()


@router.post("/flood", response_model=FloodPredictionResponse)
async def predict_flood(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate flood prediction for a location"""
    try:
        # Get recent weather and river data for the location
        recent_time = datetime.utcnow() - timedelta(hours=72)
        
        # Query weather data within 50km radius (simplified)
        weather_data = db.query(WeatherData).filter(
            WeatherData.created_at >= recent_time,
            WeatherData.latitude.between(request.latitude - 0.5, request.latitude + 0.5),
            WeatherData.longitude.between(request.longitude - 0.5, request.longitude + 0.5)
        ).all()
        
        # Query river gauge data
        river_data = db.query(RiverGaugeData).filter(
            RiverGaugeData.created_at >= recent_time,
            RiverGaugeData.latitude.between(request.latitude - 0.5, request.latitude + 0.5),
            RiverGaugeData.longitude.between(request.longitude - 0.5, request.longitude + 0.5)
        ).all()
        
        # Convert to dictionaries
        weather_dict = [
            {
                'timestamp': w.timestamp,
                'temperature': w.temperature,
                'humidity': w.humidity,
                'pressure': w.pressure,
                'precipitation': w.precipitation,
                'wind_speed': w.wind_speed
            }
            for w in weather_data
        ]
        
        river_dict = [
            {
                'timestamp': r.timestamp,
                'water_level': r.water_level,
                'flow_rate': r.flow_rate,
                'gauge_height': r.gauge_height,
                'flood_stage': r.flood_stage
            }
            for r in river_data
        ]
        
        # Location data (would be enhanced with real GIS data)
        location_data = {
            'elevation': 100,  # Default values
            'slope': 0.1,
            'soil_type': 1,
            'land_use': 1
        }
        
        # Prepare features
        features = flood_predictor.prepare_features(weather_dict, river_dict, location_data)
        
        # Make prediction
        prediction_result = flood_predictor.predict(features)
        
        # Create prediction record
        prediction_time = datetime.utcnow() + timedelta(hours=request.hours_ahead)
        
        flood_prediction = FloodPrediction(
            prediction_time=prediction_time,
            latitude=request.latitude,
            longitude=request.longitude,
            flood_probability=prediction_result['flood_probability'],
            risk_level=prediction_result['risk_level'],
            confidence_score=prediction_result['confidence'],
            model_version="1.0",
            features_used=str(prediction_result['features_used'])
        )
        
        db.add(flood_prediction)
        db.commit()
        db.refresh(flood_prediction)
        
        # Schedule alert check in background
        if prediction_result['flood_probability'] > 0.7:
            background_tasks.add_task(check_flood_alert, request.latitude, request.longitude, prediction_result)
        
        return flood_prediction
        
    except Exception as e:
        logger.error(f"Error generating flood prediction: {e}")
        raise HTTPException(status_code=500, detail="Error generating flood prediction")


@router.post("/earthquake", response_model=EarthquakePredictionResponse)
async def predict_earthquake(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate earthquake risk assessment for a location"""
    try:
        # Get recent seismic data
        recent_time = datetime.utcnow() - timedelta(days=30)
        
        # Query seismic data within 500km radius
        seismic_data = db.query(SeismicData).filter(
            SeismicData.created_at >= recent_time,
            SeismicData.latitude.between(request.latitude - 5, request.latitude + 5),
            SeismicData.longitude.between(request.longitude - 5, request.longitude + 5)
        ).all()
        
        # Convert to dictionaries
        seismic_dict = [
            {
                'timestamp': s.timestamp,
                'latitude': s.latitude,
                'longitude': s.longitude,
                'magnitude': s.magnitude,
                'depth': s.depth
            }
            for s in seismic_data
        ]
        
        # Location data
        location_data = {
            'latitude': request.latitude,
            'longitude': request.longitude,
            'population_density': 100,  # Default values
            'elevation': 100,
            'slope': 0.1
        }
        
        # Prepare features
        features = earthquake_predictor.prepare_features(seismic_dict, location_data)
        
        # Make prediction
        prediction_result = earthquake_predictor.predict(features)
        
        # Create prediction record
        prediction_time = datetime.utcnow() + timedelta(hours=request.hours_ahead)
        
        earthquake_prediction = EarthquakePrediction(
            prediction_time=prediction_time,
            latitude=request.latitude,
            longitude=request.longitude,
            risk_probability=prediction_result['risk_probability'],
            estimated_magnitude=prediction_result['estimated_magnitude'],
            risk_level=prediction_result['risk_level'],
            confidence_score=prediction_result['confidence'],
            model_version="1.0",
            features_used=str(prediction_result['features_used'])
        )
        
        db.add(earthquake_prediction)
        db.commit()
        db.refresh(earthquake_prediction)
        
        # Schedule alert check in background
        if prediction_result['risk_probability'] > 0.8:
            background_tasks.add_task(check_earthquake_alert, request.latitude, request.longitude, prediction_result)
        
        return earthquake_prediction
        
    except Exception as e:
        logger.error(f"Error generating earthquake prediction: {e}")
        raise HTTPException(status_code=500, detail="Error generating earthquake prediction")


@router.get("/flood/recent", response_model=List[FloodPredictionResponse])
async def get_recent_flood_predictions(
    limit: int = 10,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 100,
    db: Session = Depends(get_db)
):
    """Get recent flood predictions"""
    try:
        query = db.query(FloodPrediction).order_by(FloodPrediction.created_at.desc())
        
        # Filter by location if provided
        if latitude is not None and longitude is not None:
            # Simple bounding box filter (would use PostGIS in production)
            lat_range = radius_km / 111.0  # Approximate km to degrees
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                FloodPrediction.latitude.between(latitude - lat_range, latitude + lat_range),
                FloodPrediction.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        predictions = query.limit(limit).all()
        return predictions
        
    except Exception as e:
        logger.error(f"Error retrieving flood predictions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving flood predictions")


@router.get("/earthquake/recent", response_model=List[EarthquakePredictionResponse])
async def get_recent_earthquake_predictions(
    limit: int = 10,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 100,
    db: Session = Depends(get_db)
):
    """Get recent earthquake predictions"""
    try:
        query = db.query(EarthquakePrediction).order_by(EarthquakePrediction.created_at.desc())
        
        # Filter by location if provided
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                EarthquakePrediction.latitude.between(latitude - lat_range, latitude + lat_range),
                EarthquakePrediction.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        predictions = query.limit(limit).all()
        return predictions
        
    except Exception as e:
        logger.error(f"Error retrieving earthquake predictions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving earthquake predictions")


async def check_flood_alert(latitude: float, longitude: float, prediction: dict):
    """Background task to check if flood alert should be sent"""
    # This would integrate with the alert system
    logger.info(f"Checking flood alert for {latitude}, {longitude}: {prediction['flood_probability']}")


async def check_earthquake_alert(latitude: float, longitude: float, prediction: dict):
    """Background task to check if earthquake alert should be sent"""
    # This would integrate with the alert system
    logger.info(f"Checking earthquake alert for {latitude}, {longitude}: {prediction['risk_probability']}")
