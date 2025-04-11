import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import OneHotEncoder
import joblib
import logging
from typing import Dict, Tuple
import os
from ..data_collection.data_pipeline import DataPipeline

class ModelTrainer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models_dir = 'models'
        os.makedirs(self.models_dir, exist_ok=True)
        self.encoders = {}
        self.data_pipeline = DataPipeline()

    def load_and_preprocess_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load and preprocess data using the data pipeline"""
        try:
            # Run data pipeline to get latest data
            self.data_pipeline.run_pipeline()
            
            # Load processed data
            data = pd.read_csv('data/processed/updated_data.csv')
            
            # Prepare batting features
            batting_features = [
                'recent_runs_scored', 'recent_batting_strike_rate', 'recent_batting_average',
                'batting_form', 'team', 'date'
            ]
            
            # Prepare bowling features
            bowling_features = [
                'recent_wickets_taken', 'recent_economy_rate', 'recent_bowling_average',
                'bowling_form', 'team', 'date'
            ]
            
            # Create feature matrices
            X_batting = data[batting_features].copy()
            X_bowling = data[bowling_features].copy()
            
            # Handle categorical variables
            for feature in ['team']:
                if feature in X_batting.columns:
                    X_batting = pd.get_dummies(X_batting, columns=[feature])
                if feature in X_bowling.columns:
                    X_bowling = pd.get_dummies(X_bowling, columns=[feature])
            
            # Convert date to numeric features
            X_batting['year'] = pd.to_datetime(X_batting['date']).dt.year
            X_bowling['year'] = pd.to_datetime(X_bowling['date']).dt.year
            
            # Drop date column
            X_batting = X_batting.drop('date', axis=1)
            X_bowling = X_bowling.drop('date', axis=1)
            
            # Prepare target variables
            y_batting = data['runs_scored']
            y_bowling = data['wickets_taken']
            
            return (X_batting, y_batting), (X_bowling, y_bowling)
            
        except Exception as e:
            self.logger.error(f"Error loading and preprocessing data: {str(e)}")
            raise

    def train_models(self, perform_grid_search: bool = False) -> Dict:
        """Train batting and bowling prediction models"""
        try:
            # Load and preprocess data
            (X_batting, y_batting), (X_bowling, y_bowling) = self.load_and_preprocess_data()
            
            # Split data into training and testing sets
            X_bat_train, X_bat_test, y_bat_train, y_bat_test = train_test_split(
                X_batting, y_batting, test_size=0.2, random_state=42
            )
            
            X_bowl_train, X_bowl_test, y_bowl_train, y_bowl_test = train_test_split(
                X_bowling, y_bowling, test_size=0.2, random_state=42
            )
            
            # Initialize models
            batting_model = RandomForestRegressor(n_estimators=100, random_state=42)
            bowling_model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            # Perform grid search if requested
            if perform_grid_search:
                batting_model = self._perform_grid_search(
                    RandomForestRegressor(random_state=42),
                    X_bat_train, y_bat_train
                )
                bowling_model = self._perform_grid_search(
                    RandomForestRegressor(random_state=42),
                    X_bowl_train, y_bowl_train
                )
            
            # Train models
            batting_model.fit(X_bat_train, y_bat_train)
            bowling_model.fit(X_bowl_train, y_bowl_train)
            
            # Evaluate models
            batting_metrics = self._evaluate_model(
                batting_model, X_bat_test, y_bat_test, "batting"
            )
            bowling_metrics = self._evaluate_model(
                bowling_model, X_bowl_test, y_bowl_test, "bowling"
            )
            
            # Save models
            self._save_models(batting_model, bowling_model)
            
            return {
                "batting": batting_metrics,
                "bowling": bowling_metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            raise

    def _perform_grid_search(
        self,
        model,
        X_train: pd.DataFrame,
        y_train: pd.Series
    ) -> RandomForestRegressor:
        """Perform grid search for hyperparameter tuning"""
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [None, 10, 20, 30],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=5,
            scoring='neg_mean_squared_error',
            n_jobs=-1
        )
        
        grid_search.fit(X_train, y_train)
        return grid_search.best_estimator_

    def _evaluate_model(
        self,
        model: RandomForestRegressor,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_type: str
    ) -> Dict:
        """Evaluate model performance"""
        # Make predictions
        y_pred = model.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Get feature importance
        feature_importance = dict(zip(X_test.columns, model.feature_importances_))
        
        return {
            "mse": mse,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "feature_importance": feature_importance
        }

    def _save_models(
        self,
        batting_model: RandomForestRegressor,
        bowling_model: RandomForestRegressor
    ) -> None:
        """Save trained models"""
        try:
            joblib.dump(batting_model, f"{self.models_dir}/batting_model.joblib")
            joblib.dump(bowling_model, f"{self.models_dir}/bowling_model.joblib")
            self.logger.info("Models saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving models: {str(e)}")
            raise

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize trainer
    trainer = ModelTrainer()
    
    # Train models with grid search
    metrics = trainer.train_models(perform_grid_search=True)
    
    # Print results
    print("\nModel Performance Metrics:")
    print("\nBatting Model:")
    for metric, value in metrics["batting"].items():
        if metric != "feature_importance":
            print(f"{metric.upper()}: {value:.4f}")
    
    print("\nBowling Model:")
    for metric, value in metrics["bowling"].items():
        if metric != "feature_importance":
            print(f"{metric.upper()}: {value:.4f}")
    
    print("\nFeature Importance:")
    print("\nBatting Model:")
    for feature, importance in metrics["batting"]["feature_importance"].items():
        print(f"{feature}: {importance:.4f}")
    
    print("\nBowling Model:")
    for feature, importance in metrics["bowling"]["feature_importance"].items():
        print(f"{feature}: {importance:.4f}") 