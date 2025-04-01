import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging
from pathlib import Path
import json
from datetime import datetime, timedelta

class FeatureProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.scraped_path = self.data_path / 'scraped'
        self.processed_path = self.data_path / 'processed'
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def process_features(self, player_data: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and enhance features for prediction"""
        try:
            features = {}
            
            # 1. Basic Performance Features
            features.update(self._calculate_performance_features(player_data))
            
            # 2. Form and Momentum Features
            features.update(self._calculate_form_features(player_data))
            
            # 3. Context Features
            features.update(self._calculate_context_features(player_data, match_context))
            
            # 4. Team and Venue Features
            features.update(self._calculate_team_venue_features(match_context))
            
            # 5. Weather Impact Features
            features.update(self._calculate_weather_features(match_context))
            
            # 6. Player Role Features
            features.update(self._calculate_role_features(player_data))
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error processing features: {str(e)}")
            return {}
    
    def _calculate_performance_features(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate basic performance features"""
        features = {
            'recent_runs_avg': player_data.get('last_5_matches_runs_avg', 0),
            'recent_wickets_avg': player_data.get('last_5_matches_wickets_avg', 0),
            'recent_sr_avg': player_data.get('last_5_matches_sr_avg', 0),
            'recent_er_avg': player_data.get('last_5_matches_er_avg', 0),
            'career_runs_avg': player_data.get('runs_mean', 0),
            'career_wickets_avg': player_data.get('wickets_mean', 0),
            'career_sr_avg': player_data.get('strike_rate_mean', 0),
            'career_er_avg': player_data.get('economy_rate_mean', 0)
        }
        
        # Add consistency metrics
        features.update({
            'runs_consistency': 1 / (1 + player_data.get('runs_std', 1)),
            'wickets_consistency': 1 / (1 + player_data.get('wickets_std', 1)),
            'sr_consistency': 1 / (1 + player_data.get('strike_rate_std', 1)),
            'er_consistency': 1 / (1 + player_data.get('economy_rate_std', 1))
        })
        
        return features
    
    def _calculate_form_features(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate form and momentum features"""
        features = {}
        
        # Calculate form factor
        recent_runs = player_data.get('last_5_matches_runs_avg', 0)
        career_runs = player_data.get('runs_mean', 0)
        features['form_factor'] = recent_runs / career_runs if career_runs > 0 else 1.0
        
        # Calculate momentum (trend in last 3 matches)
        last_3_matches = player_data.get('last_3_matches_runs', [0, 0, 0])
        if len(last_3_matches) >= 2:
            features['momentum'] = np.mean(np.diff(last_3_matches))
        else:
            features['momentum'] = 0
        
        # Calculate consistency score
        features['consistency_score'] = player_data.get('consistency_score', 0.5)
        
        return features
    
    def _calculate_context_features(self, player_data: Dict[str, Any], match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate match context features"""
        features = {
            'is_home_game': match_context.get('is_home_game', False),
            'days_since_last_match': player_data.get('days_since_last_match', 0),
            'pressure_index': match_context.get('pressure_index', 0.5),
            'match_importance': match_context.get('match_importance', 0.5)
        }
        
        # Calculate fatigue factor
        days_since_last = features['days_since_last_match']
        features['fatigue_factor'] = 1.0
        if days_since_last < 3:
            features['fatigue_factor'] = 0.8
        elif days_since_last > 7:
            features['fatigue_factor'] = 1.2
        
        return features
    
    def _calculate_team_venue_features(self, match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team and venue specific features"""
        features = {}
        
        # Load team and venue statistics
        with open(self.scraped_path / 'processed_team_stats.json', 'r') as f:
            team_stats = json.load(f)
        with open(self.scraped_path / 'processed_venue_stats.json', 'r') as f:
            venue_stats = json.load(f)
        
        # Team strength features
        team = match_context.get('team')
        opposition = match_context.get('opposition')
        if team in team_stats and opposition in team_stats:
            features.update({
                'team_strength': team_stats[team]['runs']['mean'],
                'opposition_strength': team_stats[opposition]['runs']['mean'],
                'team_wicket_taking': team_stats[team]['wickets']['mean'],
                'opposition_wicket_taking': team_stats[opposition]['wickets']['mean']
            })
        
        # Venue features
        venue = match_context.get('venue')
        if venue in venue_stats:
            features.update({
                'venue_runs_factor': venue_stats[venue]['runs']['mean'] / 160,  # Normalize to average T20 score
                'venue_wickets_factor': venue_stats[venue]['wickets']['mean'] / 7,  # Normalize to average wickets
                'venue_sr_factor': venue_stats[venue]['strike_rate'] / 130,  # Normalize to average strike rate
                'venue_er_factor': venue_stats[venue]['economy_rate'] / 8  # Normalize to average economy rate
            })
        
        return features
    
    def _calculate_weather_features(self, match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weather impact features"""
        weather = match_context.get('weather', {})
        
        features = {
            'temperature': weather.get('temperature', 25),
            'humidity': weather.get('humidity', 60),
            'wind_speed': weather.get('wind_speed', 0),
            'rain_probability': weather.get('rain_probability', 0)
        }
        
        # Calculate weather impact factors
        features['weather_batting_factor'] = self._calculate_batting_weather_factor(weather)
        features['weather_bowling_factor'] = self._calculate_bowling_weather_factor(weather)
        
        return features
    
    def _calculate_role_features(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate player role specific features"""
        features = {
            'is_powerplay_batsman': player_data.get('is_powerplay_batsman', False),
            'is_death_bowler': player_data.get('is_death_bowler', False),
            'is_spinner': player_data.get('is_spinner', False),
            'is_pacer': player_data.get('is_pacer', False)
        }
        
        # Calculate role-specific performance metrics
        if features['is_powerplay_batsman']:
            features['powerplay_sr'] = player_data.get('powerplay_strike_rate', 0)
        if features['is_death_bowler']:
            features['death_overs_er'] = player_data.get('death_overs_economy', 0)
        
        return features
    
    def _calculate_batting_weather_factor(self, weather: Dict[str, Any]) -> float:
        """Calculate weather factor for batting"""
        factor = 1.0
        
        # Temperature impact
        temp = weather.get('temperature', 25)
        if temp > 35:
            factor *= 0.9  # Hot conditions reduce batting performance
        elif temp < 15:
            factor *= 0.95  # Cold conditions slightly reduce batting performance
        
        # Humidity impact
        humidity = weather.get('humidity', 60)
        if humidity > 80:
            factor *= 0.95  # High humidity reduces batting performance
        
        # Wind impact
        wind = weather.get('wind_speed', 0)
        if wind > 20:
            factor *= 0.9  # Strong winds reduce batting performance
        
        return factor
    
    def _calculate_bowling_weather_factor(self, weather: Dict[str, Any]) -> float:
        """Calculate weather factor for bowling"""
        factor = 1.0
        
        # Temperature impact
        temp = weather.get('temperature', 25)
        if temp > 35:
            factor *= 1.1  # Hot conditions favor bowlers
        elif temp < 15:
            factor *= 1.05  # Cold conditions slightly favor bowlers
        
        # Humidity impact
        humidity = weather.get('humidity', 60)
        if humidity > 80:
            factor *= 1.1  # High humidity favors bowlers
        
        # Wind impact
        wind = weather.get('wind_speed', 0)
        if wind > 20:
            factor *= 1.1  # Strong winds favor bowlers
        
        return factor 