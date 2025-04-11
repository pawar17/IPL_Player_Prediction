import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json
from typing import Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_collection.log'),
        logging.StreamHandler()
    ]
)

class IPLDataCollector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.dataset_path = self.base_path / 'IPL_DATASET'
        self.processed_data_path = self.base_path / 'data' / 'processed'
        
        # Create processed data directory if it doesn't exist
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

    def process_matches_data(self):
        """Process matches.csv data."""
        logging.info("Processing matches data...")
        try:
            matches_df = pd.read_csv(self.dataset_path / 'matches.csv')
            
            # Convert date columns to datetime
            matches_df['date'] = pd.to_datetime(matches_df['date'])
            
            # Handle missing values
            matches_df['winner'] = matches_df['winner'].fillna('No Result')
            matches_df['player_of_match'] = matches_df['player_of_match'].fillna('No Player')
            
            # Save processed data
            matches_df.to_csv(self.processed_data_path / 'processed_matches.csv', index=False)
            logging.info("Successfully processed matches data")
            
            return matches_df
        except Exception as e:
            logging.error(f"Error processing matches data: {str(e)}")
            raise

    def process_deliveries_data(self):
        """Process deliveries.csv data."""
        logging.info("Processing deliveries data...")
        try:
            deliveries_df = pd.read_csv(self.dataset_path / 'deliveries.csv')
            
            # Handle missing values
            deliveries_df['player_dismissed'] = deliveries_df['player_dismissed'].fillna('Not Out')
            deliveries_df['dismissal_kind'] = deliveries_df['dismissal_kind'].fillna('Not Out')
            
            # Calculate additional metrics
            deliveries_df['is_boundary'] = deliveries_df['batsman_runs'].apply(lambda x: 1 if x >= 4 else 0)
            deliveries_df['is_six'] = deliveries_df['batsman_runs'].apply(lambda x: 1 if x == 6 else 0)
            
            # Save processed data
            deliveries_df.to_csv(self.processed_data_path / 'processed_deliveries.csv', index=False)
            logging.info("Successfully processed deliveries data")
            
            return deliveries_df
        except Exception as e:
            logging.error(f"Error processing deliveries data: {str(e)}")
            raise

    def aggregate_player_stats(self, matches_df, deliveries_df):
        """Aggregate player statistics from matches and deliveries data."""
        logging.info("Aggregating player statistics...")
        try:
            # Merge matches and deliveries data
            merged_df = deliveries_df.merge(
                matches_df[['id', 'season', 'date', 'venue', 'team1', 'team2']],
                left_on='match_id',
                right_on='id'
            )
            
            # Calculate player statistics
            player_stats = merged_df.groupby('batter').agg({
                'batsman_runs': ['sum', 'count', 'mean'],
                'is_boundary': 'sum',
                'is_six': 'sum'
            }).reset_index()
            
            # Rename columns
            player_stats.columns = ['player', 'total_runs', 'balls_faced', 'average', 'fours', 'sixes']
            
            # Calculate strike rate
            player_stats['strike_rate'] = (player_stats['total_runs'] / player_stats['balls_faced']) * 100
            
            # Save aggregated stats
            player_stats.to_csv(self.processed_data_path / 'player_stats.csv', index=False)
            logging.info("Successfully aggregated player statistics")
            
            return player_stats
        except Exception as e:
            logging.error(f"Error aggregating player statistics: {str(e)}")
            raise

    def run(self):
        """Run the complete data collection and processing pipeline."""
        try:
            logging.info("Starting IPL data processing pipeline...")
            
            # Process data
            matches_df = self.process_matches_data()
            deliveries_df = self.process_deliveries_data()
            
            # Aggregate statistics
            player_stats = self.aggregate_player_stats(matches_df, deliveries_df)
            
            logging.info("Successfully completed data processing pipeline")
            
        except Exception as e:
            logging.error(f"Error in data processing pipeline: {str(e)}")
            raise

class HistoricalDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.processed_path = self.data_path / 'processed'
        
    def _get_batting_stats(self, player_data: pd.DataFrame) -> Dict:
        """Calculate batting statistics from historical data"""
        try:
            batting_stats = {
                'runs': int(player_data['batting_runs'].sum()),
                'balls': int(player_data['balls_faced'].sum()),
                'average': float(player_data['batting_runs'].sum() / max(1, len(player_data[player_data['batting_runs'] > 0]))),
                'strike_rate': float(player_data['batting_runs'].sum() / max(1, player_data['balls_faced'].sum()) * 100),
                'fours': int(player_data['fours'].sum()),
                'sixes': int(player_data['sixes'].sum())
            }
            return batting_stats
        except Exception as e:
            self.logger.error(f"Error calculating batting stats: {str(e)}")
            return {
                'runs': 0,
                'balls': 0,
                'average': 0.0,
                'strike_rate': 0.0,
                'fours': 0,
                'sixes': 0
            }
            
    def _get_bowling_stats(self, player_data: pd.DataFrame) -> Dict:
        """Calculate bowling statistics from historical data"""
        try:
            bowling_stats = {
                'wickets': int(player_data['wickets'].sum()),
                'runs_conceded': int(player_data['runs_conceded'].sum()),
                'overs': float(player_data['overs'].sum()),
                'economy': float(player_data['runs_conceded'].sum() / max(1, player_data['overs'].sum())),
                'average': float(player_data['runs_conceded'].sum() / max(1, player_data['wickets'].sum()))
            }
            return bowling_stats
        except Exception as e:
            self.logger.error(f"Error calculating bowling stats: {str(e)}")
            return {
                'wickets': 0,
                'runs_conceded': 0,
                'overs': 0.0,
                'economy': 0.0,
                'average': 0.0
            }
            
    def _get_fielding_stats(self, player_data: pd.DataFrame) -> Dict:
        """Calculate fielding statistics from historical data"""
        try:
            fielding_stats = {
                'catches': int(player_data['catches'].sum()),
                'stumpings': int(player_data['stumpings'].sum()),
                'run_outs': int(player_data['run_outs'].sum())
            }
            return fielding_stats
        except Exception as e:
            self.logger.error(f"Error calculating fielding stats: {str(e)}")
            return {
                'catches': 0,
                'stumpings': 0,
                'run_outs': 0
            }
            
    def get_player_stats(self, player_name: str) -> Dict:
        """Get player's historical statistics"""
        try:
            # Read ball-by-ball data
            ball_by_ball_path = Path('IPL-DATASET-main/IPL-DATASET-main/csv/Ball_By_Ball_Match_Data.csv')
            if not ball_by_ball_path.exists():
                self.logger.error("Ball-by-ball data file not found")
                return self._get_default_stats()
                
            ball_by_ball_data = pd.read_csv(ball_by_ball_path)
            
            # Filter data for the player (as batter and bowler)
            batting_data = ball_by_ball_data[ball_by_ball_data['Batter'] == player_name]
            bowling_data = ball_by_ball_data[ball_by_ball_data['Bowler'] == player_name]
            
            # Calculate batting stats
            batting_stats = {
                'runs': int(batting_data['BatsmanRun'].sum()),
                'balls': len(batting_data),
                'average': float(batting_data['BatsmanRun'].sum() / max(1, len(batting_data[batting_data['BatsmanRun'] > 0]))),
                'strike_rate': float(batting_data['BatsmanRun'].sum() / max(1, len(batting_data)) * 100),
                'fours': len(batting_data[batting_data['BatsmanRun'] == 4]),
                'sixes': len(batting_data[batting_data['BatsmanRun'] == 6])
            }
            
            # Calculate bowling stats
            bowling_stats = {
                'wickets': int(bowling_data['IsWicketDelivery'].sum()),
                'runs_conceded': int(bowling_data['TotalRun'].sum()),
                'overs': float(len(bowling_data) / 6),  # Convert balls to overs
                'economy': float(bowling_data['TotalRun'].sum() / max(1, len(bowling_data) / 6)),
                'average': float(bowling_data['TotalRun'].sum() / max(1, bowling_data['IsWicketDelivery'].sum()))
            }
            
            # Calculate fielding stats
            fielding_stats = {
                'catches': int(ball_by_ball_data[ball_by_ball_data['FieldersInvolved'].fillna('').str.contains(player_name, na=False)]['IsWicketDelivery'].sum()),
                'stumpings': 0,  # Need additional data to calculate stumpings
                'run_outs': 0  # Need additional data to calculate run outs
            }
            
            return {
                'batting': batting_stats,
                'bowling': bowling_stats,
                'fielding': fielding_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting historical stats for {player_name}: {str(e)}")
            return self._get_default_stats()
            
    def _get_default_stats(self) -> Dict:
        """Return default stats when data is not available"""
        return {
            'batting': {
                'runs': 0,
                'balls': 0,
                'average': 0.0,
                'strike_rate': 0.0,
                'fours': 0,
                'sixes': 0
            },
            'bowling': {
                'wickets': 0,
                'runs_conceded': 0,
                'overs': 0.0,
                'economy': 0.0,
                'average': 0.0
            },
            'fielding': {
                'catches': 0,
                'stumpings': 0,
                'run_outs': 0
            }
        }

if __name__ == "__main__":
    collector = IPLDataCollector()
    collector.run() 