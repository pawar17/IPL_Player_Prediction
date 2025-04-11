import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import json
from config import (
    DATA_DIR, HISTORICAL_DATA_FILE, PLAYER_STATS_FILE,
    VALIDATION_RULES, TEAMS, PLAYER_ROLES
)
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_path: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = data_path if data_path is not None else self.base_path / 'data'
        self.scraped_path = self.data_path / 'scraped'
        self.processed_path = self.data_path / 'processed'
        self.form_data_path = self.processed_path / 'player_form.csv'
        
        # Create necessary directories
        for path in [self.data_path, self.scraped_path, self.processed_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Weights for different data sources
        self.weights = {
            'cricbuzz_recent': 0.4,  # Last 5 matches
            'cricbuzz_current': 0.3,  # Current tournament
            'historical': 0.3         # All-time historical
        }
        
        # Player name mappings for normalization
        self.player_mappings = {
            'Virat Kohli': ['V Kohli', 'Kohli', 'VK'],
            'Faf du Plessis': ['F du Plessis', 'Faf', 'FAF'],
            'Glenn Maxwell': ['G Maxwell', 'Maxwell', 'Maxi'],
            'Mohammed Siraj': ['M Siraj', 'Siraj', 'Md Siraj'],
            'Dinesh Karthik': ['D Karthik', 'DK', 'Karthik'],
            'Shubman Gill': ['S Gill', 'Gill'],
            'Rashid Khan': ['R Khan', 'Rashid'],
            'David Miller': ['D Miller', 'Miller'],
            'Rahul Tewatia': ['R Tewatia', 'Tewatia'],
            'Mohit Sharma': ['M Sharma', 'Mohit']
        }
        
        # Default stats for new players based on role
        self.default_stats = {
            'batsman': {
                'Batting_Average': 25.0,
                'Batting_Strike_Rate': 125.0,
                'Batting_Average_3yr_avg': 25.0,
                'Batting_Strike_Rate_3yr_avg': 125.0,
                'Career_Batting_Average': 25.0,
                'Career_Batting_Strike_Rate': 125.0,
                'Career_Runs_Scored': 250,
                'Runs_Scored_3yr_avg': 25.0,
                'ball_runs': 100,
                'balls_faced': 80,
                'Bowling_Average': 50.0,
                'Economy_Rate': 9.0,
                'Career_Bowling_Average': 50.0,
                'Career_Economy_Rate': 9.0,
                'Career_Wickets_Taken': 0,
                'Wickets_Taken_3yr_avg': 0,
                'Career_Catches_Taken': 5,
                'Career_Stumpings': 0,
                'Career_Matches_Batted': 10
            },
            'bowler': {
                'Batting_Average': 12.0,
                'Batting_Strike_Rate': 100.0,
                'Batting_Average_3yr_avg': 12.0,
                'Batting_Strike_Rate_3yr_avg': 100.0,
                'Career_Batting_Average': 12.0,
                'Career_Batting_Strike_Rate': 100.0,
                'Career_Runs_Scored': 50,
                'Runs_Scored_3yr_avg': 12.0,
                'ball_runs': 20,
                'balls_faced': 20,
                'Bowling_Average': 25.0,
                'Economy_Rate': 8.0,
                'Career_Bowling_Average': 25.0,
                'Career_Economy_Rate': 8.0,
                'Career_Wickets_Taken': 15,
                'Wickets_Taken_3yr_avg': 1.5,
                'Career_Catches_Taken': 5,
                'Career_Stumpings': 0,
                'Career_Matches_Batted': 10
            },
            'all_rounder': {
                'Batting_Average': 20.0,
                'Batting_Strike_Rate': 130.0,
                'Batting_Average_3yr_avg': 20.0,
                'Batting_Strike_Rate_3yr_avg': 130.0,
                'Career_Batting_Average': 20.0,
                'Career_Batting_Strike_Rate': 130.0,
                'Career_Runs_Scored': 150,
                'Runs_Scored_3yr_avg': 20.0,
                'ball_runs': 60,
                'balls_faced': 45,
                'Bowling_Average': 28.0,
                'Economy_Rate': 8.5,
                'Career_Bowling_Average': 28.0,
                'Career_Economy_Rate': 8.5,
                'Career_Wickets_Taken': 10,
                'Wickets_Taken_3yr_avg': 1.0,
                'Career_Catches_Taken': 8,
                'Career_Stumpings': 0,
                'Career_Matches_Batted': 10
            }
        }
    
    def normalize_player_name(self, name: str) -> str:
        """Normalize player name to match historical data"""
        if pd.isna(name):
            return ""
            
        name = str(name).strip()
        
        # Check direct mappings
        for standard_name, variants in self.player_mappings.items():
            if name in variants or name == standard_name:
                return standard_name
                
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^\w\s]', '', name).strip()
        return normalized
        
    def get_player_role(self, name: str) -> str:
        """Determine player role based on name or recent performance"""
        bowlers = ['Siraj', 'Sharma', 'Yadav', 'Joseph', 'Ahmad', 'Dayal']
        all_rounders = ['Maxwell', 'Green', 'Rashid', 'Tewatia', 'Shankar']
        wicket_keepers = ['Karthik', 'Saha', 'Rawat']
        
        name_parts = name.split()
        for part in name_parts:
            if part in bowlers:
                return 'bowler'
            elif part in all_rounders:
                return 'all_rounder'
            elif part in wicket_keepers:
                return 'batsman'  # Treat wicket-keepers as batsmen for now
        return 'batsman'
    
    def process_player_data(self, player_name: str, match_no: int) -> Dict[str, Any]:
        """
        Process and combine data from multiple sources for a player
        
        Args:
            player_name: Name of the player
            match_no: Match number for context
            
        Returns:
            Dictionary containing processed player data
        """
        try:
            # Get data from different sources
            cricbuzz_recent = self._get_cricbuzz_recent_data(player_name)
            cricbuzz_current = self._get_cricbuzz_current_data(player_name)
            historical = self._get_historical_data(player_name)
            
            # If no data found from any source, return None instead of empty dict
            if not any([cricbuzz_recent, cricbuzz_current, historical]):
                self.logger.warning(f"No data found for {player_name} from any source")
                return None
            
            # Extract features for prediction with proper fallbacks
            prediction_data = {
                # Recent form features (40% weight)
                'recent_runs': cricbuzz_recent.get('batting', {}).get('runs') or historical.get('batting', {}).get('runs', 0),
                'recent_strike_rate': cricbuzz_recent.get('batting', {}).get('strike_rate') or historical.get('batting', {}).get('strike_rate', 0),
                'recent_average': cricbuzz_recent.get('batting', {}).get('average') or historical.get('batting', {}).get('average', 0),
                'recent_wickets': cricbuzz_recent.get('bowling', {}).get('wickets') or historical.get('bowling', {}).get('wickets', 0),
                'recent_economy': cricbuzz_recent.get('bowling', {}).get('economy') or historical.get('bowling', {}).get('economy', 0),
                'recent_bowling_avg': cricbuzz_recent.get('bowling', {}).get('average') or historical.get('bowling', {}).get('average', 0),
                
                # Current tournament features (30% weight)
                'current_runs': cricbuzz_current.get('batting', {}).get('runs') or historical.get('batting', {}).get('runs', 0),
                'current_strike_rate': cricbuzz_current.get('batting', {}).get('strike_rate') or historical.get('batting', {}).get('strike_rate', 0),
                'current_average': cricbuzz_current.get('batting', {}).get('average') or historical.get('batting', {}).get('average', 0),
                'current_wickets': cricbuzz_current.get('bowling', {}).get('wickets') or historical.get('bowling', {}).get('wickets', 0),
                'current_economy': cricbuzz_current.get('bowling', {}).get('economy') or historical.get('bowling', {}).get('economy', 0),
                'current_bowling_avg': cricbuzz_current.get('bowling', {}).get('average') or historical.get('bowling', {}).get('average', 0),
                
                # Historical features (20% weight)
                'historical_runs': historical.get('batting', {}).get('runs', 0),
                'historical_strike_rate': historical.get('batting', {}).get('strike_rate', 0),
                'historical_average': historical.get('batting', {}).get('average', 0),
                'historical_wickets': historical.get('bowling', {}).get('wickets', 0),
                'historical_economy': historical.get('bowling', {}).get('economy', 0),
                'historical_bowling_avg': historical.get('bowling', {}).get('average', 0),
                
                # Venue features (10% weight)
                'venue_runs': historical.get('batting', {}).get('venue_runs', 0),
                'venue_strike_rate': historical.get('batting', {}).get('venue_strike_rate', 0),
                'venue_average': historical.get('batting', {}).get('venue_average', 0),
                'venue_wickets': historical.get('bowling', {}).get('venue_wickets', 0),
                'venue_economy': historical.get('bowling', {}).get('venue_economy', 0),
                'venue_bowling_avg': historical.get('bowling', {}).get('venue_bowling_avg', 0),
                
                # Additional features
                'match_importance': 1.0,  # Default for regular matches
                'team_strength': 0.5,     # Default team strength
                'opposition_strength': 0.5  # Default opposition strength
            }
            
            return prediction_data
            
        except Exception as e:
            self.logger.error(f"Error processing data for {player_name}: {str(e)}")
            return None
    
    def _get_cricbuzz_recent_data(self, player_name: str) -> Dict[str, Any]:
        """Get player's recent performance data from Cricbuzz"""
        try:
            # Try to load most recent stats file
            recent_files = sorted(self.scraped_path.glob('player_stats_*.json'))
            if recent_files:
                with open(recent_files[-1], 'r') as f:
                    all_stats = json.load(f)
                return all_stats.get(player_name, {})
            
            # If no data found, return default values
            self.logger.warning(f"No recent data found for {player_name}, using default values")
            return {
                'batting': {
                    'matches': 0,
                    'innings': 0,
                    'runs': 0,
                    'average': 0,
                    'strike_rate': 0,
                    'fifties': 0,
                    'hundreds': 0
                },
                'bowling': {
                    'matches': 0,
                    'innings': 0,
                    'wickets': 0,
                    'average': 0,
                    'economy': 0,
                    'strike_rate': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting recent data: {str(e)}")
            return {}
    
    def _get_cricbuzz_current_data(self, player_name: str) -> Dict[str, Any]:
        """Get player's current tournament data from Cricbuzz"""
        try:
            # Try to load most recent tournament stats file
            current_files = sorted(self.scraped_path.glob('tournament_stats_*.json'))
            if current_files:
                with open(current_files[-1], 'r') as f:
                    tournament_stats = json.load(f)
                return tournament_stats.get(player_name, {})
            
            # If no data found, return default values
            self.logger.warning(f"No current tournament data found for {player_name}, using default values")
            return {
                'batting': {
                    'matches': 0,
                    'innings': 0,
                    'runs': 0,
                    'average': 0,
                    'strike_rate': 0,
                    'fifties': 0,
                    'hundreds': 0
                },
                'bowling': {
                    'matches': 0,
                    'innings': 0,
                    'wickets': 0,
                    'average': 0,
                    'economy': 0,
                    'strike_rate': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current tournament data: {str(e)}")
            return {}
    
    def _get_historical_data(self, player_name: str) -> Dict[str, Any]:
        """Get player's historical performance data"""
        try:
            # Try to load from processed data first
            historical_file = self.base_path / 'data' / 'historical_data.csv'
            if historical_file.exists():
                df = pd.read_csv(historical_file)
                if not df.empty:
                    # Calculate batting stats
                    batting_stats = {
                        'matches': len(df),
                        'innings': len(df[df['runs_scored'] > 0]),
                        'runs': df['runs_scored'].sum(),
                        'average': df['runs_scored'].mean(),
                        'strike_rate': df['recent_strike_rate'].mean(),
                        'fifties': len(df[df['runs_scored'] >= 50]),
                        'hundreds': len(df[df['runs_scored'] >= 100])
                    }
                    
                    # Calculate bowling stats
                    bowling_stats = {
                        'matches': len(df),
                        'innings': len(df[df['wickets_taken'] > 0]),
                        'wickets': df['wickets_taken'].sum(),
                        'average': df['wickets_taken'].mean(),
                        'economy': df['recent_economy'].mean(),
                        'strike_rate': df['recent_strike_rate'].mean()
                    }
                    
                    return {
                        'batting': batting_stats,
                        'bowling': bowling_stats
                    }
            
            # If no data found, return default values
            self.logger.warning(f"No historical data found for {player_name}, using default values")
            return {
                'batting': {
                    'matches': 0,
                    'innings': 0,
                    'runs': 0,
                    'average': 0,
                    'strike_rate': 0,
                    'fifties': 0,
                    'hundreds': 0
                },
                'bowling': {
                    'matches': 0,
                    'innings': 0,
                    'wickets': 0,
                    'average': 0,
                    'economy': 0,
                    'strike_rate': 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {str(e)}")
            return {}
    
    def _combine_data_sources(self, recent: Dict, current: Dict, historical: Dict) -> Dict[str, Any]:
        """Combine data from different sources with appropriate weights"""
        combined = {}
        
        # Process batting statistics
        if any(source.get('batting') for source in [recent, current, historical]):
            combined['batting'] = self._combine_statistics(
                recent.get('batting', {}),
                current.get('batting', {}),
                historical.get('batting', {})
            )
        
        # Process bowling statistics
        if any(source.get('bowling') for source in [recent, current, historical]):
            combined['bowling'] = self._combine_statistics(
                recent.get('bowling', {}),
                current.get('bowling', {}),
                historical.get('bowling', {})
            )
        
        # Process fielding statistics
        if any(source.get('fielding') for source in [recent, current, historical]):
            combined['fielding'] = self._combine_statistics(
                recent.get('fielding', {}),
                current.get('fielding', {}),
                historical.get('fielding', {})
            )
        
        return combined
    
    def _combine_statistics(self, recent: Dict, current: Dict, historical: Dict) -> Dict[str, Any]:
        """Combine statistics with weights"""
        combined = {}
        
        # Get all unique keys
        all_keys = set(recent.keys()) | set(current.keys()) | set(historical.keys())
        
        for key in all_keys:
            # Get values from each source
            recent_val = recent.get(key, 0)
            current_val = current.get(key, 0)
            historical_val = historical.get(key, 0)
            
            # Calculate weighted average
            weighted_value = (
                recent_val * self.weights['cricbuzz_recent'] +
                current_val * self.weights['cricbuzz_current'] +
                historical_val * self.weights['historical']
            )
            
            combined[key] = weighted_value
        
        return combined
    
    def _get_match_context(self, match_no: int) -> Dict[str, Any]:
        """Get match-specific context data"""
        try:
            # Load match schedule
            schedule_file = self.processed_path / 'match_schedule.json'
            if not schedule_file.exists():
                return {}
            
            with open(schedule_file, 'r') as f:
                schedule = json.load(f)
            
            # Find match details
            match = next((m for m in schedule if m['match_no'] == match_no), {})
            
            return {
                'match_context': {
                    'venue': match.get('venue'),
                    'date': match.get('date'),
                    'opposition': match.get('opposition'),
                    'match_type': match.get('match_type'),
                    'stage': match.get('stage')
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting match context: {str(e)}")
            return {}

    def process_match_data(self, match_data: Dict) -> Dict:
        """Process and enrich match data with additional metrics"""
        try:
            processed_data = {
                'match_id': match_data.get('match_id'),
                'date': match_data.get('date'),
                'venue': match_data.get('venue'),
                'team1': match_data.get('team1'),
                'team2': match_data.get('team2'),
                'status': match_data.get('status'),
                'score': match_data.get('score'),
                'match_importance': self._calculate_match_importance(match_data),
                'pressure_index': self._calculate_pressure_index(match_data),
                'venue_factors': self._get_venue_factors(match_data.get('venue')),
                'team_form': self._calculate_team_form(match_data),
                'head_to_head': self._get_head_to_head_stats(match_data),
                'players': self._process_players(match_data.get('players', []))
            }
            return processed_data
        except Exception as e:
            logger.error(f"Error processing match data: {e}")
            return {}

    def _calculate_match_importance(self, match_data: Dict) -> float:
        """Calculate match importance based on tournament stage and context"""
        try:
            importance = 1.0
            status = match_data.get('status', '').lower()
            
            if 'final' in status:
                importance = 4.0
            elif 'semi' in status:
                importance = 3.0
            elif 'playoff' in status:
                importance = 2.0
            
            return importance
        except Exception as e:
            logger.error(f"Error calculating match importance: {e}")
            return 1.0

    def _calculate_pressure_index(self, match_data: Dict) -> float:
        """Calculate pressure index based on match context"""
        try:
            pressure = 1.0
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            # Check if it's a rivalry match
            if team1 in TEAMS and team2 in TEAMS:
                pressure *= 1.3
            
            # Check if it's a must-win situation
            if 'must win' in match_data.get('status', '').lower():
                pressure *= 1.4
            
            return pressure
        except Exception as e:
            logger.error(f"Error calculating pressure index: {e}")
            return 1.0

    def _get_venue_factors(self, venue: str) -> Dict:
        """Get venue-specific factors"""
        try:
            factors = {
                'home_advantage': 1.0,
                'pitch_type': 'unknown',
                'boundary_size': 'medium'
            }
            
            # Check if venue is home ground for any team
            for team, info in TEAMS.items():
                if info['home_ground'] == venue:
                    factors['home_advantage'] = 1.2
                    break
            
            return factors
        except Exception as e:
            logger.error(f"Error getting venue factors: {e}")
            return {'home_advantage': 1.0, 'pitch_type': 'unknown', 'boundary_size': 'medium'}

    def _calculate_team_form(self, match_data: Dict) -> Dict:
        """Calculate team form based on recent matches"""
        try:
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            form = {
                team1: {'wins': 0, 'losses': 0, 'form_score': 0.5},
                team2: {'wins': 0, 'losses': 0, 'form_score': 0.5}
            }
            
            if self.historical_data is not None:
                for team in [team1, team2]:
                    recent_matches = self.historical_data[
                        (self.historical_data['team1'] == team) | 
                        (self.historical_data['team2'] == team)
                    ].tail(5)
                    
                    for _, match in recent_matches.iterrows():
                        if match['winner'] == team:
                            form[team]['wins'] += 1
                        else:
                            form[team]['losses'] += 1
                    
                    total = form[team]['wins'] + form[team]['losses']
                    if total > 0:
                        form[team]['form_score'] = form[team]['wins'] / total
            
            return form
        except Exception as e:
            logger.error(f"Error calculating team form: {e}")
            return {}

    def _get_head_to_head_stats(self, match_data: Dict) -> Dict:
        """Get head-to-head statistics between teams"""
        try:
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            h2h = {
                'total_matches': 0,
                'team1_wins': 0,
                'team2_wins': 0,
                'win_ratio': 0.5
            }
            
            if self.historical_data is not None:
                h2h_matches = self.historical_data[
                    ((self.historical_data['team1'] == team1) & (self.historical_data['team2'] == team2)) |
                    ((self.historical_data['team1'] == team2) & (self.historical_data['team2'] == team1))
                ]
                
                h2h['total_matches'] = len(h2h_matches)
                h2h['team1_wins'] = len(h2h_matches[h2h_matches['winner'] == team1])
                h2h['team2_wins'] = len(h2h_matches[h2h_matches['winner'] == team2])
                
                if h2h['total_matches'] > 0:
                    h2h['win_ratio'] = h2h['team1_wins'] / h2h['total_matches']
            
            return h2h
        except Exception as e:
            logger.error(f"Error getting head-to-head stats: {e}")
            return {}

    def _process_players(self, players: List[Dict]) -> List[Dict]:
        """Process and enrich player data"""
        try:
            processed_players = []
            for player in players:
                player_id = player.get('id')
                if player_id in self.player_stats:
                    stats = self.player_stats[player_id]
                    processed_player = {
                        'id': player_id,
                        'name': player.get('name'),
                        'role': player.get('role'),
                        'form': self._calculate_player_form(stats),
                        'role_metrics': self._calculate_role_metrics(stats, player.get('role')),
                        'batting_metrics': self._calculate_batting_metrics(stats),
                        'bowling_metrics': self._calculate_bowling_metrics(stats),
                        'consistency_score': self._calculate_consistency_score(stats),
                        'pressure_metrics': self._calculate_pressure_metrics(stats)
                    }
                    processed_players.append(processed_player)
            return processed_players
        except Exception as e:
            logger.error(f"Error processing players: {e}")
            return []

    def _calculate_player_form(self, stats: Dict) -> Dict:
        """Calculate player form based on recent performances"""
        try:
            form = {
                'runs': 0,
                'wickets': 0,
                'strike_rate': 0,
                'economy_rate': 0,
                'form_score': 0.5
            }
            
            if 'recent_matches' in stats:
                recent = stats['recent_matches'][:5]  # Last 5 matches
                total_runs = sum(match.get('runs', 0) for match in recent)
                total_wickets = sum(match.get('wickets', 0) for match in recent)
                
                form['runs'] = total_runs / len(recent) if recent else 0
                form['wickets'] = total_wickets / len(recent) if recent else 0
                form['strike_rate'] = stats.get('batting', {}).get('strike_rate', 0)
                form['economy_rate'] = stats.get('bowling', {}).get('economy_rate', 0)
                
                # Calculate form score based on performance consistency
                form['form_score'] = self._calculate_form_score(recent)
            
            return form
        except Exception as e:
            logger.error(f"Error calculating player form: {e}")
            return {}

    def _calculate_role_metrics(self, stats: Dict, role: str) -> Dict:
        """Calculate role-specific metrics"""
        try:
            metrics = {
                'role_importance': 1.0,
                'role_performance': 0.5
            }
            
            if role == 'Batsman':
                metrics['role_importance'] = 1.2
                metrics['role_performance'] = stats.get('batting', {}).get('average', 0) / 50
            elif role == 'Bowler':
                metrics['role_importance'] = 1.1
                metrics['role_performance'] = stats.get('bowling', {}).get('average', 0) / 30
            elif role == 'All-Rounder':
                metrics['role_importance'] = 1.3
                batting_perf = stats.get('batting', {}).get('average', 0) / 50
                bowling_perf = stats.get('bowling', {}).get('average', 0) / 30
                metrics['role_performance'] = (batting_perf + bowling_perf) / 2
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating role metrics: {e}")
            return {}

    def _calculate_batting_metrics(self, stats: Dict) -> Dict:
        """Calculate batting-specific metrics"""
        try:
            batting = stats.get('batting', {})
            return {
                'average': batting.get('average', 0),
                'strike_rate': batting.get('strike_rate', 0),
                'boundary_rate': batting.get('boundary_rate', 0),
                'consistency': batting.get('consistency', 0.5)
            }
        except Exception as e:
            logger.error(f"Error calculating batting metrics: {e}")
            return {}

    def _calculate_bowling_metrics(self, stats: Dict) -> Dict:
        """Calculate bowling-specific metrics"""
        try:
            bowling = stats.get('bowling', {})
            return {
                'average': bowling.get('average', 0),
                'economy_rate': bowling.get('economy_rate', 0),
                'wicket_rate': bowling.get('wicket_rate', 0),
                'consistency': bowling.get('consistency', 0.5)
            }
        except Exception as e:
            logger.error(f"Error calculating bowling metrics: {e}")
            return {}

    def _calculate_consistency_score(self, stats: Dict) -> float:
        """Calculate overall consistency score"""
        try:
            batting_consistency = stats.get('batting', {}).get('consistency', 0.5)
            bowling_consistency = stats.get('bowling', {}).get('consistency', 0.5)
            return (batting_consistency + bowling_consistency) / 2
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.5

    def _calculate_pressure_metrics(self, player_data: Dict) -> Dict:
        """Calculate player's performance under pressure"""
        try:
            # Load match data
            match_data = pd.read_csv(self.data_path / 'processed' / 'match_data.csv')
            
            # Get player's matches
            player_matches = match_data[
                (match_data['player_name'] == player_data['name']) |
                (match_data['opponent'] == player_data['name'])
            ]
            
            # Calculate pressure metrics
            close_matches = player_matches[abs(player_matches['margin'] <= 20)]  # Matches won/lost by 20 runs or less
            chase_performance = player_matches[player_matches['is_chase'] == True]
            knockout_matches = player_matches[player_matches['is_knockout'] == True]
            
            metrics = {
                'pressure_batting_avg': close_matches['batting_average'].mean() if not close_matches.empty else 0.0,
                'pressure_strike_rate': close_matches['strike_rate'].mean() if not close_matches.empty else 0.0,
                'chase_batting_avg': chase_performance['batting_average'].mean() if not chase_performance.empty else 0.0,
                'chase_strike_rate': chase_performance['strike_rate'].mean() if not chase_performance.empty else 0.0,
                'knockout_batting_avg': knockout_matches['batting_average'].mean() if not knockout_matches.empty else 0.0,
                'knockout_strike_rate': knockout_matches['strike_rate'].mean() if not knockout_matches.empty else 0.0,
                'pressure_bowling_avg': close_matches['bowling_average'].mean() if not close_matches.empty else 0.0,
                'pressure_economy': close_matches['economy'].mean() if not close_matches.empty else 0.0,
                'knockout_bowling_avg': knockout_matches['bowling_average'].mean() if not knockout_matches.empty else 0.0,
                'knockout_economy': knockout_matches['economy'].mean() if not knockout_matches.empty else 0.0
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating pressure metrics: {str(e)}")
            return {}

    def get_head_to_head_stats(self, player1: str, player2: str) -> Dict:
        """Get head-to-head statistics between two players"""
        try:
            # Load match data
            match_data = pd.read_csv(self.data_path / 'processed' / 'match_data.csv')
            
            # Get matches where both players played
            h2h_matches = match_data[
                ((match_data['player_name'] == player1) & (match_data['opponent'] == player2)) |
                ((match_data['player_name'] == player2) & (match_data['opponent'] == player1))
            ]
            
            if h2h_matches.empty:
                return {}
                
            # Calculate head-to-head stats
            player1_stats = h2h_matches[h2h_matches['player_name'] == player1]
            player2_stats = h2h_matches[h2h_matches['player_name'] == player2]
            
            h2h_stats = {
                player1: {
                    'matches': len(player1_stats),
                    'batting_avg': player1_stats['batting_average'].mean(),
                    'strike_rate': player1_stats['strike_rate'].mean(),
                    'bowling_avg': player1_stats['bowling_average'].mean(),
                    'economy': player1_stats['economy'].mean(),
                    'win_rate': (player1_stats['result'] == 'won').mean()
                },
                player2: {
                    'matches': len(player2_stats),
                    'batting_avg': player2_stats['batting_average'].mean(),
                    'strike_rate': player2_stats['strike_rate'].mean(),
                    'bowling_avg': player2_stats['bowling_average'].mean(),
                    'economy': player2_stats['economy'].mean(),
                    'win_rate': (player2_stats['result'] == 'won').mean()
                }
            }
            
            return h2h_stats
            
        except Exception as e:
            self.logger.error(f"Error getting head-to-head stats: {str(e)}")
            return {}

    def validate_data(self, data: Dict) -> bool:
        """Validate data against defined rules"""
        try:
            # Validate player statistics
            for player in data.get('players', []):
                stats = player.get('recent_stats', {})
                
                # Check runs
                runs = stats.get('batting', {}).get('runs', 0)
                if not (VALIDATION_RULES['min_runs'] <= runs <= VALIDATION_RULES['max_runs']):
                    logger.warning(f"Invalid runs value: {runs}")
                    return False
                
                # Check wickets
                wickets = stats.get('bowling', {}).get('wickets', 0)
                if not (VALIDATION_RULES['min_wickets'] <= wickets <= VALIDATION_RULES['max_wickets']):
                    logger.warning(f"Invalid wickets value: {wickets}")
                    return False
                
                # Check strike rate
                strike_rate = stats.get('batting', {}).get('strike_rate', 0)
                if not (VALIDATION_RULES['min_strike_rate'] <= strike_rate <= VALIDATION_RULES['max_strike_rate']):
                    logger.warning(f"Invalid strike rate: {strike_rate}")
                    return False
                
                # Check economy rate
                economy_rate = stats.get('bowling', {}).get('economy_rate', 0)
                if not (VALIDATION_RULES['min_economy_rate'] <= economy_rate <= VALIDATION_RULES['max_economy_rate']):
                    logger.warning(f"Invalid economy rate: {economy_rate}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return False

    def save_processed_data(self, data: Dict, match_id: str):
        """Save processed data to file"""
        try:
            output_file = self.data_dir / f"processed_match_{match_id}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved processed data for match {match_id}")
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")

    def get_player_historical_stats(self, player_name: str) -> Dict:
        """Get historical statistics for a player from processed data"""
        try:
            # Load processed data
            data_path = self.processed_path / 'combined_data.csv'
            if not data_path.exists():
                logger.error(f"Processed data file not found at {data_path}")
                return self._get_default_stats(player_name)
                
            data = pd.read_csv(data_path)
            
            # Try to find player with normalized name
            normalized_name = self.normalize_player_name(player_name)
            player_data = data[data['Player_Name'].apply(self.normalize_player_name) == normalized_name]
            
            if player_data.empty:
                logger.warning(f"No historical data found for player {player_name}, using defaults")
                return self._get_default_stats(player_name)
                
            # Get the most recent record
            latest_data = player_data.iloc[-1]
            
            # Format historical stats with proper type conversion
            historical_stats = {}
            for col in latest_data.index:
                try:
                    value = float(latest_data[col]) if pd.notnull(latest_data[col]) else 0.0
                    historical_stats[col] = value
                except (ValueError, TypeError):
                    historical_stats[col] = 0.0
            
            return historical_stats
            
        except Exception as e:
            logger.error(f"Error getting historical stats for {player_name}: {str(e)}")
            return self._get_default_stats(player_name)
            
    def _get_default_stats(self, player_name: str) -> Dict:
        """Get default statistics based on player role"""
        role = self.get_player_role(player_name)
        return self.default_stats[role].copy()

    def process_raw_data(self):
        """Process raw cricket data to create combined dataset with player statistics."""
        try:
            logging.info("Starting raw data processing...")
            
            # Load matches and deliveries data
            matches_df = pd.read_csv('data/historical/matches.csv')
            deliveries_df = pd.read_csv('data/historical/deliveries.csv')
            
            # Process deliveries data to get player statistics
            player_stats = {}
            
            # Calculate batting statistics
            batting_stats = deliveries_df.groupby('batter').agg({
                'batsman_runs': ['sum', 'count'],
                'ball': 'count'
            }).reset_index()
            
            batting_stats.columns = ['Player_Name', 'Runs_Scored', 'Balls_Faced', 'Innings_Batted']
            batting_stats['Batting_Average'] = batting_stats['Runs_Scored'] / batting_stats['Innings_Batted']
            batting_stats['Batting_Strike_Rate'] = (batting_stats['Runs_Scored'] / batting_stats['Balls_Faced']) * 100
            
            # Calculate bowling statistics
            bowling_stats = deliveries_df.groupby('bowler').agg({
                'ball': 'count',
                'total_runs': 'sum',
                'is_wicket': 'sum'
            }).reset_index()
            
            bowling_stats.columns = ['Player_Name', 'Balls_Bowled', 'Runs_Conceded', 'Wickets']
            bowling_stats['Bowling_Average'] = bowling_stats['Runs_Conceded'] / bowling_stats['Wickets'].replace(0, 1)
            bowling_stats['Economy_Rate'] = (bowling_stats['Runs_Conceded'] / (bowling_stats['Balls_Bowled'] / 6))
            
            # Merge batting and bowling statistics
            combined_stats = pd.merge(batting_stats, bowling_stats, on='Player_Name', how='outer').fillna(0)
            
            # Calculate recent form for each player
            for player in combined_stats['Player_Name']:
                # Recent batting form
                recent_matches = deliveries_df[deliveries_df['batter'] == player].sort_values('match_id').tail(3)
                recent_runs = recent_matches['batsman_runs'].sum()
                recent_balls = len(recent_matches)
                
                # Recent bowling form
                recent_bowling = deliveries_df[deliveries_df['bowler'] == player].sort_values('match_id').tail(3)
                recent_wickets = recent_bowling['is_wicket'].sum()
                recent_economy = recent_bowling['total_runs'].sum() / (len(recent_bowling) / 6) if len(recent_bowling) > 0 else 0
                
                # Add recent form to player stats
                combined_stats.loc[combined_stats['Player_Name'] == player, 'Recent_Form_Runs'] = recent_runs
                combined_stats.loc[combined_stats['Player_Name'] == player, 'Recent_Form_SR'] = (recent_runs / recent_balls * 100) if recent_balls > 0 else 0
                combined_stats.loc[combined_stats['Player_Name'] == player, 'Recent_Form_Wickets'] = recent_wickets
                combined_stats.loc[combined_stats['Player_Name'] == player, 'Recent_Form_Economy'] = recent_economy
            
            # Save processed data
            combined_stats.to_csv('data/processed/combined_data.csv', index=False)
            logging.info(f"Successfully processed {len(combined_stats)} players' data")
            
        except Exception as e:
            logging.error(f"Error processing raw data: {str(e)}")
            raise e

    def get_player_form(self, player_name: str) -> Dict:
        """Get player's recent form data"""
        try:
            # Check if form data exists
            if not self.form_data_path.exists():
                self.logger.warning("Form data file not found")
                return self._get_default_form()
                
            # Read form data
            form_data = pd.read_csv(self.form_data_path)
            
            # Filter data for the player
            player_form = form_data[form_data['player_name'] == player_name]
            
            if len(player_form) == 0:
                self.logger.warning(f"No form data found for player: {player_name}")
                return self._get_default_form()
                
            # Get the most recent form data
            latest_form = player_form.iloc[-1]
            
            return {
                'batting_average': float(latest_form['batting_average']),
                'strike_rate': float(latest_form['strike_rate']),
                'runs': int(latest_form['runs']),
                'wickets': int(latest_form['wickets']),
                'economy': float(latest_form['economy']),
                'bowling_average': float(latest_form['bowling_average']),
                'catches': int(latest_form['catches']),
                'stumpings': int(latest_form['stumpings']),
                'matches': int(latest_form['matches']),
                'last_updated': str(latest_form['last_updated'])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting form data for {player_name}: {str(e)}")
            return self._get_default_form()
            
    def _get_default_form(self) -> Dict:
        """Return default form data"""
        return {
            'batting_average': 0.0,
            'strike_rate': 0.0,
            'runs': 0,
            'wickets': 0,
            'economy': 0.0,
            'bowling_average': 0.0,
            'catches': 0,
            'stumpings': 0,
            'matches': 0,
            'last_updated': None
        }
        
    def update_player_form(self, match_data: Dict) -> bool:
        """Update player form data with new match performance"""
        try:
            # Read existing form data or create new DataFrame
            if self.form_data_path.exists():
                form_data = pd.read_csv(self.form_data_path)
            else:
                form_data = pd.DataFrame(columns=[
                    'player_name', 'batting_average', 'strike_rate', 'runs',
                    'wickets', 'economy', 'bowling_average', 'catches',
                    'stumpings', 'matches', 'last_updated'
                ])
                
            # Update form for each player
            for player in match_data.get('players', []):
                player_name = player['name']
                
                # Calculate new stats
                batting = player['batting']
                bowling = player['bowling']
                
                new_stats = {
                    'player_name': player_name,
                    'batting_average': batting['runs'],
                    'strike_rate': (batting['runs'] / batting['balls'] * 100) if batting['balls'] > 0 else 0,
                    'runs': batting['runs'],
                    'wickets': bowling['wickets'],
                    'economy': (bowling['runs_conceded'] / bowling['overs']) if bowling['overs'] > 0 else 0,
                    'bowling_average': (bowling['runs_conceded'] / bowling['wickets']) if bowling['wickets'] > 0 else 0,
                    'catches': 0,  # Need to add fielding stats
                    'stumpings': 0,
                    'matches': 1,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Update or append player stats
                if player_name in form_data['player_name'].values:
                    # Update existing player stats
                    mask = form_data['player_name'] == player_name
                    old_stats = form_data[mask].iloc[0]
                    
                    # Calculate moving averages
                    matches = old_stats['matches'] + 1
                    form_data.loc[mask, 'batting_average'] = (
                        (old_stats['batting_average'] * old_stats['matches'] + new_stats['batting_average'])
                        / matches
                    )
                    form_data.loc[mask, 'strike_rate'] = (
                        (old_stats['strike_rate'] * old_stats['matches'] + new_stats['strike_rate'])
                        / matches
                    )
                    form_data.loc[mask, 'runs'] += new_stats['runs']
                    form_data.loc[mask, 'wickets'] += new_stats['wickets']
                    form_data.loc[mask, 'economy'] = (
                        (old_stats['economy'] * old_stats['matches'] + new_stats['economy'])
                        / matches
                    )
                    form_data.loc[mask, 'bowling_average'] = (
                        (old_stats['bowling_average'] * old_stats['matches'] + new_stats['bowling_average'])
                        / matches
                    )
                    form_data.loc[mask, 'matches'] = matches
                    form_data.loc[mask, 'last_updated'] = new_stats['last_updated']
                else:
                    # Add new player stats
                    form_data = form_data.append(new_stats, ignore_index=True)
                    
            # Save updated form data
            form_data.to_csv(self.form_data_path, index=False)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating player form: {str(e)}")
            return False

    def get_venue_performance(self, player_name: str, venue: str) -> Dict:
        """Get player's performance at specific venues"""
        try:
            # Load match data
            match_data = pd.read_csv(self.data_path / 'processed' / 'match_data.csv')
            
            # Get player's matches at the venue
            venue_matches = match_data[
                (match_data['player_name'] == player_name) &
                (match_data['venue'] == venue)
            ]
            
            if venue_matches.empty:
                return {}
                
            # Calculate venue-specific stats
            venue_stats = {
                'matches': len(venue_matches),
                'batting_avg': venue_matches['batting_average'].mean(),
                'strike_rate': venue_matches['strike_rate'].mean(),
                'highest_score': venue_matches['runs'].max(),
                'fifties': len(venue_matches[venue_matches['runs'] >= 50]),
                'hundreds': len(venue_matches[venue_matches['runs'] >= 100]),
                'bowling_avg': venue_matches['bowling_average'].mean(),
                'economy': venue_matches['economy'].mean(),
                'best_bowling': venue_matches['wickets'].max(),
                'win_rate': (venue_matches['result'] == 'won').mean(),
                'avg_win_margin': venue_matches[venue_matches['result'] == 'won']['margin'].mean(),
                'avg_loss_margin': venue_matches[venue_matches['result'] == 'lost']['margin'].mean()
            }
            
            return venue_stats
            
        except Exception as e:
            self.logger.error(f"Error getting venue performance: {str(e)}")
            return {}
            
    def get_venue_conditions(self, venue: str) -> Dict:
        """Get venue-specific conditions and characteristics"""
        try:
            # Load venue data
            venue_data = pd.read_csv(self.data_path / 'processed' / 'venue_data.csv')
            
            # Get venue characteristics
            venue_info = venue_data[venue_data['venue'] == venue].iloc[0]
            
            conditions = {
                'avg_first_innings_score': venue_info['avg_first_innings_score'],
                'avg_second_innings_score': venue_info['avg_second_innings_score'],
                'win_rate_batting_first': venue_info['win_rate_batting_first'],
                'win_rate_chasing': venue_info['win_rate_chasing'],
                'avg_runs_per_over': venue_info['avg_runs_per_over'],
                'avg_wickets_per_match': venue_info['avg_wickets_per_match'],
                'pitch_type': venue_info['pitch_type'],
                'ground_size': venue_info['ground_size'],
                'boundary_length': venue_info['boundary_length'],
                'is_spinner_friendly': venue_info['is_spinner_friendly'],
                'is_pacer_friendly': venue_info['is_pacer_friendly']
            }
            
            return conditions
            
        except Exception as e:
            self.logger.error(f"Error getting venue conditions: {str(e)}")
            return {}

if __name__ == "__main__":
    processor = DataProcessor()
    # Example usage
    test_match = {
        'match_id': 'test123',
        'date': '2024-04-02',
        'venue': 'Wankhede Stadium',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'status': 'Final',
        'score': '180/5',
        'players': []
    }
    processed_data = processor.process_match_data(test_match)
    processor.save_processed_data(processed_data, 'test123') 