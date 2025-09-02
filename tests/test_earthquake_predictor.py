"""
Tests for earthquake prediction model
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.models.earthquake_predictor import EarthquakePredictor


class TestEarthquakePredictor:
    
    @pytest.fixture
    def predictor(self):
        """Create an EarthquakePredictor instance for testing"""
        return EarthquakePredictor()
    
    @pytest.fixture
    def sample_seismic_data(self):
        """Sample seismic data for testing"""
        base_time = datetime.now()
        return [
            {
                'timestamp': base_time - timedelta(days=i),
                'latitude': 37.7749 + i * 0.01,
                'longitude': -122.4194 + i * 0.01,
                'magnitude': 3.0 + i * 0.2,
                'depth': 10 + i * 2
            }
            for i in range(30)
        ]
    
    @pytest.fixture
    def sample_location_data(self):
        """Sample location data for testing"""
        return {
            'latitude': 37.7749,
            'longitude': -122.4194,
            'population_density': 500,
            'elevation': 50,
            'slope': 0.1
        }
    
    def test_predictor_initialization(self, predictor):
        """Test that predictor initializes correctly"""
        assert predictor.model is None
        assert predictor.scaler is not None
        assert predictor.feature_columns is not None
        assert len(predictor.feature_columns) > 0
        assert not predictor.is_trained
    
    def test_calculate_seismic_features(self, predictor, sample_seismic_data):
        """Test seismic feature calculation"""
        location = (37.7749, -122.4194)
        features = predictor.calculate_seismic_features(sample_seismic_data, location)
        
        assert isinstance(features, dict)
        
        # Check that all expected features are present
        expected_features = [
            'seismic_activity_7d', 'seismic_activity_30d', 'avg_magnitude_7d',
            'max_magnitude_30d', 'earthquake_count_100km', 'fault_distance',
            'tectonic_stress', 'geological_stability', 'depth_variance',
            'magnitude_trend', 'foreshock_count', 'b_value', 'time_since_last'
        ]
        
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], (int, float))
    
    def test_calculate_seismic_features_empty_data(self, predictor):
        """Test seismic feature calculation with empty data"""
        location = (37.7749, -122.4194)
        features = predictor.calculate_seismic_features([], location)
        
        assert isinstance(features, dict)
        
        # Should return default values
        assert features['seismic_activity_7d'] == 0
        assert features['seismic_activity_30d'] == 0
        assert features['avg_magnitude_7d'] == 0
        assert features['geological_stability'] == 0.8  # Default stability
    
    def test_prepare_features_with_data(self, predictor, sample_seismic_data, sample_location_data):
        """Test feature preparation with valid data"""
        features = predictor.prepare_features(sample_seismic_data, sample_location_data)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
        assert all(col in features.columns for col in predictor.feature_columns)
        
        # Check location features
        assert features['population_density'].iloc[0] == 500
        assert features['elevation'].iloc[0] == 50
        assert features['slope'].iloc[0] == 0.1
    
    def test_prepare_features_empty_data(self, predictor):
        """Test feature preparation with empty data"""
        location_data = {'latitude': 0, 'longitude': 0}
        features = predictor.prepare_features([], location_data)
        
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
        assert all(col in features.columns for col in predictor.feature_columns)
        
        # Should have default values
        assert features['seismic_activity_7d'].iloc[0] == 0
        assert features['population_density'].iloc[0] == 100  # Default
    
    def test_predict_untrained_model(self, predictor, sample_seismic_data, sample_location_data):
        """Test prediction with untrained model returns default values"""
        features = predictor.prepare_features(sample_seismic_data, sample_location_data)
        
        result = predictor.predict(features)
        
        assert isinstance(result, dict)
        assert 'risk_probability' in result
        assert 'estimated_magnitude' in result
        assert 'risk_level' in result
        assert 'confidence' in result
        assert 'features_used' in result
        
        assert 0 <= result['risk_probability'] <= 1
        assert result['estimated_magnitude'] >= 3.0
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
        
        # Create synthetic target (earthquake_risk)
        # Make it somewhat correlated with seismic activity features
        risk_score = (
            training_data['seismic_activity_30d'] * 0.3 +
            training_data['max_magnitude_30d'] * 0.4 +
            training_data['tectonic_stress'] * 0.2 +
            np.random.randn(n_samples) * 0.1
        )
        training_data['earthquake_risk'] = (risk_score > risk_score.median()).astype(int)
        
        # Train the model
        metrics = predictor.train(training_data)
        
        assert predictor.is_trained
        assert predictor.model is not None
        assert 'auc_score' in metrics
        assert 'feature_importance' in metrics
        
        # Check that feature importance is calculated
        assert len(metrics['feature_importance']) == len(predictor.feature_columns)
        assert 0 <= metrics['auc_score'] <= 1
    
    def test_predict_trained_model(self, predictor):
        """Test prediction with trained model"""
        # First train the model
        np.random.seed(42)
        n_samples = 500
        
        training_data = pd.DataFrame({
            col: np.random.randn(n_samples) for col in predictor.feature_columns
        })
        
        # Create target with some pattern
        risk_score = (
            training_data['seismic_activity_30d'] * 0.3 +
            training_data['max_magnitude_30d'] * 0.4 +
            np.random.randn(n_samples) * 0.1
        )
        training_data['earthquake_risk'] = (risk_score > 0).astype(int)
        
        predictor.train(training_data)
        
        # Now test prediction
        test_features = pd.DataFrame({
            col: [0.5] for col in predictor.feature_columns
        })
        
        result = predictor.predict(test_features)
        
        assert isinstance(result, dict)
        assert 0 <= result['risk_probability'] <= 1
        assert result['estimated_magnitude'] >= 3.0
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
            # Mock predict_proba to return the desired probability
            predictor.model['rf'].predict_proba.return_value = np.array([[1-prob, prob]])
            predictor.model['gb'].predict_proba.return_value = np.array([[1-prob, prob]])
            
            test_features = pd.DataFrame({
                col: [0.5] for col in predictor.feature_columns
            })
            
            result = predictor.predict(test_features)
            assert result['risk_level'] == expected_level
    
    def test_magnitude_estimation(self, predictor):
        """Test earthquake magnitude estimation"""
        # Mock a trained model
        predictor.is_trained = True
        predictor.model = {
            'rf': Mock(),
            'gb': Mock(),
            'type': 'ensemble'
        }
        predictor.scaler = Mock()
        predictor.scaler.transform.return_value = np.array([[0.5] * len(predictor.feature_columns)])
        
        # Mock prediction
        predictor.model['rf'].predict_proba.return_value = np.array([[0.3, 0.7]])
        predictor.model['gb'].predict_proba.return_value = np.array([[0.3, 0.7]])
        
        test_features = pd.DataFrame({
            col: [1.0] if col in ['seismic_activity_30d', 'max_magnitude_30d'] else [0.5] 
            for col in predictor.feature_columns
        })
        
        result = predictor.predict(test_features)
        
        # Magnitude should be influenced by seismic activity and max magnitude
        assert 3.0 <= result['estimated_magnitude'] <= 8.0
    
    def test_save_and_load_model(self, predictor, tmp_path):
        """Test model saving and loading"""
        # Train a simple model first
        np.random.seed(42)
        n_samples = 100
        
        training_data = pd.DataFrame({
            col: np.random.randn(n_samples) for col in predictor.feature_columns
        })
        training_data['earthquake_risk'] = np.random.randint(0, 2, n_samples)
        
        predictor.train(training_data)
        
        # Save model
        model_path = tmp_path / "test_earthquake_model.pkl"
        predictor.save_model(str(model_path))
        
        assert model_path.exists()
        
        # Create new predictor and load model
        new_predictor = EarthquakePredictor()
        assert not new_predictor.is_trained
        
        new_predictor.load_model(str(model_path))
        
        assert new_predictor.is_trained
        assert new_predictor.model is not None
        assert new_predictor.feature_columns == predictor.feature_columns
    
    def test_distance_calculation(self, predictor):
        """Test distance calculation in seismic features"""
        # Test with earthquakes at known distances
        seismic_data = [
            {
                'timestamp': datetime.now(),
                'latitude': 37.7749,  # Same location
                'longitude': -122.4194,
                'magnitude': 4.0,
                'depth': 10
            },
            {
                'timestamp': datetime.now(),
                'latitude': 38.7749,  # ~111 km north
                'longitude': -122.4194,
                'magnitude': 4.5,
                'depth': 15
            }
        ]
        
        location = (37.7749, -122.4194)
        features = predictor.calculate_seismic_features(seismic_data, location)
        
        # Should find earthquakes within 100km
        assert features['earthquake_count_100km'] == 2
        assert features['fault_distance'] == 0  # Closest earthquake is at same location
    
    def test_b_value_calculation(self, predictor):
        """Test Gutenberg-Richter b-value calculation"""
        # Create data with known magnitude distribution
        seismic_data = []
        base_time = datetime.now()
        
        # Create earthquakes with decreasing frequency for higher magnitudes
        for mag in [3.0, 3.1, 3.2, 3.3, 3.4, 3.5, 4.0, 4.1, 4.2, 4.5, 5.0]:
            for i in range(int(10 / (mag - 2.5))):  # Fewer large earthquakes
                seismic_data.append({
                    'timestamp': base_time - timedelta(days=i),
                    'latitude': 37.7749,
                    'longitude': -122.4194,
                    'magnitude': mag,
                    'depth': 10
                })
        
        location = (37.7749, -122.4194)
        features = predictor.calculate_seismic_features(seismic_data, location)
        
        # b-value should be positive (typically around 1.0)
        assert features['b_value'] > 0
        assert features['b_value'] < 3.0  # Reasonable upper bound
    
    def test_error_handling_invalid_data(self, predictor):
        """Test error handling with invalid data"""
        # Test with invalid seismic data
        invalid_seismic = [{'invalid': 'data'}]
        location_data = {'latitude': 0, 'longitude': 0}
        
        features = predictor.prepare_features(invalid_seismic, location_data)
        
        # Should return default features without crashing
        assert isinstance(features, pd.DataFrame)
        assert len(features) == 1
    
    def test_feature_validation(self, predictor):
        """Test that all required features are present"""
        expected_features = [
            'seismic_activity_7d', 'seismic_activity_30d', 'avg_magnitude_7d',
            'max_magnitude_30d', 'earthquake_count_100km', 'fault_distance',
            'tectonic_stress', 'geological_stability', 'depth_variance',
            'magnitude_trend', 'foreshock_count', 'b_value', 'time_since_last',
            'population_density', 'elevation', 'slope'
        ]
        
        assert all(feature in predictor.feature_columns for feature in expected_features)
    
    @patch('src.models.earthquake_predictor.logger')
    def test_logging_on_errors(self, mock_logger, predictor):
        """Test that errors are properly logged"""
        # Test with data that will cause an error in feature preparation
        with patch.object(predictor, 'calculate_seismic_features', side_effect=Exception("Test error")):
            features = predictor.prepare_features([], {'latitude': 0, 'longitude': 0})
            
            # Should log error and return default features
            mock_logger.error.assert_called()
            assert isinstance(features, pd.DataFrame)
