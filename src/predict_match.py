import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import logging
from typing import Dict, List
from datetime import datetime
from src.data_collection.web_scraper import CricketWebScraper
from src.data_collection.data_processor import DataProcessor
from src.data_collection.test_data import SAMPLE_PLAYER_STATS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchPredictor:
    def __init__(self, use_test_data=False):
        self.base_path = Path(__file__).parent.parent
        self.models_path = self.base_path / 'models'
        self.use_test_data = use_test_data
        
        # Load trained models
        self.batting_model = joblib.load(self.models_path / 'batting_model.joblib')
        self.bowling_model = joblib.load(self.models_path / 'bowling_model.joblib')
        self.fielding_model = joblib.load(self.models_path / 'fielding_model.joblib')
        
        # Initialize data collectors
        self.scraper = CricketWebScraper(use_test_data=use_test_data)
        self.processor = DataProcessor()
        
        # Define feature sets in exact order
        self.batting_features = [
            'Batting_Average', 'Batting_Strike_Rate',
            'Batting_Average_3yr_avg', 'Batting_Strike_Rate_3yr_avg',
            'Career_Batting_Average', 'Career_Batting_Strike_Rate',
            'Career_Runs_Scored', 'Runs_Scored_3yr_avg',
            'matches_played', 'recent_form_runs', 'is_batsman', 'is_all_rounder'
        ]
        
        self.bowling_features = [
            'Bowling_Average', 'Economy_Rate',
            'Bowling_Average_3yr_avg', 'Economy_Rate_3yr_avg',
            'Career_Wickets_Taken', 'Wickets_Taken_3yr_avg',
            'recent_form_wickets', 'is_bowler', 'is_all_rounder'
        ]
        
        self.fielding_features = [
            'Career_Catches_Taken', 'Career_Stumpings',
            'recent_form_catches'
        ]
        
    def get_player_stats(self, player_name: str) -> Dict:
        """Get combined player statistics from historical and real-time data"""
        try:
            if self.use_test_data:
                # Use test data if available
                stats = SAMPLE_PLAYER_STATS.get(player_name, {})
                if not stats:
                    logger.warning(f"No historical data found for player {player_name}, using defaults")
                    stats = {
                        'Batting_Average': 0,
                        'Batting_Strike_Rate': 0,
                        'Batting_Average_3yr_avg': 0,
                        'Batting_Strike_Rate_3yr_avg': 0,
                        'Career_Batting_Average': 0,
                        'Career_Batting_Strike_Rate': 0,
                        'Career_Runs_Scored': 0,
                        'Runs_Scored_3yr_avg': 0,
                        'matches_played': 0,
                        'Bowling_Average': 0,
                        'Economy_Rate': 0,
                        'Bowling_Average_3yr_avg': 0,
                        'Economy_Rate_3yr_avg': 0,
                        'Career_Wickets_Taken': 0,
                        'Wickets_Taken_3yr_avg': 0,
                        'Career_Catches_Taken': 0,
                        'Career_Stumpings': 0
                    }
            else:
                # Get real-time stats from Cricbuzz
                cricbuzz_stats = self.scraper.get_player_stats(player_name)
                
                # Get historical stats from our processed data
                historical_stats = self.processor.get_player_historical_stats(player_name)
                
                # Combine and format stats
                stats = {
                    'Batting_Average': cricbuzz_stats.get('batting_average', historical_stats.get('Batting_Average', 0)),
                    'Batting_Strike_Rate': cricbuzz_stats.get('strike_rate', historical_stats.get('Batting_Strike_Rate', 0)),
                    'Batting_Average_3yr_avg': historical_stats.get('Batting_Average_3yr_avg', 0),
                    'Batting_Strike_Rate_3yr_avg': historical_stats.get('Batting_Strike_Rate_3yr_avg', 0),
                    'Career_Batting_Average': historical_stats.get('Career_Batting_Average', 0),
                    'Career_Batting_Strike_Rate': historical_stats.get('Career_Batting_Strike_Rate', 0),
                    'Career_Runs_Scored': historical_stats.get('Career_Runs_Scored', 0),
                    'Runs_Scored_3yr_avg': historical_stats.get('Runs_Scored_3yr_avg', 0),
                    'matches_played': historical_stats.get('matches_played', 0),
                    
                    'Bowling_Average': cricbuzz_stats.get('bowling_average', historical_stats.get('Bowling_Average', 0)),
                    'Economy_Rate': cricbuzz_stats.get('economy_rate', historical_stats.get('Economy_Rate', 0)),
                    'Bowling_Average_3yr_avg': historical_stats.get('Bowling_Average_3yr_avg', 0),
                    'Economy_Rate_3yr_avg': historical_stats.get('Economy_Rate_3yr_avg', 0),
                    'Career_Wickets_Taken': historical_stats.get('Career_Wickets_Taken', 0),
                    'Wickets_Taken_3yr_avg': historical_stats.get('Wickets_Taken_3yr_avg', 0),
                    
                    'Career_Catches_Taken': historical_stats.get('Career_Catches_Taken', 0),
                    'Career_Stumpings': historical_stats.get('Career_Stumpings', 0)
                }
            
            # Add role features
            stats['is_batsman'] = int(stats['Career_Batting_Average'] > 25)
            stats['is_bowler'] = int(stats['Career_Wickets_Taken'] > 20)
            stats['is_all_rounder'] = int((stats['Career_Batting_Average'] > 15) and 
                                        (stats['Career_Wickets_Taken'] > 10))
            
            # Add recent form features
            stats['recent_form_runs'] = stats['Runs_Scored_3yr_avg']
            stats['recent_form_wickets'] = stats['Wickets_Taken_3yr_avg']
            stats['recent_form_catches'] = stats['Career_Catches_Taken'] / max(1, stats['matches_played'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats for {player_name}: {str(e)}")
            return {}
            
    def predict_player_performance(self, player_name: str) -> Dict:
        """Predict performance for a single player"""
        try:
            # Get player stats
            stats = self.get_player_stats(player_name)
            if not stats:
                return {'error': f'No stats found for player {player_name}'}
                
            # Prepare features in exact order
            batting_features = pd.DataFrame([{col: stats[col] for col in self.batting_features}])
            bowling_features = pd.DataFrame([{col: stats[col] for col in self.bowling_features}])
            fielding_features = pd.DataFrame([{col: stats[col] for col in self.fielding_features}])
            
            # Make predictions
            predicted_runs = self.batting_model.predict(batting_features)[0]
            predicted_wickets = self.bowling_model.predict(bowling_features)[0]
            predicted_catches = self.fielding_model.predict(fielding_features)[0]
            
            return {
                'player_name': player_name,
                'predicted_runs': round(predicted_runs, 2),
                'predicted_wickets': round(predicted_wickets, 2),
                'predicted_catches': round(predicted_catches, 2)
            }
            
        except Exception as e:
            logger.error(f"Error predicting for {player_name}: {str(e)}")
            return {'error': str(e)}
            
    def predict_match(self, team1: str, team2: str, date: str) -> Dict:
        """Predict performance for all players in a match"""
        try:
            match_id = f"{team1}_vs_{team2}_{date}"
            logger.info(f"Predicting match {match_id}")
            
            # Get playing XI from Cricbuzz
            team1_players = self.scraper.get_team_players(team1)
            team2_players = self.scraper.get_team_players(team2)
            
            # Make predictions for each team
            predictions = {
                team1: [self.predict_player_performance(player) for player in team1_players],
                team2: [self.predict_player_performance(player) for player in team2_players]
            }
            
            # Calculate team totals
            for team in [team1, team2]:
                team_predictions = predictions[team]
                predictions[f"{team}_totals"] = {
                    'total_runs': sum(p['predicted_runs'] for p in team_predictions if 'predicted_runs' in p),
                    'total_wickets': sum(p['predicted_wickets'] for p in team_predictions if 'predicted_wickets' in p)
                }
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting match: {str(e)}")
            return {'error': str(e)}

if __name__ == "__main__":
    # Example: RCB vs GT on April 2nd
    predictor = MatchPredictor()
    predictions = predictor.predict_match(
        team1="Royal Challengers Bangalore",
        team2="Gujarat Titans",
        date="2024-04-02"
    )
    
    # Print predictions
    print("\nMatch Predictions:")
    for team, team_preds in predictions.items():
        if not team.endswith('_totals'):
            print(f"\n{team}:")
            for player in team_preds:
                if 'error' not in player:
                    print(f"{player['player_name']}:")
                    print(f"  Predicted runs: {player['predicted_runs']}")
                    print(f"  Predicted wickets: {player['predicted_wickets']}")
                    print(f"  Predicted catches: {player['predicted_catches']}")
        else:
            print(f"\n{team}:")
            print(f"Total runs: {predictions[team]['total_runs']}")
            print(f"Total wickets: {predictions[team]['total_wickets']}") 