import unittest
import pandas as pd
import numpy as np
from pathlib import Path
from src.models.player_predictor import PlayerPredictor
from src.data_preparation.data_processor import DataProcessor

class TestModelTraining(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / 'data' / 'raw'
        self.processed_path = self.base_path / 'data' / 'processed'
        self.models_path = self.base_path / 'models' / 'saved'
        
        # Create test data
        self.test_data = pd.DataFrame({
            'last_5_matches_runs_avg': np.random.uniform(0, 100, 100),
            'last_5_matches_wickets_avg': np.random.uniform(0, 5, 100),
            'last_5_matches_sr_avg': np.random.uniform(50, 200, 100),
            'last_5_matches_er_avg': np.random.uniform(5, 15, 100),
            'form_factor': np.random.uniform(0, 2, 100),
            'consistency_score': np.random.uniform(0, 1, 100),
            'pressure_index': np.random.uniform(0, 1, 100),
            'days_since_last_match': np.random.randint(1, 15, 100),
            'is_home_game': np.random.randint(0, 2, 100),
            'is_powerplay_batsman': np.random.randint(0, 2, 100),
            'is_death_bowler': np.random.randint(0, 2, 100),
            'runs': np.random.randint(0, 150, 100),
            'wickets': np.random.randint(0, 5, 100),
            'strike_rate': np.random.uniform(50, 200, 100),
            'economy_rate': np.random.uniform(5, 15, 100)
        })
        
        self.predictor = PlayerPredictor()
        self.processor = DataProcessor()

    def test_feature_preparation(self):
        """Test feature preparation"""
        # Test with sample player data
        player_data = {
            'last_5_matches_runs_avg': 45.5,
            'last_5_matches_wickets_avg': 2.3,
            'last_5_matches_sr_avg': 135.2,
            'last_5_matches_er_avg': 8.5,
            'form_factor': 1.2,
            'consistency_score': 0.8,
            'pressure_index': 0.6,
            'days_since_last_match': 3,
            'is_home_game': 1,
            'is_powerplay_batsman': 1,
            'is_death_bowler': 0
        }
        
        features = self.predictor.prepare_features(player_data)
        self.assertEqual(features.shape, (1, len(self.predictor.feature_columns)))
        self.assertTrue(np.all(np.isfinite(features)))

    def test_model_training(self):
        """Test model training"""
        # Train models with test data
        self.predictor.train(self.test_data)
        
        # Check if models are trained
        for name, model in self.predictor.models.items():
            self.assertTrue(hasattr(model, 'fit'))
            self.assertTrue(hasattr(model, 'predict'))

    def test_model_prediction(self):
        """Test model prediction"""
        # Train models first
        self.predictor.train(self.test_data)
        
        # Test prediction with sample data
        player_data = {
            'last_5_matches_runs_avg': 45.5,
            'last_5_matches_wickets_avg': 2.3,
            'last_5_matches_sr_avg': 135.2,
            'last_5_matches_er_avg': 8.5,
            'form_factor': 1.2,
            'consistency_score': 0.8,
            'pressure_index': 0.6,
            'days_since_last_match': 3,
            'is_home_game': 1,
            'is_powerplay_batsman': 1,
            'is_death_bowler': 0
        }
        
        prediction = self.predictor.predict(player_data)
        
        # Check prediction structure
        self.assertIsInstance(prediction, dict)
        self.assertIn('runs', prediction)
        self.assertIn('wickets', prediction)
        self.assertIn('strike_rate', prediction)
        self.assertIn('economy_rate', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('form', prediction)
        self.assertIn('momentum', prediction)

    def test_model_saving_loading(self):
        """Test model saving and loading"""
        # Train models
        self.predictor.train(self.test_data)
        
        # Save models
        self.predictor.save_models()
        
        # Create new predictor and load models
        new_predictor = PlayerPredictor()
        new_predictor.load_models()
        
        # Check if models are loaded
        for name, model in new_predictor.models.items():
            self.assertTrue(hasattr(model, 'predict'))

    def test_feature_engineering(self):
        """Test feature engineering"""
        # Test form factor calculation
        recent_performances = [50, 45, 60, 40, 55]
        form_factor = self.processor._calculate_form_factor(recent_performances)
        self.assertIsInstance(form_factor, float)
        self.assertGreater(form_factor, 0)
        
        # Test consistency score calculation
        consistency = self.processor._calculate_consistency(recent_performances)
        self.assertIsInstance(consistency, float)
        self.assertGreaterEqual(consistency, 0)
        self.assertLessEqual(consistency, 1)
        
        # Test pressure index calculation
        pressure = self.processor._calculate_pressure_index(
            is_knockout=False,
            opponent_strength=0.7,
            player_role='batsman'
        )
        self.assertIsInstance(pressure, float)
        self.assertGreaterEqual(pressure, 0)
        self.assertLessEqual(pressure, 1)

if __name__ == '__main__':
    unittest.main() 