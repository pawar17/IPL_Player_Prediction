import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.output_dir = self.data_dir / "predictions"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize ML models
        self.batting_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.bowling_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        
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

def main():
    predictor = MLPredictor()
    
    # Example usage
    match = {
        'match_id': 'test_match',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'date': '2024-03-20',
        'venue': 'Wankhede Stadium'
    }
    
    predictions = predictor.get_match_predictions(match)
    if predictions:
        print("\nMatch Predictions:")
        print("=" * 50)
        print(f"Match: {predictions['match']['team1']} vs {predictions['match']['team2']}")
        print(f"Date: {predictions['match']['date']}")
        print(f"Venue: {predictions['match']['venue']}")
        
        print("\nTeam 1 Predictions:")
        for pred in predictions['team1']['predictions']:
            print(f"\n{pred['name']}:")
            print(f"Predicted: {pred['predicted_runs']} runs, {pred['predicted_wickets']} wickets")
            print(f"Confidence: {pred['confidence']}")
            
            print("\nRecent Matches:")
            print("-" * 30)
            for i, match in enumerate(pred['recent_matches'], 1):
                print(f"Match {i}:")
                print(f"  Runs: {match.get('runs', 'N/A')}")
                print(f"  Wickets: {match.get('wickets', 'N/A')}")
                print(f"  Strike Rate: {match.get('strike_rate', 'N/A')}")
                print(f"  Economy Rate: {match.get('economy_rate', 'N/A')}")
            
            print("\nPerformance Factors:")
            for factor, value in pred['factors'].items():
                print(f"  {factor}: {value}")
            print("-" * 50)

if __name__ == "__main__":
    main() 