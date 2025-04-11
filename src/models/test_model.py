import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from src.predict_match import MatchPredictor
from src.data_collection.test_data import SAMPLE_MATCHES, SAMPLE_RESULTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_predictions(predictions: dict, actual_results: dict) -> dict:
    """Evaluate model predictions against actual results"""
    metrics = {
        'batting': {'mae': 0, 'rmse': 0, 'r2': 0},
        'bowling': {'mae': 0, 'rmse': 0, 'r2': 0},
        'fielding': {'mae': 0, 'rmse': 0, 'r2': 0}
    }
    
    # Collect predictions and actual values
    pred_runs = []
    actual_runs = []
    pred_wickets = []
    actual_wickets = []
    pred_catches = []
    actual_catches = []
    
    for team in predictions:
        if not team.endswith('_totals'):
            for player_pred in predictions[team]:
                if 'error' not in player_pred:
                    # Find corresponding player in actual results
                    for actual_player in actual_results[team]:
                        if actual_player['name'] == player_pred['player_name']:
                            pred_runs.append(player_pred['predicted_runs'])
                            actual_runs.append(actual_player['runs'])
                            pred_wickets.append(player_pred['predicted_wickets'])
                            actual_wickets.append(actual_player['wickets'])
                            pred_catches.append(player_pred['predicted_catches'])
                            actual_catches.append(actual_player['catches'])
                            break
    
    # Calculate metrics
    if pred_runs:
        metrics['batting']['mae'] = np.mean(np.abs(np.array(pred_runs) - np.array(actual_runs)))
        metrics['batting']['rmse'] = np.sqrt(np.mean((np.array(pred_runs) - np.array(actual_runs)) ** 2))
        metrics['batting']['r2'] = 1 - np.sum((np.array(pred_runs) - np.array(actual_runs)) ** 2) / np.sum((np.array(actual_runs) - np.mean(actual_runs)) ** 2)
    
    if pred_wickets:
        metrics['bowling']['mae'] = np.mean(np.abs(np.array(pred_wickets) - np.array(actual_wickets)))
        metrics['bowling']['rmse'] = np.sqrt(np.mean((np.array(pred_wickets) - np.array(actual_wickets)) ** 2))
        metrics['bowling']['r2'] = 1 - np.sum((np.array(pred_wickets) - np.array(actual_wickets)) ** 2) / np.sum((np.array(actual_wickets) - np.mean(actual_wickets)) ** 2)
    
    if pred_catches:
        metrics['fielding']['mae'] = np.mean(np.abs(np.array(pred_catches) - np.array(actual_catches)))
        metrics['fielding']['rmse'] = np.sqrt(np.mean((np.array(pred_catches) - np.array(actual_catches)) ** 2))
        metrics['fielding']['r2'] = 1 - np.sum((np.array(pred_catches) - np.array(actual_catches)) ** 2) / np.sum((np.array(actual_catches) - np.mean(actual_catches)) ** 2)
    
    return metrics

def test_model():
    """Test the model on sample matches"""
    predictor = MatchPredictor(use_test_data=True)
    all_metrics = {
        'batting': {'mae': [], 'rmse': [], 'r2': []},
        'bowling': {'mae': [], 'rmse': [], 'r2': []},
        'fielding': {'mae': [], 'rmse': [], 'r2': []}
    }
    
    for match in SAMPLE_MATCHES:
        match_id = f"{match['team1']}_vs_{match['team2']}_{match['date']}"
        logger.info(f"Testing match: {match_id}")
        
        # Get predictions
        predictions = predictor.predict_match(match['team1'], match['team2'], match['date'])
        
        # Get actual results
        actual_results = SAMPLE_RESULTS[match['match_id']]
        
        # Evaluate predictions
        metrics = evaluate_predictions(predictions, actual_results)
        
        # Accumulate metrics
        for category in ['batting', 'bowling', 'fielding']:
            for metric in ['mae', 'rmse', 'r2']:
                all_metrics[category][metric].append(metrics[category][metric])
    
    # Calculate average metrics
    print("\nModel Test Results")
    print("=" * 50)
    print(f"Matches Tested: {len(SAMPLE_MATCHES)}\n")
    print("Overall Metrics:")
    print("-" * 20 + "\n")
    
    for category in ['batting', 'bowling', 'fielding']:
        print(f"{category.title()}:")
        print(f"  Mean Absolute Error: {np.mean(all_metrics[category]['mae']):.2f}")
        print(f"  Root Mean Square Error: {np.mean(all_metrics[category]['rmse']):.2f}")
        print(f"  R² Score: {np.mean(all_metrics[category]['r2']):.2f}\n")
    
    print("Match Details:")
    print("-" * 20 + "\n")

if __name__ == "__main__":
    test_model() 