import logging
import argparse
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from ..data_collection.data_processor import DataProcessor
from ..models.player_predictor import PlayerPredictor
from ..data_collection.cricket_sources import CricketDataSources
from ..data_collection.cricbuzz_collector import CricbuzzCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('player_prediction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlayerPredictionSystem:
    """
    Main system for predicting player performance in IPL matches
    """
    def __init__(self, data_dir: str = None):
        """Initialize the prediction system"""
        self.logger = logging.getLogger(__name__)
        self.data_dir = data_dir or str(Path(__file__).parent.parent.parent / 'data')
        self.historical_data = None
        self.batting_model = None
        self.bowling_model = None
        self.form_data = {}
        self.initialize()
        
    def initialize(self):
        self.base_path = Path(__file__).parent.parent.parent
        
        # Initialize components
        self.logger.info("Initializing data processor...")
        self.data_processor = DataProcessor()
        
        self.logger.info("Initializing prediction model...")
        self.predictor = PlayerPredictor()
        
        # Initialize cricket data sources
        self.logger.info("Initializing cricket data sources...")
        self.cricket_sources = CricketDataSources()
        
        self.cricbuzz = CricbuzzCollector()
        self.batting_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.bowling_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self._load_historical_data()
        
        # Create output directory
        self.output_path = self.base_path / 'data' / 'predictions'
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Load scheduler data
        self.scraped_path = self.base_path / 'data' / 'scraped'
        self._load_scheduler_data()
        
        # Try to load existing models
        try:
            self.predictor.load_models()
            self.logger.info("Loaded existing prediction models")
        except Exception as e:
            self.logger.warning(f"Could not load existing models: {str(e)}. Will need to train new models.")
    
    def _load_scheduler_data(self):
        """Load latest data from scheduler"""
        try:
            # Load latest injury updates
            injury_files = sorted(self.scraped_path.glob('injury_updates_*.json'))
            if injury_files:
                with open(injury_files[-1], 'r') as f:
                    self.injury_data = json.load(f)
            else:
                self.injury_data = {}
            
            # Load latest team compositions
            team_files = sorted(self.scraped_path.glob('team_changes_*.json'))
            if team_files:
                with open(team_files[-1], 'r') as f:
                    self.team_data = json.load(f)
            else:
                self.team_data = {}
            
            # Load latest venue conditions
            venue_files = sorted(self.scraped_path.glob('venue_conditions_*.json'))
            if venue_files:
                with open(venue_files[-1], 'r') as f:
                    self.venue_data = json.load(f)
            else:
                self.venue_data = {}
            
            # Load latest player form
            form_files = sorted(self.scraped_path.glob('player_form_*.json'))
            if form_files:
                with open(form_files[-1], 'r') as f:
                    self.form_data = json.load(f)
            else:
                self.form_data = {}
            
            self.logger.info("Loaded scheduler data successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading scheduler data: {str(e)}")
            self.injury_data = {}
            self.team_data = {}
            self.venue_data = {}
            self.form_data = {}
    
    def _get_player_availability(self, player_name: str) -> bool:
        """Check if player is available based on injury data"""
        if player_name in self.injury_data:
            return not self.injury_data[player_name].get('is_injured', False)
        return True
    
    def _get_team_composition(self, team: str) -> Dict:
        """Get team composition from form data"""
        try:
            # Load form data
            form_data_path = Path(self.data_dir) / 'scraped' / 'player_form_20250403_155713.json'
            if not form_data_path.exists():
                self.logger.warning(f"Form data file not found at {form_data_path}")
                return {}
                
            with open(form_data_path, 'r') as f:
                form_data = json.load(f)
            
            # Filter players by team
            team_players = {}
            for player_name, player_data in form_data.items():
                # Determine player role based on stats
                batting_stats = player_data.get('batting', {})
                bowling_stats = player_data.get('bowling', {})
                
                if bowling_stats.get('wickets', 0) > 0:
                    if batting_stats.get('runs', 0) > 30:
                        role = 'All-rounder'
                    else:
                        role = 'Bowler'
                else:
                    role = 'Batsman'
                
                team_players[player_name] = {
                    'role': role,
                    'form_factor': player_data.get('form_factor', 1.0)
                }
            
            return team_players
            
        except Exception as e:
            self.logger.error(f"Error getting team composition: {str(e)}")
            return {}
    
    def _get_venue_conditions(self, venue: str) -> Dict:
        """Get latest venue conditions"""
        return self.venue_data.get(venue, {})
    
    def _get_player_form(self, player_name: str) -> Dict:
        """Get player form data from the form data file"""
        try:
            # Load form data
            form_data_path = Path(self.data_dir) / 'scraped' / 'player_form_20250403_155713.json'
            if not form_data_path.exists():
                self.logger.warning(f"Form data file not found at {form_data_path}")
                return self._get_default_form()
                
            with open(form_data_path, 'r') as f:
                form_data = json.load(f)
                
            # Get player data
            player_data = form_data.get(player_name, {})
            if not player_data:
                self.logger.warning(f"No form data found for player {player_name}")
                return self._get_default_form()
                
            # Extract batting and bowling stats
            batting_stats = player_data.get('batting', {})
            bowling_stats = player_data.get('bowling', {})
            
            # Calculate form factor based on recent performance
            batting_form = (
                float(batting_stats.get('runs', 0)) / 100 +
                float(batting_stats.get('strike_rate', 0)) / 200 +
                float(batting_stats.get('average', 0)) / 50
            ) / 3
            
            bowling_form = (
                float(bowling_stats.get('wickets', 0)) / 3 +
                (10 - float(bowling_stats.get('economy', 10))) / 10 +
                (50 - float(bowling_stats.get('average', 50))) / 50
            ) / 3
            
            # Combine batting and bowling form
            form_factor = max(batting_form, bowling_form)
            
            return {
                'batting': {
                    'runs': float(batting_stats.get('runs', 0)),
                    'strike_rate': float(batting_stats.get('strike_rate', 0)),
                    'average': float(batting_stats.get('average', 0))
                },
                'bowling': {
                    'wickets': float(bowling_stats.get('wickets', 0)),
                    'economy': float(bowling_stats.get('economy', 0)),
                    'average': float(bowling_stats.get('average', 0))
                },
                'form_factor': max(0.5, min(1.5, form_factor))  # Cap between 0.5 and 1.5
            }
            
        except Exception as e:
            self.logger.error(f"Error getting player form: {str(e)}")
            return self._get_default_form()
            
    def _get_default_form(self) -> Dict:
        """Return default form data"""
        return {
            'batting': {
                'runs': 25.0,
                'strike_rate': 125.0,
                'average': 25.0
            },
            'bowling': {
                'wickets': 1.0,
                'economy': 8.0,
                'average': 30.0
            },
            'form_factor': 1.0
        }
    
    def _load_historical_data(self):
        """Load and prepare historical data for training"""
        try:
            # Load historical data from CSV
            self.historical_data = pd.read_csv('data/historical_data.csv')
            
            # Convert categorical variables to numeric using one-hot encoding
            categorical_features = ['venue', 'opposition', 'match_type']
            self.historical_data = pd.get_dummies(
                self.historical_data,
                columns=categorical_features,
                prefix=categorical_features
            )
            
            # Prepare features for batting
            batting_features = [
                col for col in self.historical_data.columns
                if col.startswith(('venue_', 'opposition_', 'match_type_')) or
                col in ['season', 'recent_runs', 'recent_strike_rate', 'recent_average',
                       'opposition_strength', 'venue_performance']
            ]
            
            # Prepare features for bowling
            bowling_features = [
                col for col in self.historical_data.columns
                if col.startswith(('venue_', 'opposition_', 'match_type_')) or
                col in ['season', 'recent_wickets', 'recent_economy', 'recent_average',
                       'opposition_strength', 'venue_performance']
            ]
            
            # Train models
            self.batting_model.fit(
                self.historical_data[batting_features],
                self.historical_data['runs_scored']
            )
            
            self.bowling_model.fit(
                self.historical_data[bowling_features],
                self.historical_data['wickets_taken']
            )
            
            self.logger.info("Historical data loaded and models trained successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading historical data: {str(e)}")
            raise
    
    def train_models(self, perform_grid_search: bool = False) -> None:
        """
        Train prediction models using combined data
        
        Args:
            perform_grid_search: Whether to perform grid search for hyperparameter tuning
        """
        self.logger.info("Loading and processing data for training...")
        
        # Get data from all sources
        # Create a sample player name for testing
        sample_player = "Virat Kohli"
        
        # Get historical data for the sample player
        historical_data = self.data_processor._get_historical_data(sample_player)
        
        # Get current tournament data
        cricbuzz_data = self.data_processor._get_cricbuzz_current_data(sample_player)
        
        # Get recent data
        recent_data = self.data_processor._get_cricbuzz_recent_data(sample_player)
        
        # Combine data
        combined_data = self.data_processor._combine_data_sources(
            recent_data,
            cricbuzz_data,
            historical_data
        )
        
        if not combined_data:
            self.logger.error("No data available for training")
            return
        
        # Format data for training
        training_data = {
            'batting_performance': combined_data['batting']['runs'],
            'bowling_performance': combined_data['bowling']['wickets'],
            'fielding_performance': 0,  # Default value for now
            'recent_runs': combined_data['batting'].get('runs', 0),
            'recent_strike_rate': combined_data['batting'].get('strike_rate', 0),
            'recent_average': combined_data['batting'].get('average', 0),
            'current_runs': cricbuzz_data.get('batting', {}).get('runs', 0),
            'current_strike_rate': cricbuzz_data.get('batting', {}).get('strike_rate', 0),
            'current_average': cricbuzz_data.get('batting', {}).get('average', 0),
            'historical_runs': historical_data.get('batting', {}).get('runs', 0),
            'historical_strike_rate': historical_data.get('batting', {}).get('strike_rate', 0),
            'historical_average': historical_data.get('batting', {}).get('average', 0),
            'venue_runs': 0,  # Default value for now
            'venue_strike_rate': 0,  # Default value for now
            'venue_average': 0  # Default value for now
        }
        
        # Convert to DataFrame for training
        training_df = pd.DataFrame([training_data])
        
        self.logger.info(f"Training models with combined data...")
        metrics = self.predictor.train(training_df, perform_grid_search)
        
        self.logger.info("Training complete. Metrics:")
        for target, target_metrics in metrics.items():
            self.logger.info(f"{target}:")
            for metric_name, metric_value in target_metrics.items():
                self.logger.info(f"  {metric_name}: {metric_value:.3f}")
    
    def predict_player_performance(
        self,
        player_id: str,
        match_id: int,
        historical_data: Dict,
        current_form: Optional[Dict] = None
    ) -> Dict:
        """Predict player performance using both historical and real-time data"""
        try:
            # Get player details
            player = self._get_player_details(player_id)
            if not player:
                return self._get_default_prediction()

            # Get real-time stats from Cricbuzz
            cricbuzz_stats = self.cricbuzz.get_player_stats(player['name'])
            
            # Combine historical and real-time data
            features = self._prepare_features(
                player,
                match_id,
                historical_data,
                current_form,
                cricbuzz_stats
            )
            
            # Make predictions
            batting_prediction = self._predict_batting(features)
            bowling_prediction = self._predict_bowling(features)
            
            # Calculate confidence intervals
            batting_ci = self._calculate_confidence_interval(batting_prediction)
            bowling_ci = self._calculate_confidence_interval(bowling_prediction)
            
            return {
                "batting": {
                    "value": float(batting_prediction),
                    "confidence_interval": batting_ci,
                    "strike_rate": features.get('strike_rate', 0),
                    "form_factor": features.get('form_factor', 1.0)
                },
                "bowling": {
                    "value": float(bowling_prediction),
                    "confidence_interval": bowling_ci,
                    "economy_rate": features.get('economy_rate', 0),
                    "form_factor": features.get('form_factor', 1.0)
                },
                "timestamp": datetime.now().isoformat(),
                "data_sources": {
                    "historical": bool(historical_data),
                    "current_form": bool(current_form),
                    "cricbuzz": bool(cricbuzz_stats)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting performance for player {player_id}: {str(e)}")
            return self._get_default_prediction()

    def _get_player_details(self, player_id: str) -> Optional[Dict]:
        """Get player details from the database"""
        try:
            # This would typically query your database
            # For now, return mock data
            return {
                "id": player_id,
                "name": "Player Name",
                "role": "All-rounder",
                "team": "Team Name"
            }
        except Exception as e:
            self.logger.error(f"Error getting player details: {str(e)}")
            return None

    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare features for prediction"""
        # Get player form data
        form_data = self._get_player_form(features['name'])
        if not form_data:
            self.logger.warning(f"No form data found for player {features['name']}")
            form_data = {
                'batting': {
                    'runs': 0,
                    'strike_rate': 0,
                    'average': 0
                },
                'bowling': {
                    'wickets': 0,
                    'economy': 0,
                    'average': 0
                },
                'form_factor': 1.0
            }

        # Create feature vector with weights matching PlayerPredictor
        feature_vector = []
        
        # Recent form features (40% weight)
        recent_batting_features = [
            form_data.get('batting', {}).get('runs', 0),
            form_data.get('batting', {}).get('strike_rate', 0),
            form_data.get('batting', {}).get('average', 0)
        ]
        recent_bowling_features = [
            form_data.get('bowling', {}).get('wickets', 0),
            form_data.get('bowling', {}).get('economy', 0),
            form_data.get('bowling', {}).get('average', 0)
        ]
        feature_vector.extend([f * 0.4 for f in recent_batting_features + recent_bowling_features])
        
        # Current tournament features (30% weight)
        current_batting_features = [
            features.get('current_runs', 0),
            features.get('current_strike_rate', 0),
            features.get('current_average', 0)
        ]
        current_bowling_features = [
            features.get('current_wickets', 0),
            features.get('current_economy', 0),
            features.get('current_bowling_average', 0)
        ]
        feature_vector.extend([f * 0.3 for f in current_batting_features + current_bowling_features])
        
        # Historical features (20% weight)
        historical_batting_features = [
            features.get('historical_runs', 0),
            features.get('historical_strike_rate', 0),
            features.get('historical_average', 0)
        ]
        historical_bowling_features = [
            features.get('historical_wickets', 0),
            features.get('historical_economy', 0),
            features.get('historical_bowling_average', 0)
        ]
        feature_vector.extend([f * 0.2 for f in historical_batting_features + historical_bowling_features])
        
        # Venue features (10% weight)
        venue_batting_features = [
            features.get('venue_runs', 0),
            features.get('venue_strike_rate', 0),
            features.get('venue_average', 0)
        ]
        venue_bowling_features = [
            features.get('venue_wickets', 0),
            features.get('venue_economy', 0),
            features.get('venue_bowling_average', 0)
        ]
        feature_vector.extend([f * 0.1 for f in venue_batting_features + venue_bowling_features])
        
        # Additional features
        feature_vector.extend([
            features.get('match_importance', 1.0),
            features.get('team_strength', 0.5),
            features.get('opposition_strength', 0.5)
        ])
        
        # Ensure exactly 27 features
        if len(feature_vector) != 27:
            self.logger.warning(f"Feature vector has {len(feature_vector)} features, expected 27")
            if len(feature_vector) > 27:
                feature_vector = feature_vector[:27]
            else:
                feature_vector.extend([0] * (27 - len(feature_vector)))
        
        return np.array(feature_vector)

    def _predict_batting(self, features: Dict) -> float:
        """Predict batting performance"""
        try:
            # Prepare features
            feature_vector = self._prepare_features(features)
            
            # Get form data for form factor
            form_data = self._get_player_form(features['name'])
            form_factor = form_data.get('form_factor', 1.0) if form_data else 1.0
            
            # Make prediction
            prediction = self.batting_model.predict(feature_vector.reshape(1, -1))[0]
            
            # Apply form factor
            prediction *= form_factor
            
            return max(0, prediction)  # Ensure non-negative prediction
            
        except Exception as e:
            self.logger.error(f"Error predicting batting performance: {str(e)}")
            return 0.0
    
    def _predict_bowling(self, features: Dict) -> float:
        """Predict bowling performance"""
        try:
            # Prepare features
            feature_vector = self._prepare_features(features)
            
            # Get form data for form factor
            form_data = self._get_player_form(features['name'])
            form_factor = form_data.get('form_factor', 1.0) if form_data else 1.0
            
            # Make prediction
            prediction = self.bowling_model.predict(feature_vector.reshape(1, -1))[0]
            
            # Apply form factor
            prediction *= form_factor
            
            return max(0, prediction)  # Ensure non-negative prediction
            
        except Exception as e:
            self.logger.error(f"Error predicting bowling performance: {str(e)}")
            return 0.0
    
    def _calculate_confidence_interval(self, prediction: float) -> Dict[str, float]:
        """Calculate confidence interval for prediction"""
        try:
            # Base confidence interval
            std_dev = prediction * 0.2  # 20% standard deviation
            
            # Adjust based on data availability
            if self.injury_data and self.team_data and self.venue_data and self.form_data:
                std_dev *= 0.8  # More confident with all data available
            elif not (self.injury_data or self.team_data or self.venue_data or self.form_data):
                std_dev *= 1.2  # Less confident with missing data
            
            return {
                'lower': max(0, prediction - 1.96 * std_dev),
                'upper': prediction + 1.96 * std_dev
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {str(e)}")
            return {'lower': 0, 'upper': prediction * 1.5}

    def _get_default_prediction(self) -> Dict:
        """Return default prediction when data is insufficient"""
        return {
            "batting": {
                "value": 0.0,
                "confidence_interval": {"lower": 0, "upper": 0},
                "strike_rate": 0.0,
                "form_factor": 1.0
            },
            "bowling": {
                "value": 0.0,
                "confidence_interval": {"lower": 0, "upper": 0},
                "economy_rate": 0.0,
                "form_factor": 1.0
            },
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "historical": False,
                "current_form": False,
                "cricbuzz": False
            }
        }
    
    def predict_team_performance(self, match_no: int, team_name: str) -> List[Dict[str, Any]]:
        """
        Predict performance for all players in a team for a specific match
        
        Args:
            match_no: Match number in the IPL schedule
            team_name: Name of the team
            
        Returns:
            List of dictionaries containing performance predictions for each player
        """
        self.logger.info(f"Predicting performance for team {team_name} in match {match_no}...")
        
        # Get team players from Cricbuzz
        team_info = self.cricket_sources.get_team_composition(team_name)
        if not team_info:
            self.logger.error(f"Team {team_name} not found")
            return []
        
        players = team_info.get('players', [])
        if not players:
            self.logger.error(f"No players found for team {team_name}")
            return []
        
        # Predict performance for each player
        predictions = []
        for player in players:
            player_name = player['name']
            prediction = self.predict_player_performance(player_name, match_no, {}, {})
            predictions.append({
                'player_name': player_name,
                'role': player['role'],
                'prediction': prediction
            })
        
        return predictions
    
    def predict_match_performance(self, match_no: int) -> Dict[str, Any]:
        """
        Predict performance for all players in both teams for a specific match
        
        Args:
            match_no: Match number in the IPL schedule
            
        Returns:
            Dictionary containing performance predictions for both teams
        """
        self.logger.info(f"Predicting performance for match {match_no}...")
        
        # Get match details from Cricbuzz
        match_data = self.cricket_sources.get_match_details(match_no)
        if not match_data:
            self.logger.error(f"Match {match_no} not found")
            return {"error": "Match not found"}
        
        team1_name = match_data.get('team1')
        team2_name = match_data.get('team2')
        
        # Predict performance for both teams
        team1_predictions = self.predict_team_performance(match_no, team1_name)
        team2_predictions = self.predict_team_performance(match_no, team2_name)
        
        # Combine predictions
        match_predictions = {
            'match_no': match_no,
            'date': match_data.get('date'),
            'venue': match_data.get('venue'),
            'team1': {
                'name': team1_name,
                'predictions': team1_predictions
            },
            'team2': {
                'name': team2_name,
                'predictions': team2_predictions
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Save match predictions
        self._save_match_predictions(match_no, match_predictions)
        
        return match_predictions
    
    def _save_prediction(self, match_no: int, player_name: str, prediction: Dict[str, Any]) -> None:
        """Save player prediction to file"""
        try:
            filename = f"prediction_{match_no}_{player_name.replace(' ', '_')}.json"
            filepath = self.output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(prediction, f, indent=2)
                
            self.logger.info(f"Saved prediction to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving prediction: {str(e)}")
    
    def _save_match_predictions(self, match_no: int, predictions: Dict[str, Any]) -> None:
        """Save match predictions to file"""
        try:
            filename = f"match_predictions_{match_no}.json"
            filepath = self.output_path / filename
            
            with open(filepath, 'w') as f:
                json.dump(predictions, f, indent=2)
                
            self.logger.info(f"Saved match predictions to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error saving match predictions: {str(e)}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='IPL Player Performance Prediction System')
    parser.add_argument('--train', action='store_true', help='Train the prediction models')
    parser.add_argument('--grid-search', action='store_true', help='Perform grid search during training')
    parser.add_argument('--match', type=int, help='Match number to predict')
    parser.add_argument('--player', type=str, help='Player name to predict')
    parser.add_argument('--team', type=str, help='Team name to predict')
    
    args = parser.parse_args()
    
    system = PlayerPredictionSystem()
    
    if args.train:
        system.train_models(args.grid_search)
    
    if args.match:
        if args.player:
            prediction = system.predict_player_performance(args.player, args.match, {}, {})
            print(json.dumps(prediction, indent=2))
        elif args.team:
        predictions = system.predict_team_performance(args.match, args.team)
            print(json.dumps(predictions, indent=2))
        else:
        predictions = system.predict_match_performance(args.match)
            print(json.dumps(predictions, indent=2))
