import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from src.test_match_prediction import MatchPredictor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_player_prediction():
    """Test player performance prediction"""
    predictor = MatchPredictor()
    
    # Test players
    players = [
        ("Virat Kohli", "RCB"),
        ("MS Dhoni", "CSK"),
        ("Rohit Sharma", "MI")
    ]
    
    print("\nTesting Player Performance Predictions:")
    print("-" * 50)
    
    for player_name, team_name in players:
        print(f"\nPredicting performance for {player_name} ({team_name}):")
        
        # Get player features
        features = predictor.get_player_features(player_name, team_name)
        print("\nPlayer Features:")
        print(f"Batting: {features['batting']}")
        print(f"Bowling: {features['bowling']}")
        print(f"Fielding: {features['fielding']}")
        
        # Get performance prediction
        prediction = predictor.predict_player_performance(player_name, team_name)
        print("\nPerformance Prediction:")
        print(f"Batting: {prediction['batting']}")
        print(f"Bowling: {prediction['bowling']}")
        print(f"Fielding: {prediction['fielding']}")

def test_match_prediction():
    """Test match outcome prediction"""
    predictor = MatchPredictor()
    
    # Test match
    match_id = "1"  # First match
    
    print("\nTesting Match Prediction:")
    print("-" * 50)
    
    prediction = predictor.predict_match(match_id)
    
    if prediction:
        print(f"\nMatch: {prediction['team1']['name']} vs {prediction['team2']['name']}")
        print(f"\n{prediction['team1']['name']}:")
        print(f"Win Probability: {prediction['team1']['win_probability']:.2%}")
        print(f"Performance: {prediction['team1']['prediction']}")
        print(f"\n{prediction['team2']['name']}:")
        print(f"Win Probability: {prediction['team2']['win_probability']:.2%}")
        print(f"Performance: {prediction['team2']['prediction']}")
    else:
        print("Error getting match prediction")

if __name__ == "__main__":
    print("Testing IPL Match Predictor")
    print("=" * 50)
    
    # Test player predictions
    test_player_prediction()
    
    # Test match prediction
    test_match_prediction() 