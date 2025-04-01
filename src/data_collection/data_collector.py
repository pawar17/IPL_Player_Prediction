import requests
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta
import pandas as pd
import time

class DataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.raw_path = self.data_path / 'raw'
        self.scraped_path = self.data_path / 'scraped'
        
        # Create necessary directories
        for path in [self.data_path, self.raw_path, self.scraped_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Set up headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds
    
    def collect_all_data(self) -> bool:
        """Collect data from all sources"""
        try:
            success = True
            
            # 1. Load historical data
            success &= self._load_historical_data()
            
            # 2. Collect current season data
            success &= self._collect_current_season_data()
            
            # 3. Collect player availability
            success &= self._collect_player_availability()
            
            # 4. Collect venue information
            success &= self._collect_venue_data()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error collecting data: {str(e)}")
            return False
    
    def _load_historical_data(self) -> bool:
        """Load and validate historical data"""
        try:
            # Load matches data
            matches_df = pd.read_csv(self.raw_path / 'matches.csv')
            deliveries_df = pd.read_csv(self.raw_path / 'deliveries.csv')
            
            # Validate data
            if matches_df.empty or deliveries_df.empty:
                self.logger.error("Historical data files are empty")
                return False
            
            # Save processed historical data
            self._process_historical_data(matches_df, deliveries_df)
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {str(e)}")
            return False
    
    def _collect_current_season_data(self) -> bool:
        """Collect current season data from IPL website"""
        try:
            # Collect match schedules
            schedules = self._collect_match_schedules()
            if schedules:
                self._save_data('match_schedules.json', schedules)
            
            # Collect team rosters
            rosters = self._collect_team_rosters()
            if rosters:
                self._save_data('team_rosters.json', rosters)
            
            # Collect player statistics
            player_stats = self._collect_player_statistics()
            if player_stats:
                self._save_data('player_statistics.json', player_stats)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error collecting current season data: {str(e)}")
            return False
    
    def _collect_player_availability(self) -> bool:
        """Collect player availability information"""
        try:
            # Collect from multiple sources
            availability_data = {
                'injuries': self._collect_injury_reports(),
                'squad_changes': self._collect_squad_changes(),
                'player_status': self._collect_player_status()
            }
            
            self._save_data('player_availability.json', availability_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Error collecting player availability: {str(e)}")
            return False
    
    def _collect_venue_data(self) -> bool:
        """Collect venue-specific information"""
        try:
            venue_data = {
                'grounds': self._collect_ground_statistics(),
                'weather': self._collect_weather_forecasts(),
                'pitch_conditions': self._collect_pitch_conditions()
            }
            
            self._save_data('venue_data.json', venue_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Error collecting venue data: {str(e)}")
            return False
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with rate limiting and error handling"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last_request)
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            self.last_request_time = time.time()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    def _save_data(self, filename: str, data: Any) -> bool:
        """Save data to JSON file"""
        try:
            filepath = self.scraped_path / filename
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to {filename}: {str(e)}")
            return False
    
    def _process_historical_data(self, matches_df: pd.DataFrame, deliveries_df: pd.DataFrame) -> None:
        """Process and save historical data"""
        try:
            # Calculate player statistics
            player_stats = self._calculate_player_statistics(deliveries_df)
            
            # Calculate team statistics
            team_stats = self._calculate_team_statistics(matches_df, deliveries_df)
            
            # Calculate venue statistics
            venue_stats = self._calculate_venue_statistics(matches_df, deliveries_df)
            
            # Save processed data
            self._save_data('processed_player_stats.json', player_stats)
            self._save_data('processed_team_stats.json', team_stats)
            self._save_data('processed_venue_stats.json', venue_stats)
            
        except Exception as e:
            self.logger.error(f"Error processing historical data: {str(e)}")
    
    def _calculate_player_statistics(self, deliveries_df: pd.DataFrame) -> Dict:
        """Calculate player statistics from deliveries data"""
        stats = {}
        
        # Group by player and calculate metrics
        player_stats = deliveries_df.groupby('player_name').agg({
            'runs': ['mean', 'std', 'count'],
            'wickets': ['mean', 'std'],
            'strike_rate': ['mean', 'std'],
            'economy_rate': ['mean', 'std']
        }).reset_index()
        
        # Convert to dictionary format
        for _, row in player_stats.iterrows():
            player = row['player_name']
            stats[player] = {
                'runs': {
                    'mean': row[('runs', 'mean')],
                    'std': row[('runs', 'std')],
                    'matches': row[('runs', 'count')]
                },
                'wickets': {
                    'mean': row[('wickets', 'mean')],
                    'std': row[('wickets', 'std')]
                },
                'strike_rate': {
                    'mean': row[('strike_rate', 'mean')],
                    'std': row[('strike_rate', 'std')]
                },
                'economy_rate': {
                    'mean': row[('economy_rate', 'mean')],
                    'std': row[('economy_rate', 'std')]
                }
            }
        
        return stats
    
    def _calculate_team_statistics(self, matches_df: pd.DataFrame, deliveries_df: pd.DataFrame) -> Dict:
        """Calculate team statistics"""
        stats = {}
        
        # Calculate team performance metrics
        team_stats = deliveries_df.groupby('team').agg({
            'runs': ['mean', 'std'],
            'wickets': ['mean', 'std'],
            'strike_rate': ['mean'],
            'economy_rate': ['mean']
        }).reset_index()
        
        # Convert to dictionary format
        for _, row in team_stats.iterrows():
            team = row['team']
            stats[team] = {
                'runs': {
                    'mean': row[('runs', 'mean')],
                    'std': row[('runs', 'std')]
                },
                'wickets': {
                    'mean': row[('wickets', 'mean')],
                    'std': row[('wickets', 'std')]
                },
                'strike_rate': row[('strike_rate', 'mean')],
                'economy_rate': row[('economy_rate', 'mean')]
            }
        
        return stats
    
    def _calculate_venue_statistics(self, matches_df: pd.DataFrame, deliveries_df: pd.DataFrame) -> Dict:
        """Calculate venue-specific statistics"""
        stats = {}
        
        # Merge matches and deliveries data
        merged_df = pd.merge(deliveries_df, matches_df[['match_id', 'venue']], on='match_id')
        
        # Calculate venue metrics
        venue_stats = merged_df.groupby('venue').agg({
            'runs': ['mean', 'std'],
            'wickets': ['mean', 'std'],
            'strike_rate': ['mean'],
            'economy_rate': ['mean']
        }).reset_index()
        
        # Convert to dictionary format
        for _, row in venue_stats.iterrows():
            venue = row['venue']
            stats[venue] = {
                'runs': {
                    'mean': row[('runs', 'mean')],
                    'std': row[('runs', 'std')]
                },
                'wickets': {
                    'mean': row[('wickets', 'mean')],
                    'std': row[('wickets', 'std')]
                },
                'strike_rate': row[('strike_rate', 'mean')],
                'economy_rate': row[('economy_rate', 'mean')]
            }
        
        return stats 