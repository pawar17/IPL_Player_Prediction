import os
import sys
from pathlib import Path

# Add project root directory to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import IPL 2025 data
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from data_collection.ipl_2025_data import schedule, teams
except ImportError as e:
    logging.error(f"Error importing IPL 2025 data: {str(e)}")
    schedule = []
    teams = []

class MLPredictor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_dir = self.base_path / 'data'
        self.historical_dir = self.data_dir / 'historical'
        self.models_dir = self.base_path / 'models'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.batting_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.bowling_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        
        # Try to load pre-trained models
        try:
            if (self.models_dir / 'batting_model.joblib').exists():
                self.batting_model = joblib.load(self.models_dir / 'batting_model.joblib')
                self.bowling_model = joblib.load(self.models_dir / 'bowling_model.joblib')
                self.scaler = joblib.load(self.models_dir / 'scaler.joblib')
                self.logger.info("Loaded pre-trained models")
        except Exception as e:
            self.logger.warning(f"Could not load pre-trained models: {str(e)}")
            # Models will be trained when needed
        
        # Load and prepare data
        self.prepare_ml_data()

    def load_all_data(self) -> tuple:
        """Load data from all available sources."""
        try:
            # Load historical data
            historical_file = self.historical_dir / "processed_historical_matches.csv"
            if historical_file.exists():
                historical_matches = pd.read_csv(historical_file)
                logger.info(f"Loaded {len(historical_matches)} historical matches")
            else:
                historical_matches = pd.DataFrame()
            
            # Load current season data and team rosters
            from ipl_2025_data import matches as current_matches_data, teams as teams_data
            
            # Process current matches into the same format as historical data
            current_matches = []
            for match in current_matches_data:
                for team in ['team1', 'team2']:
                    team_name = match[team]
                    team_data = next((t for t in teams_data if t['name'] == team_name), None)
                    if team_data:
                        for player in team_data['players']:
                            match_entry = {
                                'match_id': match['match_id'],
                                'date': match['date'],
                                'venue': match['venue'],
                                'team1': match['team1'],
                                'team2': match['team2'],
                                'winner': match.get('winner', ''),
                                'player_id': player['id'],
                                'player_name': player['name'],
                                'runs': player.get('recent_stats', {}).get('runs', 0),
                                'wickets': player.get('recent_stats', {}).get('wickets', 0),
                                'strike_rate': player.get('recent_stats', {}).get('strike_rate', 0),
                                'economy_rate': player.get('recent_stats', {}).get('economy_rate', 0),
                                'opponent': match['team2'] if team == 'team1' else match['team1'],
                                'match_importance': match.get('match_importance', 0.5),
                                'pressure_index': match.get('pressure_index', 0.5)
                            }
                            current_matches.append(match_entry)
            
            current_matches_df = pd.DataFrame(current_matches)
            logger.info(f"Loaded {len(current_matches_df)} current season matches")
            
            # Create player stats from team rosters
            player_stats = []
            for team in teams_data:
                for player in team['players']:
                    recent_stats = player.get('recent_stats', {})
                    recent_matches = player.get('recent_matches', [])
                    
                    # Calculate player statistics
                    stats = {
                        'player_id': player['id'],
                        'name': player['name'],
                        'team': team['name'],
                        'matches_played': len(recent_matches),
                        'total_runs': sum(m.get('runs', 0) for m in recent_matches),
                        'total_wickets': sum(m.get('wickets', 0) for m in recent_matches),
                        'batting_average': recent_stats.get('batting_average', 0),
                        'bowling_average': recent_stats.get('bowling_average', 0),
                        'strike_rate': recent_stats.get('strike_rate', 0),
                        'economy_rate': recent_stats.get('economy_rate', 0),
                        'recent_matches': json.dumps(recent_matches[:5])  # Last 5 matches
                    }
                    player_stats.append(stats)
            
            player_stats_df = pd.DataFrame(player_stats)
            logger.info(f"Loaded {len(player_stats_df)} player statistics")
            
            # Combine historical and current data
            all_matches = pd.concat([historical_matches, current_matches_df], ignore_index=True)
            all_matches = all_matches.sort_values('date', ascending=False)
            
            return all_matches, current_matches_df, pd.DataFrame(), [], player_stats_df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), [], pd.DataFrame()

    def prepare_ml_data(self):
        """Prepare data for machine learning models."""
        try:
            # Load all data
            all_matches, current_matches, latest_matches, ipl_website_data, player_stats = self.load_all_data()
            
            # Only use historical matches for training (since current/latest matches don't have results yet)
            all_matches = all_matches.copy()
            
            # Drop rows with missing essential data
            all_matches = all_matches.dropna(subset=['runs', 'wickets', 'strike_rate', 'economy_rate'])
            
            # Fill missing match situation features with neutral values
            all_matches['match_importance'] = all_matches['match_importance'].fillna(0.5)
            all_matches['pressure_index'] = all_matches['pressure_index'].fillna(0.5)
            
            # Prepare batting features
            batting_features = []
            batting_targets = []
            
            for _, row in all_matches.iterrows():
                player_data = player_stats[player_stats['player_id'] == row['player_id']]
                if not player_data.empty:
                    # Basic stats
                    features = [
                        float(player_data['batting_average'].iloc[0]),
                        float(player_data['strike_rate'].iloc[0]),
                        self.calculate_form(player_data['recent_matches'].iloc[0]),
                        self.calculate_consistency(player_data['recent_matches'].iloc[0])
                    ]
                    
                    # Add venue performance
                    venue_perf = self.calculate_venue_performance(
                        row['player_id'], 
                        row['venue'], 
                        all_matches
                    )
                    features.append(venue_perf)
                    
                    # Add opponent performance
                    opponent_perf = self.calculate_opponent_performance(
                        row['player_id'], 
                        row['opponent'], 
                        all_matches
                    )
                    features.append(opponent_perf)
                    
                    # Add match situation features
                    features.extend([
                        float(row['match_importance']),
                        float(row['pressure_index'])
                    ])
                    
                    batting_features.append(features)
                    batting_targets.append(float(row['runs']))
            
            # Prepare bowling features
            bowling_features = []
            bowling_targets = []
            
            for _, row in all_matches.iterrows():
                player_data = player_stats[player_stats['player_id'] == row['player_id']]
                if not player_data.empty:
                    # Basic stats
                    features = [
                        float(player_data['bowling_average'].iloc[0]),
                        float(player_data['economy_rate'].iloc[0]),
                        self.calculate_form(player_data['recent_matches'].iloc[0]),
                        self.calculate_consistency(player_data['recent_matches'].iloc[0])
                    ]
                    
                    # Add venue performance
                    venue_perf = self.calculate_venue_performance(
                        row['player_id'], 
                        row['venue'], 
                        all_matches,
                        is_bowling=True
                    )
                    features.append(venue_perf)
                    
                    # Add opponent performance
                    opponent_perf = self.calculate_opponent_performance(
                        row['player_id'], 
                        row['opponent'], 
                        all_matches,
                        is_bowling=True
                    )
                    features.append(opponent_perf)
                    
                    # Add match situation features
                    features.extend([
                        float(row['match_importance']),
                        float(row['pressure_index'])
                    ])
                    
                    bowling_features.append(features)
                    bowling_targets.append(float(row['wickets']))
            
            if not batting_features or not bowling_features:
                raise ValueError("No valid features found for training")
            
            # Convert to numpy arrays
            batting_features = np.array(batting_features)
            batting_targets = np.array(batting_targets)
            bowling_features = np.array(bowling_features)
            bowling_targets = np.array(bowling_targets)
            
            # Scale features
            self.batting_features_scaled = self.scaler.fit_transform(batting_features)
            self.bowling_features_scaled = self.scaler.fit_transform(bowling_features)
            
            # Split data for validation
            X_bat_train, X_bat_test, y_bat_train, y_bat_test = train_test_split(
                self.batting_features_scaled, batting_targets, test_size=0.2, random_state=42
            )
            X_bowl_train, X_bowl_test, y_bowl_train, y_bowl_test = train_test_split(
                self.bowling_features_scaled, bowling_targets, test_size=0.2, random_state=42
            )
            
            # Train models
            self.batting_model.fit(X_bat_train, y_bat_train)
            self.bowling_model.fit(X_bowl_train, y_bowl_train)
            
            # Evaluate models
            bat_pred = self.batting_model.predict(X_bat_test)
            bowl_pred = self.bowling_model.predict(X_bowl_test)
            
            bat_mse = mean_squared_error(y_bat_test, bat_pred)
            bowl_mse = mean_squared_error(y_bowl_test, bowl_pred)
            bat_r2 = r2_score(y_bat_test, bat_pred)
            bowl_r2 = r2_score(y_bowl_test, bowl_pred)
            
            logger.info(f"Batting Model - MSE: {bat_mse:.2f}, R2: {bat_r2:.2f}")
            logger.info(f"Bowling Model - MSE: {bowl_mse:.2f}, R2: {bowl_r2:.2f}")
            
        except Exception as e:
            logger.error(f"Error preparing ML data: {str(e)}")
            raise

    def calculate_venue_performance(self, player_id: str, venue: str, 
                                  matches: pd.DataFrame, is_bowling: bool = False) -> float:
        """Calculate player's performance at a specific venue."""
        try:
            venue_matches = matches[
                (matches['player_id'] == player_id) & 
                (matches['venue'] == venue)
            ]
            
            if venue_matches.empty:
                return 0.5  # Neutral score if no venue data
            
            if is_bowling:
                return min(venue_matches['wickets'].mean() / 5, 1.0)
            else:
                return min(venue_matches['runs'].mean() / 100, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating venue performance: {str(e)}")
            return 0.5

    def calculate_opponent_performance(self, player_id: str, opponent: str, 
                                     matches: pd.DataFrame, is_bowling: bool = False) -> float:
        """Calculate player's performance against a specific opponent."""
        try:
            opponent_matches = matches[
                (matches['player_id'] == player_id) & 
                (matches['opponent'] == opponent)
            ]
            
            if opponent_matches.empty:
                return 0.5  # Neutral score if no opponent data
            
            if is_bowling:
                return min(opponent_matches['wickets'].mean() / 5, 1.0)
            else:
                return min(opponent_matches['runs'].mean() / 100, 1.0)
                
        except Exception as e:
            logger.error(f"Error calculating opponent performance: {str(e)}")
            return 0.5

    def calculate_form(self, recent_matches: str) -> float:
        """Calculate player's recent form."""
        try:
            matches = json.loads(recent_matches)
            if not matches:
                return 0.0
            
            weights = [0.3, 0.25, 0.2, 0.15, 0.1]
            form_score = 0.0
            
            for i, match in enumerate(matches[:5]):
                if i < len(weights):
                    runs = float(match.get('runs', 0))
                    wickets = float(match.get('wickets', 0))
                    strike_rate = float(match.get('strike_rate', 0))
                    economy_rate = float(match.get('economy_rate', 0))
                    
                    runs_score = min(runs / 100, 1.0)
                    wickets_score = min(wickets / 5, 1.0)
                    strike_rate_score = min(strike_rate / 200, 1.0)
                    economy_score = max(1 - (economy_rate / 12), 0)
                    
                    match_score = (runs_score * 0.4 + wickets_score * 0.3 + 
                                 strike_rate_score * 0.2 + economy_score * 0.1)
                    form_score += match_score * weights[i]
            
            return round(form_score, 2)
        except Exception as e:
            logger.error(f"Error calculating form: {str(e)}")
            return 0.0

    def calculate_consistency(self, recent_matches: str) -> float:
        """Calculate player's consistency."""
        try:
            matches = json.loads(recent_matches)
            if not matches:
                return 0.0
            
            performances = []
            for match in matches[:10]:
                runs = float(match.get('runs', 0))
                wickets = float(match.get('wickets', 0))
                strike_rate = float(match.get('strike_rate', 0))
                economy_rate = float(match.get('economy_rate', 0))
                
                performance = (runs/100 + wickets/5 + strike_rate/200 + (1-economy_rate/12)) / 4
                performances.append(performance)
            
            if not performances:
                return 0.0
            
            std_dev = np.std(performances)
            consistency = 1 / (1 + std_dev)
            return round(consistency, 2)
        except Exception as e:
            logger.error(f"Error calculating consistency: {str(e)}")
            return 0.0

    def get_recent_matches(self, player_id: str, player_data: pd.Series, num_matches: int = 5) -> List[Dict]:
        """Get recent match statistics for a player."""
        try:
            recent_matches = json.loads(player_data['recent_matches'])
            return recent_matches[:num_matches]
        except Exception as e:
            logger.error(f"Error getting recent matches: {str(e)}")
            return []

    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Make predictions for a player's performance"""
        try:
            # Prepare features
            feature_vector = self._prepare_feature_vector(features)
            
            if self.scaler is None:
                self.scaler = StandardScaler()
                # Since we don't have training data, use a simple standardization
                feature_vector = (feature_vector - np.mean(feature_vector)) / np.std(feature_vector)
            else:
                feature_vector = self.scaler.transform(feature_vector.reshape(1, -1))
            
            # Make predictions
            runs_pred = self.batting_model.predict(feature_vector)[0] if self.batting_model else 0
            wickets_pred = self.bowling_model.predict(feature_vector)[0] if self.bowling_model else 0
            
            # Calculate confidence based on historical data and recent form
            confidence = self._calculate_confidence(features)
            
            return {
                'runs': max(0, runs_pred),
                'wickets': max(0, wickets_pred),
                'confidence': confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error making prediction: {str(e)}")
            return {
                'runs': 0,
                'wickets': 0,
                'confidence': 0
            }
    
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare feature vector for prediction"""
        try:
            # Extract historical stats
            hist = features.get('historical_stats', {})
            recent = features.get('recent_stats', {})
            current = features.get('current_stats', {})
            
            # Create feature vector
            feature_vector = np.array([
                recent.get('avg_runs', 0),                    # last_5_matches_runs_avg
                recent.get('avg_wickets', 0),                 # last_5_matches_wickets_avg
                recent.get('strike_rate', 0),                 # last_5_matches_sr_avg
                recent.get('economy_rate', 0),               # last_5_matches_er_avg
                hist.get('avg_runs', 0),                     # career_runs_avg
                hist.get('avg_wickets', 0),                  # career_wickets_avg
                hist.get('avg_strike_rate', 0),              # career_sr_avg
                hist.get('avg_economy_rate', 0),             # career_er_avg
                recent.get('form', 0.5),                     # form_factor
                current.get('consistency', 0.5),             # consistency_score
                1 if features.get('is_home_game', False) else 0  # is_home_match
            ])
            
            return feature_vector.reshape(1, -1)
            
        except Exception as e:
            self.logger.error(f"Error preparing feature vector: {str(e)}")
            # Return zero vector with correct shape
            return np.zeros((1, 11))
    
    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate prediction confidence score"""
        try:
            # Get relevant statistics
            hist = features.get('historical_stats', {})
            recent = features.get('recent_stats', {})
            
            # Factors affecting confidence
            factors = [
                min(1.0, hist.get('total_matches', 0) / 50),  # More matches = higher confidence
                recent.get('form', 0.5),                      # Better form = higher confidence
                0.8 if features.get('is_home_game') else 0.6  # Home game advantage
            ]
            
            # Calculate weighted average
            confidence = sum(factors) / len(factors)
            
            return max(0.1, min(1.0, confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {str(e)}")
            return 0.1  # Return minimum confidence on error

    def predict_player_performance(self, player_id: str, player_data: pd.Series, 
                                 opponent_team: str, historical_data: pd.DataFrame) -> Dict:
        """Predict player performance using ML models."""
        try:
            # Get recent match statistics
            recent_matches = self.get_recent_matches(player_id, player_data)
            
            # Prepare features for prediction
            batting_features = [
                float(player_data['batting_average']),
                float(player_data['strike_rate']),
                self.calculate_form(player_data['recent_matches']),
                self.calculate_consistency(player_data['recent_matches']),
                self.calculate_venue_performance(player_id, historical_data['venue'].iloc[0], historical_data),
                self.calculate_opponent_performance(player_id, opponent_team, historical_data),
                0.5,  # Default match importance
                0.5   # Default pressure index
            ]
            
            bowling_features = [
                float(player_data['bowling_average']),
                float(player_data['economy_rate']),
                self.calculate_form(player_data['recent_matches']),
                self.calculate_consistency(player_data['recent_matches']),
                self.calculate_venue_performance(player_id, historical_data['venue'].iloc[0], historical_data, is_bowling=True),
                self.calculate_opponent_performance(player_id, opponent_team, historical_data, is_bowling=True),
                0.5,  # Default match importance
                0.5   # Default pressure index
            ]
            
            # Scale features
            batting_features_scaled = self.scaler.transform([batting_features])
            bowling_features_scaled = self.scaler.transform([bowling_features])
            
            # Make predictions
            predicted_runs = self.batting_model.predict(batting_features_scaled)[0]
            predicted_wickets = self.bowling_model.predict(bowling_features_scaled)[0]
            
            # Calculate confidence based on feature importance
            batting_importance = self.batting_model.feature_importances_
            bowling_importance = self.bowling_model.feature_importances_
            
            confidence = (
                np.mean(batting_importance) * 0.6 +  # Weight batting more heavily
                np.mean(bowling_importance) * 0.4
            )
            
            return {
                'player_id': player_id,
                'name': player_data['name'],
                'predicted_runs': round(predicted_runs, 2),
                'predicted_wickets': round(predicted_wickets, 2),
                'confidence': round(confidence, 2),
                'recent_matches': recent_matches,
                'factors': {
                    'form': self.calculate_form(player_data['recent_matches']),
                    'consistency': self.calculate_consistency(player_data['recent_matches']),
                    'batting_average': float(player_data['batting_average']),
                    'bowling_average': float(player_data['bowling_average']),
                    'venue_performance': self.calculate_venue_performance(player_id, historical_data['venue'].iloc[0], historical_data),
                    'opponent_performance': self.calculate_opponent_performance(player_id, opponent_team, historical_data)
                }
            }
        except Exception as e:
            logger.error(f"Error predicting player performance: {str(e)}")
            return {}

    def get_match_predictions(self, match: Dict) -> Dict:
        """Get predictions for a specific match."""
        try:
            # Load all data
            all_matches, current_matches, latest_matches, ipl_website_data, player_stats = self.load_all_data()
            
            # Combine all match data
            all_matches = pd.concat([
                all_matches,
                current_matches,
                latest_matches
            ], ignore_index=True)
            
            # Get team squads
            from ipl_2025_data import teams
            squads = {team['name']: team['players'] for team in teams}
            
            # Generate predictions
            predictions = {
                'match': match,
                'team1': {
                    'name': match['team1'],
                    'predictions': [
                        self.predict_player_performance(
                            player['id'],
                            player_stats[player_stats['player_id'] == player['id']].iloc[0],
                            match['team2'],
                            all_matches
                        )
                        for player in squads.get(match['team1'], [])
                    ]
                },
                'team2': {
                    'name': match['team2'],
                    'predictions': [
                        self.predict_player_performance(
                            player['id'],
                            player_stats[player_stats['player_id'] == player['id']].iloc[0],
                            match['team1'],
                            all_matches
                        )
                        for player in squads.get(match['team2'], [])
                    ]
                }
            }
            
            # Save predictions
            output_file = self.output_dir / f"predictions_{match['match_id']}.json"
            with open(output_file, 'w') as f:
                json.dump(predictions, f, indent=2)
            
            return predictions
        except Exception as e:
            logger.error(f"Error getting match predictions: {str(e)}")
            return None

    def get_comprehensive_match_prediction(self, match_id: int) -> Dict[str, Any]:
        """
        Get comprehensive predictions for all players in both teams for a specific match,
        combining historical data, recent performance, and current roster information.
        
        Args:
            match_id: ID of the match to predict
            
        Returns:
            Dictionary containing predictions for all players in both teams
        """
        try:
            # Load all data
            all_matches, current_matches, latest_matches, ipl_website_data, player_stats = self.load_all_data()
            
            # Get match data from current matches or schedule
            match_data = None
            if not current_matches.empty and match_id in current_matches['match_id'].values:
                match_data = current_matches[current_matches['match_id'] == match_id].iloc[0]
            else:
                # Try to get from IPL 2025 schedule
                try:
                    from src.data_collection.ipl_2025_data import schedule, teams as teams_data
                except ImportError:
                    self.logger.error("Could not import IPL 2025 data. Please check the data files.")
                    return {}
                
                if not schedule:
                    self.logger.error("IPL 2025 schedule is empty")
                    return {}
                    
                match_data = next((m for m in schedule if m.get('match_id') == match_id), None)
            
            if match_data is None:
                self.logger.error(f"Match {match_id} not found in current matches or schedule")
                return {}
            
            # Get team names
            team1 = match_data.get('team1') if isinstance(match_data, dict) else match_data['team1']
            team2 = match_data.get('team2') if isinstance(match_data, dict) else match_data['team2']
            
            # Get team rosters
            if 'teams_data' not in locals():
                try:
                    from src.data_collection.ipl_2025_data import teams as teams_data
                except ImportError:
                    self.logger.error("Could not import IPL 2025 teams data")
                    return {}
            
            if not teams_data:
                self.logger.error("IPL 2025 teams data is empty")
                return {}
            
            team1_data = next((t for t in teams_data if t['name'] == team1), None)
            team2_data = next((t for t in teams_data if t['name'] == team2), None)
            
            if not team1_data or not team2_data:
                self.logger.error(f"Could not find roster data for {team1} or {team2}")
                return {}
            
            # Initialize predictions dictionary
            predictions = {
                'match_id': match_id,
                'date': match_data.get('date') if isinstance(match_data, dict) else match_data['date'],
                'venue': match_data.get('venue') if isinstance(match_data, dict) else match_data['venue'],
                'team1': {
                    'name': team1,
                    'players': []
                },
                'team2': {
                    'name': team2,
                    'players': []
                }
            }
            
            # Process each team
            for team_data, team_key in [(team1_data, 'team1'), (team2_data, 'team2')]:
                for player in team_data['players']:
                    player_name = player['name']
                    
                    # Get historical performance
                    historical_perf = all_matches[all_matches['player_name'] == player_name] if not all_matches.empty else pd.DataFrame()
                    
                    if not historical_perf.empty:
                        historical_stats = {
                            'total_matches': len(historical_perf),
                            'avg_runs': historical_perf['runs'].mean(),
                            'avg_wickets': historical_perf['wickets'].mean(),
                            'avg_strike_rate': historical_perf['strike_rate'].mean(),
                            'avg_economy_rate': historical_perf['economy_rate'].mean(),
                            'best_runs': historical_perf['runs'].max(),
                            'best_wickets': historical_perf['wickets'].max()
                        }
                    else:
                        historical_stats = {
                            'total_matches': 0,
                            'avg_runs': 0,
                            'avg_wickets': 0,
                            'avg_strike_rate': 0,
                            'avg_economy_rate': 0,
                            'best_runs': 0,
                            'best_wickets': 0
                        }
                    
                    # Get recent performance (last 5 matches)
                    recent_matches = player.get('recent_matches', [])[:5]  # Ensure only last 5 matches
                    recent_stats = {
                        'matches_played': len(recent_matches),
                        'total_runs': sum(m.get('runs', 0) for m in recent_matches),
                        'total_wickets': sum(m.get('wickets', 0) for m in recent_matches),
                        'avg_runs': sum(m.get('runs', 0) for m in recent_matches) / max(1, len(recent_matches)),
                        'avg_wickets': sum(m.get('wickets', 0) for m in recent_matches) / max(1, len(recent_matches)),
                        'form': player.get('recent_stats', {}).get('form', 0.5)
                    }
                    
                    # Get current stats from roster
                    current_stats = player.get('recent_stats', {})
                    
                    # Prepare features for prediction
                    features = {
                        'player_name': player_name,
                        'team': team_data['name'],
                        'role': player.get('role', 'Unknown'),
                        'historical_stats': historical_stats,
                        'recent_stats': recent_stats,
                        'current_stats': current_stats,
                        'is_home_game': team_key == 'team1',  # Assuming team1 is home team
                        'opponent': team2 if team_key == 'team1' else team1,
                        'venue': predictions['venue']
                    }
                    
                    # Make prediction
                    prediction = self.predict(features)
                    
                    # Add player prediction to results
                    player_prediction = {
                        'name': player_name,
                        'role': player.get('role', 'Unknown'),
                        'historical_performance': historical_stats,
                        'recent_performance': recent_stats,
                        'current_form': current_stats,
                        'prediction': prediction
                    }
                    
                    predictions[team_key]['players'].append(player_prediction)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive match prediction: {str(e)}")
            return {}

    def train_models(self):
        """Train the batting and bowling models using historical data"""
        try:
            # Load all data
            all_matches, current_matches, latest_matches, ipl_website_data, player_stats = self.load_all_data()
            
            if all_matches.empty:
                self.logger.error("No historical data available for training")
                return
            
            # Prepare features and targets
            features = [
                'last_5_matches_runs_avg', 'last_5_matches_wickets_avg',
                'last_5_matches_sr_avg', 'last_5_matches_er_avg',
                'career_runs_avg', 'career_wickets_avg',
                'career_sr_avg', 'career_er_avg',
                'form_factor', 'consistency_score',
                'is_home_match'
            ]
            
            # Check if all required features are present
            missing_features = [f for f in features if f not in all_matches.columns]
            if missing_features:
                self.logger.error(f"Missing required features: {missing_features}")
                # Add missing features with default values
                for feature in missing_features:
                    all_matches[feature] = 0.0
            
            X = all_matches[features].fillna(0)
            y_batting = all_matches['runs'].fillna(0)
            y_bowling = all_matches['wickets'].fillna(0)
            
            # Initialize and fit scaler
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Train batting model
            self.batting_model.fit(X_scaled, y_batting)
            
            # Train bowling model
            self.bowling_model.fit(X_scaled, y_bowling)
            
            # Calculate and log metrics
            batting_pred = self.batting_model.predict(X_scaled)
            bowling_pred = self.bowling_model.predict(X_scaled)
            
            batting_mse = mean_squared_error(y_batting, batting_pred)
            batting_r2 = r2_score(y_batting, batting_pred)
            bowling_mse = mean_squared_error(y_bowling, bowling_pred)
            bowling_r2 = r2_score(y_bowling, bowling_pred)
            
            self.logger.info(f"Batting Model - MSE: {batting_mse:.2f}, R2: {batting_r2:.2f}")
            self.logger.info(f"Bowling Model - MSE: {bowling_mse:.2f}, R2: {bowling_r2:.2f}")
            
            # Save models
            joblib.dump(self.batting_model, self.models_dir / 'batting_model.joblib')
            joblib.dump(self.bowling_model, self.models_dir / 'bowling_model.joblib')
            joblib.dump(self.scaler, self.models_dir / 'scaler.joblib')
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            raise  # Re-raise the exception for debugging

def main():
    try:
        predictor = MLPredictor()
        
        # Train models if needed
        predictor.train_models()
        
        # Get comprehensive predictions for a specific match
        match_id = 1  # You can change this to any match ID you want to predict
        predictions = predictor.get_comprehensive_match_prediction(match_id)
        
        if not predictions:
            print("\nNo predictions available. Please check the logs for errors.")
            return
        
        # Print predictions in a readable format
        print("\nComprehensive Match Predictions:")
        print("=" * 50)
        
        if 'team1' not in predictions or 'team2' not in predictions:
            print("Error: Invalid prediction format")
            return
            
        print(f"Match: {predictions['team1']['name']} vs {predictions['team2']['name']}")
        print(f"Date: {predictions.get('date', 'N/A')}")
        print(f"Venue: {predictions.get('venue', 'N/A')}\n")
        
        # Print predictions for each team
        for team_key in ['team1', 'team2']:
            team = predictions[team_key]
            print(f"\n{team['name']} Predictions:")
            print("-" * 30)
            
            if not team.get('players'):
                print("No player predictions available")
                continue
            
            for player in team['players']:
                print(f"\n{player['name']} ({player.get('role', 'Unknown')}):")
                
                prediction = player.get('prediction', {})
                print(f"Predicted: {prediction.get('runs', 0):.1f} runs, {prediction.get('wickets', 0):.1f} wickets")
                print(f"Confidence: {prediction.get('confidence', 0):.2f}")
                
                hist = player.get('historical_performance', {})
                if hist:
                    print("\nHistorical Performance:")
                    print(f"  Total Matches: {hist.get('total_matches', 0)}")
                    print(f"  Average Runs: {hist.get('avg_runs', 0):.1f}")
                    print(f"  Average Wickets: {hist.get('avg_wickets', 0):.1f}")
                    print(f"  Best Runs: {hist.get('best_runs', 0)}")
                    print(f"  Best Wickets: {hist.get('best_wickets', 0)}")
                
                recent = player.get('recent_performance', {})
                if recent:
                    print("\nRecent Performance (Last 5 matches):")
                    print(f"  Matches Played: {recent.get('matches_played', 0)}")
                    print(f"  Average Runs: {recent.get('avg_runs', 0):.1f}")
                    print(f"  Average Wickets: {recent.get('avg_wickets', 0):.1f}")
                    print(f"  Form: {recent.get('form', 0):.2f}")
                
                current = player.get('current_form', {})
                if current:
                    print("\nCurrent Form:")
                    for stat, value in current.items():
                        print(f"  {stat}: {value}")
                
                print("-" * 50)
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        logging.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 