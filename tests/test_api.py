"""
Tests for API endpoints
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from src.api.main import app
from src.api.database import get_db
from src.models.database import Base, WeatherData, SeismicData, FloodPrediction, EarthquakePrediction, Alert


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create database session for testing"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestHealthEndpoints:
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    def test_system_status(self, client):
        """Test system status endpoint"""
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "system_status" in data
        assert "data_counts" in data
        assert "recent_activity" in data


class TestDataEndpoints:
    
    def test_create_weather_data(self, client):
        """Test creating weather data"""
        weather_data = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "temperature": 20.5,
            "humidity": 65.0,
            "pressure": 1013.25,
            "precipitation": 0.0,
            "wind_speed": 5.2,
            "wind_direction": 180.0,
            "visibility": 10.0,
            "source": "test"
        }
        
        response = client.post("/api/v1/data/weather", json=weather_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["latitude"] == weather_data["latitude"]
        assert data["longitude"] == weather_data["longitude"]
        assert data["temperature"] == weather_data["temperature"]
        assert "id" in data
        assert "timestamp" in data
    
    def test_get_weather_data(self, client, db_session):
        """Test retrieving weather data"""
        # Add test data
        weather = WeatherData(
            latitude=37.7749,
            longitude=-122.4194,
            temperature=20.0,
            humidity=60.0,
            source="test"
        )
        db_session.add(weather)
        db_session.commit()
        
        response = client.get("/api/v1/data/weather")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_weather_data_with_filters(self, client):
        """Test retrieving weather data with location filters"""
        response = client.get(
            "/api/v1/data/weather",
            params={
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_km": 50,
                "hours": 24,
                "limit": 10
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_seismic_data(self, client):
        """Test creating seismic data"""
        seismic_data = {
            "event_id": "test_earthquake_001",
            "timestamp": datetime.utcnow().isoformat(),
            "latitude": 37.7749,
            "longitude": -122.4194,
            "magnitude": 4.5,
            "depth": 10.0,
            "magnitude_type": "Mw",
            "place": "Test Location",
            "source": "test"
        }
        
        response = client.post("/api/v1/data/seismic", json=seismic_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["event_id"] == seismic_data["event_id"]
        assert data["magnitude"] == seismic_data["magnitude"]
        assert "id" in data
    
    def test_get_seismic_data(self, client):
        """Test retrieving seismic data"""
        response = client.get("/api/v1/data/seismic")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_seismic_data_with_filters(self, client):
        """Test retrieving seismic data with filters"""
        response = client.get(
            "/api/v1/data/seismic",
            params={
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_km": 500,
                "days": 30,
                "min_magnitude": 3.0,
                "limit": 50
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_data_statistics(self, client):
        """Test data statistics endpoint"""
        response = client.get("/api/v1/data/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_records" in data
        assert "recent_activity_24h" in data
        assert "latest_data" in data


class TestPredictionEndpoints:
    
    @patch('src.api.endpoints.predictions.flood_predictor')
    def test_flood_prediction(self, mock_predictor, client):
        """Test flood prediction endpoint"""
        # Mock the predictor
        mock_predictor.prepare_features.return_value = Mock()
        mock_predictor.predict.return_value = {
            'flood_probability': 0.65,
            'risk_level': 'HIGH',
            'confidence': 0.8,
            'features_used': ['temperature', 'precipitation']
        }
        
        prediction_request = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "hours_ahead": 24
        }
        
        response = client.post("/api/v1/predictions/flood", json=prediction_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["latitude"] == prediction_request["latitude"]
        assert data["longitude"] == prediction_request["longitude"]
        assert data["flood_probability"] == 0.65
        assert data["risk_level"] == "HIGH"
        assert "id" in data
    
    @patch('src.api.endpoints.predictions.earthquake_predictor')
    def test_earthquake_prediction(self, mock_predictor, client):
        """Test earthquake prediction endpoint"""
        # Mock the predictor
        mock_predictor.prepare_features.return_value = Mock()
        mock_predictor.predict.return_value = {
            'risk_probability': 0.45,
            'estimated_magnitude': 5.2,
            'risk_level': 'MEDIUM',
            'confidence': 0.7,
            'features_used': ['seismic_activity_30d', 'magnitude_trend']
        }
        
        prediction_request = {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "hours_ahead": 72
        }
        
        response = client.post("/api/v1/predictions/earthquake", json=prediction_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["latitude"] == prediction_request["latitude"]
        assert data["longitude"] == prediction_request["longitude"]
        assert data["risk_probability"] == 0.45
        assert data["estimated_magnitude"] == 5.2
        assert data["risk_level"] == "MEDIUM"
        assert "id" in data
    
    def test_get_recent_flood_predictions(self, client, db_session):
        """Test retrieving recent flood predictions"""
        # Add test prediction
        prediction = FloodPrediction(
            prediction_time=datetime.utcnow() + timedelta(hours=24),
            latitude=37.7749,
            longitude=-122.4194,
            flood_probability=0.6,
            risk_level="MEDIUM",
            confidence_score=0.75,
            model_version="1.0"
        )
        db_session.add(prediction)
        db_session.commit()
        
        response = client.get("/api/v1/predictions/flood/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_recent_earthquake_predictions(self, client):
        """Test retrieving recent earthquake predictions"""
        response = client.get("/api/v1/predictions/earthquake/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_prediction_validation(self, client):
        """Test prediction request validation"""
        # Test with invalid latitude
        invalid_request = {
            "latitude": 91.0,  # Invalid latitude
            "longitude": -122.4194,
            "hours_ahead": 24
        }
        
        response = client.post("/api/v1/predictions/flood", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_prediction_with_location_filter(self, client):
        """Test predictions with location filtering"""
        response = client.get(
            "/api/v1/predictions/flood/recent",
            params={
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_km": 100,
                "limit": 5
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestAlertEndpoints:
    
    def test_create_alert(self, client):
        """Test creating an alert"""
        alert_data = {
            "alert_type": "FLOOD",
            "severity": "HIGH",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "title": "Test Flood Alert",
            "message": "This is a test flood alert for validation purposes."
        }
        
        response = client.post("/api/v1/alerts/", json=alert_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["alert_type"] == alert_data["alert_type"]
        assert data["severity"] == alert_data["severity"]
        assert data["title"] == alert_data["title"]
        assert data["is_active"] == True
        assert "id" in data
    
    def test_get_alerts(self, client, db_session):
        """Test retrieving alerts"""
        # Add test alert
        alert = Alert(
            alert_type="EARTHQUAKE",
            severity="MEDIUM",
            latitude=37.7749,
            longitude=-122.4194,
            title="Test Alert",
            message="Test message",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()
        
        response = client.get("/api/v1/alerts/")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_alerts_with_filters(self, client):
        """Test retrieving alerts with filters"""
        response = client.get(
            "/api/v1/alerts/",
            params={
                "active_only": True,
                "alert_type": "FLOOD",
                "severity": "HIGH",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_km": 50,
                "limit": 10
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_alert_by_id(self, client, db_session):
        """Test retrieving specific alert by ID"""
        # Add test alert
        alert = Alert(
            alert_type="FLOOD",
            severity="CRITICAL",
            latitude=37.7749,
            longitude=-122.4194,
            title="Critical Flood Alert",
            message="Critical flood conditions detected",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.get(f"/api/v1/alerts/{alert.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == alert.id
        assert data["title"] == alert.title
    
    def test_deactivate_alert(self, client, db_session):
        """Test deactivating an alert"""
        # Add test alert
        alert = Alert(
            alert_type="EARTHQUAKE",
            severity="HIGH",
            latitude=37.7749,
            longitude=-122.4194,
            title="Test Alert",
            message="Test message",
            is_active=True
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)
        
        response = client.put(f"/api/v1/alerts/{alert.id}/deactivate")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
    
    def test_alert_statistics(self, client):
        """Test alert statistics endpoint"""
        response = client.get("/api/v1/alerts/statistics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_alerts" in data
        assert "active_alerts" in data
        assert "alerts_by_type" in data
        assert "active_by_severity" in data


class TestDashboardEndpoints:
    
    def test_dashboard_summary(self, client):
        """Test dashboard summary endpoint"""
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_alerts" in data
        assert "recent_predictions" in data
        assert "weather_summary" in data
        assert "seismic_activity" in data
        assert "system_status" in data
    
    def test_map_data(self, client):
        """Test map data endpoint"""
        response = client.get(
            "/api/v1/dashboard/map-data",
            params={
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_km": 500
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "earthquakes" in data
        assert "alerts" in data
        assert "flood_predictions" in data
        assert "earthquake_predictions" in data
        assert "river_gauges" in data
    
    def test_analytics_data(self, client):
        """Test analytics data endpoint"""
        response = client.get(
            "/api/v1/dashboard/analytics",
            params={"days": 30}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "alert_trends" in data
        assert "earthquake_distribution" in data
        assert "prediction_summary" in data


class TestErrorHandling:
    
    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint"""
        response = client.get("/api/v1/invalid-endpoint")
        assert response.status_code == 404
    
    def test_invalid_method(self, client):
        """Test using invalid HTTP method"""
        response = client.delete("/api/v1/data/weather")
        assert response.status_code == 405
    
    def test_invalid_json(self, client):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/v1/data/weather",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in request"""
        incomplete_data = {
            "latitude": 37.7749
            # Missing longitude and other required fields
        }
        
        response = client.post("/api/v1/data/weather", json=incomplete_data)
        assert response.status_code == 422
