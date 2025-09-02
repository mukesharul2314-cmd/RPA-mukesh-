"""
Tests for flood prediction model
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.models.flood_predictor import FloodPredictor


class TestFloodPredictor:
    
    @pytest.fixture
    def predictor(self):
        """Create a FloodPredictor instance for testing"""
        return FloodPredictor()
    
    @pytest.fixture
    def sample_weather_data(self):
        """Sample weather data for testing"""
        base_time = datetime.now()
        return [
            {
                'timestamp': base_time - timedelta(hours=i),
                'temperature': 20 + i * 0.5,
                'humidity': 60 + i,
                'pressure': 1013 - i,
                'precipitation': i * 2,
                'wind_speed': 5 + i * 0.5
            }
            for i in range(24)
        ]
    
    @pytest.fixture
    def sample_river_data(self):
        """Sample river gauge data for testing"""
        base_time = datetime.now()
        return [
            {
                'timestamp': base_time - timedelta(hours=i),
                'water_level': 2.0 + i * 0.1,
                'flow_rate': 100 + i * 5,
                'gauge_height': 2.5 + i * 0.1,
                'flood_stage': 4.0
            }
            for i in range(12)
        ]
    
    @pytest.fixture
    def sample_location_data(self):
        """Sample location data for testing"""
        return {
            'elevation': 150,
            'slope': 0.05,
            'soil_type': 2,
            'land_use': 1
        }
    
    def test_predictor_initialization(self, predictor):
        """Test that predictor initializes correctly"""
        assert predictor.model is None
        assert predictor.scaler is not None
        assert predictor.feature_columns is not None
        assert len(predictor.feature_columns) > 0
        assert not predictor.is_trained
    
    def test_prepare_features_with_data(self, predictor, sample_weather_data, 
                                       sample_river_data, sample_location_data):
        """Test feature preparation with valid data"""
        features = predictor.prepare_features(
            sample_weather_data, 
            sample_river_data, 
            sample_location_data
        )
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
        assert all(col in features.columns for col in predictor.feature_columns)
        
        # Check that precipitation aggregates are calculated
        assert features['precipitation_24h'].iloc[0] >= 0
        assert features['precipitation_48h'].iloc[0] >= features['precipitation_24h'].iloc[0]
        
        # Check location features
        assert features['elevation'].iloc[0] == 150
        assert features['slope'].iloc[0] == 0.05
    
    def test_prepare_features_empty_data(self, predictor):
        """Test feature preparation with empty data"""
        features = predictor.prepare_features([], [], {})
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
        assert all(col in features.columns for col in predictor.feature_columns)
        
        # Should have default values
        assert features['precipitation_24h'].iloc[0] == 0
        assert features['temperature'].iloc[0] == 20  # Default temperature
    
    def test_prepare_features_partial_data(self, predictor, sample_weather_data):
        """Test feature preparation with partial data"""
        features = predictor.prepare_features(
            sample_weather_data, 
            [],  # No river data
            {'elevation': 100}
        )
        
        assert isinstance(features, pd.DataFrame)
        assert features['water_level'].iloc[0] == 0  # Default for missing river data
        assert features['elevation'].iloc[0] == 100
    
    def test_predict_untrained_model(self, predictor, sample_weather_data, 
                                   sample_river_data, sample_location_data):
        """Test prediction with untrained model returns default values"""
        features = predictor.prepare_features(
            sample_weather_data, 
            sample_river_data, 
            sample_location_data
        )
        
        result = predictor.predict(features)
        
        assert isinstance(result, dict)
        assert 'flood_probability' in result
        assert 'risk_level' in result
        assert 'confidence' in result
        assert 'features_used' in result
        
        assert 0 <= result['flood_probability'] <= 1
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0 <= result['confidence'] <= 1
    
    def test_train_model(self, predictor):
        """Test model training with synthetic data"""
        # Create synthetic training data
        np.random.seed(42)
        n_samples = 1000
        
        training_data = pd.DataFrame({
            col: np.random.randn(n_samples) for col in predictor.feature_columns
        })
        
        # Create synthetic target (flood_occurred)
        # Make it somewhat correlated with precipitation features
        flood_probability = (
            training_data['precipitation_24h'] * 0.3 +
            training_data['precipitation_48h'] * 0.2 +
            training_data['water_level'] * 0.4 +
            np.random.randn(n_samples) * 0.1
        )
        training_data['flood_occurred'] = (flood_probability > flood_probability.median()).astype(int)
        
        # Train the model
        metrics = predictor.train(training_data)
        
        assert predictor.is_trained
        assert predictor.model is not None
        assert 'mse' in metrics
        assert 'r2_score' in metrics
        assert 'feature_importance' in metrics
        
        # Check that feature importance is calculated
        assert len(metrics['feature_importance']) == len(predictor.feature_columns)
    
    def test_predict_trained_model(self, predictor):
        """Test prediction with trained model"""
        # First train the model
        np.random.seed(42)
        n_samples = 500
        
        training_data = pd.DataFrame({
            col: np.random.randn(n_samples) for col in predictor.feature_columns
        })
        
        # Create target with some pattern
        flood_probability = (
            training_data['precipitation_24h'] * 0.3 +
            training_data['water_level'] * 0.4 +
            np.random.randn(n_samples) * 0.1
        )
        training_data['flood_occurred'] = (flood_probability > 0).astype(int)
        
        predictor.train(training_data)
        
        # Now test prediction
        test_features = pd.DataFrame({
            col: [0.5] for col in predictor.feature_columns
        })
        
        result = predictor.predict(test_features)
        
        assert isinstance(result, dict)
        assert 0 <= result['flood_probability'] <= 1
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 0 <= result['confidence'] <= 1
    
    def test_risk_level_calculation(self, predictor):
        """Test risk level calculation based on probability"""
        # Mock a trained model
        predictor.is_trained = True
        predictor.model = {
            'rf': Mock(),
            'gb': Mock(),
            'type': 'ensemble'
        }
        predictor.scaler = Mock()
        predictor.scaler.transform.return_value = np.array([[0.5] * len(predictor.feature_columns)])
        
        # Test different probability levels
        test_cases = [
            (0.1, 'LOW'),
            (0.4, 'MEDIUM'),
            (0.7, 'HIGH'),
            (0.9, 'CRITICAL')
        ]
        
        for prob, expected_level in test_cases:
            predictor.model['rf'].predict.return_value = [prob]
            predictor.model['gb'].predict.return_value = [prob]
            
            test_features = pd.DataFrame({
                col: [0.5] for col in predictor.feature_columns
            })
            
            result = predictor.predict(test_features)
            assert result['risk_level'] == expected_level
    
    def test_save_and_load_model(self, predictor, tmp_path):
        """Test model saving and loading"""
        # Train a simple model first
        np.random.seed(42)
        n_samples = 100
        
        training_data = pd.DataFrame({
            col: np.random.randn(n_samples) for col in predictor.feature_columns
        })
        training_data['flood_occurred'] = np.random.randint(0, 2, n_samples)
        
        predictor.train(training_data)
        
        # Save model
        model_path = tmp_path / "test_flood_model.pkl"
        predictor.save_model(str(model_path))
        
        assert model_path.exists()
        
        # Create new predictor and load model
        new_predictor = FloodPredictor()
        assert not new_predictor.is_trained
        
        new_predictor.load_model(str(model_path))
        
        assert new_predictor.is_trained
        assert new_predictor.model is not None
        assert new_predictor.feature_columns == predictor.feature_columns
    
    def test_error_handling_invalid_data(self, predictor):
        """Test error handling with invalid data"""
        # Test with invalid weather data
        invalid_weather = [{'invalid': 'data'}]
        
        features = predictor.prepare_features(invalid_weather, [], {})
        
        # Should return default features without crashing
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
    
    def test_feature_validation(self, predictor):
        """Test that all required features are present"""
        expected_features = [
            'precipitation_24h', 'precipitation_48h', 'precipitation_72h',
            'temperature', 'humidity', 'pressure', 'wind_speed',
            'water_level', 'flow_rate', 'gauge_height', 'flood_stage_ratio',
            'elevation', 'slope', 'soil_type_encoded', 'land_use_encoded',
            'season', 'hour_of_day', 'day_of_year'
        ]
        
        assert all(feature in predictor.feature_columns for feature in expected_features)
    
    @patch('src.models.flood_predictor.logger')
    def test_logging_on_errors(self, mock_logger, predictor):
        """Test that errors are properly logged"""
        # Test with data that will cause an error in feature preparation
        with patch.object(predictor, 'prepare_features', side_effect=Exception("Test error")):
            features = predictor.prepare_features([], [], {})
            
            # Should log error and return default features
            mock_logger.error.assert_called()
            assert isinstance(features, pd.DataFrame)
