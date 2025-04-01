import numpy as np
from typing import Dict, Any
import logging
from pathlib import Path
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

class PredictionModel:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.models_path = self.base_path / 'models'
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.runs_model = None
        self.wickets_model = None
        self.sr_model = None
        self.er_model = None
        self.scaler = StandardScaler()
        
        # Load models if they exist
        self._load_models()
        
        # Define feature importance weights
        self.feature_weights = {
            'recent_performance': 0.3,
            'form_factor': 0.2,
            'context': 0.2,
            'team_venue': 0.2,
            'weather': 0.1
        }
    
    def _load_models(self):
        """Load trained models if they exist"""
        try:
            if (self.models_path / 'runs_model.joblib').exists():
                self.runs_model = joblib.load(self.models_path / 'runs_model.joblib')
            if (self.models_path / 'wickets_model.joblib').exists():
                self.wickets_model = joblib.load(self.models_path / 'wickets_model.joblib')
            if (self.models_path / 'sr_model.joblib').exists():
                self.sr_model = joblib.load(self.models_path / 'sr_model.joblib')
            if (self.models_path / 'er_model.joblib').exists():
                self.er_model = joblib.load(self.models_path / 'er_model.joblib')
            if (self.models_path / 'scaler.joblib').exists():
                self.scaler = joblib.load(self.models_path / 'scaler.joblib')
                
            self.logger.info("Models loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Make predictions using the statistical approach"""
        try:
            # If models are available, use them
            if all([self.runs_model, self.wickets_model, self.sr_model, self.er_model]):
                return self._predict_with_models(features)
            
            # Otherwise, use the statistical approach
            return self._predict_statistical(features)
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return self._get_default_prediction()
    
    def _predict_with_models(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Make predictions using trained models"""
        # Convert features to DataFrame
        feature_df = pd.DataFrame([features])
        
        # Scale features
        scaled_features = self.scaler.transform(feature_df)
        
        # Make predictions
        predictions = {
            'runs': float(self.runs_model.predict(scaled_features)[0]),
            'wickets': float(self.wickets_model.predict(scaled_features)[0]),
            'strike_rate': float(self.sr_model.predict(scaled_features)[0]),
            'economy_rate': float(self.er_model.predict(scaled_features)[0])
        }
        
        # Calculate confidence score
        predictions['confidence'] = self._calculate_confidence(predictions, features)
        
        return predictions
    
    def _predict_statistical(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Make predictions using statistical approach"""
        # Calculate base predictions
        base_runs = self._calculate_base_runs(features)
        base_wickets = self._calculate_base_wickets(features)
        base_sr = self._calculate_base_sr(features)
        base_er = self._calculate_base_er(features)
        
        # Apply adjustments
        runs = self._apply_adjustments(base_runs, features)
        wickets = self._apply_adjustments(base_wickets, features)
        sr = self._apply_adjustments(base_sr, features)
        er = self._apply_adjustments(base_er, features)
        
        # Calculate confidence score
        confidence = self._calculate_confidence({
            'runs': runs,
            'wickets': wickets,
            'strike_rate': sr,
            'economy_rate': er
        }, features)
        
        return {
            'runs': runs,
            'wickets': wickets,
            'strike_rate': sr,
            'economy_rate': er,
            'confidence': confidence
        }
    
    def _calculate_base_runs(self, features: Dict[str, Any]) -> float:
        """Calculate base runs prediction"""
        recent_runs = features.get('recent_runs_avg', 0)
        career_runs = features.get('career_runs_avg', 0)
        form_factor = features.get('form_factor', 1.0)
        
        # Weight recent and career performance
        base_runs = (0.6 * recent_runs + 0.4 * career_runs) * form_factor
        
        return max(0, base_runs)
    
    def _calculate_base_wickets(self, features: Dict[str, Any]) -> float:
        """Calculate base wickets prediction"""
        recent_wickets = features.get('recent_wickets_avg', 0)
        career_wickets = features.get('career_wickets_avg', 0)
        form_factor = features.get('form_factor', 1.0)
        
        # Weight recent and career performance
        base_wickets = (0.6 * recent_wickets + 0.4 * career_wickets) * form_factor
        
        return max(0, base_wickets)
    
    def _calculate_base_sr(self, features: Dict[str, Any]) -> float:
        """Calculate base strike rate prediction"""
        recent_sr = features.get('recent_sr_avg', 0)
        career_sr = features.get('career_sr_avg', 0)
        form_factor = features.get('form_factor', 1.0)
        
        # Weight recent and career performance
        base_sr = (0.6 * recent_sr + 0.4 * career_sr) * form_factor
        
        return max(0, base_sr)
    
    def _calculate_base_er(self, features: Dict[str, Any]) -> float:
        """Calculate base economy rate prediction"""
        recent_er = features.get('recent_er_avg', 0)
        career_er = features.get('career_er_avg', 0)
        form_factor = features.get('form_factor', 1.0)
        
        # Weight recent and career performance
        base_er = (0.6 * recent_er + 0.4 * career_er) * form_factor
        
        return max(0, base_er)
    
    def _apply_adjustments(self, base_value: float, features: Dict[str, Any]) -> float:
        """Apply context-based adjustments to base predictions"""
        adjusted_value = base_value
        
        # Apply context adjustments
        if features.get('is_home_game', False):
            adjusted_value *= 1.1  # 10% boost for home games
        
        # Apply weather adjustments
        weather_batting_factor = features.get('weather_batting_factor', 1.0)
        weather_bowling_factor = features.get('weather_bowling_factor', 1.0)
        
        # Apply venue adjustments
        venue_runs_factor = features.get('venue_runs_factor', 1.0)
        venue_wickets_factor = features.get('venue_wickets_factor', 1.0)
        
        # Apply team strength adjustments
        team_strength = features.get('team_strength', 0.5)
        opposition_strength = features.get('opposition_strength', 0.5)
        
        # Calculate final adjustment
        adjustment = (
            weather_batting_factor * 0.3 +
            weather_bowling_factor * 0.3 +
            venue_runs_factor * 0.2 +
            venue_wickets_factor * 0.2
        )
        
        # Apply team strength adjustment
        team_adjustment = (team_strength - opposition_strength) * 0.1
        
        # Apply final adjustments
        adjusted_value *= (adjustment + team_adjustment)
        
        return max(0, adjusted_value)
    
    def _calculate_confidence(self, predictions: Dict[str, float], features: Dict[str, Any]) -> float:
        """Calculate confidence score for predictions"""
        confidence_factors = []
        
        # Recent performance consistency
        if features.get('recent_performance'):
            consistency = np.std(features['recent_performance'])
            confidence_factors.append(1 - min(1, consistency / 50))
        
        # Form factor confidence
        form_factor = features.get('form_factor', 1.0)
        confidence_factors.append(1 - abs(1 - form_factor))
        
        # Context confidence
        context_factors = [
            features.get('is_home_game', False),
            features.get('weather_batting_factor', 1.0),
            features.get('venue_runs_factor', 1.0)
        ]
        context_confidence = np.mean([1 - abs(1 - factor) for factor in context_factors])
        confidence_factors.append(context_confidence)
        
        # Calculate final confidence score
        confidence = np.mean(confidence_factors)
        
        return max(0, min(1, confidence))
    
    def _get_default_prediction(self) -> Dict[str, float]:
        """Return default prediction values"""
        return {
            'runs': 20.0,
            'wickets': 1.0,
            'strike_rate': 120.0,
            'economy_rate': 8.0,
            'confidence': 0.5
        } 