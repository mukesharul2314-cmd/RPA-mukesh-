"""
Database models for disaster management system
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
# from geoalchemy2 import Geometry  # Commented out for Windows compatibility

Base = declarative_base()


class WeatherData(Base):
    """Weather data for flood prediction"""
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float)  # Celsius
    humidity = Column(Float)  # Percentage
    pressure = Column(Float)  # hPa
    precipitation = Column(Float)  # mm
    wind_speed = Column(Float)  # m/s
    wind_direction = Column(Float)  # degrees
    visibility = Column(Float)  # km
    source = Column(String(50))  # API source
    created_at = Column(DateTime, default=datetime.utcnow)


class RiverGaugeData(Base):
    """River gauge data for flood monitoring"""
    __tablename__ = "river_gauge_data"
    
    id = Column(Integer, primary_key=True, index=True)
    gauge_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    water_level = Column(Float)  # meters
    flow_rate = Column(Float)  # cubic meters per second
    gauge_height = Column(Float)  # meters
    flood_stage = Column(Float)  # meters
    river_name = Column(String(100))
    station_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class SeismicData(Base):
    """Seismic data for earthquake monitoring"""
    __tablename__ = "seismic_data"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    magnitude = Column(Float, nullable=False)
    depth = Column(Float)  # kilometers
    magnitude_type = Column(String(10))  # Mw, ML, etc.
    place = Column(String(200))
    source = Column(String(50))  # USGS, etc.
    significance = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class FloodPrediction(Base):
    """Flood prediction results"""
    __tablename__ = "flood_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    prediction_time = Column(DateTime, nullable=False)  # When prediction is for
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    flood_probability = Column(Float, nullable=False)  # 0-1
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Float)  # 0-1
    model_version = Column(String(50))
    features_used = Column(Text)  # JSON string of features
    created_at = Column(DateTime, default=datetime.utcnow)


class EarthquakePrediction(Base):
    """Earthquake risk assessment results"""
    __tablename__ = "earthquake_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    prediction_time = Column(DateTime, nullable=False)
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    risk_probability = Column(Float, nullable=False)  # 0-1
    estimated_magnitude = Column(Float)
    risk_level = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Float)  # 0-1
    model_version = Column(String(50))
    features_used = Column(Text)  # JSON string of features
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Alert notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(20), nullable=False)  # FLOOD, EARTHQUAKE
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    sent_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class HistoricalDisaster(Base):
    """Historical disaster records for training"""
    __tablename__ = "historical_disasters"
    
    id = Column(Integer, primary_key=True, index=True)
    disaster_type = Column(String(20), nullable=False)  # FLOOD, EARTHQUAKE
    event_date = Column(DateTime, nullable=False, index=True)
    # location = Column(Geometry('POINT'), nullable=False)  # Simplified for Windows
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    magnitude = Column(Float)  # For earthquakes
    severity = Column(String(20))  # LOW, MEDIUM, HIGH, CRITICAL
    affected_area = Column(Float)  # square kilometers
    casualties = Column(Integer)
    economic_damage = Column(Float)  # USD
    description = Column(Text)
    source = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
