"""
Data collection from external APIs and sources
"""
import requests
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """Configuration for a data source"""
    name: str
    url: str
    api_key: Optional[str] = None
    update_interval: int = 3600  # seconds
    enabled: bool = True


class WeatherDataCollector:
    """Collect weather data from various APIs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
    
    async def get_current_weather(self, lat: float, lon: float) -> Dict:
        """Get current weather data for a location"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_weather_data(data, lat, lon)
                    else:
                        logger.error(f"Weather API error: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return {}
    
    async def get_weather_forecast(self, lat: float, lon: float, hours: int = 48) -> List[Dict]:
        """Get weather forecast data"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_forecast_data(data, lat, lon, hours)
                    else:
                        logger.error(f"Forecast API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching forecast data: {e}")
            return []
    
    def _parse_weather_data(self, data: Dict, lat: float, lon: float) -> Dict:
        """Parse weather API response"""
        try:
            main = data.get('main', {})
            weather = data.get('weather', [{}])[0]
            wind = data.get('wind', {})
            
            return {
                'timestamp': datetime.utcnow(),
                'latitude': lat,
                'longitude': lon,
                'temperature': main.get('temp'),
                'humidity': main.get('humidity'),
                'pressure': main.get('pressure'),
                'precipitation': data.get('rain', {}).get('1h', 0),
                'wind_speed': wind.get('speed'),
                'wind_direction': wind.get('deg'),
                'visibility': data.get('visibility', 0) / 1000,  # Convert to km
                'source': 'openweathermap'
            }
        except Exception as e:
            logger.error(f"Error parsing weather data: {e}")
            return {}
    
    def _parse_forecast_data(self, data: Dict, lat: float, lon: float, hours: int) -> List[Dict]:
        """Parse forecast API response"""
        try:
            forecasts = []
            forecast_list = data.get('list', [])
            
            for item in forecast_list[:hours//3]:  # 3-hour intervals
                main = item.get('main', {})
                weather = item.get('weather', [{}])[0]
                wind = item.get('wind', {})
                
                forecast = {
                    'timestamp': datetime.fromtimestamp(item.get('dt', 0)),
                    'latitude': lat,
                    'longitude': lon,
                    'temperature': main.get('temp'),
                    'humidity': main.get('humidity'),
                    'pressure': main.get('pressure'),
                    'precipitation': item.get('rain', {}).get('3h', 0),
                    'wind_speed': wind.get('speed'),
                    'wind_direction': wind.get('deg'),
                    'visibility': 10,  # Default visibility
                    'source': 'openweathermap_forecast'
                }
                forecasts.append(forecast)
            
            return forecasts
        except Exception as e:
            logger.error(f"Error parsing forecast data: {e}")
            return []


class SeismicDataCollector:
    """Collect seismic data from USGS and other sources"""
    
    def __init__(self):
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    async def get_recent_earthquakes(self, lat: float, lon: float, 
                                   radius_km: float = 500, 
                                   days: int = 30) -> List[Dict]:
        """Get recent earthquakes near a location"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            
            params = {
                'format': 'geojson',
                'latitude': lat,
                'longitude': lon,
                'maxradiuskm': radius_km,
                'starttime': start_time.isoformat(),
                'endtime': end_time.isoformat(),
                'minmagnitude': 2.0
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_seismic_data(data)
                    else:
                        logger.error(f"USGS API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching seismic data: {e}")
            return []
    
    def _parse_seismic_data(self, data: Dict) -> List[Dict]:
        """Parse USGS earthquake data"""
        try:
            earthquakes = []
            features = data.get('features', [])
            
            for feature in features:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coordinates = geometry.get('coordinates', [])
                
                if len(coordinates) >= 3:
                    earthquake = {
                        'event_id': properties.get('ids', '').split(',')[0],
                        'timestamp': datetime.fromtimestamp(properties.get('time', 0) / 1000),
                        'latitude': coordinates[1],
                        'longitude': coordinates[0],
                        'magnitude': properties.get('mag'),
                        'depth': coordinates[2],
                        'magnitude_type': properties.get('magType'),
                        'place': properties.get('place'),
                        'source': 'usgs',
                        'significance': properties.get('sig')
                    }
                    earthquakes.append(earthquake)
            
            return earthquakes
        except Exception as e:
            logger.error(f"Error parsing seismic data: {e}")
            return []


class RiverGaugeCollector:
    """Collect river gauge data from USGS Water Services"""
    
    def __init__(self):
        self.base_url = "https://waterservices.usgs.gov/nwis/iv"
    
    async def get_gauge_data(self, site_codes: List[str]) -> List[Dict]:
        """Get current river gauge readings"""
        try:
            params = {
                'format': 'json',
                'sites': ','.join(site_codes),
                'parameterCd': '00065,00060',  # Gauge height and discharge
                'period': 'P1D'  # Last 1 day
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_gauge_data(data)
                    else:
                        logger.error(f"USGS Water API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching gauge data: {e}")
            return []
    
    def _parse_gauge_data(self, data: Dict) -> List[Dict]:
        """Parse USGS water data"""
        try:
            gauge_readings = []
            time_series = data.get('value', {}).get('timeSeries', [])
            
            for series in time_series:
                site_info = series.get('sourceInfo', {})
                values = series.get('values', [{}])[0].get('value', [])
                
                if values:
                    latest_value = values[-1]
                    
                    gauge_reading = {
                        'gauge_id': site_info.get('siteCode', [{}])[0].get('value'),
                        'timestamp': datetime.fromisoformat(latest_value.get('dateTime', '').replace('Z', '+00:00')),
                        'latitude': float(site_info.get('geoLocation', {}).get('geogLocation', {}).get('latitude', 0)),
                        'longitude': float(site_info.get('geoLocation', {}).get('geogLocation', {}).get('longitude', 0)),
                        'water_level': float(latest_value.get('value', 0)),
                        'station_name': site_info.get('siteName'),
                        'river_name': site_info.get('siteName', '').split(' ')[0]  # Simplified
                    }
                    gauge_readings.append(gauge_reading)
            
            return gauge_readings
        except Exception as e:
            logger.error(f"Error parsing gauge data: {e}")
            return []


class DataCollectionManager:
    """Manage all data collection processes"""
    
    def __init__(self):
        self.weather_collector = WeatherDataCollector(os.getenv('OPENWEATHER_API_KEY', ''))
        self.seismic_collector = SeismicDataCollector()
        self.river_collector = RiverGaugeCollector()
        self.collection_tasks = []
    
    async def collect_all_data(self, locations: List[Dict]) -> Dict:
        """Collect data from all sources for given locations"""
        try:
            all_data = {
                'weather': [],
                'seismic': [],
                'river_gauge': []
            }
            
            tasks = []
            
            for location in locations:
                lat, lon = location['latitude'], location['longitude']
                
                # Weather data
                tasks.append(self.weather_collector.get_current_weather(lat, lon))
                
                # Seismic data
                tasks.append(self.seismic_collector.get_recent_earthquakes(lat, lon))
                
                # River gauge data (if site codes provided)
                if 'gauge_sites' in location:
                    tasks.append(self.river_collector.get_gauge_data(location['gauge_sites']))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Data collection task {i} failed: {result}")
                    continue
                
                # Categorize results based on task type
                if i % 3 == 0:  # Weather data
                    if result:
                        all_data['weather'].append(result)
                elif i % 3 == 1:  # Seismic data
                    all_data['seismic'].extend(result)
                else:  # River gauge data
                    all_data['river_gauge'].extend(result)
            
            return all_data

        except Exception as e:
            logger.error(f"Error in data collection: {e}")
            return {'weather': [], 'seismic': [], 'river_gauge': []}

    def start_scheduled_collection(self, locations: List[Dict], interval: int = 3600):
        """Start scheduled data collection"""
        import schedule
        import time
        import threading

        def collect_data():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                data = loop.run_until_complete(self.collect_all_data(locations))
                logger.info(f"Collected data: {len(data['weather'])} weather, {len(data['seismic'])} seismic, {len(data['river_gauge'])} gauge records")
            except Exception as e:
                logger.error(f"Scheduled collection error: {e}")

        schedule.every(interval).seconds.do(collect_data)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)

        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info(f"Started scheduled data collection every {interval} seconds")
