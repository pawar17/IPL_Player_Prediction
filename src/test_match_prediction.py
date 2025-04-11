import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from data.ipl_2025_data import IPL_2025_MATCHES, get_match_by_id
from data.team_rosters import (
    get_team_roster,
    get_team_batsmen,
    get_team_bowlers,
    get_team_all_rounders,
    get_player_role
)
from data_collection.cricbuzz_collector import CricbuzzCollector
from data_collection.historical_data import HistoricalDataCollector
from data_collection.ipl_dataset_collector import IPLDatasetCollector
from data_collection.data_processor import DataProcessor
from data_collection.web_scraper import CricketWebScraper
import random

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchPredictor:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.models_path = self.base_path / 'models'
        self.data_path = self.base_path / 'data'
        
        # Load trained models
        self.batting_model = joblib.load(self.models_path / 'batting_model.joblib')
        self.bowling_model = joblib.load(self.models_path / 'bowling_model.joblib')
        self.fielding_model = joblib.load(self.models_path / 'fielding_model.joblib')
        
        # Load player data
        self.player_data = pd.read_csv(self.data_path / 'processed' / 'combined_data.csv')
        
        # Load matches data
        self.matches_data = pd.read_csv(self.data_path / 'historical' / 'matches.csv')
        self.deliveries_data = pd.read_csv(self.data_path / 'historical' / 'deliveries.csv')
        
        # Define 2025 season matches
        self.matches_2025 = IPL_2025_MATCHES
        
        # Initialize data collectors
        self.cricbuzz = CricbuzzCollector()
        self.historical = HistoricalDataCollector()
        self.dataset_path = "IPL-DATASET-main/IPL-DATASET-main/csv"
        self.ipl_dataset = IPLDatasetCollector(dataset_path=self.dataset_path)
        self.web_scraper = CricketWebScraper()
        
        # Download IPL dataset if not already present
        if not (self.data_path / 'ipl_dataset').exists():
            self.ipl_dataset.download_dataset()
        
        # Load latest player form data
        self.player_form_data = self._load_latest_player_form()
        
        # Cache for player stats
        self._player_stats_cache = {}
        self._cache_duration = 3600  # 1 hour cache
        
        self.logger = logging.getLogger(__name__)
        self.data_processor = DataProcessor()
        
        # Initialize cache
        self._cache = {}
        self._cache_duration = 3600  # 1 hour
        
        # Define role-based baseline stats
        self._role_baselines = {
            'batsman': {
                'batting': {
                    'average': 25.0,
                    'strike_rate': 130.0,
                    'runs': 30.0
                },
                'bowling': {
                    'wickets': 0.0,
                    'economy': 12.0,
                    'average': 0.0
                },
                'fielding': {
                    'catches': 0.5,
                    'stumpings': 0.0
                }
            },
            'bowler': {
                'batting': {
                    'average': 10.0,
                    'strike_rate': 100.0,
                    'runs': 5.0
                },
                'bowling': {
                    'wickets': 1.5,
                    'economy': 8.0,
                    'average': 25.0
                },
                'fielding': {
                    'catches': 0.3,
                    'stumpings': 0.0
                }
            },
            'all-rounder': {
                'batting': {
                    'average': 20.0,
                    'strike_rate': 120.0,
                    'runs': 20.0
                },
                'bowling': {
                    'wickets': 1.0,
                    'economy': 9.0,
                    'average': 30.0
                },
                'fielding': {
                    'catches': 0.4,
                    'stumpings': 0.0
                }
            },
            'wicket-keeper': {
                'batting': {
                    'average': 22.0,
                    'strike_rate': 125.0,
                    'runs': 25.0
                },
                'bowling': {
                    'wickets': 0.0,
                    'economy': 12.0,
                    'average': 0.0
                },
                'fielding': {
                    'catches': 0.6,
                    'stumpings': 0.2
                }
            }
        }

    def _load_latest_player_form(self) -> Dict:
        """Load the most recent player form data from scheduler output"""
        try:
            # Find the latest player form file
            form_files = list(self.data_path.glob('scraped/player_form_*.json'))
            if not form_files:
                logger.warning("No player form data found")
                return {}
                
            # Sort by timestamp in filename
            latest_file = max(form_files, key=lambda x: x.stem.split('_')[-1])
            
            # Load the data
            with open(latest_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading player form data: {str(e)}")
            return {}

    def get_available_matches(self) -> pd.DataFrame:
        """Get all available matches for prediction"""
        matches_df = pd.DataFrame(self.matches_2025)
        matches_df['display'] = matches_df.apply(
            lambda x: f"Match {x['match_no']} - {x['team1']} vs {x['team2']} on {x['date']}",
            axis=1
        )
        # Ensure match_id is included
        if 'match_id' not in matches_df.columns:
            matches_df['match_id'] = matches_df['match_no']
        return matches_df

    def get_team_players(self, team_name):
        """
        Get the list of players for a team from the 2025 season data
        
        Args:
            team_name: Name of the team
            
        Returns:
            list: List of player names
        """
        try:
            # Load the 2024 players details
            players_df = pd.read_csv('IPL-DATASET-main/IPL-DATASET-main/csv/2024_players_details.csv')
            
            # Filter players for the given team
            team_players = players_df[players_df['Name'].notna()]['Name'].tolist()
            
            if not team_players:
                logger.warning(f"No players found for team {team_name}")
                return []
                
            return team_players
            
        except Exception as e:
            logger.error(f"Error getting team players: {str(e)}")
            return []

    def get_player_features(self, player_name: str, team_name: str) -> Dict:
        """
        Get features for a player
        
        Args:
            player_name: Name of the player
            team_name: Name of the team
            
        Returns:
            dict: Dictionary of player features
        """
        try:
            # Check cache first
            cache_key = f"{player_name}_{team_name}"
            if cache_key in self._player_stats_cache:
                cache_entry = self._player_stats_cache[cache_key]
                if (datetime.now() - cache_entry['timestamp']).seconds < self._cache_duration:
                    return cache_entry['data']
            
            # Get player role
            role = get_player_role(player_name)
            if not role:
                role = 'batsman'  # Default role
            
            # Get historical stats
            try:
                historical_stats = self.historical.get_player_stats(player_name)
            except Exception as e:
                logger.error(f"Error getting historical stats for {player_name}: {str(e)}")
                historical_stats = {}
            
            # Get IPL dataset stats
            try:
                ipl_stats = self.ipl_dataset.get_player_stats(player_name)
            except Exception as e:
                logger.error(f"Error getting IPL stats for {player_name}: {str(e)}")
                ipl_stats = {}
            
            # Get form data
            form_data = self.player_form_data.get(player_name, {})
            
            # Get role-based baseline stats
            baseline_stats = self._role_baselines.get(role, self._role_baselines['batsman'])
            
            # Combine all stats with fallbacks
            combined_stats = {
                'batting': {
                    'average': float(historical_stats.get('batting_average', 0) or ipl_stats.get('batting_average', 0) or form_data.get('batting_average', 0) or baseline_stats['batting']['average']),
                    'strike_rate': float(historical_stats.get('strike_rate', 0) or ipl_stats.get('strike_rate', 0) or form_data.get('strike_rate', 0) or baseline_stats['batting']['strike_rate']),
                    'runs': float(historical_stats.get('runs', 0) or ipl_stats.get('runs', 0) or form_data.get('runs', 0) or baseline_stats['batting']['runs'])
                },
                'bowling': {
                    'wickets': float(historical_stats.get('wickets', 0) or ipl_stats.get('wickets', 0) or form_data.get('wickets', 0) or baseline_stats['bowling']['wickets']),
                    'economy': float(historical_stats.get('economy', 0) or ipl_stats.get('economy', 0) or form_data.get('economy', 0) or baseline_stats['bowling']['economy']),
                    'average': float(historical_stats.get('bowling_average', 0) or ipl_stats.get('bowling_average', 0) or form_data.get('bowling_average', 0) or baseline_stats['bowling']['average'])
                },
                'fielding': {
                    'catches': float(historical_stats.get('catches', 0) or ipl_stats.get('catches', 0) or form_data.get('catches', 0) or baseline_stats['fielding']['catches']),
                    'stumpings': float(historical_stats.get('stumpings', 0) or ipl_stats.get('stumpings', 0) or form_data.get('stumpings', 0) or baseline_stats['fielding']['stumpings'])
                }
            }
            
            # Cache the results
            self._player_stats_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': combined_stats
            }
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Error getting player features for {player_name}: {str(e)}")
            return self._role_baselines.get(role, self._role_baselines['batsman'])

    def _get_new_player_features_with_web_data(self, player_name: str, team_name: str, web_data: Dict) -> Dict:
        """Get features for a new player using web data and team averages"""
        try:
            # Get team stats
            team_stats = self.ipl_dataset.get_team_stats(team_name)
            
            # Get player role from web data or determine it
            player_role = web_data.get('role', self._determine_player_role(player_name, team_name))
            
            # Get role-based baseline
            baseline = self._role_baselines.get(player_role, self._role_baselines['all-rounder'])
            
            # Get team averages
            team_batting_avg = team_stats.get('batting', {}).get('average', 0)
            team_bowling_avg = team_stats.get('bowling', {}).get('average', 0)
            
            # Extract web data
            web_batting = web_data.get('batting', {})
            web_bowling = web_data.get('bowling', {})
            web_fielding = web_data.get('fielding', {})
            
            # Combine web data with team averages (70% web data, 30% team average)
            features = {
                'batting': [
                    web_batting.get('average', baseline['batting']['average']) * 0.7 + team_batting_avg * 0.3,
                    web_batting.get('strike_rate', baseline['batting']['strike_rate']),
                    web_batting.get('runs', baseline['batting']['runs'])
                ],
                'bowling': [
                    web_bowling.get('wickets', baseline['bowling']['wickets']),
                    web_bowling.get('economy', baseline['bowling']['economy']),
                    web_bowling.get('average', baseline['bowling']['average']) * 0.7 + team_bowling_avg * 0.3
                ],
                'fielding': [
                    web_fielding.get('catches', baseline['fielding']['catches']),
                    web_fielding.get('stumpings', baseline['fielding']['stumpings'])
                ]
            }
            
            # Add small random variation
            features = self._add_random_variation(features)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error getting features for new player {player_name} with web data: {str(e)}")
            return self._get_new_player_features(player_name, team_name)

    def _is_new_player(self, ipl_data: Dict, historical_data: Dict) -> bool:
        """Check if player is new based on available data"""
        try:
            # Check if we have meaningful data from either source
            has_ipl_data = (
                ipl_data.get('batting', {}).get('current_form', {}).get('average', 0) > 0 or
                ipl_data.get('bowling', {}).get('current_form', {}).get('wickets', 0) > 0
            )
            
            has_historical_data = (
                historical_data.get('batting', {}).get('average', 0) > 0 or
                historical_data.get('bowling', {}).get('wickets', 0) > 0
            )
            
            return not (has_ipl_data or has_historical_data)
            
        except Exception as e:
            self.logger.error(f"Error checking if player is new: {str(e)}")
            return True

    def _get_new_player_features(self, player_name: str, team_name: str) -> Dict:
        """Get features for a new player using team averages and role-based baselines"""
        try:
            # Get team stats
            team_stats = self.ipl_dataset.get_team_stats(team_name)
            
            # Determine player role (you would need to implement this based on your data)
            player_role = self._determine_player_role(player_name, team_name)
            
            # Get role-based baseline
            baseline = self._role_baselines.get(player_role, self._role_baselines['all-rounder'])
            
            # Get team averages
            team_batting_avg = team_stats.get('batting', {}).get('average', 0)
            team_bowling_avg = team_stats.get('bowling', {}).get('average', 0)
            
            # Combine baseline with team averages (70% baseline, 30% team average)
            features = {
                'batting': [
                    baseline['batting']['average'] * 0.7 + team_batting_avg * 0.3,
                    baseline['batting']['strike_rate'],
                    baseline['batting']['runs']
                ],
                'bowling': [
                    baseline['bowling']['wickets'],
                    baseline['bowling']['economy'],
                    baseline['bowling']['average'] * 0.7 + team_bowling_avg * 0.3
                ],
                'fielding': [
                    baseline['fielding']['catches'],
                    baseline['fielding']['stumpings']
                ]
            }
            
            # Add small random variation
            features = self._add_random_variation(features)
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error getting features for new player {player_name}: {str(e)}")
            return self._get_default_features()

    def _determine_player_role(self, player_name: str, team_name: str) -> str:
        """Determine player's role based on available data"""
        try:
            # Try to get role from IPL dataset
            ipl_data = self.ipl_dataset.get_player_stats(player_name)
            if ipl_data and 'role' in ipl_data:
                return ipl_data['role']
            
            # Try to get role from historical data
            historical_data = self.historical.get_player_stats(player_name)
            if historical_data and 'role' in historical_data:
                return historical_data['role']
            
            # If no role data available, use team roster
            team_roster = self.ipl_dataset.get_team_roster(team_name)
            for player in team_roster:
                if player['name'].lower() == player_name.lower():
                    return player.get('role', 'all-rounder')
            
            # Default to all-rounder if no role information is found
            return 'all-rounder'
            
        except Exception as e:
            self.logger.error(f"Error determining player role: {str(e)}")
            return 'all-rounder'

    def _combine_batting_features(self, ipl_data: Dict, historical_data: Dict, form_data: Dict, weights: Dict) -> List[float]:
        """Combine batting features from different sources"""
        try:
            # IPL data features
            ipl_features = [
                float(ipl_data.get('current_form', {}).get('average', 0)),
                float(ipl_data.get('current_form', {}).get('strike_rate', 0)),
                float(ipl_data.get('current_form', {}).get('runs', 0))
            ]
            
            # Historical data features
            historical_features = [
                float(historical_data.get('average', 0)),
                float(historical_data.get('strike_rate', 0)),
                float(historical_data.get('runs', 0))
            ]
            
            # Combine with weights
            combined = [
                ipl_features[0] * weights['ipl'] + historical_features[0] * weights['historical'],
                ipl_features[1] * weights['ipl'] + historical_features[1] * weights['historical'],
                ipl_features[2] * weights['ipl'] + historical_features[2] * weights['historical']
            ]
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining batting features: {str(e)}")
            return [0.0, 0.0, 0.0]
            
    def _combine_bowling_features(self, ipl_data: Dict, historical_data: Dict, form_data: Dict, weights: Dict) -> List[float]:
        """Combine bowling features from different sources"""
        try:
            # IPL data features
            ipl_features = [
                float(ipl_data.get('current_form', {}).get('wickets', 0)),
                float(ipl_data.get('current_form', {}).get('economy', 0)),
                float(ipl_data.get('current_form', {}).get('average', 0))
            ]
            
            # Historical data features
            historical_features = [
                float(historical_data.get('wickets', 0)),
                float(historical_data.get('economy', 0)),
                float(historical_data.get('average', 0))
            ]
            
            # Combine with weights
            combined = [
                ipl_features[0] * weights['ipl'] + historical_features[0] * weights['historical'],
                ipl_features[1] * weights['ipl'] + historical_features[1] * weights['historical'],
                ipl_features[2] * weights['ipl'] + historical_features[2] * weights['historical']
            ]
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining bowling features: {str(e)}")
            return [0.0, 0.0, 0.0]
            
    def _combine_fielding_features(self, ipl_data: Dict, historical_data: Dict, form_data: Dict, weights: Dict) -> List[float]:
        """Combine fielding features from different sources"""
        try:
            # IPL data features
            ipl_features = [
                float(ipl_data.get('catches', 0)),
                float(ipl_data.get('stumpings', 0))
            ]
            
            # Historical data features
            historical_features = [
                float(historical_data.get('catches', 0)),
                float(historical_data.get('stumpings', 0))
            ]
            
            # Combine with weights
            combined = [
                ipl_features[0] * weights['ipl'] + historical_features[0] * weights['historical'],
                ipl_features[1] * weights['ipl'] + historical_features[1] * weights['historical']
            ]
            
            return combined
            
        except Exception as e:
            self.logger.error(f"Error combining fielding features: {str(e)}")
            return [0.0, 0.0]
            
    def _add_random_variation(self, features: Dict) -> Dict:
        """Add small random variation to features to prevent overfitting"""
        variation = 0.05  # 5% variation
        
        for category in features:
            for i in range(len(features[category])):
                if features[category][i] != 0:
                    variation_factor = 1 + random.uniform(-variation, variation)
                    features[category][i] *= variation_factor
                    
        return features
        
    def _get_default_features(self) -> Dict:
        """Get default features when data is missing"""
        return {
            'batting': [0.0, 0.0, 0.0],
            'bowling': [0.0, 0.0, 0.0],
            'fielding': [0.0, 0.0]
        }
        
    def predict_player_performance(self, player_name: str, team_name: str) -> Dict:
        """Predict player's performance in the match"""
        try:
            # Get player features
            features = self.get_player_features(player_name, team_name)
            
            # Predict batting performance
            batting_prediction = self._predict_batting(features['batting'])
            
            # Predict bowling performance
            bowling_prediction = self._predict_bowling(features['bowling'])
            
            # Predict fielding performance
            fielding_prediction = self._predict_fielding(features['fielding'])
            
            return {
                'batting': batting_prediction,
                'bowling': bowling_prediction,
                'fielding': fielding_prediction
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting performance for {player_name}: {str(e)}")
            return self._get_default_prediction()
            
    def _predict_batting(self, features: List[float]) -> Dict:
        """Predict batting performance"""
        try:
            # Simple linear model for batting
            runs = max(0, min(150, features[0] * 1.2 + features[1] * 0.8 + features[2] * 0.5))
            strike_rate = max(0, min(200, features[1] * 1.1))
            
            return {
                'runs': round(runs, 2),
                'strike_rate': round(strike_rate, 2),
                'probability': min(1.0, (runs / 100) * 0.7 + (strike_rate / 150) * 0.3)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting batting: {str(e)}")
            return {'runs': 0, 'strike_rate': 0, 'probability': 0}
            
    def _predict_bowling(self, features: List[float]) -> Dict:
        """Predict bowling performance"""
        try:
            # Simple linear model for bowling
            wickets = max(0, min(5, features[0] * 1.1))
            economy = max(0, min(15, features[1] * 1.2))
            
            return {
                'wickets': round(wickets, 2),
                'economy': round(economy, 2),
                'probability': min(1.0, (wickets / 3) * 0.6 + (1 - economy / 15) * 0.4)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting bowling: {str(e)}")
            return {'wickets': 0, 'economy': 0, 'probability': 0}
            
    def _predict_fielding(self, features: List[float]) -> Dict:
        """Predict fielding performance"""
        try:
            # Simple linear model for fielding
            catches = max(0, min(3, features[0] * 1.2))
            stumpings = max(0, min(2, features[1] * 1.1))
            
            return {
                'catches': round(catches, 2),
                'stumpings': round(stumpings, 2),
                'probability': min(1.0, (catches / 2) * 0.7 + (stumpings / 1) * 0.3)
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting fielding: {str(e)}")
            return {'catches': 0, 'stumpings': 0, 'probability': 0}
            
    def _get_default_prediction(self) -> Dict:
        """Get default prediction when data is missing"""
        return {
            'batting': {'runs': 0, 'strike_rate': 0, 'probability': 0},
            'bowling': {'wickets': 0, 'economy': 0, 'probability': 0},
            'fielding': {'catches': 0, 'stumpings': 0, 'probability': 0}
        }
        
    def predict_match(self, match_id: int) -> Dict:
        """
        Predict the outcome of a match
        
        Args:
            match_id: ID of the match to predict
            
        Returns:
            dict: Dictionary containing match prediction results
        """
        try:
            # Get match details
            match = get_match_by_id(match_id)
            if not match:
                logger.error(f"Match {match_id} not found")
                return {}
            
            # Get team performances
            team1_performance = self._predict_team_performance(match['team1'])
            team2_performance = self._predict_team_performance(match['team2'])
            
            # Calculate win probabilities based on team performances
            team1_strength = (
                team1_performance['batting']['average'] * 0.4 +
                team1_performance['bowling']['wickets'] * 0.4 +
                team1_performance['fielding']['catches'] * 0.2
            )
            
            team2_strength = (
                team2_performance['batting']['average'] * 0.4 +
                team2_performance['bowling']['wickets'] * 0.4 +
                team2_performance['fielding']['catches'] * 0.2
            )
            
            # Normalize strengths to probabilities
            total_strength = team1_strength + team2_strength
            if total_strength == 0:
                team1_prob = 0.5
                team2_prob = 0.5
            else:
                team1_prob = team1_strength / total_strength
                team2_prob = team2_strength / total_strength
            
            # Ensure probabilities sum to 1
            total_prob = team1_prob + team2_prob
            if total_prob > 0:
                team1_prob = team1_prob / total_prob
                team2_prob = team2_prob / total_prob
            
            return {
                'match_id': match_id,
                'team1': match['team1'],
                'team2': match['team2'],
                'date': match['date'],
                'venue': match.get('venue', 'Unknown'),
                'team1_probability': round(team1_prob * 100, 2),
                'team2_probability': round(team2_prob * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error predicting match {match_id}: {str(e)}")
            return {}
            
    def _predict_team_performance(self, team_name: str) -> Dict:
        """
        Predict performance metrics for a team
        
        Args:
            team_name: Name of the team
            
        Returns:
            dict: Dictionary of team performance predictions
        """
        try:
            # Get team players
            players = self.get_team_players(team_name)
            if not players:
                logger.warning(f"No players found for team {team_name}")
                return {
                    'batting': {'average': 0, 'strike_rate': 0, 'runs': 0},
                    'bowling': {'wickets': 0, 'economy': 0, 'average': 0},
                    'fielding': {'catches': 0, 'stumpings': 0}
                }
            
            # Get features for each player
            player_features = []
            for player in players:
                features = self.get_player_features(player, team_name)
                if features:
                    player_features.append(features)
            
            if not player_features:
                logger.warning(f"No features found for team {team_name}")
                return {
                    'batting': {'average': 0, 'strike_rate': 0, 'runs': 0},
                    'bowling': {'wickets': 0, 'economy': 0, 'average': 0},
                    'fielding': {'catches': 0, 'stumpings': 0}
                }
            
            # Calculate team averages
            team_performance = {
                'batting': {
                    'average': np.mean([p['batting']['average'] for p in player_features]),
                    'strike_rate': np.mean([p['batting']['strike_rate'] for p in player_features]),
                    'runs': np.mean([p['batting']['runs'] for p in player_features])
                },
                'bowling': {
                    'wickets': np.mean([p['bowling']['wickets'] for p in player_features]),
                    'economy': np.mean([p['bowling']['economy'] for p in player_features]),
                    'average': np.mean([p['bowling']['average'] for p in player_features])
                },
                'fielding': {
                    'catches': np.mean([p['fielding']['catches'] for p in player_features]),
                    'stumpings': np.mean([p['fielding']['stumpings'] for p in player_features])
                }
            }
            
            return team_performance
            
        except Exception as e:
            logger.error(f"Error predicting team performance: {str(e)}")
            return {
                'batting': {'average': 0, 'strike_rate': 0, 'runs': 0},
                'bowling': {'wickets': 0, 'economy': 0, 'average': 0},
                'fielding': {'catches': 0, 'stumpings': 0}
            }

def test_new_player_prediction():
    """Test prediction for a new player using web scraping"""
    predictor = MatchPredictor()
    
    # Test with a new player
    new_player = "Shubman Gill"  # Example new player
    team = "Gujarat Titans"
    
    # Get player features
    features = predictor.get_player_features(new_player, team)
    
    # Log the results
    logger.info(f"\nTesting new player prediction for {new_player}:")
    logger.info(f"Features extracted: {json.dumps(features, indent=2)}")
    
    # Verify that we got some data
    assert features is not None, "Should get features for new player"
    assert 'batting' in features, "Should have batting features"
    assert 'bowling' in features, "Should have bowling features"
    assert 'fielding' in features, "Should have fielding features"
    
    logger.info("New player prediction test completed successfully")

def main():
    predictor = MatchPredictor()
    
    # Get available matches
    matches = predictor.get_available_matches()
    print("\nAvailable IPL 2025 Matches:")
    for idx, match in matches.iterrows():
        print(f"{idx + 1}. {match['display']}")
    
    # Get user input
    match_num = int(input("\nEnter the number of the match you want to predict (1-72): ")) - 1
    match = matches.iloc[match_num]
    
    # Get predictions
    predictions = predictor.predict_match(match['match_id'])
    
    # Print predictions
    print(f"\nPredictions for Match {match['match_no']}: {match['team1']} vs {match['team2']}")
    print(f"Date: {match['date']} at {match['venue']}")
    
    if 'team1' in predictions and 'team2' in predictions:
        print(f"\nTeam 1 ({match['team1']}) Win Probability: {predictions['team1_probability']:.2%}")
        print(f"Team 2 ({match['team2']}) Win Probability: {predictions['team2_probability']:.2%}")
    else:
        print("\nCould not generate predictions for this match.")

if __name__ == "__main__":
    test_new_player_prediction()
    main() 