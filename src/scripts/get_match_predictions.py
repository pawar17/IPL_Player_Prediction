import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MatchPredictor:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.output_dir = self.data_dir / "predictions"
        self.output_dir.mkdir(exist_ok=True)

    def get_tomorrows_match(self) -> Optional[Dict]:
        """Get tomorrow's match details from all sources."""
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Check IPL website schedule
            with open(self.data_dir / "ipl_website_match_schedule.json", 'r') as f:
                ipl_schedule = json.load(f)
                for match in ipl_schedule:
                    if match['date'].startswith(tomorrow):
                        return match

            # Check Cricbuzz latest matches
            for file in self.data_dir.glob("latest_match_*.json"):
                with open(file, 'r') as f:
                    matches = json.load(f)
                    for match in matches:
                        if match['date'].startswith(tomorrow):
                            return match

            # Check current season data
            from ipl_2025_data import matches
            for match in matches:
                if match['date'].startswith(tomorrow):
                    return match

            logger.warning("No match found for tomorrow")
            return None
        except Exception as e:
            logger.error(f"Error getting tomorrow's match: {str(e)}")
            return None

    def get_team_squads(self) -> Dict:
        """Get current team squads."""
        try:
            # Load IPL website squads
            with open(self.data_dir / "ipl_website_team_squads.json", 'r') as f:
                ipl_squads = json.load(f)
            
            # Load current season data
            from ipl_2025_data import teams
            
            # Combine squads
            all_squads = {}
            for team in teams:
                all_squads[team['name']] = team['players']
            
            for squad in ipl_squads:
                all_squads[squad['team']] = squad['players']
            
            return all_squads
        except Exception as e:
            logger.error(f"Error getting team squads: {str(e)}")
            return {}

    def get_player_stats(self) -> pd.DataFrame:
        """Get player statistics from all sources."""
        try:
            # Load historical stats
            stats_df = pd.read_csv(self.historical_dir / "player_stats.csv")
            
            # Load IPL website stats
            with open(self.data_dir / "ipl_website_player_stats.json", 'r') as f:
                ipl_stats = pd.DataFrame(json.load(f))
            
            # Combine stats
            all_stats = pd.concat([stats_df, ipl_stats], ignore_index=True)
            all_stats = all_stats.drop_duplicates(subset=['player_id'])
            
            return all_stats
        except Exception as e:
            logger.error(f"Error getting player stats: {str(e)}")
            return pd.DataFrame()

    def predict_player_performance(self, player_id: str, player_stats: pd.DataFrame) -> Dict:
        """Predict player performance based on historical stats."""
        try:
            player_data = player_stats[player_stats['player_id'] == player_id].iloc[0]
            
            # Calculate batting predictions
            batting_avg = float(player_data.get('batting_average', 0))
            strike_rate = float(player_data.get('strike_rate', 0))
            recent_runs = float(player_data.get('recent_runs', 0))
            
            # Calculate bowling predictions
            bowling_avg = float(player_data.get('bowling_average', 0))
            economy_rate = float(player_data.get('economy_rate', 0))
            recent_wickets = float(player_data.get('recent_wickets', 0))
            
            # Calculate predicted performance
            predicted_runs = (batting_avg + recent_runs) / 2
            predicted_wickets = (bowling_avg + recent_wickets) / 2
            
            return {
                'player_id': player_id,
                'name': player_data['name'],
                'predicted_runs': round(predicted_runs, 2),
                'predicted_wickets': round(predicted_wickets, 2),
                'confidence': self.calculate_confidence(player_data)
            }
        except Exception as e:
            logger.error(f"Error predicting player performance: {str(e)}")
            return {}

    def calculate_confidence(self, player_data: pd.Series) -> float:
        """Calculate confidence level for prediction."""
        try:
            # Factors affecting confidence
            matches_played = float(player_data.get('matches_played', 0))
            recent_form = float(player_data.get('recent_form', 0))
            consistency = float(player_data.get('consistency', 0))
            
            # Weighted average of factors
            confidence = (matches_played * 0.4 + recent_form * 0.3 + consistency * 0.3) / 100
            return round(min(confidence, 1.0), 2)
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 0.0

    def get_match_predictions(self):
        """Get predictions for tomorrow's match."""
        try:
            # Get tomorrow's match
            match = self.get_tomorrows_match()
            if not match:
                logger.error("No match found for tomorrow")
                return

            # Get team squads
            squads = self.get_team_squads()
            team1_squad = squads.get(match['team1'], [])
            team2_squad = squads.get(match['team2'], [])

            # Get player stats
            player_stats = self.get_player_stats()

            # Generate predictions for each team
            predictions = {
                'match': match,
                'team1': {
                    'name': match['team1'],
                    'predictions': [
                        self.predict_player_performance(player['id'], player_stats)
                        for player in team1_squad
                    ]
                },
                'team2': {
                    'name': match['team2'],
                    'predictions': [
                        self.predict_player_performance(player['id'], player_stats)
                        for player in team2_squad
                    ]
                }
            }

            # Save predictions
            output_file = self.output_dir / f"predictions_{match['match_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(predictions, f, indent=2)
            
            logger.info(f"Saved predictions to {output_file}")
            return predictions
        except Exception as e:
            logger.error(f"Error getting match predictions: {str(e)}")
            return None

def main():
    predictor = MatchPredictor()
    predictions = predictor.get_match_predictions()
    if predictions:
        print("\nMatch Predictions:")
        print("=" * 50)
        print(f"Match: {predictions['match']['team1']} vs {predictions['match']['team2']}")
        print(f"Date: {predictions['match']['date']}")
        print(f"Venue: {predictions['match']['venue']}")
        
        print("\nTeam 1 Predictions:")
        for pred in predictions['team1']['predictions']:
            print(f"{pred['name']}: {pred['predicted_runs']} runs, {pred['predicted_wickets']} wickets (Confidence: {pred['confidence']})")
        
        print("\nTeam 2 Predictions:")
        for pred in predictions['team2']['predictions']:
            print(f"{pred['name']}: {pred['predicted_runs']} runs, {pred['predicted_wickets']} wickets (Confidence: {pred['confidence']})")

if __name__ == "__main__":
    main() 