import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from pathlib import Path
import logging
from typing import Dict, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / 'data' / 'processed'
        self.models_path = self.base_path / 'models'
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.batting_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.bowling_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.fielding_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
    def load_data(self) -> pd.DataFrame:
        """Load the processed data"""
        logger.info("Loading processed data...")
        data = pd.read_csv(self.data_path / 'combined_data.csv')
        logger.info(f"Loaded {len(data)} records")
        return data
        
    def prepare_features(self, data: pd.DataFrame) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """Prepare features and targets for training"""
        logger.info("Preparing features...")
        
        # Batting features
        batting_features = [
            'Batting_Average', 'Batting_Strike_Rate', 'Runs_Scored',
            'Balls_Faced', 'Innings_Batted', 'Recent_Form_Runs',
            'Recent_Form_SR'
        ]
        
        # Bowling features
        bowling_features = [
            'Bowling_Average', 'Economy_Rate', 'Balls_Bowled',
            'Runs_Conceded', 'Wickets', 'Recent_Form_Wickets',
            'Recent_Form_Economy'
        ]
        
        # Fielding features - using available metrics as proxy
        fielding_features = [
            'Innings_Batted',  # Using innings played as a proxy for fielding opportunities
            'Recent_Form_Wickets'  # Using recent wickets as a proxy for fielding involvement
        ]
        
        # Prepare feature sets
        X_batting = data[batting_features].fillna(0).values
        X_bowling = data[bowling_features].fillna(0).values
        X_fielding = data[fielding_features].fillna(0).values
        
        # Prepare targets
        y_batting = data['Runs_Scored'].fillna(0).values
        y_bowling = data['Wickets'].fillna(0).values
        y_fielding = data['Recent_Form_Wickets'].fillna(0).values  # Using recent wickets as a proxy for catches
        
        return {
            'batting': (X_batting, y_batting),
            'bowling': (X_bowling, y_bowling),
            'fielding': (X_fielding, y_fielding)
        }
        
    def train_models(self, feature_sets: Dict[str, Tuple[np.ndarray, np.ndarray]]) -> Dict[str, Dict]:
        """Train all models and return performance metrics"""
        logger.info("Training models...")
        metrics = {}
        
        # Train batting model
        X_batting, y_batting = feature_sets['batting']
        X_train, X_val, y_train, y_val = train_test_split(X_batting, y_batting, test_size=0.2, random_state=42)
        self.batting_model.fit(X_train, y_train)
        batting_pred = self.batting_model.predict(X_val)
        metrics['batting'] = {
            'mse': mean_squared_error(y_val, batting_pred),
            'r2': r2_score(y_val, batting_pred)
        }
        
        # Train bowling model
        X_bowling, y_bowling = feature_sets['bowling']
        X_train, X_val, y_train, y_val = train_test_split(X_bowling, y_bowling, test_size=0.2, random_state=42)
        self.bowling_model.fit(X_train, y_train)
        bowling_pred = self.bowling_model.predict(X_val)
        metrics['bowling'] = {
            'mse': mean_squared_error(y_val, bowling_pred),
            'r2': r2_score(y_val, bowling_pred)
        }
        
        # Train fielding model
        X_fielding, y_fielding = feature_sets['fielding']
        X_train, X_val, y_train, y_val = train_test_split(X_fielding, y_fielding, test_size=0.2, random_state=42)
        self.fielding_model.fit(X_train, y_train)
        fielding_pred = self.fielding_model.predict(X_val)
        metrics['fielding'] = {
            'mse': mean_squared_error(y_val, fielding_pred),
            'r2': r2_score(y_val, fielding_pred)
        }
        
        return metrics
        
    def save_models(self):
        """Save trained models"""
        logger.info("Saving models...")
        joblib.dump(self.batting_model, self.models_path / 'batting_model.joblib')
        joblib.dump(self.bowling_model, self.models_path / 'bowling_model.joblib')
        joblib.dump(self.fielding_model, self.models_path / 'fielding_model.joblib')
        
    def run_training(self):
        """Run the complete training pipeline"""
        try:
            # Load data
            data = self.load_data()
            
            # Prepare features
            feature_sets = self.prepare_features(data)
            
            # Train models
            metrics = self.train_models(feature_sets)
            
            # Save models
            self.save_models()
            
            # Log results
            logger.info("\nTraining Results:")
            for model_type, model_metrics in metrics.items():
                logger.info(f"\n{model_type.title()} Model:")
                logger.info(f"MSE: {model_metrics['mse']:.4f}")
                logger.info(f"R2 Score: {model_metrics['r2']:.4f}")
                
        except Exception as e:
            logger.error(f"Error during training: {str(e)}")
            raise

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.run_training() 