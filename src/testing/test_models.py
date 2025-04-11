import pandas as pd
import numpy as np
import joblib
import logging
from typing import Dict, List
from datetime import datetime
from ..data_collection.cricbuzz_collector import CricbuzzCollector
from ..data_collection.ipl_2025_data import get_match, get_team

class ModelTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models_dir = 'models'
        self.cricbuzz = CricbuzzCollector()
        
        # Load trained models
        self.batting_model = joblib.load(f"{self.models_dir}/batting_model.joblib")
        self.bowling_model = joblib.load(f"{self.models_dir}/bowling_model.joblib")

    def test_match_prediction(self, match_no: int) -> Dict:
        """Test model predictions for a specific match"""
        try:
            # Get match details
            match = get_match(match_no)
            if not match:
                raise ValueError(f"Match {match_no} not found")
            
            # Get team details
            team1 = get_team(match['team1'])
            team2 = get_team(match['team2'])
            
            if not team1 or not team2:
                raise ValueError("Team data not found")
            
            # Get match squads
            squads = self.cricbuzz.get_match_squads(match_no)
            
            # Test predictions for each team
            team1_predictions = self._test_team_predictions(
                team1['players'],
                squads['team1']['playing_xi'],
                match
            )
            
            team2_predictions = self._test_team_predictions(
                team2['players'],
                squads['team2']['playing_xi'],
                match
            )
            
            return {
                "match": match,
                "team1": {
                    "name": match['team1'],
                    "predictions": team1_predictions
                },
                "team2": {
                    "name": match['team2'],
                    "predictions": team2_predictions
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error testing match prediction: {str(e)}")
            raise

    def _test_team_predictions(
        self,
        players: List[Dict],
        playing_xi: List[str],
        match: Dict
    ) -> List[Dict]:
        """Test predictions for a team's players"""
        predictions = []
        
        for player in players:
            is_playing = player['name'] in playing_xi
            
            if is_playing:
                # Get player's current form
                current_form = self.cricbuzz.get_player_stats(player['name'])
                
                # Prepare features
                features = self._prepare_features(player, match, current_form)
                
                # Make predictions
                batting_pred = self.batting_model.predict([features['batting']])[0]
                bowling_pred = self.bowling_model.predict([features['bowling']])[0]
                
                predictions.append({
                    "player": player,
                    "is_playing": True,
                    "predictions": {
                        "batting": {
                            "runs": float(batting_pred),
                            "confidence": self._calculate_confidence(batting_pred)
                        },
                        "bowling": {
                            "wickets": float(bowling_pred),
                            "confidence": self._calculate_confidence(bowling_pred)
                        }
                    },
                    "current_form": current_form
                })
            else:
                predictions.append({
                    "player": player,
                    "is_playing": False,
                    "predictions": None
                })
        
        return predictions

    def _prepare_features(
        self,
        player: Dict,
        match: Dict,
        current_form: Dict
    ) -> Dict:
        """Prepare features for prediction"""
        # Batting features
        batting_features = [
            match['venue'],
            match['team2'],  # opposition
            'T20',  # match_type
            2025,  # season
            current_form.get('current_form', {}).get('batting', {}).get('runs', 0),
            current_form.get('current_form', {}).get('batting', {}).get('strike_rate', 0),
            current_form.get('current_form', {}).get('batting', {}).get('average', 0),
            0.5,  # opposition_strength (placeholder)
            0.5   # venue_performance (placeholder)
        ]
        
        # Bowling features
        bowling_features = [
            match['venue'],
            match['team2'],  # opposition
            'T20',  # match_type
            2025,  # season
            current_form.get('current_form', {}).get('bowling', {}).get('wickets', 0),
            current_form.get('current_form', {}).get('bowling', {}).get('economy', 0),
            current_form.get('current_form', {}).get('bowling', {}).get('average', 0),
            0.5,  # opposition_strength (placeholder)
            0.5   # venue_performance (placeholder)
        ]
        
        return {
            "batting": batting_features,
            "bowling": bowling_features
        }

    def _calculate_confidence(self, prediction: float) -> float:
        """Calculate confidence score for prediction"""
        # Simple confidence calculation based on prediction value
        # Higher predictions get lower confidence due to higher variability
        return max(0.5, min(0.95, 1 - (prediction / 100)))

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize tester
    tester = ModelTester()
    
    # Test predictions for a specific match
    match_no = 1  # Example match number
    results = tester.test_match_prediction(match_no)
    
    # Print results
    print(f"\nTest Results for Match {match_no}:")
    print(f"{results['match']['team1']} vs {results['match']['team2']}")
    print(f"Venue: {results['match']['venue']}")
    print(f"Date: {results['match']['date']}")
    
    print("\nTeam 1 Predictions:")
    for pred in results['team1']['predictions']:
        if pred['is_playing']:
            print(f"\n{pred['player']['name']}:")
            print(f"  Batting: {pred['predictions']['batting']['runs']:.1f} runs "
                  f"(confidence: {pred['predictions']['batting']['confidence']:.2f})")
            print(f"  Bowling: {pred['predictions']['bowling']['wickets']:.1f} wickets "
                  f"(confidence: {pred['predictions']['bowling']['confidence']:.2f})")
        else:
            print(f"\n{pred['player']['name']}: Not in playing XI")
    
    print("\nTeam 2 Predictions:")
    for pred in results['team2']['predictions']:
        if pred['is_playing']:
            print(f"\n{pred['player']['name']}:")
            print(f"  Batting: {pred['predictions']['batting']['runs']:.1f} runs "
                  f"(confidence: {pred['predictions']['batting']['confidence']:.2f})")
            print(f"  Bowling: {pred['predictions']['bowling']['wickets']:.1f} wickets "
                  f"(confidence: {pred['predictions']['bowling']['confidence']:.2f})")
        else:
            print(f"\n{pred['player']['name']}: Not in playing XI") 