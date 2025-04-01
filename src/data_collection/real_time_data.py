import os
import json
import requests
import logging
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, List, Optional
import pandas as pd

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_time_data.log'),
        logging.StreamHandler()
    ]
)

class CricbuzzDataCollector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.raw_data_path = self.base_path / 'data' / 'raw'
        self.processed_data_path = self.base_path / 'data' / 'processed'
        
        # Create directories if they don't exist
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # API configuration
        self.base_url = "https://cricbuzz-cricket.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }

    def get_matches_list(self) -> List[Dict]:
        """Get list of current and upcoming matches."""
        try:
            url = f"{self.base_url}/matches/list"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching matches list: {str(e)}")
            raise

    def get_match_info(self, match_id: str) -> Dict:
        """Get detailed information about a specific match."""
        try:
            url = f"{self.base_url}/matches/get-info"
            params = {"id": match_id}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching match info: {str(e)}")
            raise

    def get_match_scorecard(self, match_id: str) -> Dict:
        """Get match scorecard data."""
        try:
            url = f"{self.base_url}/matches/get-scorecard"
            params = {"id": match_id}
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching match scorecard: {str(e)}")
            raise

    def process_match_data(self, match_data: Dict) -> pd.DataFrame:
        """Process match data into a structured format."""
        try:
            # Extract relevant information
            match_info = {
                'match_id': match_data.get('id'),
                'match_type': match_data.get('matchType'),
                'status': match_data.get('status'),
                'venue': match_data.get('venue', {}).get('name'),
                'start_time': match_data.get('startTime'),
                'team1': match_data.get('team1', {}).get('name'),
                'team2': match_data.get('team2', {}).get('name')
            }
            
            # Create DataFrame
            df = pd.DataFrame([match_info])
            return df
        except Exception as e:
            logging.error(f"Error processing match data: {str(e)}")
            raise

    def process_scorecard_data(self, scorecard_data: Dict) -> pd.DataFrame:
        """Process scorecard data into a structured format."""
        try:
            innings_data = []
            
            for innings in scorecard_data.get('innings', []):
                for player in innings.get('batsmen', []):
                    player_data = {
                        'match_id': scorecard_data.get('matchId'),
                        'innings_number': innings.get('inningsNumber'),
                        'player_name': player.get('name'),
                        'runs': player.get('runs'),
                        'balls_faced': player.get('ballsFaced'),
                        'fours': player.get('fours'),
                        'sixes': player.get('sixes'),
                        'strike_rate': player.get('strikeRate')
                    }
                    innings_data.append(player_data)
            
            return pd.DataFrame(innings_data)
        except Exception as e:
            logging.error(f"Error processing scorecard data: {str(e)}")
            raise

    def save_data(self, data: pd.DataFrame, filename: str):
        """Save data to CSV file."""
        try:
            filepath = self.processed_data_path / filename
            data.to_csv(filepath, index=False)
            logging.info(f"Successfully saved data to {filename}")
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            raise

    def collect_live_match_data(self, match_id: str):
        """Collect and process live match data."""
        try:
            # Get match info
            match_info = self.get_match_info(match_id)
            match_df = self.process_match_data(match_info)
            
            # Get scorecard
            scorecard = self.get_match_scorecard(match_id)
            scorecard_df = self.process_scorecard_data(scorecard)
            
            # Save data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_data(match_df, f"live_match_{timestamp}.csv")
            self.save_data(scorecard_df, f"live_scorecard_{timestamp}.csv")
            
            return match_df, scorecard_df
        except Exception as e:
            logging.error(f"Error collecting live match data: {str(e)}")
            raise

    def monitor_matches(self, interval: int = 300):
        """Monitor matches and collect data at regular intervals."""
        try:
            while True:
                logging.info("Starting match monitoring cycle...")
                
                # Get current matches
                matches = self.get_matches_list()
                
                # Process each match
                for match in matches:
                    if match.get('status') == 'LIVE':
                        match_id = match.get('id')
                        logging.info(f"Processing live match: {match_id}")
                        self.collect_live_match_data(match_id)
                
                logging.info(f"Waiting {interval} seconds before next update...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logging.info("Match monitoring stopped by user")
        except Exception as e:
            logging.error(f"Error in match monitoring: {str(e)}")
            raise

if __name__ == "__main__":
    collector = CricbuzzDataCollector()
    collector.monitor_matches() 