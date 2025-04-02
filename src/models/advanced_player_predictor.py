import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime

class AdvancedPlayerPredictor:
    """
    Advanced player performance prediction model that combines historical data with
    real-time updates for accurate predictions.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize models with optimized hyperparameters
        self.models = {
            'runs': XGBRegressor(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=5,
                min_child_weight=3,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1,
                random_state=42
            ),
            'wickets': RandomForestRegressor(
                n_estimators=150,
                max_depth=6,
                min_samples_split=8,
                min_samples_leaf=3,
                max_features='sqrt',
                bootstrap=True,
                random_state=42
            ),
            'strike_rate': GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=5,
                min_samples_split=8,
                min_samples_leaf=3,
                subsample=0.8,
                max_features='sqrt',
                random_state=42
            ),
            'economy_rate': GradientBoostingRegressor(
                n_estimators=150,
                learning_rate=0.05,
                max_depth=5,
                min_samples_split=8,
                min_samples_leaf=3,
                subsample=0.8,
                max_features='sqrt',
                random_state=42
            )
        }
        
        # Initialize scalers for each target
        self.scalers = {
            'runs': StandardScaler(),
            'wickets': StandardScaler(),
            'strike_rate': StandardScaler(),
            'economy_rate': StandardScaler()
        }
        
        # Core feature columns
        self.feature_columns = [
            # Player's recent performance
            'last_5_matches_runs_avg',
            'last_5_matches_wickets_avg',
            'last_5_matches_sr_avg',
            'last_5_matches_er_avg',
            'last_10_matches_runs_avg',
            'last_10_matches_wickets_avg',
            'last_10_matches_sr_avg',
            'last_10_matches_er_avg',
            
            # Player's career stats
            'career_runs_avg',
            'career_wickets_avg',
            'career_sr_avg',
            'career_er_avg',
            
            # Player's role-specific features
            'is_batsman',
            'is_bowler',
            'is_all_rounder',
            'is_wicket_keeper',
            
            # Player's form and consistency
            'form_factor',
            'consistency_score',
            
            # Match context
            'is_home_match',
            'is_day_match',
            'is_knockout_match',
            
            # Venue statistics
            'venue_avg_first_innings_score',
            'venue_avg_second_innings_score',
            'venue_avg_wickets_per_match',
            
            # Opposition strength
            'opposition_bowling_strength',
            'opposition_batting_strength',
            
            # Team strength
            'team_batting_strength',
            'team_bowling_strength',
            
            # Recent team form
            'team_last_5_matches_win_rate',
            
            # Weather and pitch conditions
            'is_pitch_batting_friendly',
            'is_pitch_bowling_friendly',
            'is_windy',
            'is_humid',
            
            # Player vs opposition history
            'player_vs_opposition_runs_avg',
            'player_vs_opposition_wickets_avg',
            'player_vs_opposition_sr_avg',
            'player_vs_opposition_er_avg',
            
            # Player vs venue history
            'player_at_venue_runs_avg',
            'player_at_venue_wickets_avg',
            'player_at_venue_sr_avg',
            'player_at_venue_er_avg',
            
            # Recent injuries and fitness
            'days_since_last_injury',
            'is_fully_fit'
        ]
        
        # Set up model paths
        self.base_path = Path(__file__).parent.parent.parent
        self.models_path = self.base_path / 'models' / 'saved'
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize model metadata
        self.model_metadata = {
            'last_trained': None,
            'training_samples': 0,
            'feature_importance': {},
            'metrics': {}
        }
    
    def prepare_features(self, player_data: Dict[str, Any]) -> np.ndarray:
        """
        Prepare features for prediction with advanced feature engineering
        
        Args:
            player_data: Dictionary containing player statistics and match context
            
        Returns:
            Numpy array of prepared features
        """
        features = []
        
        # Extract features from player_data
        for col in self.feature_columns:
            if col in player_data:
                features.append(player_data[col])
            else:
                # Default values based on feature type
                if 'avg' in col:
                    features.append(0.0)  # Default average
                elif 'is_' in col:
                    features.append(0)    # Default boolean
                elif 'factor' in col or 'score' in col or 'strength' in col or 'rate' in col:
                    features.append(0.5)  # Default normalized score
                elif 'days' in col:
                    features.append(30)   # Default days
                else:
                    features.append(0)    # Default other
        
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_data: pd.DataFrame, perform_grid_search: bool = False) -> Dict[str, Any]:
        """
        Train the prediction models with advanced validation and hyperparameter tuning
        
        Args:
            historical_data: DataFrame containing historical player performance data
            perform_grid_search: Whether to perform grid search for hyperparameter tuning
            
        Returns:
            Dictionary containing training metrics
        """
        try:
            self.logger.info("Starting model training...")
            
            # Handle missing values
            historical_data = self._preprocess_data(historical_data)
            
            # Split features and targets
            X = historical_data[self.feature_columns]
            targets = {
                'runs': historical_data['runs'],
                'wickets': historical_data['wickets'],
                'strike_rate': historical_data['strike_rate'],
                'economy_rate': historical_data['economy_rate']
            }
            
            # Train models for each target
            metrics = {}
            for target_name, target_values in targets.items():
                self.logger.info(f"Training model for {target_name}...")
                
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(
                    X, target_values, test_size=0.2, random_state=42
                )
                
                # Scale features
                X_train_scaled = self.scalers[target_name].fit_transform(X_train)
                X_test_scaled = self.scalers[target_name].transform(X_test)
                
                # Perform grid search if requested
                if perform_grid_search:
                    self.logger.info(f"Performing grid search for {target_name} model...")
                    self.models[target_name] = self._perform_grid_search(
                        self.models[target_name], X_train_scaled, y_train
                    )
                
                # Train the model
                self.models[target_name].fit(X_train_scaled, y_train)
                
                # Make predictions on test set
                y_pred = self.models[target_name].predict(X_test_scaled)
                
                # Calculate metrics
                metrics[target_name] = {
                    'mae': mean_absolute_error(y_test, y_pred),
                    'mse': mean_squared_error(y_test, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                    'r2': r2_score(y_test, y_pred)
                }
                
                # Store feature importance
                if hasattr(self.models[target_name], 'feature_importances_'):
                    importances = pd.DataFrame({
                        'feature': self.feature_columns,
                        'importance': self.models[target_name].feature_importances_
                    }).sort_values('importance', ascending=False)
                    
                    self.model_metadata['feature_importance'][target_name] = importances.to_dict('records')
            
            # Update model metadata
            self.model_metadata['last_trained'] = datetime.now().isoformat()
            self.model_metadata['training_samples'] = len(historical_data)
            self.model_metadata['metrics'] = metrics
            
            # Save models and metadata
            self.save_models()
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            raise
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess data for model training
        
        Args:
            data: Input DataFrame
            
        Returns:
            Preprocessed DataFrame
        """
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Ensure consistent column naming
        if 'Player' in df.columns:
            df = df.rename(columns={'Player': 'player'})
        
        # Handle missing values
        for col in self.feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        # Fill missing values with appropriate defaults
        df = df.fillna({
            col: 0.0 if 'avg' in col or 'rate' in col or 'score' in col or 'strength' in col
            else 0 if 'is_' in col
            else 30 if 'days' in col
            else 0.0
            for col in df.columns
        })
        
        return df
    
    def _perform_grid_search(self, model, X_train, y_train):
        """
        Perform grid search for hyperparameter tuning
        
        Args:
            model: The model to tune
            X_train: Training features
            y_train: Training targets
            
        Returns:
            Tuned model
        """
        if isinstance(model, XGBRegressor):
            param_grid = {
                'n_estimators': [100, 150, 200],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 4, 5, 6],
                'min_child_weight': [1, 3, 5],
                'subsample': [0.7, 0.8, 0.9]
            }
        elif isinstance(model, RandomForestRegressor):
            param_grid = {
                'n_estimators': [100, 150, 200],
                'max_depth': [4, 6, 8, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif isinstance(model, GradientBoostingRegressor):
            param_grid = {
                'n_estimators': [100, 150, 200],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 4, 5],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'subsample': [0.7, 0.8, 0.9]
            }
        else:
            return model
        
        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            cv=3,
            n_jobs=-1,
            scoring='neg_mean_squared_error'
        )
        
        grid_search.fit(X_train, y_train)
        
        self.logger.info(f"Best parameters: {grid_search.best_params_}")
        
        return grid_search.best_estimator_
    
    def predict(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make predictions with confidence intervals
        
        Args:
            player_data: Dictionary containing player statistics and match context
            
        Returns:
            Dictionary containing predictions with confidence intervals
        """
        try:
            # Prepare features
            features = self.prepare_features(player_data)
            
            # Make predictions for each target
            predictions = {}
            for target_name, model in self.models.items():
                # Scale features
                features_scaled = self.scalers[target_name].transform(features)
                
                # Make prediction
                pred_value = model.predict(features_scaled)[0]
                
                # Calculate confidence interval
                if hasattr(model, 'estimators_'):
                    # For ensemble models, use the variance of individual estimator predictions
                    estimator_preds = np.array([tree.predict(features_scaled)[0] for tree in model.estimators_])
                    std_dev = np.std(estimator_preds)
                    
                    # 95% confidence interval (1.96 standard deviations)
                    lower_bound = max(0, pred_value - 1.96 * std_dev)
                    upper_bound = pred_value + 1.96 * std_dev
                else:
                    # For non-ensemble models, use a default uncertainty
                    lower_bound = max(0, pred_value * 0.8)
                    upper_bound = pred_value * 1.2
                
                # Store prediction with confidence interval
                predictions[target_name] = {
                    'value': max(0, round(pred_value, 2)),
                    'lower_bound': round(lower_bound, 2),
                    'upper_bound': round(upper_bound, 2),
                    'confidence': 0.95  # 95% confidence interval
                }
            
            # Add match context to predictions
            predictions['match_context'] = {
                'player_name': player_data.get('player_name', 'Unknown'),
                'team': player_data.get('team', 'Unknown'),
                'opposition': player_data.get('opposition', 'Unknown'),
                'venue': player_data.get('venue', 'Unknown'),
                'match_date': player_data.get('match_date', 'Unknown'),
                'match_type': player_data.get('match_type', 'League')
            }
            
            # Add prediction timestamp
            predictions['timestamp'] = datetime.now().isoformat()
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def predict_batch(self, player_data_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of players
        
        Args:
            player_data_batch: List of dictionaries containing player statistics and match context
            
        Returns:
            List of dictionaries containing predictions
        """
        return [self.predict(player_data) for player_data in player_data_batch]
    
    def save_models(self):
        """Save trained models and metadata to disk"""
        try:
            # Create timestamp for versioning
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save models
            for target_name, model in self.models.items():
                model_path = self.models_path / f"{target_name}_model_{timestamp}.joblib"
                joblib.dump(model, model_path)
                self.logger.info(f"Saved {target_name} model to {model_path}")
            
            # Save scalers
            for target_name, scaler in self.scalers.items():
                scaler_path = self.models_path / f"{target_name}_scaler_{timestamp}.joblib"
                joblib.dump(scaler, scaler_path)
                self.logger.info(f"Saved {target_name} scaler to {scaler_path}")
            
            # Save metadata
            metadata_path = self.models_path / f"model_metadata_{timestamp}.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.model_metadata, f, indent=4)
            self.logger.info(f"Saved model metadata to {metadata_path}")
            
            # Save latest model info
            latest_info = {
                'timestamp': timestamp,
                'models': {target_name: f"{target_name}_model_{timestamp}.joblib" for target_name in self.models.keys()},
                'scalers': {target_name: f"{target_name}_scaler_{timestamp}.joblib" for target_name in self.scalers.keys()},
                'metadata': f"model_metadata_{timestamp}.json"
            }
            
            latest_info_path = self.models_path / "latest_model_info.json"
            with open(latest_info_path, 'w') as f:
                json.dump(latest_info, f, indent=4)
            self.logger.info(f"Updated latest model info at {latest_info_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
            raise
    
    def load_models(self, timestamp: Optional[str] = None):
        """
        Load trained models from disk
        
        Args:
            timestamp: Optional timestamp to load specific model version.
                      If None, loads the latest models.
        """
        try:
            # Determine which models to load
            if timestamp is None:
                # Load latest models
                latest_info_path = self.models_path / "latest_model_info.json"
                if not latest_info_path.exists():
                    self.logger.warning("No saved models found. Using default models.")
                    return
                
                with open(latest_info_path, 'r') as f:
                    latest_info = json.load(f)
                
                timestamp = latest_info['timestamp']
            
            # Load models
            for target_name in self.models.keys():
                model_path = self.models_path / f"{target_name}_model_{timestamp}.joblib"
                if model_path.exists():
                    self.models[target_name] = joblib.load(model_path)
                    self.logger.info(f"Loaded {target_name} model from {model_path}")
                else:
                    self.logger.warning(f"Model file {model_path} not found. Using default model.")
            
            # Load scalers
            for target_name in self.scalers.keys():
                scaler_path = self.models_path / f"{target_name}_scaler_{timestamp}.joblib"
                if scaler_path.exists():
                    self.scalers[target_name] = joblib.load(scaler_path)
                    self.logger.info(f"Loaded {target_name} scaler from {scaler_path}")
                else:
                    self.logger.warning(f"Scaler file {scaler_path} not found. Using default scaler.")
            
            # Load metadata
            metadata_path = self.models_path / f"model_metadata_{timestamp}.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.model_metadata = json.load(f)
                self.logger.info(f"Loaded model metadata from {metadata_path}")
            else:
                self.logger.warning(f"Metadata file {metadata_path} not found.")
            
        except Exception as e:
            self.logger.error(f"Error loading models: {str(e)}")
            raise
    
    def calculate_metrics(self, actual_data: pd.DataFrame, predictions: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate performance metrics for model evaluation
        
        Args:
            actual_data: DataFrame containing actual player performance
            predictions: List of dictionaries containing predictions
            
        Returns:
            Dictionary containing metrics for each target
        """
        metrics = {}
        
        # Extract actual values
        actual_values = {
            'runs': actual_data['runs'].values,
            'wickets': actual_data['wickets'].values,
            'strike_rate': actual_data['strike_rate'].values,
            'economy_rate': actual_data['economy_rate'].values
        }
        
        # Extract predicted values
        predicted_values = {
            'runs': np.array([pred['runs']['value'] for pred in predictions]),
            'wickets': np.array([pred['wickets']['value'] for pred in predictions]),
            'strike_rate': np.array([pred['strike_rate']['value'] for pred in predictions]),
            'economy_rate': np.array([pred['economy_rate']['value'] for pred in predictions])
        }
        
        # Calculate metrics for each target
        for target_name in actual_values.keys():
            metrics[target_name] = {
                'mae': mean_absolute_error(actual_values[target_name], predicted_values[target_name]),
                'mse': mean_squared_error(actual_values[target_name], predicted_values[target_name]),
                'rmse': np.sqrt(mean_squared_error(actual_values[target_name], predicted_values[target_name])),
                'r2': r2_score(actual_values[target_name], predicted_values[target_name])
            }
        
        return metrics
