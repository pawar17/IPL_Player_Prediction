import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import logging
from pathlib import Path
from typing import Tuple, Dict, List
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CricketPlayerPredictor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.model_path = self.base_path / 'models'
        self.model_path.mkdir(exist_ok=True)
        
        # Model parameters
        self.n_estimators = 200
        self.random_state = 42
        self.test_size = 0.2
        self.n_jobs = -1
        self.min_samples_leaf = 2
        
        # Initialize models
        self.batting_model = RandomForestRegressor(n_estimators=self.n_estimators, min_samples_leaf=self.min_samples_leaf, random_state=self.random_state)
        self.bowling_model = RandomForestRegressor(n_estimators=self.n_estimators, min_samples_leaf=self.min_samples_leaf, random_state=self.random_state)
        self.fielding_model = RandomForestRegressor(n_estimators=self.n_estimators, min_samples_leaf=self.min_samples_leaf, random_state=self.random_state)
        
        # Feature sets
        self.batting_features = [
            'Batting_Average', 'Batting_Strike_Rate',
            'Batting_Average_3yr_avg', 'Batting_Strike_Rate_3yr_avg',
            'Career_Batting_Average', 'Career_Batting_Strike_Rate',
            'Career_Runs_Scored', 'Runs_Scored_3yr_avg',
            'matches_played'
        ]
        
        self.bowling_features = [
            'Bowling_Average', 'Economy_Rate',
            'Bowling_Average_3yr_avg', 'Economy_Rate_3yr_avg',
            'Career_Wickets_Taken', 'Wickets_Taken_3yr_avg'
        ]
        
        self.fielding_features = [
            'Career_Catches_Taken', 'Career_Stumpings'
        ]
        
    def prepare_data(self) -> pd.DataFrame:
        """Load and prepare data for training"""
        try:
            # Load historical data
            data = pd.read_csv(self.data_path / 'processed' / 'combined_data.csv')
            
            # Convert data types and handle missing values
            for feature in self.batting_features + self.bowling_features + self.fielding_features:
                if feature in data.columns:
                    data[feature] = pd.to_numeric(data[feature], errors='coerce').fillna(0)
            
            # Create target variables (next match performance)
            data['next_match_runs'] = data.groupby('Player_Name')['Runs_Scored'].shift(-1)
            data['next_match_wickets'] = data.groupby('Player_Name')['Wickets_Taken'].shift(-1)
            data['next_match_catches'] = data.groupby('Player_Name')['Career_Catches_Taken'].shift(-1)
            
            # Add recent form features
            data['recent_form_runs'] = data.groupby('Player_Name')['Runs_Scored'].rolling(window=3).mean().reset_index(0, drop=True)
            data['recent_form_wickets'] = data.groupby('Player_Name')['Wickets_Taken'].rolling(window=3).mean().reset_index(0, drop=True)
            data['recent_form_catches'] = data.groupby('Player_Name')['Career_Catches_Taken'].rolling(window=3).mean().reset_index(0, drop=True)
            
            # Add player role features
            data['is_batsman'] = (data['Career_Batting_Average'] > 25).astype(int)
            data['is_bowler'] = (data['Career_Wickets_Taken'] > 20).astype(int)
            data['is_all_rounder'] = ((data['Career_Batting_Average'] > 15) & (data['Career_Wickets_Taken'] > 10)).astype(int)
            
            # Drop rows with NaN targets
            data = data.dropna(subset=['next_match_runs', 'next_match_wickets', 'next_match_catches'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            raise
            
    def train_models(self) -> None:
        """Train batting, bowling and fielding models"""
        try:
            data = self.prepare_data()
            
            # Add recent form features to feature sets
            batting_features = self.batting_features + ['recent_form_runs', 'is_batsman', 'is_all_rounder']
            bowling_features = self.bowling_features + ['recent_form_wickets', 'is_bowler', 'is_all_rounder']
            fielding_features = self.fielding_features + ['recent_form_catches']
            
            # Train batting model
            X_bat = data[batting_features]
            y_bat = data['next_match_runs']
            self.batting_model.fit(X_bat, y_bat)
            
            # Train bowling model
            X_bowl = data[bowling_features]
            y_bowl = data['next_match_wickets']
            self.bowling_model.fit(X_bowl, y_bowl)
            
            # Train fielding model
            X_field = data[fielding_features]
            y_field = data['next_match_catches']
            self.fielding_model.fit(X_field, y_field)
            
            # Save models
            self._save_models()
            
        except Exception as e:
            logger.error(f"Error training models: {str(e)}")
            raise
            
    def _save_models(self) -> None:
        """Save trained models to disk"""
        joblib.dump(self.batting_model, self.model_path / 'batting_model.joblib')
        joblib.dump(self.bowling_model, self.model_path / 'bowling_model.joblib')
        joblib.dump(self.fielding_model, self.model_path / 'fielding_model.joblib')
        logger.info("Models saved successfully")
        
    def predict_player_performance(self, player_stats: Dict) -> Dict:
        """Predict player performance with confidence intervals"""
        try:
            # Prepare feature vectors
            batting_features = self.batting_features + ['recent_form_runs', 'is_batsman', 'is_all_rounder']
            bowling_features = self.bowling_features + ['recent_form_wickets', 'is_bowler', 'is_all_rounder']
            fielding_features = self.fielding_features + ['recent_form_catches']
            
            # Add role features
            player_stats['is_batsman'] = int(player_stats.get('Career_Batting_Average', 0) > 25)
            player_stats['is_bowler'] = int(player_stats.get('Career_Wickets_Taken', 0) > 20)
            player_stats['is_all_rounder'] = int((player_stats.get('Career_Batting_Average', 0) > 15) and 
                                               (player_stats.get('Career_Wickets_Taken', 0) > 10))
            
            # Add recent form if available
            player_stats['recent_form_runs'] = player_stats.get('Runs_Scored_3yr_avg', 0)
            player_stats['recent_form_wickets'] = player_stats.get('Wickets_Taken_3yr_avg', 0)
            player_stats['recent_form_catches'] = player_stats.get('Career_Catches_Taken', 0) / max(1, player_stats.get('matches_played', 1))
            
            # Create feature vectors
            X_bat = pd.DataFrame([{k: player_stats.get(k, 0) for k in batting_features}])
            X_bowl = pd.DataFrame([{k: player_stats.get(k, 0) for k in bowling_features}])
            X_field = pd.DataFrame([{k: player_stats.get(k, 0) for k in fielding_features}])
            
            # Get predictions from all trees
            batting_preds = np.array([tree.predict(X_bat) for tree in self.batting_model.estimators_])
            bowling_preds = np.array([tree.predict(X_bowl) for tree in self.bowling_model.estimators_])
            fielding_preds = np.array([tree.predict(X_field) for tree in self.fielding_model.estimators_])
            
            # Calculate mean predictions and confidence intervals
            predictions = {
                'batting': {
                    'predicted_runs': float(np.mean(batting_preds)),
                    'confidence_interval': (
                        float(np.percentile(batting_preds, 2.5)),
                        float(np.percentile(batting_preds, 97.5))
                    )
                },
                'bowling': {
                    'predicted_wickets': float(np.mean(bowling_preds)),
                    'confidence_interval': (
                        float(np.percentile(bowling_preds, 2.5)),
                        float(np.percentile(bowling_preds, 97.5))
                    )
                },
                'fielding': {
                    'predicted_catches': float(np.mean(fielding_preds)),
                    'confidence_interval': (
                        float(np.percentile(fielding_preds, 2.5)),
                        float(np.percentile(fielding_preds, 97.5))
                    )
                }
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            raise

if __name__ == '__main__':
    predictor = CricketPlayerPredictor()
    predictor.train_models() 