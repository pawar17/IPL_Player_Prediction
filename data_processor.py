import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path
import json
from config import (
    DATA_DIR, HISTORICAL_DATA_FILE, PLAYER_STATS_FILE,
    VALIDATION_RULES, TEAMS, PLAYER_ROLES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.historical_data = None
        self.player_stats = None
        self.load_data()

    def load_data(self):
        """Load historical data and player statistics"""
        try:
            if HISTORICAL_DATA_FILE.exists():
                self.historical_data = pd.read_csv(HISTORICAL_DATA_FILE)
                logger.info(f"Loaded {len(self.historical_data)} historical matches")
            else:
                self.historical_data = pd.DataFrame()
                logger.warning("No historical data found")

            if PLAYER_STATS_FILE.exists():
                self.player_stats = pd.read_csv(PLAYER_STATS_FILE)
                logger.info(f"Loaded player statistics for {len(self.player_stats)} players")
            else:
                self.player_stats = pd.DataFrame()
                logger.warning("No player statistics found")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.historical_data = pd.DataFrame()
            self.player_stats = pd.DataFrame()

    def process_match_data(self, match_data: Dict) -> Dict:
        """Process and enrich match data with additional metrics"""
        try:
            processed_match = match_data.copy()
            
            # Add match importance
            processed_match['match_importance'] = self._calculate_match_importance(match_data)
            
            # Add pressure index
            processed_match['pressure_index'] = self._calculate_pressure_index(match_data)
            
            # Add venue factors
            processed_match['venue_factors'] = self._get_venue_factors(match_data)
            
            # Add team form
            processed_match['team1_form'] = self._calculate_team_form(match_data['team1'])
            processed_match['team2_form'] = self._calculate_team_form(match_data['team2'])
            
            # Add head-to-head statistics
            processed_match['head_to_head'] = self._get_head_to_head_stats(
                match_data['team1'], match_data['team2']
            )
            
            return processed_match
        except Exception as e:
            logger.error(f"Error processing match data: {e}")
            return match_data

    def process_player_data(self, player_data: Dict) -> Dict:
        """Process and enrich player data with additional metrics"""
        try:
            processed_player = player_data.copy()
            
            # Calculate form metrics
            processed_player['form_metrics'] = self._calculate_player_form(player_data)
            
            # Add role-specific metrics
            processed_player['role_metrics'] = self._calculate_role_metrics(player_data)
            
            # Add performance consistency
            processed_player['consistency_score'] = self._calculate_consistency_score(player_data)
            
            # Add pressure handling metrics
            processed_player['pressure_metrics'] = self._calculate_pressure_metrics(player_data)
            
            return processed_player
        except Exception as e:
            logger.error(f"Error processing player data: {e}")
            return player_data

    def _calculate_match_importance(self, match_data: Dict) -> float:
        """Calculate match importance based on various factors"""
        importance = 0.5  # Base importance
        
        # Adjust based on match stage
        if match_data.get('stage') in ['playoff', 'semi_final', 'final']:
            importance += 0.3
        
        # Adjust based on team positions
        if match_data.get('team1_position') and match_data.get('team2_position'):
            position_diff = abs(match_data['team1_position'] - match_data['team2_position'])
            if position_diff <= 2:
                importance += 0.2
        
        return min(importance, 1.0)

    def _calculate_pressure_index(self, match_data: Dict) -> float:
        """Calculate pressure index based on various factors"""
        pressure = 0.5  # Base pressure
        
        # Adjust based on match stage
        if match_data.get('stage') == 'final':
            pressure += 0.3
        elif match_data.get('stage') == 'semi_final':
            pressure += 0.2
        elif match_data.get('stage') == 'playoff':
            pressure += 0.1
        
        # Adjust based on team positions
        if match_data.get('team1_position') and match_data.get('team2_position'):
            position_diff = abs(match_data['team1_position'] - match_data['team2_position'])
            if position_diff <= 2:
                pressure += 0.2
        
        return min(pressure, 1.0)

    def _get_venue_factors(self, match_data: Dict) -> Dict:
        """Get venue-specific factors"""
        venue = match_data.get('venue', '')
        factors = {
            'home_advantage': 1.0,
            'pitch_type': 'unknown',
            'weather_conditions': 'unknown',
            'historical_scoring_rate': 0.0
        }
        
        # Check if venue is home ground for either team
        for team_name, team_info in TEAMS.items():
            if venue == team_info['home_ground']:
                if match_data.get('team1') == team_name:
                    factors['home_advantage'] = 1.2
                elif match_data.get('team2') == team_name:
                    factors['home_advantage'] = 0.8
        
        return factors

    def _calculate_team_form(self, team_name: str) -> Dict:
        """Calculate team form based on recent matches"""
        if self.historical_data.empty:
            return {'recent_wins': 0, 'win_rate': 0.5, 'momentum': 0.5}
        
        # Get recent matches for the team
        recent_matches = self.historical_data[
            (self.historical_data['team1'] == team_name) |
            (self.historical_data['team2'] == team_name)
        ].tail(5)
        
        if recent_matches.empty:
            return {'recent_wins': 0, 'win_rate': 0.5, 'momentum': 0.5}
        
        # Calculate form metrics
        wins = sum(
            (recent_matches['team1'] == team_name) & (recent_matches['winner'] == team_name) |
            (recent_matches['team2'] == team_name) & (recent_matches['winner'] == team_name)
        )
        
        win_rate = wins / len(recent_matches)
        momentum = (wins / len(recent_matches)) * 0.8 + 0.2  # Add some base momentum
        
        return {
            'recent_wins': wins,
            'win_rate': win_rate,
            'momentum': momentum
        }

    def _get_head_to_head_stats(self, team1: str, team2: str) -> Dict:
        """Get head-to-head statistics between two teams"""
        if self.historical_data.empty:
            return {'total_matches': 0, 'team1_wins': 0, 'team2_wins': 0, 'win_rate': 0.5}
        
        # Get head-to-head matches
        h2h_matches = self.historical_data[
            ((self.historical_data['team1'] == team1) & (self.historical_data['team2'] == team2)) |
            ((self.historical_data['team1'] == team2) & (self.historical_data['team2'] == team1))
        ]
        
        if h2h_matches.empty:
            return {'total_matches': 0, 'team1_wins': 0, 'team2_wins': 0, 'win_rate': 0.5}
        
        # Calculate head-to-head statistics
        team1_wins = sum(h2h_matches['winner'] == team1)
        team2_wins = sum(h2h_matches['winner'] == team2)
        total_matches = len(h2h_matches)
        
        return {
            'total_matches': total_matches,
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'win_rate': team1_wins / total_matches if total_matches > 0 else 0.5
        }

    def _calculate_player_form(self, player_data: Dict) -> Dict:
        """Calculate player form based on recent performances"""
        if self.player_stats.empty:
            return {'recent_performance': 0.5, 'consistency': 0.5, 'momentum': 0.5}
        
        # Get recent performances for the player
        player_id = player_data.get('id')
        recent_stats = self.player_stats[
            self.player_stats['player_id'] == player_id
        ].tail(5)
        
        if recent_stats.empty:
            return {'recent_performance': 0.5, 'consistency': 0.5, 'momentum': 0.5}
        
        # Calculate form metrics
        recent_performance = recent_stats['performance_score'].mean()
        consistency = 1 - recent_stats['performance_score'].std()
        momentum = recent_stats['performance_score'].pct_change().mean() + 0.5
        
        return {
            'recent_performance': recent_performance,
            'consistency': consistency,
            'momentum': momentum
        }

    def _calculate_role_metrics(self, player_data: Dict) -> Dict:
        """Calculate role-specific metrics for the player"""
        role = player_data.get('role', '')
        metrics = {
            'role_specific_score': 0.5,
            'role_consistency': 0.5,
            'role_impact': 0.5
        }
        
        if role not in PLAYER_ROLES:
            return metrics
        
        # Calculate role-specific metrics based on player's role
        if role == 'Batsman':
            metrics['role_specific_score'] = self._calculate_batting_metrics(player_data)
        elif role == 'Bowler':
            metrics['role_specific_score'] = self._calculate_bowling_metrics(player_data)
        elif role == 'All-Rounder':
            metrics['role_specific_score'] = (
                self._calculate_batting_metrics(player_data) * 0.5 +
                self._calculate_bowling_metrics(player_data) * 0.5
            )
        
        return metrics

    def _calculate_batting_metrics(self, player_data: Dict) -> float:
        """Calculate batting-specific metrics"""
        if not player_data.get('recent_stats'):
            return 0.5
        
        stats = player_data['recent_stats']
        runs = stats.get('runs', 0)
        strike_rate = stats.get('strike_rate', 100)
        
        # Normalize metrics
        runs_score = min(runs / 100, 1.0)  # Cap at 100 runs
        strike_rate_score = min(strike_rate / 200, 1.0)  # Cap at 200 strike rate
        
        return (runs_score * 0.7 + strike_rate_score * 0.3)

    def _calculate_bowling_metrics(self, player_data: Dict) -> float:
        """Calculate bowling-specific metrics"""
        if not player_data.get('recent_stats'):
            return 0.5
        
        stats = player_data['recent_stats']
        wickets = stats.get('wickets', 0)
        economy_rate = stats.get('economy_rate', 10)
        
        # Normalize metrics
        wickets_score = min(wickets / 5, 1.0)  # Cap at 5 wickets
        economy_score = max(1 - (economy_rate / 20), 0)  # Lower is better
        
        return (wickets_score * 0.7 + economy_score * 0.3)

    def _calculate_consistency_score(self, player_data: Dict) -> float:
        """Calculate player's consistency score"""
        if not player_data.get('recent_stats'):
            return 0.5
        
        stats = player_data['recent_stats']
        performances = []
        
        # Combine relevant statistics based on player role
        role = player_data.get('role', '')
        if role == 'Batsman':
            performances = [stats.get('runs', 0) / 100]  # Normalize runs
        elif role == 'Bowler':
            performances = [stats.get('wickets', 0) / 5]  # Normalize wickets
        elif role == 'All-Rounder':
            performances = [
                stats.get('runs', 0) / 100,
                stats.get('wickets', 0) / 5
            ]
        
        if not performances:
            return 0.5
        
        # Calculate consistency (inverse of standard deviation)
        consistency = 1 - np.std(performances)
        return max(min(consistency, 1.0), 0.0)

    def _calculate_pressure_metrics(self, player_data: Dict) -> Dict:
        """Calculate player's performance under pressure"""
        if not player_data.get('recent_stats'):
            return {'pressure_handling': 0.5, 'clutch_performance': 0.5}
        
        stats = player_data['recent_stats']
        
        # Calculate pressure handling score
        pressure_handling = 0.5  # Base score
        
        # Adjust based on performance in important matches
        if stats.get('important_match_performance', 0) > 0:
            pressure_handling += 0.2
        
        # Adjust based on performance in close matches
        if stats.get('close_match_performance', 0) > 0:
            pressure_handling += 0.2
        
        # Calculate clutch performance score
        clutch_performance = 0.5  # Base score
        
        # Adjust based on performance in final overs
        if stats.get('final_overs_performance', 0) > 0:
            clutch_performance += 0.2
        
        # Adjust based on performance in must-win matches
        if stats.get('must_win_performance', 0) > 0:
            clutch_performance += 0.2
        
        return {
            'pressure_handling': min(pressure_handling, 1.0),
            'clutch_performance': min(clutch_performance, 1.0)
        }

    def save_processed_data(self, match_data: Dict, player_data: Dict):
        """Save processed data to files"""
        try:
            # Save match data
            match_file = DATA_DIR / f"processed_match_{match_data['match_id']}.json"
            with open(match_file, 'w') as f:
                json.dump(match_data, f, indent=4)
            
            # Save player data
            player_file = DATA_DIR / f"processed_player_{player_data['id']}.json"
            with open(player_file, 'w') as f:
                json.dump(player_data, f, indent=4)
            
            logger.info("Saved processed data successfully")
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")

    def update_historical_data(self, new_match_data: Dict):
        """Update historical data with new match information"""
        try:
            # Convert new match data to DataFrame
            new_match_df = pd.DataFrame([new_match_data])
            
            # Append to historical data
            self.historical_data = pd.concat([self.historical_data, new_match_df])
            
            # Remove duplicates
            self.historical_data = self.historical_data.drop_duplicates(subset=['match_id'])
            
            # Save updated historical data
            self.historical_data.to_csv(HISTORICAL_DATA_FILE, index=False)
            
            logger.info(f"Updated historical data with new match {new_match_data['match_id']}")
        except Exception as e:
            logger.error(f"Error updating historical data: {e}")

    def update_player_stats(self, new_player_data: Dict):
        """Update player statistics with new performance data"""
        try:
            # Convert new player data to DataFrame
            new_player_df = pd.DataFrame([new_player_data])
            
            # Update or append to player stats
            if not self.player_stats.empty:
                self.player_stats = self.player_stats[
                    self.player_stats['player_id'] != new_player_data['id']
                ]
            
            self.player_stats = pd.concat([self.player_stats, new_player_df])
            
            # Save updated player stats
            self.player_stats.to_csv(PLAYER_STATS_FILE, index=False)
            
            logger.info(f"Updated player statistics for player {new_player_data['id']}")
        except Exception as e:
            logger.error(f"Error updating player statistics: {e}") 