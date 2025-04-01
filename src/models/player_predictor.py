import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
from datetime import datetime

class PlayerPredictor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {
            'runs': XGBRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1,
                random_state=42
            ),
            'wickets': RandomForestRegressor(
                n_estimators=100,
                max_depth=6,
                min_samples_split=10,
                min_samples_leaf=4,
                max_features='sqrt',
                bootstrap=True,
                random_state=42
            ),
            'strike_rate': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                min_samples_split=10,
                min_samples_leaf=4,
                subsample=0.8,
                max_features='sqrt',
                random_state=42
            ),
            'economy_rate': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                min_samples_split=10,
                min_samples_leaf=4,
                subsample=0.8,
                max_features='sqrt',
                random_state=42
            )
        }
        self.scaler = StandardScaler()
        self.feature_columns = [
            # Core Performance Features
            'last_5_matches_runs_avg',
            'last_5_matches_wickets_avg',
            'last_5_matches_sr_avg',
            'last_5_matches_er_avg',
            
            # Derived Features
            'form_factor',
            'consistency_score',
            'pressure_index',
            
            # Match Context
            'days_since_last_match',
            'is_home_game',
            'is_powerplay_batsman',
            'is_death_bowler',
            
            # Basic Stats
            'runs_mean', 'runs_std',
            'wickets_mean', 'wickets_std',
            'strike_rate_mean', 'strike_rate_std',
            'economy_rate_mean', 'economy_rate_std'
        ]
        
        # Set up model paths
        self.base_path = Path(__file__).parent.parent.parent
        self.models_path = self.base_path / 'models' / 'saved'
        self.models_path.mkdir(parents=True, exist_ok=True)
    
    def prepare_features(self, player_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for prediction with advanced feature engineering"""
        features = []
        for col in self.feature_columns:
            if col in player_data:
                features.append(player_data[col])
            else:
                # Advanced default value calculation based on feature type
                if 'avg' in col:
                    features.append(0.0)
                elif 'is_' in col:
                    features.append(0)
                elif 'factor' in col or 'score' in col or 'index' in col:
                    features.append(0.5)  # Neutral value for derived features
                elif 'mean' in col:
                    features.append(0.0)  # Default mean
                elif 'std' in col:
                    features.append(1.0)  # Default standard deviation
                else:
                    features.append(0)
        
        # Add derived features
        features.extend([
            # Form factor (recent performance vs career average)
            player_data.get('form_factor', 1.0),
            
            # Pressure index (based on match importance and player role)
            player_data.get('pressure_index', 0.5),
            
            # Consistency score (based on performance variance)
            player_data.get('consistency_score', 0.5)
        ])
        
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_data: pd.DataFrame):
        """Train the prediction models with advanced validation and feature importance analysis"""
        try:
            self.logger.info("Starting model training...")
            
            # Handle missing values
            historical_data = historical_data.fillna({
                col: 0.0 if 'avg' in col or 'mean' in col else 1.0 if 'std' in col else 0
                for col in self.feature_columns
            })
            
            # Split features and targets
            X = historical_data[self.feature_columns]
            targets = {
                'runs': historical_data['runs'],
                'wickets': historical_data['wickets'],
                'strike_rate': historical_data['strike_rate'],
                'economy_rate': historical_data['economy_rate']
            }
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            X_scaled_df = pd.DataFrame(X_scaled, columns=self.feature_columns)
            
            # Train models with cross-validation and feature importance analysis
            for name, model in self.models.items():
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled_df, targets[name], test_size=0.2, random_state=42
                )
                
                # Perform cross-validation
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                self.logger.info(f"{name} model CV scores: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
                
                # Train final model
                model.fit(X_train, y_train)
                
                # Evaluate on test set
                y_pred = model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                self.logger.info(f"{name} model MSE: {mse:.3f}, R²: {r2:.3f}")
                
                # Feature importance analysis
                if hasattr(model, 'feature_importances_'):
                    importances = pd.DataFrame({
                        'feature': self.feature_columns,
                        'importance': model.feature_importances_
                    }).sort_values('importance', ascending=False)
                    self.logger.info(f"\nTop 5 important features for {name} prediction:")
                    for _, row in importances.head().iterrows():
                        self.logger.info(f"{row['feature']}: {row['importance']:.3f}")
            
            # Save models
            self.save_models()
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            raise
    
    def predict(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make predictions with confidence intervals"""
        try:
            # Prepare features
            features = self.prepare_features(player_data)
            features_scaled = self.scaler.transform(features)
            
            # Make predictions with confidence intervals
            predictions = {}
            for name, model in self.models.items():
                pred = model.predict(features_scaled)[0]
                std = np.std([tree.predict(features_scaled) for tree in model.estimators_])
                predictions[name] = {
                    'value': max(0, round(pred, 2)),
                    'lower_bound': max(0, round(pred - 1.96 * std, 2)),
                    'upper_bound': max(0, round(pred + 1.96 * std, 2))
                }
            
            # Calculate confidence scores
            confidence = self._calculate_confidence(features_scaled)
            
            # Determine form and momentum
            form = self._determine_form(predictions, player_data)
            momentum = self._calculate_momentum(player_data)
            
            return {
                'runs': predictions['runs']['value'],
                'runs_ci': (predictions['runs']['lower_bound'], predictions['runs']['upper_bound']),
                'wickets': predictions['wickets']['value'],
                'wickets_ci': (predictions['wickets']['lower_bound'], predictions['wickets']['upper_bound']),
                'strike_rate': predictions['strike_rate']['value'],
                'strike_rate_ci': (predictions['strike_rate']['lower_bound'], predictions['strike_rate']['upper_bound']),
                'economy_rate': predictions['economy_rate']['value'],
                'economy_rate_ci': (predictions['economy_rate']['lower_bound'], predictions['economy_rate']['upper_bound']),
                'confidence': confidence,
                'form': form,
                'momentum': momentum
            }
            
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            return {
                'error': str(e),
                'runs': 0,
                'wickets': 0,
                'strike_rate': 0,
                'economy_rate': 0,
                'confidence': 0,
                'form': 'Unknown',
                'momentum': 'Neutral'
            }
    
    def _calculate_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence score with advanced metrics"""
        confidence = 0.0
        
        # Feature completeness
        non_zero_features = np.count_nonzero(features)
        feature_completeness = non_zero_features / len(self.feature_columns)
        confidence += feature_completeness * 0.3
        
        # Feature variance
        feature_variance = np.var(features)
        confidence += min(1.0, feature_variance) * 0.2
        
        # Model performance
        model_confidence = 0.7  # This should be calculated based on model performance metrics
        confidence += model_confidence * 0.5
        
        return min(1.0, confidence)
    
    def _determine_form(self, predictions: Dict[str, Any], player_data: Dict[str, Any]) -> str:
        """Determine player's current form with advanced metrics"""
        if 'last_5_matches_runs_avg' not in player_data:
            return 'Unknown'
            
        recent_avg = player_data['last_5_matches_runs_avg']
        predicted = predictions['runs']['value']
        
        # Calculate form factor
        form_factor = predicted / recent_avg if recent_avg > 0 else 1.0
        
        if form_factor > 1.3:
            return 'Excellent'
        elif form_factor > 1.1:
            return 'Good'
        elif form_factor > 0.9:
            return 'Average'
        else:
            return 'Poor'
    
    def _calculate_momentum(self, player_data: Dict[str, Any]) -> str:
        """Calculate player's momentum based on recent performance trend"""
        if 'last_5_matches_runs_avg' not in player_data:
            return 'Neutral'
            
        recent_scores = player_data.get('last_5_matches_scores', [])
        if len(recent_scores) < 2:
            return 'Neutral'
            
        # Calculate trend
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]
        
        if trend > 0.5:
            return 'Strong Upward'
        elif trend > 0.2:
            return 'Upward'
        elif trend < -0.5:
            return 'Strong Downward'
        elif trend < -0.2:
            return 'Downward'
        else:
            return 'Neutral'
    
    def save_models(self):
        """Save trained models with metadata"""
        try:
            for name, model in self.models.items():
                model_path = self.models_path / f"{name}_model.joblib"
                joblib.dump(model, model_path)
            
            scaler_path = self.models_path / "scaler.joblib"
            joblib.dump(self.scaler, scaler_path)
            
            # Save model metadata
            metadata = {
                'feature_columns': self.feature_columns,
                'model_types': {name: type(model).__name__ for name, model in self.models.items()},
                'last_trained': datetime.now().isoformat()
            }
            
            with open(self.models_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)
            
            self.logger.info("Models and metadata saved successfully")
            
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
            raise
    
    def load_models(self):
        """Load trained models and metadata"""
        try:
            for name in self.models.keys():
                model_path = self.models_path / f"{name}_model.joblib"
                if model_path.exists():
                    self.models[name] = joblib.load(model_path)
            
            scaler_path = self.models_path / "scaler.joblib"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            
            # Load metadata
            metadata_path = self.models_path / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    self.feature_columns = metadata['feature_columns']
            
            self.logger.info("Models and metadata loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            raise
    
    def predict_batch(self, data: pd.DataFrame) -> pd.DataFrame:
        """Make predictions for a batch of players"""
        try:
            predictions = []
            for _, row in data.iterrows():
                player_data = row.to_dict()
                pred = self.predict(player_data)
                predictions.append(pred)
            
            return pd.DataFrame(predictions)
            
        except Exception as e:
            self.logger.error(f"Error in batch prediction: {str(e)}")
            raise
    
    def calculate_metrics(self, actual_data: pd.DataFrame, predictions: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance metrics for the models"""
        try:
            metrics = {}
            
            # Calculate metrics for each target variable
            for target in ['runs', 'wickets', 'strike_rate', 'economy_rate']:
                if target in actual_data.columns and target in predictions.columns:
                    # Mean Absolute Error
                    mae = np.mean(np.abs(actual_data[target] - predictions[target]))
                    metrics[f'{target}_mae'] = mae
                    
                    # Root Mean Square Error
                    rmse = np.sqrt(np.mean((actual_data[target] - predictions[target])**2))
                    metrics[f'{target}_rmse'] = rmse
                    
                    # R-squared Score
                    r2 = 1 - np.sum((actual_data[target] - predictions[target])**2) / np.sum((actual_data[target] - actual_data[target].mean())**2)
                    metrics[f'{target}_r2'] = r2
            
            # Calculate overall metrics
            metrics['mean_confidence'] = predictions['confidence'].mean()
            metrics['prediction_std'] = predictions['confidence'].std()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            raise 