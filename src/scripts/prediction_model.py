import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StatisticalPredictor:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.output_dir = self.data_dir / "predictions"
        self.output_dir.mkdir(exist_ok=True)

    def load_historical_data(self) -> pd.DataFrame:
        """Load historical match data."""
        try:
            matches_df = pd.read_csv(self.historical_dir / "ipl_matches_2008_2023.csv")
            logger.info(f"Loaded {len(matches_df)} historical matches")
            return matches_df
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()

    def calculate_player_form(self, player_data: pd.Series) -> float:
        """Calculate player's recent form based on last 5 matches."""
        try:
            recent_matches = player_data.get('recent_matches', [])
            if not recent_matches:
                return 0.0

            # Weight recent performances more heavily
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]
            form_score = 0.0
            
            for i, match in enumerate(recent_matches[:5]):
                if i < len(weights):
                    # Calculate match performance score
                    runs = float(match.get('runs', 0))
                    wickets = float(match.get('wickets', 0))
                    strike_rate = float(match.get('strike_rate', 0))
                    economy_rate = float(match.get('economy_rate', 0))
                    
                    # Normalize scores
                    runs_score = min(runs / 100, 1.0)  # Cap at 100 runs
                    wickets_score = min(wickets / 5, 1.0)  # Cap at 5 wickets
                    strike_rate_score = min(strike_rate / 200, 1.0)  # Cap at 200
                    economy_score = max(1 - (economy_rate / 12), 0)  # Lower is better
            
                    # Combine scores with weights
                    match_score = (runs_score * 0.4 + wickets_score * 0.3 + 
                                 strike_rate_score * 0.2 + economy_score * 0.1)
                    form_score += match_score * weights[i]
            
            return round(form_score, 2)
        except Exception as e:
            logger.error(f"Error calculating player form: {str(e)}")
            return 0.0

    def calculate_consistency(self, player_data: pd.Series) -> float:
        """Calculate player's consistency based on performance variance."""
        try:
            recent_matches = player_data.get('recent_matches', [])
            if not recent_matches:
                return 0.0

            # Calculate standard deviation of performance
            performances = []
            for match in recent_matches[:10]:  # Last 10 matches
                runs = float(match.get('runs', 0))
                wickets = float(match.get('wickets', 0))
                strike_rate = float(match.get('strike_rate', 0))
                economy_rate = float(match.get('economy_rate', 0))
                
                # Normalize and combine metrics
                performance = (runs/100 + wickets/5 + strike_rate/200 + (1-economy_rate/12)) / 4
                performances.append(performance)

            if not performances:
                return 0.0

            # Calculate consistency (inverse of standard deviation)
            std_dev = np.std(performances)
            consistency = 1 / (1 + std_dev)  # Add 1 to avoid division by zero
            return round(consistency, 2)
        except Exception as e:
            logger.error(f"Error calculating consistency: {str(e)}")
            return 0.0

    def calculate_head_to_head(self, player_id: str, opponent_team: str, 
                             historical_data: pd.DataFrame) -> float:
        """Calculate player's performance against specific opponent."""
        try:
            # Filter matches against opponent
            opponent_matches = historical_data[
                (historical_data['opponent'] == opponent_team) & 
                (historical_data['player_id'] == player_id)
            ]
            
            if opponent_matches.empty:
                return 0.5  # Neutral score if no head-to-head data
            
            # Calculate average performance against opponent
            avg_runs = opponent_matches['runs'].mean()
            avg_wickets = opponent_matches['wickets'].mean()
            avg_strike_rate = opponent_matches['strike_rate'].mean()
            avg_economy = opponent_matches['economy_rate'].mean()
            
            # Normalize and combine metrics
            runs_score = min(avg_runs / 100, 1.0)
            wickets_score = min(avg_wickets / 5, 1.0)
            strike_rate_score = min(avg_strike_rate / 200, 1.0)
            economy_score = max(1 - (avg_economy / 12), 0)
            
            h2h_score = (runs_score * 0.4 + wickets_score * 0.3 + 
                        strike_rate_score * 0.2 + economy_score * 0.1)
            
            return round(h2h_score, 2)
        except Exception as e:
            logger.error(f"Error calculating head-to-head: {str(e)}")
            return 0.5

    def predict_player_performance(self, player_id: str, player_data: pd.Series, 
                                 opponent_team: str, historical_data: pd.DataFrame) -> Dict:
        """Predict player performance using multiple statistical factors."""
        try:
            # Calculate various factors
            form = self.calculate_player_form(player_data)
            consistency = self.calculate_consistency(player_data)
            h2h = self.calculate_head_to_head(player_id, opponent_team, historical_data)
            
            # Get base statistics
            batting_avg = float(player_data.get('batting_average', 0))
            strike_rate = float(player_data.get('strike_rate', 0))
            bowling_avg = float(player_data.get('bowling_average', 0))
            economy_rate = float(player_data.get('economy_rate', 0))
            
            # Calculate weighted predictions
            form_weight = 0.3
            consistency_weight = 0.2
            h2h_weight = 0.2
            historical_weight = 0.3
            
            # Batting prediction
            predicted_runs = (
                batting_avg * historical_weight +
                (form * 100) * form_weight +
                (h2h * 100) * h2h_weight +
                (consistency * batting_avg) * consistency_weight
            )
            
            # Bowling prediction
            predicted_wickets = (
                (bowling_avg * historical_weight +
                (form * 5) * form_weight +
                (h2h * 5) * h2h_weight +
                (consistency * bowling_avg) * consistency_weight)
            )
            
            # Calculate confidence
            confidence = (
                form * 0.3 +
                consistency * 0.3 +
                h2h * 0.2 +
                (min(len(player_data.get('recent_matches', [])), 10) / 10) * 0.2
            )
            
            return {
                'player_id': player_id,
                'name': player_data['name'],
                'predicted_runs': round(predicted_runs, 2),
                'predicted_wickets': round(predicted_wickets, 2),
                'confidence': round(confidence, 2),
                'factors': {
                    'form': form,
                    'consistency': consistency,
                    'head_to_head': h2h,
                    'historical_average': batting_avg
                }
            }
        except Exception as e:
            logger.error(f"Error predicting player performance: {str(e)}")
            return {}

    def get_match_predictions(self, match: Dict) -> Dict:
        """Get predictions for a specific match."""
        try:
            # Load historical data
            historical_data = self.load_historical_data()
            
            # Get team squads
            from ipl_2025_data import teams
            squads = {team['name']: team['players'] for team in teams}
            
            # Get player stats
            player_stats = pd.read_csv(self.historical_dir / "player_stats.csv")
            
            # Generate predictions
            predictions = {
                'match': match,
                'team1': {
                    'name': match['team1'],
                    'predictions': [
                        self.predict_player_performance(
                            player['id'],
                            player_stats[player_stats['player_id'] == player['id']].iloc[0],
                            match['team2'],
                            historical_data
                        )
                        for player in squads.get(match['team1'], [])
                    ]
                },
                'team2': {
                    'name': match['team2'],
                    'predictions': [
                        self.predict_player_performance(
                            player['id'],
                            player_stats[player_stats['player_id'] == player['id']].iloc[0],
                            match['team1'],
                            historical_data
                        )
                        for player in squads.get(match['team2'], [])
                    ]
                }
            }
            
            # Save predictions
            output_file = self.output_dir / f"predictions_{match['match_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(predictions, f, indent=2)
            
            return predictions
        except Exception as e:
            logger.error(f"Error getting match predictions: {str(e)}")
            return None

def main():
    predictor = StatisticalPredictor()
    
    # Example usage
    match = {
        'match_id': 'test_match',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'date': '2024-03-20',
        'venue': 'Wankhede Stadium'
    }
    
    predictions = predictor.get_match_predictions(match)
    if predictions:
        print("\nMatch Predictions:")
        print("=" * 50)
        print(f"Match: {predictions['match']['team1']} vs {predictions['match']['team2']}")
        print(f"Date: {predictions['match']['date']}")
        print(f"Venue: {predictions['match']['venue']}")
        
        print("\nTeam 1 Predictions:")
        for pred in predictions['team1']['predictions']:
            print(f"\n{pred['name']}:")
            print(f"Predicted: {pred['predicted_runs']} runs, {pred['predicted_wickets']} wickets")
            print(f"Confidence: {pred['confidence']}")
            print("Factors:")
            for factor, value in pred['factors'].items():
                print(f"  {factor}: {value}")

if __name__ == "__main__":
    main() 