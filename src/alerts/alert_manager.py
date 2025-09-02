"""
Alert management system for disaster predictions
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from .notification_service import NotificationService, AlertNotification, NotificationRecipient
from ..models.database import Alert, FloodPrediction, EarthquakePrediction, WeatherData, SeismicData
from ..models.schemas import AlertCreate

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert generation, processing, and notifications"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.notification_service = NotificationService()
        self.alert_thresholds = self._load_alert_thresholds()
        self.active_alerts = {}  # Cache of active alerts
        
        # Load default recipients
        self._load_default_recipients()
    
    def _load_alert_thresholds(self) -> Dict:
        """Load alert thresholds configuration"""
        return {
            'flood': {
                'low': 0.3,
                'medium': 0.5,
                'high': 0.7,
                'critical': 0.85
            },
            'earthquake': {
                'low': 0.2,
                'medium': 0.4,
                'high': 0.6,
                'critical': 0.8
            },
            'weather': {
                'heavy_rain_mm': 50,  # mm in 24 hours
                'extreme_wind_ms': 25,  # m/s
                'temperature_extreme_c': 45  # Celsius
            },
            'seismic': {
                'significant_magnitude': 5.0,
                'major_magnitude': 6.0,
                'great_magnitude': 7.0
            }
        }
    
    def _load_default_recipients(self):
        """Load default notification recipients"""
        # In production, this would load from database or configuration
        default_recipients = [
            NotificationRecipient(
                name="Emergency Management",
                email="emergency@disaster-management.com",
                phone="+1234567890"
            ),
            NotificationRecipient(
                name="Weather Service",
                email="weather@disaster-management.com"
            )
        ]
        
        for recipient in default_recipients:
            self.notification_service.add_recipient(recipient)
    
    async def process_prediction_alerts(self):
        """Process predictions and generate alerts if thresholds are exceeded"""
        try:
            with Session(self.engine) as db:
                # Check recent flood predictions
                await self._check_flood_predictions(db)
                
                # Check recent earthquake predictions
                await self._check_earthquake_predictions(db)
                
                # Check weather conditions
                await self._check_weather_conditions(db)
                
                # Check seismic activity
                await self._check_seismic_activity(db)
                
        except Exception as e:
            logger.error(f"Error processing prediction alerts: {e}")
    
    async def _check_flood_predictions(self, db: Session):
        """Check flood predictions for alert conditions"""
        try:
            # Get recent flood predictions
            recent_time = datetime.utcnow() - timedelta(hours=1)
            predictions = db.query(FloodPrediction).filter(
                FloodPrediction.created_at >= recent_time,
                FloodPrediction.flood_probability >= self.alert_thresholds['flood']['low']
            ).all()
            
            for prediction in predictions:
                # Check if alert already exists for this location
                alert_key = f"flood_{prediction.latitude}_{prediction.longitude}"
                
                if alert_key in self.active_alerts:
                    continue
                
                # Determine severity based on probability
                severity = self._get_flood_severity(prediction.flood_probability)
                
                if severity:
                    await self._create_and_send_alert(
                        alert_type="FLOOD",
                        severity=severity,
                        title=f"Flood Warning - {severity} Risk",
                        message=f"Flood prediction indicates {severity.lower()} risk with {prediction.flood_probability*100:.1f}% probability. "
                               f"Prediction valid until {prediction.prediction_time.strftime('%Y-%m-%d %H:%M')}.",
                        latitude=prediction.latitude,
                        longitude=prediction.longitude,
                        expires_at=prediction.prediction_time + timedelta(hours=6),
                        metadata={
                            'prediction_id': prediction.id,
                            'probability': prediction.flood_probability,
                            'confidence': prediction.confidence_score
                        },
                        db=db
                    )
                    
                    self.active_alerts[alert_key] = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"Error checking flood predictions: {e}")
    
    async def _check_earthquake_predictions(self, db: Session):
        """Check earthquake predictions for alert conditions"""
        try:
            recent_time = datetime.utcnow() - timedelta(hours=1)
            predictions = db.query(EarthquakePrediction).filter(
                EarthquakePrediction.created_at >= recent_time,
                EarthquakePrediction.risk_probability >= self.alert_thresholds['earthquake']['low']
            ).all()
            
            for prediction in predictions:
                alert_key = f"earthquake_{prediction.latitude}_{prediction.longitude}"
                
                if alert_key in self.active_alerts:
                    continue
                
                severity = self._get_earthquake_severity(prediction.risk_probability)
                
                if severity:
                    await self._create_and_send_alert(
                        alert_type="EARTHQUAKE",
                        severity=severity,
                        title=f"Earthquake Risk Alert - {severity} Risk",
                        message=f"Earthquake risk assessment indicates {severity.lower()} risk with {prediction.risk_probability*100:.1f}% probability. "
                               f"Estimated magnitude: M{prediction.estimated_magnitude:.1f}. "
                               f"Assessment valid until {prediction.prediction_time.strftime('%Y-%m-%d %H:%M')}.",
                        latitude=prediction.latitude,
                        longitude=prediction.longitude,
                        expires_at=prediction.prediction_time + timedelta(hours=24),
                        metadata={
                            'prediction_id': prediction.id,
                            'probability': prediction.risk_probability,
                            'estimated_magnitude': prediction.estimated_magnitude,
                            'confidence': prediction.confidence_score
                        },
                        db=db
                    )
                    
                    self.active_alerts[alert_key] = datetime.utcnow()
                    
        except Exception as e:
            logger.error(f"Error checking earthquake predictions: {e}")
    
    async def _check_weather_conditions(self, db: Session):
        """Check current weather conditions for extreme events"""
        try:
            recent_time = datetime.utcnow() - timedelta(hours=1)
            weather_data = db.query(WeatherData).filter(
                WeatherData.timestamp >= recent_time
            ).all()
            
            for weather in weather_data:
                alerts_to_create = []
                
                # Check for heavy precipitation
                if weather.precipitation and weather.precipitation >= self.alert_thresholds['weather']['heavy_rain_mm']:
                    alerts_to_create.append({
                        'type': 'FLOOD',
                        'severity': 'HIGH' if weather.precipitation >= 100 else 'MEDIUM',
                        'title': 'Heavy Rainfall Alert',
                        'message': f'Heavy rainfall detected: {weather.precipitation:.1f}mm. Flood risk increased.'
                    })
                
                # Check for extreme wind
                if weather.wind_speed and weather.wind_speed >= self.alert_thresholds['weather']['extreme_wind_ms']:
                    severity = 'CRITICAL' if weather.wind_speed >= 35 else 'HIGH'
                    alerts_to_create.append({
                        'type': 'WEATHER',
                        'severity': severity,
                        'title': 'Extreme Wind Alert',
                        'message': f'Extreme wind conditions: {weather.wind_speed:.1f} m/s. Take shelter immediately.'
                    })
                
                # Check for extreme temperature
                if weather.temperature and abs(weather.temperature) >= self.alert_thresholds['weather']['temperature_extreme_c']:
                    alerts_to_create.append({
                        'type': 'WEATHER',
                        'severity': 'HIGH',
                        'title': 'Extreme Temperature Alert',
                        'message': f'Extreme temperature: {weather.temperature:.1f}°C. Take appropriate precautions.'
                    })
                
                # Create alerts
                for alert_data in alerts_to_create:
                    alert_key = f"weather_{weather.latitude}_{weather.longitude}_{alert_data['type']}"
                    
                    if alert_key not in self.active_alerts:
                        await self._create_and_send_alert(
                            alert_type=alert_data['type'],
                            severity=alert_data['severity'],
                            title=alert_data['title'],
                            message=alert_data['message'],
                            latitude=weather.latitude,
                            longitude=weather.longitude,
                            expires_at=datetime.utcnow() + timedelta(hours=6),
                            metadata={'weather_id': weather.id},
                            db=db
                        )
                        
                        self.active_alerts[alert_key] = datetime.utcnow()
                        
        except Exception as e:
            logger.error(f"Error checking weather conditions: {e}")
    
    async def _check_seismic_activity(self, db: Session):
        """Check recent seismic activity for significant events"""
        try:
            recent_time = datetime.utcnow() - timedelta(hours=1)
            earthquakes = db.query(SeismicData).filter(
                SeismicData.timestamp >= recent_time,
                SeismicData.magnitude >= self.alert_thresholds['seismic']['significant_magnitude']
            ).all()
            
            for earthquake in earthquakes:
                alert_key = f"seismic_{earthquake.event_id}"
                
                if alert_key in self.active_alerts:
                    continue
                
                # Determine severity based on magnitude
                if earthquake.magnitude >= self.alert_thresholds['seismic']['great_magnitude']:
                    severity = 'CRITICAL'
                elif earthquake.magnitude >= self.alert_thresholds['seismic']['major_magnitude']:
                    severity = 'HIGH'
                else:
                    severity = 'MEDIUM'
                
                await self._create_and_send_alert(
                    alert_type="EARTHQUAKE",
                    severity=severity,
                    title=f"Earthquake Detected - M{earthquake.magnitude:.1f}",
                    message=f"Earthquake detected: M{earthquake.magnitude:.1f} at depth {earthquake.depth:.1f}km. "
                           f"Location: {earthquake.place or 'Unknown'}. "
                           f"Time: {earthquake.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC.",
                    latitude=earthquake.latitude,
                    longitude=earthquake.longitude,
                    expires_at=datetime.utcnow() + timedelta(hours=12),
                    metadata={
                        'earthquake_id': earthquake.id,
                        'event_id': earthquake.event_id,
                        'magnitude': earthquake.magnitude,
                        'depth': earthquake.depth
                    },
                    db=db
                )
                
                self.active_alerts[alert_key] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error checking seismic activity: {e}")
    
    async def _create_and_send_alert(self, alert_type: str, severity: str, title: str, 
                                   message: str, latitude: float, longitude: float,
                                   expires_at: datetime, metadata: Dict, db: Session):
        """Create alert in database and send notifications"""
        try:
            # Create alert in database
            alert_create = AlertCreate(
                alert_type=alert_type,
                severity=severity,
                latitude=latitude,
                longitude=longitude,
                title=title,
                message=message,
                expires_at=expires_at
            )
            
            db_alert = Alert(**alert_create.dict())
            db.add(db_alert)
            db.commit()
            db.refresh(db_alert)
            
            # Create notification
            notification = AlertNotification(
                title=title,
                message=message,
                severity=severity,
                alert_type=alert_type,
                location={'lat': latitude, 'lon': longitude},
                expires_at=expires_at,
                metadata=metadata
            )
            
            # Send notification
            await self.notification_service.send_alert(notification)
            
            # Update alert as sent
            db_alert.sent_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Alert created and sent: {title} ({severity})")
            
        except Exception as e:
            logger.error(f"Error creating and sending alert: {e}")
            raise
    
    def _get_flood_severity(self, probability: float) -> Optional[str]:
        """Determine flood alert severity based on probability"""
        thresholds = self.alert_thresholds['flood']
        
        if probability >= thresholds['critical']:
            return 'CRITICAL'
        elif probability >= thresholds['high']:
            return 'HIGH'
        elif probability >= thresholds['medium']:
            return 'MEDIUM'
        elif probability >= thresholds['low']:
            return 'LOW'
        
        return None
    
    def _get_earthquake_severity(self, probability: float) -> Optional[str]:
        """Determine earthquake alert severity based on probability"""
        thresholds = self.alert_thresholds['earthquake']
        
        if probability >= thresholds['critical']:
            return 'CRITICAL'
        elif probability >= thresholds['high']:
            return 'HIGH'
        elif probability >= thresholds['medium']:
            return 'MEDIUM'
        elif probability >= thresholds['low']:
            return 'LOW'
        
        return None
    
    def cleanup_expired_alerts(self):
        """Clean up expired alerts from cache"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, created_time in self.active_alerts.items():
            if current_time - created_time > timedelta(hours=24):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.active_alerts[key]
        
        logger.info(f"Cleaned up {len(expired_keys)} expired alert cache entries")
    
    async def start_monitoring(self, interval_seconds: int = 300):
        """Start continuous monitoring for alert conditions"""
        logger.info(f"Starting alert monitoring with {interval_seconds}s interval")
        
        while True:
            try:
                await self.process_prediction_alerts()
                self.cleanup_expired_alerts()
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
