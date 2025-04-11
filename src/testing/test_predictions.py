import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import pandas as pd

from ..prediction.predict_player_performance import PlayerPredictionSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MatchPredictionTester:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.predictor = PlayerPredictionSystem()
        
        # Create output directory
        self.output_path = self.base_path / 'data' / 'predictions' / 'test'
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def predict_match(self, team1: str, team2: str, venue: str) -> Dict:
        """Predict performance for all players in a match"""
        try:
            self.logger.info(f"Predicting match: {team1} vs {team2} at {venue}")
            
            # Get team compositions
            team1_players = self.predictor._get_team_composition(team1)
            team2_players = self.predictor._get_team_composition(team2)
            
            # Get venue conditions
            venue_conditions = self.predictor._get_venue_conditions(venue)
            
            # Predict for each player
            predictions = {
                team1: self._predict_team_players(team1, team1_players, team2, venue_conditions),
                team2: self._predict_team_players(team2, team2_players, team1, venue_conditions)
            }
            
            # Save predictions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"match_prediction_{team1}_vs_{team2}_{timestamp}.json"
            filepath = self.output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(predictions, f, indent=4)
            
            self.logger.info(f"Saved predictions to {filepath}")
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting match: {str(e)}")
            return {}
    
    def _predict_team_players(
        self,
        team: str,
        players: Dict,
        opposition: str,
        venue_conditions: Dict
    ) -> List[Dict]:
        """Predict performance for all players in a team"""
        predictions = []
        
        for player_name, player_data in players.items():
            try:
                # Get player form
                form_data = self.predictor._get_player_form(player_name)
                
                # Prepare features
                features = {
                    'name': player_name,
                    'team': team,
                    'venue': venue_conditions.get('venue', 'Unknown'),
                    'opposition': opposition,
                    'form_factor': form_data.get('form_factor', 1.0),
                    'match_importance': 1.0,
                    'team_strength': 0.5,
                    'opposition_strength': 0.5,
                    'season': datetime.now().year
                }
                
                # Make predictions
                batting_pred = self.predictor._predict_batting(features)
                bowling_pred = self.predictor._predict_bowling(features)
                
                # Calculate confidence intervals
                batting_ci = self.predictor._calculate_confidence_interval(batting_pred)
                bowling_ci = self.predictor._calculate_confidence_interval(bowling_pred)
                
                predictions.append({
                    'player_name': player_name,
                    'role': player_data.get('role', 'Unknown'),
                    'batting': {
                        'predicted_runs': float(batting_pred),
                        'confidence_interval': batting_ci
                    },
                    'bowling': {
                        'predicted_wickets': float(bowling_pred),
                        'confidence_interval': bowling_ci
                    }
                })
                
            except Exception as e:
                self.logger.error(f"Error predicting for player {player_name}: {str(e)}")
                continue
        
        return predictions

if __name__ == "__main__":
    # Test CSK vs MI match
    tester = MatchPredictionTester()
    predictions = tester.predict_match(
        team1="CSK",
        team2="MI",
        venue="MA Chidambaram Stadium"
    )
    
    # Print summary
    print("\nMatch Prediction Summary:")
    print("=" * 50)
    
    for team, team_preds in predictions.items():
        print(f"\n{team} Predictions:")
        print("-" * 30)
        
        # Sort by predicted runs for batsmen
        batsmen = sorted(
            [p for p in team_preds if p['role'] in ['Batsman', 'All-rounder']],
            key=lambda x: x['batting']['predicted_runs'],
            reverse=True
        )
        
        # Sort by predicted wickets for bowlers
        bowlers = sorted(
            [p for p in team_preds if p['role'] in ['Bowler', 'All-rounder']],
            key=lambda x: x['bowling']['predicted_wickets'],
            reverse=True
        )
        
        print("\nTop 5 Batsmen:")
        for player in batsmen[:5]:
            print(f"{player['player_name']}: {player['batting']['predicted_runs']:.1f} runs "
                  f"(CI: {player['batting']['confidence_interval']['lower']:.1f} - "
                  f"{player['batting']['confidence_interval']['upper']:.1f})")
        
        print("\nTop 5 Bowlers:")
        for player in bowlers[:5]:
            print(f"{player['player_name']}: {player['bowling']['predicted_wickets']:.1f} wickets "
                  f"(CI: {player['bowling']['confidence_interval']['lower']:.1f} - "
                  f"{player['bowling']['confidence_interval']['upper']:.1f})") 