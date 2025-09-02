"""
Pydantic schemas for API requests and responses
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class WeatherDataCreate(LocationBase):
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(None, ge=0, le=100)
    pressure: Optional[float] = None
    precipitation: Optional[float] = Field(None, ge=0)
    wind_speed: Optional[float] = Field(None, ge=0)
    wind_direction: Optional[float] = Field(None, ge=0, le=360)
    visibility: Optional[float] = Field(None, ge=0)
    source: Optional[str] = None


class WeatherDataResponse(WeatherDataCreate):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RiverGaugeDataCreate(LocationBase):
    gauge_id: str
    water_level: Optional[float] = None
    flow_rate: Optional[float] = Field(None, ge=0)
    gauge_height: Optional[float] = None
    flood_stage: Optional[float] = None
    river_name: Optional[str] = None
    station_name: Optional[str] = None


class RiverGaugeDataResponse(RiverGaugeDataCreate):
    id: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SeismicDataCreate(LocationBase):
    event_id: str
    timestamp: datetime
    magnitude: float = Field(..., ge=0)
    depth: Optional[float] = Field(None, ge=0)
    magnitude_type: Optional[str] = None
    place: Optional[str] = None
    source: Optional[str] = None
    significance: Optional[int] = None


class SeismicDataResponse(SeismicDataCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionBase(LocationBase):
    prediction_time: datetime
    risk_level: str = Field(..., regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    model_version: Optional[str] = None


class FloodPredictionCreate(PredictionBase):
    flood_probability: float = Field(..., ge=0, le=1)


class FloodPredictionResponse(FloodPredictionCreate):
    id: int
    timestamp: datetime
    features_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EarthquakePredictionCreate(PredictionBase):
    risk_probability: float = Field(..., ge=0, le=1)
    estimated_magnitude: Optional[float] = Field(None, ge=0)


class EarthquakePredictionResponse(EarthquakePredictionCreate):
    id: int
    timestamp: datetime
    features_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(LocationBase):
    alert_type: str = Field(..., regex="^(FLOOD|EARTHQUAKE)$")
    severity: str = Field(..., regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    title: str = Field(..., max_length=200)
    message: str
    expires_at: Optional[datetime] = None


class AlertResponse(AlertCreate):
    id: int
    is_active: bool
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoricalDisasterCreate(LocationBase):
    disaster_type: str = Field(..., regex="^(FLOOD|EARTHQUAKE)$")
    event_date: datetime
    magnitude: Optional[float] = None
    severity: Optional[str] = Field(None, regex="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    affected_area: Optional[float] = Field(None, ge=0)
    casualties: Optional[int] = Field(None, ge=0)
    economic_damage: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    source: Optional[str] = None


class HistoricalDisasterResponse(HistoricalDisasterCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionRequest(LocationBase):
    """Request for getting predictions for a specific location"""
    hours_ahead: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week


class DashboardData(BaseModel):
    """Dashboard summary data"""
    active_alerts: List[AlertResponse]
    recent_predictions: dict
    weather_summary: dict
    seismic_activity: List[SeismicDataResponse]
    system_status: dict
