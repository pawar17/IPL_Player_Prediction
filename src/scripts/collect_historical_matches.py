import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.historical_dir.mkdir(parents=True, exist_ok=True)
    
    def load_historical_data(self) -> pd.DataFrame:
        """Load historical data from CSV files."""
        try:
            # Load main historical dataset
            main_file = self.historical_dir / "ipl_matches_2008_2023.csv"
            if main_file.exists():
                logger.info(f"Loading main historical dataset from {main_file}")
                data = pd.read_csv(main_file)
                logger.info(f"Loaded {len(data)} matches from main dataset")
                return data
            
            logger.error("Main historical dataset not found")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()
    
    def process_match_data(self, match_data: pd.Series) -> Dict:
        """Process match data into required format."""
        try:
            processed = {
                'match_id': match_data['match_id'],
                'date': match_data['date'],
                'venue': match_data['venue'],
                'team1': match_data['team1'],
                'team2': match_data['team2'],
                'winner': match_data['winner'],
                'player_id': match_data['player_id'],
                'player_name': match_data['player_name'],
                'runs': match_data['runs'],
                'wickets': match_data['wickets'],
                'strike_rate': match_data['strike_rate'],
                'economy_rate': match_data['economy_rate'],
                'opponent': match_data['opponent'],
                'match_importance': match_data['match_importance'],
                'pressure_index': match_data['pressure_index']
            }
            return processed
        except Exception as e:
            logger.error(f"Error processing match data: {str(e)}")
            return {}
    
    def collect_all_historical_data(self):
        """Process and combine all historical data."""
        try:
            # Load and process historical data
            historical_data = self.load_historical_data()
            
            if not historical_data.empty:
                # Process each match
                processed_matches = []
                for _, match in historical_data.iterrows():
                    processed_data = self.process_match_data(match)
                    if processed_data:
                        processed_matches.append(processed_data)
                
                # Save processed data
                output_file = self.historical_dir / "processed_historical_matches.csv"
                pd.DataFrame(processed_matches).to_csv(output_file, index=False)
                logger.info(f"Processed data saved with {len(processed_matches)} matches")
                
                # Group matches by player to create player statistics
                player_stats = []
                for player_id in historical_data['player_id'].unique():
                    player_matches = historical_data[historical_data['player_id'] == player_id]
                    player_name = player_matches['player_name'].iloc[0]
                    
                    # Calculate player statistics
                    stats = {
                        'player_id': player_id,
                        'name': player_name,
                        'matches_played': len(player_matches),
                        'total_runs': player_matches['runs'].sum(),
                        'total_wickets': player_matches['wickets'].sum(),
                        'batting_average': player_matches['runs'].mean(),
                        'bowling_average': player_matches['wickets'].mean(),
                        'strike_rate': player_matches['strike_rate'].mean(),
                        'economy_rate': player_matches['economy_rate'].mean(),
                        'recent_matches': json.dumps(player_matches.tail(5).to_dict('records'))
                    }
                    player_stats.append(stats)
                
                # Save player statistics
                stats_file = self.historical_dir / "player_stats.csv"
                pd.DataFrame(player_stats).to_csv(stats_file, index=False)
                logger.info(f"Player statistics saved for {len(player_stats)} players")
            
        except Exception as e:
            logger.error(f"Error processing historical data: {str(e)}")

def main():
    collector = HistoricalDataCollector()
    collector.collect_all_historical_data()

if __name__ == "__main__":
    main() 