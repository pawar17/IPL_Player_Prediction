import logging
import argparse
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.data_collection.efficient_data_collector import EfficientDataCollector
from src.models.advanced_player_predictor import AdvancedPlayerPredictor
from src.data_collection.ipl_2025_data import IPL2025Data

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
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent
        
        # Initialize components
        self.logger.info("Initializing data collector...")
        self.data_collector = EfficientDataCollector()
        
        self.logger.info("Initializing prediction model...")
        self.predictor = AdvancedPlayerPredictor()
        
        # Load IPL 2025 data for match information
        self.logger.info("Loading IPL 2025 data...")
        self.ipl_data = IPL2025Data()
        
        # Create output directory
        self.output_path = self.base_path / 'data' / 'predictions'
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing models
        try:
            self.predictor.load_models()
            self.logger.info("Loaded existing prediction models")
        except Exception as e:
            self.logger.warning(f"Could not load existing models: {str(e)}. Will need to train new models.")
    
    def train_models(self, perform_grid_search: bool = False) -> None:
        """
        Train prediction models using historical data
        
        Args:
            perform_grid_search: Whether to perform grid search for hyperparameter tuning
        """
        self.logger.info("Loading historical data for training...")
        historical_data = self.data_collector.load_historical_data()
        
        if historical_data.empty:
            self.logger.error("No historical data available for training")
            return
        
        self.logger.info(f"Training models with {len(historical_data)} samples...")
        metrics = self.predictor.train(historical_data, perform_grid_search)
        
        self.logger.info("Training complete. Metrics:")
        for target, target_metrics in metrics.items():
            self.logger.info(f"{target}:")
            for metric_name, metric_value in target_metrics.items():
                self.logger.info(f"  {metric_name}: {metric_value:.3f}")
    
    def predict_player_performance(self, match_no: int, player_name: str) -> Dict[str, Any]:
        """
        Predict performance for a specific player in a specific match
        
        Args:
            match_no: Match number in the IPL 2025 schedule
            player_name: Name of the player
            
        Returns:
            Dictionary containing performance predictions
        """
        self.logger.info(f"Predicting performance for {player_name} in match {match_no}...")
        
        # Prepare prediction data
        prediction_data = self.data_collector.prepare_prediction_data(match_no, player_name)
        
        if not prediction_data:
            self.logger.error(f"Could not prepare prediction data for {player_name} in match {match_no}")
            return {"error": "Could not prepare prediction data"}
        
        # Make prediction
        prediction = self.predictor.predict(prediction_data)
        
        # Save prediction
        self._save_prediction(match_no, player_name, prediction)
        
        return prediction
    
    def predict_team_performance(self, match_no: int, team_name: str) -> List[Dict[str, Any]]:
        """
        Predict performance for all players in a team for a specific match
        
        Args:
            match_no: Match number in the IPL 2025 schedule
            team_name: Name of the team
            
        Returns:
            List of dictionaries containing performance predictions for each player
        """
        self.logger.info(f"Predicting performance for team {team_name} in match {match_no}...")
        
        # Get team players
        team_info = self.ipl_data.teams.get(team_name, {})
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
            prediction = self.predict_player_performance(match_no, player_name)
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
            match_no: Match number in the IPL 2025 schedule
            
        Returns:
            Dictionary containing performance predictions for both teams
        """
        self.logger.info(f"Predicting performance for match {match_no}...")
        
        # Find match in schedule
        match_data = None
        for match in self.ipl_data.schedule:
            if match.get('match_no') == match_no:
                match_data = match
                break
        
        if not match_data:
            self.logger.error(f"Match {match_no} not found in schedule")
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
        """
        Save player prediction to file
        
        Args:
            match_no: Match number
            player_name: Player name
            prediction: Prediction data
        """
        try:
            # Create filename
            safe_player_name = player_name.replace(' ', '_')
            filename = f"match_{match_no}_{safe_player_name}.json"
            file_path = self.output_path / filename
            
            # Save prediction
            with open(file_path, 'w') as f:
                json.dump(prediction, f, indent=4)
            
            self.logger.info(f"Saved prediction to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving prediction: {str(e)}")
    
    def _save_match_predictions(self, match_no: int, predictions: Dict[str, Any]) -> None:
        """
        Save match predictions to file
        
        Args:
            match_no: Match number
            predictions: Match predictions data
        """
        try:
            # Create filename
            filename = f"match_{match_no}_predictions.json"
            file_path = self.output_path / filename
            
            # Save predictions
            with open(file_path, 'w') as f:
                json.dump(predictions, f, indent=4)
            
            self.logger.info(f"Saved match predictions to {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving match predictions: {str(e)}")
    
    def get_match_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all matches in the IPL 2025 schedule
        
        Returns:
            List of dictionaries containing match information
        """
        return [
            {
                'match_no': match.get('match_no'),
                'date': match.get('date'),
                'team1': match.get('team1'),
                'team2': match.get('team2'),
                'venue': match.get('venue')
            }
            for match in self.ipl_data.schedule
        ]
    
    def get_team_players(self, team_name: str) -> List[Dict[str, Any]]:
        """
        Get information about all players in a team
        
        Args:
            team_name: Name of the team
            
        Returns:
            List of dictionaries containing player information
        """
        team_info = self.ipl_data.teams.get(team_name, {})
        if not team_info:
            return []
        
        return team_info.get('players', [])


def main():
    """Main function to run the player prediction system"""
    parser = argparse.ArgumentParser(description='IPL Player Performance Prediction System')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train prediction models')
    train_parser.add_argument('--grid-search', action='store_true', help='Perform grid search for hyperparameter tuning')
    
    # Predict player command
    predict_player_parser = subparsers.add_parser('predict-player', help='Predict player performance')
    predict_player_parser.add_argument('--match', type=int, required=True, help='Match number')
    predict_player_parser.add_argument('--player', type=str, required=True, help='Player name')
    
    # Predict team command
    predict_team_parser = subparsers.add_parser('predict-team', help='Predict team performance')
    predict_team_parser.add_argument('--match', type=int, required=True, help='Match number')
    predict_team_parser.add_argument('--team', type=str, required=True, help='Team name')
    
    # Predict match command
    predict_match_parser = subparsers.add_parser('predict-match', help='Predict match performance')
    predict_match_parser.add_argument('--match', type=int, required=True, help='Match number')
    
    # List matches command
    subparsers.add_parser('list-matches', help='List all matches')
    
    # List team players command
    list_players_parser = subparsers.add_parser('list-players', help='List team players')
    list_players_parser.add_argument('--team', type=str, required=True, help='Team name')
    
    args = parser.parse_args()
    
    # Initialize system
    system = PlayerPredictionSystem()
    
    # Execute command
    if args.command == 'train':
        system.train_models(args.grid_search)
    
    elif args.command == 'predict-player':
        prediction = system.predict_player_performance(args.match, args.player)
        print(json.dumps(prediction, indent=4))
    
    elif args.command == 'predict-team':
        predictions = system.predict_team_performance(args.match, args.team)
        print(json.dumps(predictions, indent=4))
    
    elif args.command == 'predict-match':
        predictions = system.predict_match_performance(args.match)
        print(json.dumps(predictions, indent=4))
    
    elif args.command == 'list-matches':
        matches = system.get_match_info()
        print(json.dumps(matches, indent=4))
    
    elif args.command == 'list-players':
        players = system.get_team_players(args.team)
        print(json.dumps(players, indent=4))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
