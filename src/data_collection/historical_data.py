import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

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

if __name__ == "__main__":
    collector = IPLDataCollector()
    collector.run() 