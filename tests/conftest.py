"""
Pytest configuration and shared fixtures
"""
import pytest
import os
import tempfile
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from src.models.database import Base


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def test_database_url():
    """Create test database URL"""
    return "sqlite:///./test_disaster_analytics.db"


@pytest.fixture(scope="function")
def test_db_engine(test_database_url):
    """Create test database engine"""
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    
    # Clean up database file
    db_file = test_database_url.replace("sqlite:///./", "")
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create test database session"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing"""
    base_time = datetime.utcnow()
    return [
        {
            'timestamp': base_time - timedelta(hours=i),
            'latitude': 37.7749,
            'longitude': -122.4194,
            'temperature': 20.0 + i * 0.5,
            'humidity': 60.0 + i,
            'pressure': 1013.0 - i,
            'precipitation': i * 2.0,
            'wind_speed': 5.0 + i * 0.5,
            'wind_direction': (i * 15) % 360,
            'visibility': 10.0,
            'source': 'test'
        }
        for i in range(24)
    ]


@pytest.fixture
def sample_seismic_data():
    """Sample seismic data for testing"""
    base_time = datetime.utcnow()
    return [
        {
            'event_id': f'test_eq_{i:03d}',
            'timestamp': base_time - timedelta(days=i),
            'latitude': 37.7749 + i * 0.01,
            'longitude': -122.4194 + i * 0.01,
            'magnitude': 3.0 + i * 0.1,
            'depth': 10.0 + i * 2,
            'magnitude_type': 'Mw',
            'place': f'Test Location {i}',
            'source': 'test',
            'significance': 100 + i * 10
        }
        for i in range(30)
    ]


@pytest.fixture
def sample_river_data():
    """Sample river gauge data for testing"""
    base_time = datetime.utcnow()
    return [
        {
            'gauge_id': f'test_gauge_{i:02d}',
            'timestamp': base_time - timedelta(hours=i),
            'latitude': 37.7749 + i * 0.001,
            'longitude': -122.4194 + i * 0.001,
            'water_level': 2.0 + i * 0.1,
            'flow_rate': 100.0 + i * 5,
            'gauge_height': 2.5 + i * 0.1,
            'flood_stage': 4.0,
            'river_name': f'Test River {i}',
            'station_name': f'Test Station {i}'
        }
        for i in range(12)
    ]


@pytest.fixture
def sample_location_data():
    """Sample location data for testing"""
    return {
        'latitude': 37.7749,
        'longitude': -122.4194,
        'elevation': 150.0,
        'slope': 0.05,
        'soil_type': 2,
        'land_use': 1,
        'population_density': 500.0
    }


@pytest.fixture
def mock_api_responses():
    """Mock API responses for external services"""
    return {
        'weather': {
            'main': {
                'temp': 20.5,
                'humidity': 65,
                'pressure': 1013.25
            },
            'weather': [{'description': 'clear sky'}],
            'wind': {
                'speed': 5.2,
                'deg': 180
            },
            'visibility': 10000,
            'rain': {'1h': 0.0}
        },
        'earthquake': {
            'features': [
                {
                    'properties': {
                        'mag': 4.5,
                        'place': 'Test Location',
                        'time': int(datetime.utcnow().timestamp() * 1000),
                        'ids': 'test_eq_001',
                        'magType': 'Mw',
                        'sig': 300
                    },
                    'geometry': {
                        'coordinates': [-122.4194, 37.7749, 10.0]
                    }
                }
            ]
        }
    }


@pytest.fixture
def test_config():
    """Test configuration settings"""
    return {
        'DATABASE_URL': 'sqlite:///./test.db',
        'API_HOST': '127.0.0.1',
        'API_PORT': 8001,
        'DEBUG': True,
        'FLOOD_MODEL_THRESHOLD': 0.7,
        'EARTHQUAKE_MODEL_THRESHOLD': 0.8,
        'PREDICTION_INTERVAL_HOURS': 6
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers based on test file names
    for item in items:
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if "test_model_training" in item.nodeid or "test_large_dataset" in item.nodeid:
            item.add_marker(pytest.mark.slow)
