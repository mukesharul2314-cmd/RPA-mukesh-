"""
Earthquake risk assessment and prediction models
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import logging
import math
# from scipy.spatial.distance import haversine  # Simplified for Windows compatibility

logger = logging.getLogger(__name__)


class EarthquakePredictor:
    """Machine learning model for earthquake risk assessment"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            'seismic_activity_7d', 'seismic_activity_30d', 'avg_magnitude_7d',
            'max_magnitude_30d', 'earthquake_count_100km', 'fault_distance',
            'tectonic_stress', 'geological_stability', 'depth_variance',
            'magnitude_trend', 'foreshock_count', 'b_value', 'time_since_last',
            'population_density', 'elevation', 'slope'
        ]
        self.is_trained = False
    
    def calculate_seismic_features(self, seismic_data: List[Dict], 
                                 location: Tuple[float, float]) -> Dict:
        """Calculate seismic activity features for a location"""
        try:
            if not seismic_data:
                return self._default_seismic_features()
            
            df = pd.DataFrame(seismic_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            lat, lon = location
            features = {}
            
            # Calculate distances to earthquakes
            distances = []
            for _, row in df.iterrows():
                dist = self._calculate_distance((lat, lon), (row['latitude'], row['longitude']))
                distances.append(dist)
            df['distance_km'] = distances
            
            # Recent seismic activity
            now = datetime.now()
            last_7d = df[df['timestamp'] >= now - timedelta(days=7)]
            last_30d = df[df['timestamp'] >= now - timedelta(days=30)]
            
            features['seismic_activity_7d'] = len(last_7d)
            features['seismic_activity_30d'] = len(last_30d)
            features['avg_magnitude_7d'] = last_7d['magnitude'].mean() if len(last_7d) > 0 else 0
            features['max_magnitude_30d'] = last_30d['magnitude'].max() if len(last_30d) > 0 else 0
            
            # Nearby earthquake activity (within 100km)
            nearby = df[df['distance_km'] <= 100]
            features['earthquake_count_100km'] = len(nearby)
            
            # Distance to nearest fault (simplified - would use real geological data)
            features['fault_distance'] = min(distances) if distances else 100
            
            # Tectonic stress indicators (simplified)
            if len(last_30d) > 0:
                features['tectonic_stress'] = last_30d['magnitude'].std()
                features['depth_variance'] = last_30d['depth'].std() if 'depth' in last_30d.columns else 0
            else:
                features['tectonic_stress'] = 0
                features['depth_variance'] = 0
            
            # Geological stability (simplified)
            features['geological_stability'] = max(0, 1 - features['seismic_activity_30d'] / 100)
            
            # Magnitude trend (increasing/decreasing)
            if len(last_30d) >= 2:
                magnitudes = last_30d['magnitude'].values
                features['magnitude_trend'] = np.polyfit(range(len(magnitudes)), magnitudes, 1)[0]
            else:
                features['magnitude_trend'] = 0
            
            # Foreshock analysis
            features['foreshock_count'] = len(last_7d[last_7d['magnitude'] < 4.0])
            
            # Gutenberg-Richter b-value (simplified)
            if len(last_30d) > 10:
                mags = last_30d['magnitude'].values
                mag_bins = np.arange(mags.min(), mags.max() + 0.1, 0.1)
                counts = np.histogram(mags, bins=mag_bins)[0]
                if len(counts) > 1:
                    log_counts = np.log10(counts + 1)
                    features['b_value'] = -np.polyfit(mag_bins[:-1], log_counts, 1)[0]
                else:
                    features['b_value'] = 1.0
            else:
                features['b_value'] = 1.0
            
            # Time since last significant earthquake
            significant = df[df['magnitude'] >= 5.0]
            if len(significant) > 0:
                last_significant = significant.iloc[-1]['timestamp']
                features['time_since_last'] = (now - last_significant).days
            else:
                features['time_since_last'] = 365  # Default to 1 year
            
            return features
            
        except Exception as e:
            logger.error(f"Error calculating seismic features: {e}")
            return self._default_seismic_features()

    def _calculate_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two locations in kilometers using Haversine formula"""
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return 6371 * c  # Earth's radius in km

    def _default_seismic_features(self) -> Dict:
        """Return default seismic features when no data available"""
        return {
            'seismic_activity_7d': 0,
            'seismic_activity_30d': 0,
            'avg_magnitude_7d': 0,
            'max_magnitude_30d': 0,
            'earthquake_count_100km': 0,
            'fault_distance': 100,
            'tectonic_stress': 0,
            'geological_stability': 0.8,
            'depth_variance': 0,
            'magnitude_trend': 0,
            'foreshock_count': 0,
            'b_value': 1.0,
            'time_since_last': 365
        }
    
    def prepare_features(self, seismic_data: List[Dict], 
                        location_data: Dict) -> pd.DataFrame:
        """Prepare features for earthquake prediction"""
        try:
            location = (location_data['latitude'], location_data['longitude'])
            
            # Calculate seismic features
            seismic_features = self.calculate_seismic_features(seismic_data, location)
            
            # Add location-based features
            features = seismic_features.copy()
            features['population_density'] = location_data.get('population_density', 100)
            features['elevation'] = location_data.get('elevation', 100)
            features['slope'] = location_data.get('slope', 0.1)
            
            # Convert to DataFrame
            feature_df = pd.DataFrame([features])
            
            # Ensure all required columns exist
            for col in self.feature_columns:
                if col not in feature_df.columns:
                    feature_df[col] = 0
            
            return feature_df[self.feature_columns]
            
        except Exception as e:
            logger.error(f"Error preparing earthquake features: {e}")
            # Return default features
            default_features = {col: 0 for col in self.feature_columns}
            return pd.DataFrame([default_features])
    
    def train(self, training_data: pd.DataFrame, target_column: str = 'earthquake_risk'):
        """Train the earthquake prediction model"""
        try:
            logger.info("Starting earthquake prediction model training")
            
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
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
            
            gb_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
            
            # Train models
            rf_model.fit(X_train_scaled, y_train)
            gb_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            rf_pred = rf_model.predict_proba(X_test_scaled)[:, 1]
            gb_pred = gb_model.predict_proba(X_test_scaled)[:, 1]
            ensemble_pred = (rf_pred + gb_pred) / 2
            
            auc_score = roc_auc_score(y_test, ensemble_pred)
            
            logger.info(f"Earthquake model training completed - AUC: {auc_score:.4f}")
            
            # Store the ensemble model
            self.model = {
                'rf': rf_model,
                'gb': gb_model,
                'type': 'ensemble'
            }
            self.is_trained = True
            
            return {
                'auc_score': auc_score,
                'feature_importance': dict(zip(
                    self.feature_columns,
                    rf_model.feature_importances_
                ))
            }
            
        except Exception as e:
            logger.error(f"Error training earthquake prediction model: {e}")
            raise
    
    def predict(self, features: pd.DataFrame) -> Dict:
        """Make earthquake risk prediction"""
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model not trained, using default prediction")
                return {
                    'risk_probability': 0.1,
                    'estimated_magnitude': 4.0,
                    'risk_level': 'LOW',
                    'confidence': 0.5,
                    'features_used': list(features.columns)
                }
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Ensemble prediction
            rf_pred = self.model['rf'].predict_proba(features_scaled)[0, 1]
            gb_pred = self.model['gb'].predict_proba(features_scaled)[0, 1]
            risk_probability = (rf_pred + gb_pred) / 2
            
            # Estimate magnitude based on features
            seismic_activity = features.iloc[0]['seismic_activity_30d']
            max_mag_30d = features.iloc[0]['max_magnitude_30d']
            estimated_magnitude = min(8.0, max(3.0, 4.0 + seismic_activity * 0.01 + max_mag_30d * 0.1))
            
            # Determine risk level
            if risk_probability < 0.3:
                risk_level = 'LOW'
            elif risk_probability < 0.6:
                risk_level = 'MEDIUM'
            elif risk_probability < 0.8:
                risk_level = 'HIGH'
            else:
                risk_level = 'CRITICAL'
            
            # Calculate confidence
            confidence = min(0.9, 0.5 + abs(risk_probability - 0.5))
            
            return {
                'risk_probability': float(risk_probability),
                'estimated_magnitude': float(estimated_magnitude),
                'risk_level': risk_level,
                'confidence': float(confidence),
                'features_used': list(features.columns)
            }
            
        except Exception as e:
            logger.error(f"Error making earthquake prediction: {e}")
            return {
                'risk_probability': 0.1,
                'estimated_magnitude': 4.0,
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
            logger.info(f"Earthquake model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving earthquake model: {e}")
            raise
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            self.is_trained = model_data['is_trained']
            logger.info(f"Earthquake model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading earthquake model: {e}")
            raise
