"""
Dashboard API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ...models.schemas import DashboardData, AlertResponse
from ...models.database import (
    Alert, WeatherData, SeismicData, RiverGaugeData,
    FloodPrediction, EarthquakePrediction
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=DashboardData)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary data"""
    try:
        # Active alerts
        active_alerts = db.query(Alert).filter(
            Alert.is_active == True,
            (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.utcnow())
        ).order_by(Alert.created_at.desc()).limit(10).all()
        
        # Recent predictions
        recent_flood_predictions = db.query(FloodPrediction).order_by(
            FloodPrediction.created_at.desc()
        ).limit(5).all()
        
        recent_earthquake_predictions = db.query(EarthquakePrediction).order_by(
            EarthquakePrediction.created_at.desc()
        ).limit(5).all()
        
        recent_predictions = {
            "flood": [
                {
                    "id": p.id,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "probability": p.flood_probability,
                    "risk_level": p.risk_level,
                    "prediction_time": p.prediction_time,
                    "created_at": p.created_at
                }
                for p in recent_flood_predictions
            ],
            "earthquake": [
                {
                    "id": p.id,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "probability": p.risk_probability,
                    "estimated_magnitude": p.estimated_magnitude,
                    "risk_level": p.risk_level,
                    "prediction_time": p.prediction_time,
                    "created_at": p.created_at
                }
                for p in recent_earthquake_predictions
            ]
        }
        
        # Weather summary
        last_24h = datetime.utcnow() - timedelta(hours=24)
        weather_summary = get_weather_summary(db, last_24h)
        
        # Recent seismic activity
        recent_seismic = db.query(SeismicData).filter(
            SeismicData.timestamp >= last_24h
        ).order_by(SeismicData.timestamp.desc()).limit(10).all()
        
        seismic_activity = [
            {
                "id": s.id,
                "event_id": s.event_id,
                "timestamp": s.timestamp,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "magnitude": s.magnitude,
                "depth": s.depth,
                "place": s.place
            }
            for s in recent_seismic
        ]
        
        # System status
        system_status = get_system_status(db)
        
        return DashboardData(
            active_alerts=active_alerts,
            recent_predictions=recent_predictions,
            weather_summary=weather_summary,
            seismic_activity=seismic_activity,
            system_status=system_status
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving dashboard data")


@router.get("/map-data")
async def get_map_data(
    latitude: float,
    longitude: float,
    radius_km: float = 500,
    db: Session = Depends(get_db)
):
    """Get map data for a specific region"""
    try:
        # Calculate bounding box
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(latitude))
        
        # Recent earthquakes
        last_30d = datetime.utcnow() - timedelta(days=30)
        earthquakes = db.query(SeismicData).filter(
            SeismicData.timestamp >= last_30d,
            SeismicData.latitude.between(latitude - lat_range, latitude + lat_range),
            SeismicData.longitude.between(longitude - lon_range, longitude + lon_range)
        ).all()
        
        # Active alerts in region
        alerts = db.query(Alert).filter(
            Alert.is_active == True,
            Alert.latitude.between(latitude - lat_range, latitude + lat_range),
            Alert.longitude.between(longitude - lon_range, longitude + lon_range)
        ).all()
        
        # Recent predictions
        flood_predictions = db.query(FloodPrediction).filter(
            FloodPrediction.latitude.between(latitude - lat_range, latitude + lat_range),
            FloodPrediction.longitude.between(longitude - lon_range, longitude + lon_range),
            FloodPrediction.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        earthquake_predictions = db.query(EarthquakePrediction).filter(
            EarthquakePrediction.latitude.between(latitude - lat_range, latitude + lat_range),
            EarthquakePrediction.longitude.between(longitude - lon_range, longitude + lon_range),
            EarthquakePrediction.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).all()
        
        # River gauges
        gauges = db.query(RiverGaugeData).filter(
            RiverGaugeData.latitude.between(latitude - lat_range, latitude + lat_range),
            RiverGaugeData.longitude.between(longitude - lon_range, longitude + lon_range),
            RiverGaugeData.timestamp >= datetime.utcnow() - timedelta(hours=6)
        ).all()
        
        return {
            "earthquakes": [
                {
                    "id": eq.id,
                    "latitude": eq.latitude,
                    "longitude": eq.longitude,
                    "magnitude": eq.magnitude,
                    "depth": eq.depth,
                    "timestamp": eq.timestamp,
                    "place": eq.place
                }
                for eq in earthquakes
            ],
            "alerts": [
                {
                    "id": alert.id,
                    "latitude": alert.latitude,
                    "longitude": alert.longitude,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "title": alert.title,
                    "created_at": alert.created_at
                }
                for alert in alerts
            ],
            "flood_predictions": [
                {
                    "id": fp.id,
                    "latitude": fp.latitude,
                    "longitude": fp.longitude,
                    "probability": fp.flood_probability,
                    "risk_level": fp.risk_level,
                    "prediction_time": fp.prediction_time
                }
                for fp in flood_predictions
            ],
            "earthquake_predictions": [
                {
                    "id": ep.id,
                    "latitude": ep.latitude,
                    "longitude": ep.longitude,
                    "probability": ep.risk_probability,
                    "estimated_magnitude": ep.estimated_magnitude,
                    "risk_level": ep.risk_level,
                    "prediction_time": ep.prediction_time
                }
                for ep in earthquake_predictions
            ],
            "river_gauges": [
                {
                    "id": gauge.id,
                    "gauge_id": gauge.gauge_id,
                    "latitude": gauge.latitude,
                    "longitude": gauge.longitude,
                    "water_level": gauge.water_level,
                    "flood_stage": gauge.flood_stage,
                    "station_name": gauge.station_name,
                    "timestamp": gauge.timestamp
                }
                for gauge in gauges
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting map data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving map data")


@router.get("/analytics")
async def get_analytics_data(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics data for charts and graphs"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Alert trends
        alert_trends = db.query(
            func.date(Alert.created_at).label('date'),
            Alert.alert_type,
            func.count(Alert.id).label('count')
        ).filter(
            Alert.created_at >= start_date
        ).group_by(
            func.date(Alert.created_at),
            Alert.alert_type
        ).all()
        
        # Earthquake magnitude distribution
        earthquake_distribution = db.query(
            func.floor(SeismicData.magnitude).label('magnitude_range'),
            func.count(SeismicData.id).label('count')
        ).filter(
            SeismicData.timestamp >= start_date
        ).group_by(
            func.floor(SeismicData.magnitude)
        ).all()
        
        # Prediction accuracy (simplified)
        flood_predictions_count = db.query(FloodPrediction).filter(
            FloodPrediction.created_at >= start_date
        ).count()
        
        earthquake_predictions_count = db.query(EarthquakePrediction).filter(
            EarthquakePrediction.created_at >= start_date
        ).count()
        
        return {
            "alert_trends": [
                {
                    "date": str(trend.date),
                    "alert_type": trend.alert_type,
                    "count": trend.count
                }
                for trend in alert_trends
            ],
            "earthquake_distribution": [
                {
                    "magnitude_range": f"{int(dist.magnitude_range)}-{int(dist.magnitude_range)+1}",
                    "count": dist.count
                }
                for dist in earthquake_distribution
            ],
            "prediction_summary": {
                "flood_predictions": flood_predictions_count,
                "earthquake_predictions": earthquake_predictions_count,
                "period_days": days
            },
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics data")


def get_weather_summary(db: Session, since: datetime) -> Dict[str, Any]:
    """Get weather summary statistics"""
    try:
        weather_stats = db.query(
            func.avg(WeatherData.temperature).label('avg_temp'),
            func.avg(WeatherData.humidity).label('avg_humidity'),
            func.avg(WeatherData.pressure).label('avg_pressure'),
            func.sum(WeatherData.precipitation).label('total_precip'),
            func.max(WeatherData.wind_speed).label('max_wind'),
            func.count(WeatherData.id).label('record_count')
        ).filter(WeatherData.timestamp >= since).first()
        
        return {
            "average_temperature": float(weather_stats.avg_temp) if weather_stats.avg_temp else None,
            "average_humidity": float(weather_stats.avg_humidity) if weather_stats.avg_humidity else None,
            "average_pressure": float(weather_stats.avg_pressure) if weather_stats.avg_pressure else None,
            "total_precipitation": float(weather_stats.total_precip) if weather_stats.total_precip else 0,
            "max_wind_speed": float(weather_stats.max_wind) if weather_stats.max_wind else None,
            "record_count": weather_stats.record_count,
            "period": "24 hours"
        }
    except Exception as e:
        logger.error(f"Error getting weather summary: {e}")
        return {}


def get_system_status(db: Session) -> Dict[str, Any]:
    """Get system status information"""
    try:
        # Data freshness
        latest_weather = db.query(WeatherData).order_by(WeatherData.timestamp.desc()).first()
        latest_seismic = db.query(SeismicData).order_by(SeismicData.timestamp.desc()).first()
        latest_gauge = db.query(RiverGaugeData).order_by(RiverGaugeData.timestamp.desc()).first()
        
        # Active components
        active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
        
        return {
            "status": "operational",
            "data_freshness": {
                "weather": latest_weather.timestamp if latest_weather else None,
                "seismic": latest_seismic.timestamp if latest_seismic else None,
                "river_gauge": latest_gauge.timestamp if latest_gauge else None
            },
            "active_components": {
                "alerts": active_alerts,
                "prediction_models": 2,  # flood and earthquake
                "data_sources": 3  # weather, seismic, river
            },
            "last_updated": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {"status": "error", "last_updated": datetime.utcnow()}
