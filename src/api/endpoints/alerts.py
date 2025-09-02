"""
Alert API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ...models.schemas import AlertCreate, AlertResponse
from ...models.database import Alert

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    try:
        db_alert = Alert(**alert_data.dict())
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
        
        # Send alert in background
        background_tasks.add_task(send_alert_notification, db_alert)
        
        return db_alert
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Error creating alert")


@router.get("/", response_model=List[AlertResponse])
async def get_alerts(
    active_only: bool = True,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = 100,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filters"""
    try:
        query = db.query(Alert)
        
        # Active alerts only
        if active_only:
            query = query.filter(Alert.is_active == True)
            query = query.filter(
                (Alert.expires_at.is_(None)) | (Alert.expires_at > datetime.utcnow())
            )
        
        # Alert type filter
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type.upper())
        
        # Severity filter
        if severity:
            query = query.filter(Alert.severity == severity.upper())
        
        # Location filter
        if latitude is not None and longitude is not None:
            lat_range = radius_km / 111.0
            lon_range = radius_km / (111.0 * abs(latitude))
            
            query = query.filter(
                Alert.latitude.between(latitude - lat_range, latitude + lat_range),
                Alert.longitude.between(longitude - lon_range, longitude + lon_range)
            )
        
        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
        return alerts
        
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alerts")


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alert")


@router.put("/{alert_id}/deactivate")
async def deactivate_alert(alert_id: int, db: Session = Depends(get_db)):
    """Deactivate an alert"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.is_active = False
        db.commit()
        
        return {"message": "Alert deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deactivating alert")


@router.delete("/{alert_id}")
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        db.delete(alert)
        db.commit()
        
        return {"message": "Alert deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting alert")


@router.get("/statistics/summary")
async def get_alert_statistics(db: Session = Depends(get_db)):
    """Get alert statistics and summary"""
    try:
        # Total alerts
        total_alerts = db.query(Alert).count()
        active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
        
        # Alerts by type
        flood_alerts = db.query(Alert).filter(Alert.alert_type == 'FLOOD').count()
        earthquake_alerts = db.query(Alert).filter(Alert.alert_type == 'EARTHQUAKE').count()
        
        # Alerts by severity
        critical_alerts = db.query(Alert).filter(
            Alert.severity == 'CRITICAL',
            Alert.is_active == True
        ).count()
        high_alerts = db.query(Alert).filter(
            Alert.severity == 'HIGH',
            Alert.is_active == True
        ).count()
        
        # Recent alerts (last 24 hours)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = db.query(Alert).filter(Alert.created_at >= last_24h).count()
        
        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "alerts_by_type": {
                "flood": flood_alerts,
                "earthquake": earthquake_alerts
            },
            "active_by_severity": {
                "critical": critical_alerts,
                "high": high_alerts
            },
            "recent_24h": recent_alerts,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error retrieving alert statistics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving alert statistics")


async def send_alert_notification(alert: Alert):
    """Background task to send alert notifications"""
    try:
        # This would integrate with notification services (email, SMS, push notifications)
        logger.info(f"Sending alert notification: {alert.title} - {alert.severity}")
        
        # Example notification logic:
        # - Send email to subscribers
        # - Send SMS for critical alerts
        # - Push notifications to mobile apps
        # - Update external monitoring systems
        
        # Update alert as sent
        # alert.sent_at = datetime.utcnow()
        # db.commit()
        
    except Exception as e:
        logger.error(f"Error sending alert notification: {e}")
