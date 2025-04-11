import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os
import csv
import time

class EfficientDataCollector:
    """
    Efficient data collection system that minimizes API calls by:
    1. Using local data storage with incremental updates
    2. Implementing smart caching and update strategies
    3. Combining multiple data sources for comprehensive player information
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        
        # Set up data paths
        self.data_path = self.base_path / 'data'
        self.historical_path = self.data_path / 'historical'
        self.processed_path = self.data_path / 'processed'
        self.cache_path = self.data_path / 'cache'
        self.updates_path = self.data_path / 'updates'
        
        # Create necessary directories
        for path in [self.processed_path, self.cache_path, self.updates_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data caches
        self.player_cache = {}
        self.team_cache = {}
        self.match_cache = {}
        self.venue_cache = {}
        
        # Load IPL 2025 data
        self.ipl_data = self._load_ipl_data()
        
        # Set up update tracking
        self.last_update_time = {}
        self.update_frequencies = {
            'player_stats': timedelta(hours=6),
            'team_stats': timedelta(hours=12),
            'match_data': timedelta(hours=1),
            'venue_data': timedelta(days=1),
            'injury_updates': timedelta(hours=3),
            'weather_data': timedelta(hours=3)
        }
    
    def _load_ipl_data(self):
        """Load IPL 2025 schedule and team data"""
        try:
            from .ipl_2025_data import IPL2025Data
            return IPL2025Data()
        except ImportError:
            self.logger.error("Failed to import IPL2025Data. Using empty data.")
            return None
    
    def load_historical_data(self) -> pd.DataFrame:
        """
        Load and process historical IPL data from CSV files
        
        Returns:
            DataFrame containing processed historical data
        """
        try:
            # Check if processed data already exists
            processed_file = self.processed_path / 'historical_data_processed.csv'
            if processed_file.exists():
                self.logger.info(f"Loading processed historical data from {processed_file}")
                return pd.read_csv(processed_file)
            
            # Load raw historical data
            matches_file = self.historical_path / 'ipl_matches_2008_2023.csv'
            player_stats_file = self.historical_path / 'player_stats.csv'
            
            if not matches_file.exists() or not player_stats_file.exists():
                self.logger.error("Historical data files not found")
                return pd.DataFrame()
            
            self.logger.info("Loading and processing historical data...")
            
            # Load matches data
            matches_data = pd.read_csv(matches_file)
            
            # Load player stats data
            player_stats = pd.read_csv(player_stats_file)
            
            # Process and merge data
            processed_data = self._process_historical_data(matches_data, player_stats)
            
            # Save processed data
            processed_data.to_csv(processed_file, index=False)
            self.logger.info(f"Saved processed historical data to {processed_file}")
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()
    
    def _process_historical_data(self, matches_data: pd.DataFrame, player_stats: pd.DataFrame) -> pd.DataFrame:
        """
        Process and merge historical data
        
        Args:
            matches_data: DataFrame containing match data
            player_stats: DataFrame containing player statistics
            
        Returns:
            Processed DataFrame
        """
        # Ensure consistent column naming
        if 'Player' in player_stats.columns:
            player_stats = player_stats.rename(columns={'Player': 'player'})
        
        # Merge matches and player stats
        merged_data = pd.merge(
            player_stats,
            matches_data,
            on='match_id',
            how='left'
        )
        
        # Calculate derived features
        processed_data = self._calculate_derived_features(merged_data)
        
        return processed_data
    
    def _calculate_derived_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived features for model training
        
        Args:
            data: Input DataFrame
            
        Returns:
            DataFrame with additional derived features
        """
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Sort by date for time-based calculations
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        
        # Calculate rolling averages for each player
        player_groups = df.groupby('player_id')
        
        # Last 5 matches stats
        df['last_5_matches_runs_avg'] = player_groups['runs'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        
        df['last_5_matches_wickets_avg'] = player_groups['wickets'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        
        df['last_5_matches_sr_avg'] = player_groups['strike_rate'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        
        df['last_5_matches_er_avg'] = player_groups['economy_rate'].transform(
            lambda x: x.rolling(5, min_periods=1).mean()
        )
        
        # Last 10 matches stats
        df['last_10_matches_runs_avg'] = player_groups['runs'].transform(
            lambda x: x.rolling(10, min_periods=1).mean()
        )
        
        df['last_10_matches_wickets_avg'] = player_groups['wickets'].transform(
            lambda x: x.rolling(10, min_periods=1).mean()
        )
        
        df['last_10_matches_sr_avg'] = player_groups['strike_rate'].transform(
            lambda x: x.rolling(10, min_periods=1).mean()
        )
        
        df['last_10_matches_er_avg'] = player_groups['economy_rate'].transform(
            lambda x: x.rolling(10, min_periods=1).mean()
        )
        
        # Career averages
        df['career_runs_avg'] = player_groups['runs'].transform('mean')
        df['career_wickets_avg'] = player_groups['wickets'].transform('mean')
        df['career_sr_avg'] = player_groups['strike_rate'].transform('mean')
        df['career_er_avg'] = player_groups['economy_rate'].transform('mean')
        
        # Form factor (recent performance vs career average)
        df['form_factor'] = np.where(
            df['career_runs_avg'] > 0,
            df['last_5_matches_runs_avg'] / df['career_runs_avg'],
            1.0
        )
        
        # Consistency score (based on standard deviation of performance)
        df['runs_std'] = player_groups['runs'].transform('std')
        df['consistency_score'] = np.where(
            df['career_runs_avg'] > 0,
            1 - (df['runs_std'] / df['career_runs_avg']).clip(0, 1),
            0.5
        )
        
        # Player role indicators
        df['is_batsman'] = np.where(df['player_role'].str.contains('Batsman', na=False), 1, 0)
        df['is_bowler'] = np.where(df['player_role'].str.contains('Bowler', na=False), 1, 0)
        df['is_all_rounder'] = np.where(df['player_role'].str.contains('All-rounder', na=False), 1, 0)
        df['is_wicket_keeper'] = np.where(df['player_role'].str.contains('Wicket', na=False), 1, 0)
        
        # Match context
        df['is_home_match'] = np.where(df['team'] == df['home_team'], 1, 0)
        
        # Fill any remaining NaN values
        df = df.fillna(0)
        
        return df
    
    def get_player_data(self, player_name: str, update_if_needed: bool = True) -> Dict[str, Any]:
        """
        Get comprehensive player data combining historical and recent information
        
        Args:
            player_name: Name of the player
            update_if_needed: Whether to update data if it's stale
            
        Returns:
            Dictionary containing player data
        """
        try:
            # Check cache first
            if player_name in self.player_cache:
                player_data = self.player_cache[player_name]
                
                # Check if update is needed
                last_update = self.last_update_time.get(f"player_{player_name}", datetime.min)
                if (datetime.now() - last_update) < self.update_frequencies['player_stats']:
                    return player_data
            
            # Need to load or update data
            if update_if_needed:
                player_data = self._update_player_data(player_name)
                self.player_cache[player_name] = player_data
                self.last_update_time[f"player_{player_name}"] = datetime.now()
                return player_data
            
            # No data available and not updating
            return {}
            
        except Exception as e:
            self.logger.error(f"Error getting player data for {player_name}: {str(e)}")
            return {}
    
    def _update_player_data(self, player_name: str) -> Dict[str, Any]:
        """
        Update player data from various sources
        
        Args:
            player_name: Name of the player
            
        Returns:
            Updated player data dictionary
        """
        # Check if we have cached data first
        cache_file = self.cache_path / f"player_{player_name.replace(' ', '_')}.json"
        player_data = {}
        
        if cache_file.exists():
            # Load cached data
            with open(cache_file, 'r') as f:
                player_data = json.load(f)
        
        # Supplement with historical data
        historical_data = self._get_player_historical_data(player_name)
        if historical_data:
            player_data.update(historical_data)
        
        # Add team information
        for team_name, team_info in self.ipl_data.teams.items():
            for player in team_info['players']:
                if player['name'] == player_name:
                    player_data['current_team'] = team_name
                    player_data['role'] = player['role']
                    player_data['price'] = player['price']
                    break
        
        # Add injury information
        injury_data = self._get_player_injury_data(player_name)
        if injury_data:
            player_data['injury_status'] = injury_data
        
        # Add recent form data
        recent_form = self._get_player_recent_form(player_name)
        if recent_form:
            player_data['recent_form'] = recent_form
        
        # Save updated data to cache
        with open(cache_file, 'w') as f:
            json.dump(player_data, f, indent=4)
        
        return player_data
    
    def _get_player_historical_data(self, player_name: str) -> Dict[str, Any]:
        """
        Get player historical data from processed historical data
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dictionary with historical statistics
        """
        # Load processed historical data
        historical_file = self.processed_path / 'historical_data_processed.csv'
        if not historical_file.exists():
            return {}
        
        # Load only the player's data to save memory
        player_data = pd.read_csv(historical_file, usecols=lambda col: col in [
            'player_name', 'runs', 'wickets', 'strike_rate', 'economy_rate',
            'career_runs_avg', 'career_wickets_avg', 'career_sr_avg', 'career_er_avg',
            'last_5_matches_runs_avg', 'last_5_matches_wickets_avg',
            'last_5_matches_sr_avg', 'last_5_matches_er_avg'
        ])
        
        player_data = player_data[player_data['player_name'] == player_name]
        
        if player_data.empty:
            return {}
        
        # Get the latest record
        latest_record = player_data.iloc[-1].to_dict()
        
        # Extract relevant fields
        return {
            'career_runs_avg': latest_record.get('career_runs_avg', 0),
            'career_wickets_avg': latest_record.get('career_wickets_avg', 0),
            'career_sr_avg': latest_record.get('career_sr_avg', 0),
            'career_er_avg': latest_record.get('career_er_avg', 0),
            'last_5_matches_runs_avg': latest_record.get('last_5_matches_runs_avg', 0),
            'last_5_matches_wickets_avg': latest_record.get('last_5_matches_wickets_avg', 0),
            'last_5_matches_sr_avg': latest_record.get('last_5_matches_sr_avg', 0),
            'last_5_matches_er_avg': latest_record.get('last_5_matches_er_avg', 0)
        }
    
    def _get_player_injury_data(self, player_name: str) -> Dict[str, Any]:
        """
        Get player injury data from local storage
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dictionary with injury information
        """
        # Check for injury updates file
        injury_file = self.updates_path / 'injury_updates.json'
        if not injury_file.exists():
            return {}
        
        try:
            with open(injury_file, 'r') as f:
                injury_data = json.load(f)
            
            # Find player's injury data
            for player_injury in injury_data:
                if player_injury.get('player_name') == player_name:
                    return {
                        'is_injured': player_injury.get('is_injured', False),
                        'injury_type': player_injury.get('injury_type', ''),
                        'expected_recovery': player_injury.get('expected_recovery', ''),
                        'last_updated': player_injury.get('last_updated', '')
                    }
            
            # No injury data found
            return {
                'is_injured': False,
                'days_since_last_injury': 30,  # Default value
                'is_fully_fit': True
            }
            
        except Exception as e:
            self.logger.error(f"Error reading injury data: {str(e)}")
            return {}
    
    def _get_player_recent_form(self, player_name: str) -> Dict[str, Any]:
        """
        Get player's recent form data
        
        Args:
            player_name: Name of the player
            
        Returns:
            Dictionary with recent form information
        """
        # Check for recent form file
        form_file = self.updates_path / 'recent_form.json'
        if not form_file.exists():
            return {}
        
        try:
            with open(form_file, 'r') as f:
                form_data = json.load(f)
            
            # Find player's form data
            for player_form in form_data:
                if player_form.get('player_name') == player_name:
                    return player_form
            
            # No form data found
            return {}
            
        except Exception as e:
            self.logger.error(f"Error reading form data: {str(e)}")
            return {}
    
    def get_match_data(self, match_no: int) -> Dict[str, Any]:
        """
        Get comprehensive match data including teams, venue, and conditions
        
        Args:
            match_no: Match number in the IPL 2025 schedule
            
        Returns:
            Dictionary containing match data
        """
        try:
            # Find match in schedule
            match_data = None
            for match in self.ipl_data.schedule:
                if match.get('match_no') == match_no:
                    match_data = match
                    break
            
            if not match_data:
                self.logger.error(f"Match {match_no} not found in schedule")
                return {}
            
            # Enhance with team data
            team1_name = match_data.get('team1')
            team2_name = match_data.get('team2')
            
            team1_data = self.get_team_data(team1_name)
            team2_data = self.get_team_data(team2_name)
            
            # Enhance with venue data
            venue_name = match_data.get('venue').split(',')[0].strip()
            venue_data = self.get_venue_data(venue_name)
            
            # Combine all data
            comprehensive_match_data = {
                'match_no': match_no,
                'date': match_data.get('date'),
                'time': match_data.get('time'),
                'venue': match_data.get('venue'),
                'team1': {
                    'name': team1_name,
                    'data': team1_data
                },
                'team2': {
                    'name': team2_name,
                    'data': team2_data
                },
                'venue_data': venue_data,
                'weather': self._get_weather_data(venue_name, match_data.get('date'))
            }
            
            return comprehensive_match_data
            
        except Exception as e:
            self.logger.error(f"Error getting match data for match {match_no}: {str(e)}")
            return {}
    
    def get_team_data(self, team_name: str) -> Dict[str, Any]:
        """
        Get team data including players and recent performance
        
        Args:
            team_name: Name of the team
            
        Returns:
            Dictionary containing team data
        """
        try:
            # Check cache first
            if team_name in self.team_cache:
                return self.team_cache[team_name]
            
            # Get team info from IPL data
            team_info = self.ipl_data.teams.get(team_name, {})
            if not team_info:
                return {}
            
            # Enhance with recent performance
            team_performance = self._get_team_performance(team_name)
            
            # Combine data
            team_data = {
                'captain': team_info.get('captain', ''),
                'coach': team_info.get('coach', ''),
                'home_ground': team_info.get('home_ground', ''),
                'players': team_info.get('players', []),
                'recent_performance': team_performance
            }
            
            # Cache the data
            self.team_cache[team_name] = team_data
            
            return team_data
            
        except Exception as e:
            self.logger.error(f"Error getting team data for {team_name}: {str(e)}")
            return {}
    
    def _get_team_performance(self, team_name: str) -> Dict[str, Any]:
        """
        Get team's recent performance data
        
        Args:
            team_name: Name of the team
            
        Returns:
            Dictionary with recent performance information
        """
        # Check for team performance file
        performance_file = self.updates_path / 'team_performance.json'
        if not performance_file.exists():
            return {}
        
        try:
            with open(performance_file, 'r') as f:
                performance_data = json.load(f)
            
            # Find team's performance data
            for team_performance in performance_data:
                if team_performance.get('team_name') == team_name:
                    return team_performance
            
            # No performance data found
            return {}
            
        except Exception as e:
            self.logger.error(f"Error reading team performance data: {str(e)}")
            return {}
    
    def get_venue_data(self, venue_name: str) -> Dict[str, Any]:
        """
        Get venue data including pitch conditions and historical stats
        
        Args:
            venue_name: Name of the venue
            
        Returns:
            Dictionary containing venue data
        """
        try:
            # Check cache first
            if venue_name in self.venue_cache:
                return self.venue_cache[venue_name]
            
            # Check for venue data file
            venue_file = self.updates_path / 'venue_conditions.json'
            if not venue_file.exists():
                return {}
            
            with open(venue_file, 'r') as f:
                venue_data = json.load(f)
            
            # Find venue data
            venue_info = {}
            for venue in venue_data:
                if venue.get('name') == venue_name:
                    venue_info = venue
                    break
            
            # Cache the data
            self.venue_cache[venue_name] = venue_info
            
            return venue_info
            
        except Exception as e:
            self.logger.error(f"Error getting venue data for {venue_name}: {str(e)}")
            return {}
    
    def _get_weather_data(self, venue_name: str, match_date: str) -> Dict[str, Any]:
        """
        Get weather data for a venue on a specific date
        
        Args:
            venue_name: Name of the venue
            match_date: Date of the match
            
        Returns:
            Dictionary with weather information
        """
        # Check for weather data file
        weather_file = self.updates_path / 'weather_data.json'
        if not weather_file.exists():
            return {}
        
        try:
            with open(weather_file, 'r') as f:
                weather_data = json.load(f)
            
            # Find weather data for venue and date
            for weather in weather_data:
                if (weather.get('venue') == venue_name and 
                    weather.get('date') == match_date):
                    return weather
            
            # No weather data found
            return {}
            
        except Exception as e:
            self.logger.error(f"Error reading weather data: {str(e)}")
            return {}
    
    def prepare_prediction_data(self, match_no: int, player_name: str) -> Dict[str, Any]:
        """
        Prepare comprehensive data for player performance prediction
        
        Args:
            match_no: Match number in the IPL 2025 schedule
            player_name: Name of the player
            
        Returns:
            Dictionary with all features needed for prediction
        """
        try:
            # Get match data
            match_data = self.get_match_data(match_no)
            if not match_data:
                return {}
            
            # Get player data
            player_data = self.get_player_data(player_name)
            if not player_data:
                return {}
            
            # Determine player's team and opposition
            player_team = None
            opposition_team = None
            
            team1_players = [p['name'] for p in match_data['team1']['data'].get('players', [])]
            team2_players = [p['name'] for p in match_data['team2']['data'].get('players', [])]
            
            if player_name in team1_players:
                player_team = match_data['team1']['name']
                opposition_team = match_data['team2']['name']
            elif player_name in team2_players:
                player_team = match_data['team2']['name']
                opposition_team = match_data['team1']['name']
            else:
                self.logger.warning(f"Player {player_name} not found in either team for match {match_no}")
                return {}
            
            # Get venue data
            venue_data = match_data.get('venue_data', {})
            
            # Prepare prediction features
            prediction_data = {
                # Player identification
                'player_name': player_name,
                'team': player_team,
                'opposition': opposition_team,
                'venue': match_data.get('venue', '').split(',')[0].strip(),
                'match_date': match_data.get('date', ''),
                
                # Player's recent performance
                'last_5_matches_runs_avg': player_data.get('last_5_matches_runs_avg', 0),
                'last_5_matches_wickets_avg': player_data.get('last_5_matches_wickets_avg', 0),
                'last_5_matches_sr_avg': player_data.get('last_5_matches_sr_avg', 0),
                'last_5_matches_er_avg': player_data.get('last_5_matches_er_avg', 0),
                
                # Player's career stats
                'career_runs_avg': player_data.get('career_runs_avg', 0),
                'career_wickets_avg': player_data.get('career_wickets_avg', 0),
                'career_sr_avg': player_data.get('career_sr_avg', 0),
                'career_er_avg': player_data.get('career_er_avg', 0),
                
                # Player's role
                'is_batsman': 1 if 'Batsman' in player_data.get('role', '') else 0,
                'is_bowler': 1 if 'Bowler' in player_data.get('role', '') else 0,
                'is_all_rounder': 1 if 'All-rounder' in player_data.get('role', '') else 0,
                'is_wicket_keeper': 1 if 'WK' in player_data.get('role', '') else 0,
                
                # Player's form and fitness
                'form_factor': player_data.get('recent_form', {}).get('form_factor', 1.0),
                'consistency_score': player_data.get('recent_form', {}).get('consistency_score', 0.5),
                'days_since_last_injury': player_data.get('injury_status', {}).get('days_since_last_injury', 30),
                'is_fully_fit': player_data.get('injury_status', {}).get('is_fully_fit', True),
                
                # Match context
                'is_home_match': 1 if match_data.get('venue', '').split(',')[0].strip() == 
                                 self.ipl_data.teams.get(player_team, {}).get('home_ground', '') else 0,
                'is_day_match': 1 if match_data.get('time', '') < '17:00' else 0,
                'is_knockout_match': 1 if match_no > 70 else 0,  # Playoff matches are after match 70
                
                # Venue statistics
                'venue_avg_first_innings_score': venue_data.get('avg_first_innings_score', 160),
                'venue_avg_second_innings_score': venue_data.get('avg_second_innings_score', 150),
                'venue_avg_wickets_per_match': venue_data.get('avg_wickets_per_match', 12),
                
                # Pitch conditions
                'is_pitch_batting_friendly': venue_data.get('is_batting_friendly', 0),
                'is_pitch_bowling_friendly': venue_data.get('is_bowling_friendly', 0),
                
                # Weather conditions
                'is_windy': match_data.get('weather', {}).get('is_windy', 0),
                'is_humid': match_data.get('weather', {}).get('is_humid', 0),
                
                # Team strengths
                'team_batting_strength': 0.5,  # Default values
                'team_bowling_strength': 0.5,
                'opposition_batting_strength': 0.5,
                'opposition_bowling_strength': 0.5,
                'team_last_5_matches_win_rate': 0.5
            }
            
            # Add team strength calculations if available
            team1_performance = match_data['team1']['data'].get('recent_performance', {})
            team2_performance = match_data['team2']['data'].get('recent_performance', {})
            
            if player_team == match_data['team1']['name']:
                prediction_data['team_batting_strength'] = team1_performance.get('batting_strength', 0.5)
                prediction_data['team_bowling_strength'] = team1_performance.get('bowling_strength', 0.5)
                prediction_data['opposition_batting_strength'] = team2_performance.get('batting_strength', 0.5)
                prediction_data['opposition_bowling_strength'] = team2_performance.get('bowling_strength', 0.5)
                prediction_data['team_last_5_matches_win_rate'] = team1_performance.get('last_5_win_rate', 0.5)
            else:
                prediction_data['team_batting_strength'] = team2_performance.get('batting_strength', 0.5)
                prediction_data['team_bowling_strength'] = team2_performance.get('bowling_strength', 0.5)
                prediction_data['opposition_batting_strength'] = team1_performance.get('batting_strength', 0.5)
                prediction_data['opposition_bowling_strength'] = team1_performance.get('bowling_strength', 0.5)
                prediction_data['team_last_5_matches_win_rate'] = team2_performance.get('last_5_win_rate', 0.5)
            
            return prediction_data
            
        except Exception as e:
            self.logger.error(f"Error preparing prediction data: {str(e)}")
            return {}
