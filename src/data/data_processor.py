"""
Data processing and ETL pipeline
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import logging
import json
import math
# from geopy.distance import geodesic  # Simplified for Windows compatibility

from ..models.database import (
    WeatherData, RiverGaugeData, SeismicData, 
    FloodPrediction, EarthquakePrediction, HistoricalDisaster
)

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and clean collected data"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        
    def process_weather_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Clean and validate weather data"""
        processed_data = []
        
        for record in raw_data:
            try:
                # Validate required fields
                if not all(key in record for key in ['latitude', 'longitude', 'timestamp']):
                    logger.warning(f"Skipping incomplete weather record: {record}")
                    continue
                
                # Clean and validate values
                processed_record = {
                    'timestamp': self._parse_timestamp(record['timestamp']),
                    'latitude': self._validate_latitude(record['latitude']),
                    'longitude': self._validate_longitude(record['longitude']),
                    'temperature': self._validate_temperature(record.get('temperature')),
                    'humidity': self._validate_humidity(record.get('humidity')),
                    'pressure': self._validate_pressure(record.get('pressure')),
                    'precipitation': self._validate_precipitation(record.get('precipitation')),
                    'wind_speed': self._validate_wind_speed(record.get('wind_speed')),
                    'wind_direction': self._validate_wind_direction(record.get('wind_direction')),
                    'visibility': self._validate_visibility(record.get('visibility')),
                    'source': record.get('source', 'unknown')
                }
                
                processed_data.append(processed_record)
                
            except Exception as e:
                logger.error(f"Error processing weather record: {e}")
                continue
        
        return processed_data
    
    def process_seismic_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Clean and validate seismic data"""
        processed_data = []
        
        for record in raw_data:
            try:
                # Validate required fields
                if not all(key in record for key in ['event_id', 'latitude', 'longitude', 'magnitude']):
                    logger.warning(f"Skipping incomplete seismic record: {record}")
                    continue
                
                processed_record = {
                    'event_id': str(record['event_id']),
                    'timestamp': self._parse_timestamp(record['timestamp']),
                    'latitude': self._validate_latitude(record['latitude']),
                    'longitude': self._validate_longitude(record['longitude']),
                    'magnitude': self._validate_magnitude(record['magnitude']),
                    'depth': self._validate_depth(record.get('depth')),
                    'magnitude_type': record.get('magnitude_type', 'unknown'),
                    'place': record.get('place', ''),
                    'source': record.get('source', 'unknown'),
                    'significance': record.get('significance')
                }
                
                processed_data.append(processed_record)
                
            except Exception as e:
                logger.error(f"Error processing seismic record: {e}")
                continue
        
        return processed_data
    
    def process_river_gauge_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Clean and validate river gauge data"""
        processed_data = []
        
        for record in raw_data:
            try:
                # Validate required fields
                if not all(key in record for key in ['gauge_id', 'latitude', 'longitude']):
                    logger.warning(f"Skipping incomplete gauge record: {record}")
                    continue
                
                processed_record = {
                    'gauge_id': str(record['gauge_id']),
                    'timestamp': self._parse_timestamp(record.get('timestamp', datetime.utcnow())),
                    'latitude': self._validate_latitude(record['latitude']),
                    'longitude': self._validate_longitude(record['longitude']),
                    'water_level': self._validate_water_level(record.get('water_level')),
                    'flow_rate': self._validate_flow_rate(record.get('flow_rate')),
                    'gauge_height': self._validate_gauge_height(record.get('gauge_height')),
                    'flood_stage': self._validate_flood_stage(record.get('flood_stage')),
                    'river_name': record.get('river_name', ''),
                    'station_name': record.get('station_name', '')
                }
                
                processed_data.append(processed_record)
                
            except Exception as e:
                logger.error(f"Error processing gauge record: {e}")
                continue
        
        return processed_data
    
    def aggregate_weather_data(self, data: List[Dict], 
                             location: Tuple[float, float], 
                             radius_km: float = 50) -> Dict:
        """Aggregate weather data for a location"""
        try:
            # Filter data within radius (simplified distance calculation)
            nearby_data = []
            for record in data:
                distance = self._calculate_distance(location, (record['latitude'], record['longitude']))
                if distance <= radius_km:
                    nearby_data.append(record)
            
            if not nearby_data:
                return {}
            
            # Calculate aggregates
            df = pd.DataFrame(nearby_data)
            
            aggregated = {
                'location': location,
                'count': len(nearby_data),
                'avg_temperature': df['temperature'].mean() if 'temperature' in df else None,
                'avg_humidity': df['humidity'].mean() if 'humidity' in df else None,
                'avg_pressure': df['pressure'].mean() if 'pressure' in df else None,
                'total_precipitation': df['precipitation'].sum() if 'precipitation' in df else None,
                'max_wind_speed': df['wind_speed'].max() if 'wind_speed' in df else None,
                'avg_visibility': df['visibility'].mean() if 'visibility' in df else None,
                'timestamp': datetime.utcnow()
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating weather data: {e}")
            return {}
    
    def detect_anomalies(self, data: List[Dict], data_type: str) -> List[Dict]:
        """Detect anomalies in the data"""
        try:
            if not data:
                return []
            
            df = pd.DataFrame(data)
            anomalies = []
            
            if data_type == 'weather':
                # Temperature anomalies
                if 'temperature' in df.columns:
                    temp_mean = df['temperature'].mean()
                    temp_std = df['temperature'].std()
                    temp_threshold = 3 * temp_std
                    
                    temp_anomalies = df[abs(df['temperature'] - temp_mean) > temp_threshold]
                    for _, row in temp_anomalies.iterrows():
                        anomalies.append({
                            'type': 'temperature_anomaly',
                            'value': row['temperature'],
                            'threshold': temp_threshold,
                            'location': (row['latitude'], row['longitude']),
                            'timestamp': row['timestamp']
                        })
                
                # Precipitation anomalies
                if 'precipitation' in df.columns:
                    precip_95th = df['precipitation'].quantile(0.95)
                    heavy_rain = df[df['precipitation'] > precip_95th]
                    
                    for _, row in heavy_rain.iterrows():
                        anomalies.append({
                            'type': 'heavy_precipitation',
                            'value': row['precipitation'],
                            'threshold': precip_95th,
                            'location': (row['latitude'], row['longitude']),
                            'timestamp': row['timestamp']
                        })
            
            elif data_type == 'seismic':
                # Magnitude anomalies
                if 'magnitude' in df.columns:
                    significant_earthquakes = df[df['magnitude'] >= 5.0]
                    
                    for _, row in significant_earthquakes.iterrows():
                        anomalies.append({
                            'type': 'significant_earthquake',
                            'value': row['magnitude'],
                            'threshold': 5.0,
                            'location': (row['latitude'], row['longitude']),
                            'timestamp': row['timestamp']
                        })
            
            elif data_type == 'river_gauge':
                # Water level anomalies
                if 'water_level' in df.columns and 'flood_stage' in df.columns:
                    flood_conditions = df[df['water_level'] > df['flood_stage']]
                    
                    for _, row in flood_conditions.iterrows():
                        anomalies.append({
                            'type': 'flood_stage_exceeded',
                            'value': row['water_level'],
                            'threshold': row['flood_stage'],
                            'location': (row['latitude'], row['longitude']),
                            'timestamp': row['timestamp']
                        })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two locations in kilometers using Haversine formula"""
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return 6371 * c  # Earth's radius in km

    # Validation helper methods
    def _parse_timestamp(self, timestamp) -> datetime:
        """Parse timestamp to datetime object"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            return datetime.utcnow()
    
    def _validate_latitude(self, lat) -> float:
        """Validate latitude value"""
        lat = float(lat)
        if -90 <= lat <= 90:
            return lat
        raise ValueError(f"Invalid latitude: {lat}")
    
    def _validate_longitude(self, lon) -> float:
        """Validate longitude value"""
        lon = float(lon)
        if -180 <= lon <= 180:
            return lon
        raise ValueError(f"Invalid longitude: {lon}")
    
    def _validate_temperature(self, temp) -> Optional[float]:
        """Validate temperature value"""
        if temp is None:
            return None
        temp = float(temp)
        if -100 <= temp <= 60:  # Reasonable range in Celsius
            return temp
        return None
    
    def _validate_humidity(self, humidity) -> Optional[float]:
        """Validate humidity value"""
        if humidity is None:
            return None
        humidity = float(humidity)
        if 0 <= humidity <= 100:
            return humidity
        return None
    
    def _validate_pressure(self, pressure) -> Optional[float]:
        """Validate pressure value"""
        if pressure is None:
            return None
        pressure = float(pressure)
        if 800 <= pressure <= 1200:  # Reasonable range in hPa
            return pressure
        return None
    
    def _validate_precipitation(self, precip) -> Optional[float]:
        """Validate precipitation value"""
        if precip is None:
            return None
        precip = float(precip)
        if precip >= 0:
            return precip
        return None
    
    def _validate_wind_speed(self, speed) -> Optional[float]:
        """Validate wind speed value"""
        if speed is None:
            return None
        speed = float(speed)
        if speed >= 0:
            return speed
        return None
    
    def _validate_wind_direction(self, direction) -> Optional[float]:
        """Validate wind direction value"""
        if direction is None:
            return None
        direction = float(direction)
        if 0 <= direction <= 360:
            return direction
        return None
    
    def _validate_visibility(self, visibility) -> Optional[float]:
        """Validate visibility value"""
        if visibility is None:
            return None
        visibility = float(visibility)
        if visibility >= 0:
            return visibility
        return None
    
    def _validate_magnitude(self, magnitude) -> float:
        """Validate earthquake magnitude"""
        magnitude = float(magnitude)
        if magnitude >= 0:
            return magnitude
        raise ValueError(f"Invalid magnitude: {magnitude}")
    
    def _validate_depth(self, depth) -> Optional[float]:
        """Validate earthquake depth"""
        if depth is None:
            return None
        depth = float(depth)
        if depth >= 0:
            return depth
        return None
    
    def _validate_water_level(self, level) -> Optional[float]:
        """Validate water level value"""
        if level is None:
            return None
        level = float(level)
        if level >= 0:
            return level
        return None
    
    def _validate_flow_rate(self, rate) -> Optional[float]:
        """Validate flow rate value"""
        if rate is None:
            return None
        rate = float(rate)
        if rate >= 0:
            return rate
        return None
    
    def _validate_gauge_height(self, height) -> Optional[float]:
        """Validate gauge height value"""
        if height is None:
            return None
        height = float(height)
        if height >= 0:
            return height
        return None
    
    def _validate_flood_stage(self, stage) -> Optional[float]:
        """Validate flood stage value"""
        if stage is None:
            return None
        stage = float(stage)
        if stage >= 0:
            return stage
        return None
