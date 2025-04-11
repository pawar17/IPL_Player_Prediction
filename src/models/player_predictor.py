import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class PlayerPredictor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.models_path = self.base_path / 'models'
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.batting_model = None
        self.bowling_model = None
        self.fielding_model = None
        self.scaler = StandardScaler()
        
        # Feature importance weights
        self.feature_weights = {
            'recent_form': 0.4,      # Last 5 matches
            'current_tournament': 0.3, # Current IPL season
            'historical': 0.2,        # All-time stats
            'venue': 0.1             # Venue-specific performance
        }
    
    def train(self, data: pd.DataFrame, perform_grid_search: bool = False) -> Dict[str, Dict[str, float]]:
        """
        Train prediction models using combined data
        
        Args:
            data: DataFrame containing processed player data
            perform_grid_search: Whether to perform hyperparameter tuning
            
        Returns:
            Dictionary containing model performance metrics
        """
        try:
            self.logger.info("Preparing features for training...")
            X, y_batting, y_bowling, y_fielding = self._prepare_features(data)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train models
            self.logger.info("Training batting model...")
            self.batting_model = self._train_model(X_scaled, y_batting, 'batting', perform_grid_search)
            
            self.logger.info("Training bowling model...")
            self.bowling_model = self._train_model(X_scaled, y_bowling, 'bowling', perform_grid_search)
            
            self.logger.info("Training fielding model...")
            self.fielding_model = self._train_model(X_scaled, y_fielding, 'fielding', perform_grid_search)
            
            # Calculate and return metrics
            metrics = self._calculate_metrics(X_scaled, y_batting, y_bowling, y_fielding)
            
            # Save models
            self._save_models()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            return {}
    
    def predict(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions for a player using combined data
        
        Args:
            player_data: Dictionary containing processed player data
            
        Returns:
            Dictionary containing performance predictions
        """
        try:
            # Prepare features
            features = self._prepare_prediction_features(player_data)
            features_scaled = self.scaler.transform(features)
            
            # Make predictions
            batting_pred = float(self.batting_model.predict(features_scaled)[0])
            bowling_pred = float(self.bowling_model.predict(features_scaled)[0])
            fielding_pred = float(self.fielding_model.predict(features_scaled)[0])
            
            # Calculate confidence intervals
            batting_ci = self._calculate_confidence_interval(self.batting_model, features_scaled)
            bowling_ci = self._calculate_confidence_interval(self.bowling_model, features_scaled)
            fielding_ci = self._calculate_confidence_interval(self.fielding_model, features_scaled)
            
            return {
                'batting': {
                    'prediction': batting_pred,
                    'confidence_interval': {
                        'lower': float(batting_ci['lower']),
                        'upper': float(batting_ci['upper'])
                    }
                },
                'bowling': {
                    'prediction': bowling_pred,
                    'confidence_interval': {
                        'lower': float(bowling_ci['lower']),
                        'upper': float(bowling_ci['upper'])
                    }
                },
                'fielding': {
                    'prediction': fielding_pred,
                    'confidence_interval': {
                        'lower': float(fielding_ci['lower']),
                        'upper': float(fielding_ci['upper'])
                    }
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return {}
    
    def _prepare_features(self, data: pd.DataFrame) -> tuple:
        """Prepare features for model training"""
        # Extract features with weights
        features = []
        for _, row in data.iterrows():
            feature_vector = self._extract_weighted_features(row)
            features.append(feature_vector)
        
        X = np.array(features)
        
        # Extract targets - using runs_scored and wickets_taken as performance metrics
        y_batting = data['runs_scored'].values
        y_bowling = data['wickets_taken'].values
        y_fielding = np.zeros(len(data))  # Fielding data not available yet
        
        return X, y_batting, y_bowling, y_fielding
    
    def _extract_weighted_features(self, row: pd.Series) -> List[float]:
        """Extract and weight features from player data"""
        features = []
        
        # Recent form features (40% weight)
        recent_batting_features = [
            row.get('recent_runs', 0),
            row.get('recent_strike_rate', 0),
            row.get('recent_average', 0)
        ]
        recent_bowling_features = [
            row.get('recent_wickets', 0),
            row.get('recent_economy', 0),
            row.get('recent_bowling_avg', 0)
        ]
        features.extend([f * self.feature_weights['recent_form'] for f in recent_batting_features + recent_bowling_features])
        
        # Current tournament features (30% weight)
        current_batting_features = [
            row.get('current_runs', 0),
            row.get('current_strike_rate', 0),
            row.get('current_average', 0)
        ]
        current_bowling_features = [
            row.get('current_wickets', 0),
            row.get('current_economy', 0),
            row.get('current_bowling_avg', 0)
        ]
        features.extend([f * self.feature_weights['current_tournament'] for f in current_batting_features + current_bowling_features])
        
        # Historical features (20% weight)
        historical_batting_features = [
            row.get('historical_runs', 0),
            row.get('historical_strike_rate', 0),
            row.get('historical_average', 0)
        ]
        historical_bowling_features = [
            row.get('historical_wickets', 0),
            row.get('historical_economy', 0),
            row.get('historical_bowling_avg', 0)
        ]
        features.extend([f * self.feature_weights['historical'] for f in historical_batting_features + historical_bowling_features])
        
        # Venue features (10% weight)
        venue_batting_features = [
            row.get('venue_runs', 0),
            row.get('venue_strike_rate', 0),
            row.get('venue_average', 0)
        ]
        venue_bowling_features = [
            row.get('venue_wickets', 0),
            row.get('venue_economy', 0),
            row.get('venue_bowling_avg', 0)
        ]
        features.extend([f * self.feature_weights['venue'] for f in venue_batting_features + venue_bowling_features])
        
        # Additional features
        features.extend([
            row.get('match_importance', 1.0),
            row.get('team_strength', 0.5),
            row.get('opposition_strength', 0.5)
        ])
        
        return features
    
    def _train_model(self, X: np.ndarray, y: np.ndarray, model_type: str, perform_grid_search: bool = False) -> RandomForestRegressor:
        """Train a specific model type"""
        # Validate feature count
        if X.shape[1] != 27:
            self.logger.warning(f"Expected 27 features but got {X.shape[1]} features")
            
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        if len(y) > 0:
            model.fit(X, y)
            r2 = model.score(X, y)
            self.logger.info(f"{model_type.capitalize()} model R^2 score: {r2:.3f}")
        else:
            self.logger.warning(f"No samples available for {model_type} model training")
        
        return model
    
    def _calculate_confidence_interval(self, model: RandomForestRegressor, 
                                    features: np.ndarray) -> Dict[str, float]:
        """Calculate prediction confidence intervals"""
        predictions = []
        for estimator in model.estimators_:
            pred = estimator.predict(features)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        mean_pred = np.mean(predictions, axis=0)
        std_pred = np.std(predictions, axis=0)
        
        return {
            'lower': mean_pred - 1.96 * std_pred,
            'upper': mean_pred + 1.96 * std_pred
        }
    
    def _calculate_metrics(self, X: np.ndarray, y_batting: np.ndarray, 
                         y_bowling: np.ndarray, y_fielding: np.ndarray) -> Dict[str, Dict[str, float]]:
        """Calculate model performance metrics"""
        metrics = {}
        
        # Batting metrics
        batting_pred = self.batting_model.predict(X)
        metrics['batting'] = {
            'mse': np.mean((y_batting - batting_pred) ** 2),
            'mae': np.mean(np.abs(y_batting - batting_pred)),
            'r2': self.batting_model.score(X, y_batting)
        }
        
        # Bowling metrics
        bowling_pred = self.bowling_model.predict(X)
        metrics['bowling'] = {
            'mse': np.mean((y_bowling - bowling_pred) ** 2),
            'mae': np.mean(np.abs(y_bowling - bowling_pred)),
            'r2': self.bowling_model.score(X, y_bowling)
        }
        
        # Fielding metrics
        fielding_pred = self.fielding_model.predict(X)
        metrics['fielding'] = {
            'mse': np.mean((y_fielding - fielding_pred) ** 2),
            'mae': np.mean(np.abs(y_fielding - fielding_pred)),
            'r2': self.fielding_model.score(X, y_fielding)
        }
        
        return metrics
    
    def _save_models(self) -> None:
        """Save trained models to disk"""
        try:
            joblib.dump(self.batting_model, self.models_path / 'batting_model.joblib')
            joblib.dump(self.bowling_model, self.models_path / 'bowling_model.joblib')
            joblib.dump(self.fielding_model, self.models_path / 'fielding_model.joblib')
            joblib.dump(self.scaler, self.models_path / 'scaler.joblib')
            self.logger.info("Models saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
    
    def load_models(self) -> None:
        """Load trained models from disk"""
        try:
            self.batting_model = joblib.load(self.models_path / 'batting_model.joblib')
            self.bowling_model = joblib.load(self.models_path / 'bowling_model.joblib')
            self.fielding_model = joblib.load(self.models_path / 'fielding_model.joblib')
            self.scaler = joblib.load(self.models_path / 'scaler.joblib')
            self.logger.info("Models loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
    
    def _prepare_prediction_features(self, player_data: Dict[str, Any]) -> np.ndarray:
        """
        Prepare features for prediction
        
        Args:
            player_data: Dictionary containing player data
            
        Returns:
            Array of features for prediction
        """
        try:
            # Extract features in the same order as training
            features = []
            
            # Recent form features (40% weight)
            recent_batting_features = [
                player_data.get('recent_runs', 0),
                player_data.get('recent_strike_rate', 0),
                player_data.get('recent_average', 0)
            ]
            recent_bowling_features = [
                player_data.get('recent_wickets', 0),
                player_data.get('recent_economy', 0),
                player_data.get('recent_bowling_avg', 0)
            ]
            features.extend([f * self.feature_weights['recent_form'] for f in recent_batting_features + recent_bowling_features])
            
            # Current tournament features (30% weight)
            current_batting_features = [
                player_data.get('current_runs', 0),
                player_data.get('current_strike_rate', 0),
                player_data.get('current_average', 0)
            ]
            current_bowling_features = [
                player_data.get('current_wickets', 0),
                player_data.get('current_economy', 0),
                player_data.get('current_bowling_avg', 0)
            ]
            features.extend([f * self.feature_weights['current_tournament'] for f in current_batting_features + current_bowling_features])
            
            # Historical features (20% weight)
            historical_batting_features = [
                player_data.get('historical_runs', 0),
                player_data.get('historical_strike_rate', 0),
                player_data.get('historical_average', 0)
            ]
            historical_bowling_features = [
                player_data.get('historical_wickets', 0),
                player_data.get('historical_economy', 0),
                player_data.get('historical_bowling_avg', 0)
            ]
            features.extend([f * self.feature_weights['historical'] for f in historical_batting_features + historical_bowling_features])
            
            # Venue features (10% weight)
            venue_batting_features = [
                player_data.get('venue_runs', 0),
                player_data.get('venue_strike_rate', 0),
                player_data.get('venue_average', 0)
            ]
            venue_bowling_features = [
                player_data.get('venue_wickets', 0),
                player_data.get('venue_economy', 0),
                player_data.get('venue_bowling_avg', 0)
            ]
            features.extend([f * self.feature_weights['venue'] for f in venue_batting_features + venue_bowling_features])
            
            # Additional features
            features.extend([
                player_data.get('match_importance', 1.0),
                player_data.get('team_strength', 0.5),
                player_data.get('opposition_strength', 0.5)
            ])
            
            # Convert to numpy array and reshape for prediction
            features = np.array(features).reshape(1, -1)
            
            # Ensure we have exactly 27 features
            if features.shape[1] != 27:
                self.logger.warning(f"Expected 27 features but got {features.shape[1]} features")
                if features.shape[1] > 27:
                    features = features[:, :27]
                else:
                    padding = np.zeros((1, 27 - features.shape[1]))
                    features = np.hstack([features, padding])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error preparing prediction features: {str(e)}")
            return np.zeros((1, 27))  # Return zeros if there's an error 