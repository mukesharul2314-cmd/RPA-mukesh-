"""
Flood prediction machine learning models
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging

logger = logging.getLogger(__name__)


class FloodPredictor:
    """Machine learning model for flood prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_columns = [
            'precipitation_24h', 'precipitation_48h', 'precipitation_72h',
            'temperature', 'humidity', 'pressure', 'wind_speed',
            'water_level', 'flow_rate', 'gauge_height', 'flood_stage_ratio',
            'elevation', 'slope', 'soil_type_encoded', 'land_use_encoded',
            'season', 'hour_of_day', 'day_of_year'
        ]
        self.is_trained = False
    
    def prepare_features(self, weather_data: List[Dict], 
                        river_data: List[Dict], 
                        location_data: Dict) -> pd.DataFrame:
        """Prepare features for prediction"""
        try:
            # Convert to DataFrames
            weather_df = pd.DataFrame(weather_data)
            river_df = pd.DataFrame(river_data)
            
            # Calculate precipitation aggregates
            weather_df['timestamp'] = pd.to_datetime(weather_df['timestamp'])
            weather_df = weather_df.sort_values('timestamp')
            
            features = {}
            
            # Weather features
            if not weather_df.empty:
                features['precipitation_24h'] = weather_df['precipitation'].tail(24).sum()
                features['precipitation_48h'] = weather_df['precipitation'].tail(48).sum()
                features['precipitation_72h'] = weather_df['precipitation'].tail(72).sum()
                features['temperature'] = weather_df['temperature'].iloc[-1] if len(weather_df) > 0 else 0
                features['humidity'] = weather_df['humidity'].iloc[-1] if len(weather_df) > 0 else 0
                features['pressure'] = weather_df['pressure'].iloc[-1] if len(weather_df) > 0 else 0
                features['wind_speed'] = weather_df['wind_speed'].iloc[-1] if len(weather_df) > 0 else 0
            else:
                features.update({
                    'precipitation_24h': 0, 'precipitation_48h': 0, 'precipitation_72h': 0,
                    'temperature': 20, 'humidity': 50, 'pressure': 1013, 'wind_speed': 0
                })
            
            # River gauge features
            if not river_df.empty:
                latest_river = river_df.iloc[-1]
                features['water_level'] = latest_river.get('water_level', 0)
                features['flow_rate'] = latest_river.get('flow_rate', 0)
                features['gauge_height'] = latest_river.get('gauge_height', 0)
                flood_stage = latest_river.get('flood_stage', 1)
                features['flood_stage_ratio'] = features['water_level'] / max(flood_stage, 0.1)
            else:
                features.update({
                    'water_level': 0, 'flow_rate': 0, 'gauge_height': 0, 'flood_stage_ratio': 0
                })
            
            # Location features (would be enhanced with real GIS data)
            features['elevation'] = location_data.get('elevation', 100)  # meters
            features['slope'] = location_data.get('slope', 0.1)  # percentage
            features['soil_type_encoded'] = location_data.get('soil_type', 1)  # encoded
            features['land_use_encoded'] = location_data.get('land_use', 1)  # encoded
            
            # Temporal features
            now = datetime.now()
            features['season'] = (now.month - 1) // 3  # 0-3 for seasons
            features['hour_of_day'] = now.hour
            features['day_of_year'] = now.timetuple().tm_yday
            
            # Convert to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all required columns exist
            for col in self.feature_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0
            
            return feature_df[self.feature_columns]
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            # Return default features
            default_features = {col: 0 for col in self.feature_columns}
            return pd.DataFrame([default_features])
    
    def train(self, training_data: pd.DataFrame, target_column: str = 'flood_occurred'):
        """Train the flood prediction model"""
        try:
            logger.info("Starting flood prediction model training")
            
            # Prepare features and target
            X = training_data[self.feature_columns]
            y = training_data[target_column]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train ensemble model
            rf_model = RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                random_state=42,
                n_jobs=-1
            )
            
            gb_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            # Train models
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)
            
            # Ensemble predictions
            rf_pred = rf_model.predict(X_test_scaled)
            gb_pred = gb_model.predict(X_test_scaled)
            ensemble_pred = (rf_pred + gb_pred) / 2
            
            # Evaluate
            mse = mean_squared_error(y_test, ensemble_pred)
            r2 = r2_score(y_test, ensemble_pred)
            
            logger.info(f"Model training completed - MSE: {mse:.4f}, R2: {r2:.4f}")
            
            # Store the best performing model (ensemble)
            self.model = {
                'rf': rf_model,
                'gb': gb_model,
                'type': 'ensemble'
            }
            self.is_trained = True
            
            return {
                'mse': mse,
                'r2_score': r2,
                'feature_importance': dict(zip(
                    self.feature_columns, 
                    rf_model.feature_importances_
                ))
            }
            
        except Exception as e:
            logger.error(f"Error training flood prediction model: {e}")
            raise
    
    def predict(self, features: pd.DataFrame) -> Dict:
        """Make flood prediction"""
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model not trained, using default prediction")
                return {
                    'flood_probability': 0.1,
                    'risk_level': 'LOW',
                    'confidence': 0.5,
                    'features_used': list(features.columns)
                }
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Ensemble prediction
            rf_pred = self.model['rf'].predict(features_scaled)[0]
            gb_pred = self.model['gb'].predict(features_scaled)[0]
            flood_probability = (rf_pred + gb_pred) / 2
            
            # Ensure probability is between 0 and 1
            flood_probability = max(0, min(1, flood_probability))
            
            # Determine risk level
            if flood_probability < 0.3:
                risk_level = 'LOW'
            elif flood_probability < 0.6:
                risk_level = 'MEDIUM'
            elif flood_probability < 0.8:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'
            
            # Calculate confidence (simplified)
            confidence = min(0.9, 0.5 + abs(flood_probability - 0.5))
            
            return {
                'flood_probability': float(flood_probability),
                'risk_level': risk_level,
                'confidence': float(confidence),
                'features_used': list(features.columns)
            }
            
        except Exception as e:
            logger.error(f"Error making flood prediction: {e}")
            return {
                'flood_probability': 0.1,
                'risk_level': 'LOW',
                'confidence': 0.3,
                'features_used': []
            }
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
