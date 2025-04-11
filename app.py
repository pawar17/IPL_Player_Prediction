from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.data_collection.data_collector import DataCollector
from src.data_collection.data_processor import DataProcessor
from src.prediction.predict_player_performance import PlayerPredictionSystem
import os
from logging_config import logger
from src.data_collection.cricbuzz_collector import CricbuzzCollector

# Initialize Flask app with correct static folder path
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app = Flask(__name__, static_folder=static_folder)
CORS(app)

# Log startup information
logger.info("Starting application...")
logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Static folder: {static_folder}")
logger.info(f"Directory contents: {os.listdir('.')}")
logger.info(f"Static folder contents: {os.listdir(static_folder) if os.path.exists(static_folder) else 'Static folder not found'}")

# Initialize data collector and processor
try:
    collector = DataCollector()
    processor = DataProcessor()
    logger.info("Successfully initialized DataCollector and DataProcessor")
except Exception as e:
    logger.error(f"Failed to initialize data components: {str(e)}")
    raise

def load_ipl_matches():
    """Load IPL 2025 matches from the data file"""
    try:
        with open('src/data_collection/ipl_2025_data.py', 'r') as f:
            content = f.read()
            # Extract matches data from the file
            matches = eval(content.split('matches = ')[1].split('\n')[0])
            logger.info(f"Successfully loaded {len(matches)} matches")
            return matches
    except Exception as e:
        logger.error(f"Error loading matches: {str(e)}")
        return []

@app.route('/api/matches')
def get_matches():
    """Get all IPL 2025 matches"""
    try:
        matches = load_ipl_matches()
        return jsonify(matches)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/matches/<int:match_no>/predictions')
def get_match_predictions(match_no):
    """Get predictions for all players in a specific match"""
    try:
        # Get match details
        match = get_match(match_no)
        if not match:
            return jsonify({"error": "Match not found"}), 404
            
        # Get team details
        team1 = get_team(match['team1'])
        team2 = get_team(match['team2'])
        
        if not team1 or not team2:
            return jsonify({"error": "Team data not found"}), 404
            
        # Get match squads from Cricbuzz
        cricbuzz = CricbuzzCollector()
        squads = cricbuzz.get_match_squads(match_no)
        
        # Get predictions for each player
        predictions = []
        
        # Team 1 predictions
        for player in team1['players']:
            # Check if player is in playing XI
            is_playing = player['name'] in squads['team1']['playing_xi']
            
            if is_playing:
                # Get player's current form
                current_form = cricbuzz.get_player_stats(player['name'])
                
                # Get historical data
                historical_data = processor.get_player_historical_data(player['id'])
                
                # Generate prediction
                prediction = PlayerPredictionSystem.predict_player_performance(
                    player_id=player['id'],
                    match_id=match_no,
                    historical_data=historical_data,
                    current_form=current_form
                )
                
                predictions.append({
                    'player': player,
                    'team': match['team1'],
                    'is_playing': True,
                    'prediction': prediction
                })
            else:
                predictions.append({
                    'player': player,
                    'team': match['team1'],
                    'is_playing': False,
                    'prediction': None
                })
        
        # Team 2 predictions
        for player in team2['players']:
            # Check if player is in playing XI
            is_playing = player['name'] in squads['team2']['playing_xi']
            
            if is_playing:
                # Get player's current form
                current_form = cricbuzz.get_player_stats(player['name'])
                
                # Get historical data
                historical_data = processor.get_player_historical_data(player['id'])
                
                # Generate prediction
                prediction = PlayerPredictionSystem.predict_player_performance(
                    player_id=player['id'],
                    match_id=match_no,
                    historical_data=historical_data,
                    current_form=current_form
                )
                
                predictions.append({
                    'player': player,
                    'team': match['team2'],
                    'is_playing': True,
                    'prediction': prediction
                })
            else:
                predictions.append({
                    'player': player,
                    'team': match['team2'],
                    'is_playing': False,
                    'prediction': None
                })
        
        # Get team news
        team1_news = cricbuzz.get_team_news(match['team1'])
        team2_news = cricbuzz.get_team_news(match['team2'])
        
        return jsonify({
            'match': match,
            'predictions': predictions,
            'team_news': {
                match['team1']: team1_news,
                match['team2']: team2_news
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/players/<player_id>/predictions')
def get_player_predictions(player_id):
    """Get predictions for a specific player"""
    try:
        # Get player's recent matches
        recent_matches = processor.get_player_recent_matches(player_id)
        
        # Get predictions for each match
        predictions = []
        for match in recent_matches:
            prediction = PlayerPredictionSystem.predict_player_performance(
                player_id=player_id,
                match_id=match['match_id'],
                historical_data=processor.get_historical_data(),
                current_form=processor.get_player_form(player_id)
            )
            predictions.append({
                'match': match,
                'prediction': prediction
            })
        
        return jsonify(predictions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/teams')
def get_teams():
    """Get all IPL 2025 teams"""
    try:
        teams = get_all_teams()
        return jsonify(teams)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/players')
def get_players():
    """Get all players with their statistics"""
    players = []
    for team in collector.teams:
        for player in team['players']:
            player_data = {
                'id': player['id'],
                'name': player['name'],
                'team': team['name'],
                'role': player['role'],
                'stats': processor.get_player_stats(player['id']),
                'form': processor.get_player_form(player['id'])
            }
            players.append(player_data)
    return jsonify(players)

@app.route('/api/health')
def health_check():
    """Check API health"""
    try:
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.environ.get('FLASK_ENV', 'production'),
            "static_folder": static_folder,
            "static_folder_exists": os.path.exists(static_folder)
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Serve React App - Updated to handle all routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    try:
        logger.info(f"Serving path: {path}")
        logger.info(f"Static folder: {app.static_folder}")
        logger.info(f"Static folder exists: {os.path.exists(app.static_folder)}")
        
        # If the path starts with /api, it's an API request
        if path.startswith('api/'):
            logger.info(f"API request: {path}")
            return handle_api_request(path)
            
        # For all other paths, try to serve the file
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            logger.info(f"Serving file: {path}")
            return send_from_directory(app.static_folder, path)
        else:
            # For all other routes, serve index.html
            logger.info("Serving index.html for client-side routing")
            return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        logger.error(f"Error serving static file: {str(e)}")
        return jsonify({"error": str(e)}), 500

def handle_api_request(path):
    """Handle API requests"""
    try:
        # Remove 'api/' prefix
        api_path = path[4:]
        
        # Map API paths to functions
        api_routes = {
            'matches': get_matches,
            'teams': get_teams,
            'players': get_players,
            'health': health_check
        }
        
        # Handle dynamic routes
        if api_path.startswith('matches/'):
            match_id = api_path.split('/')[1]
            if len(api_path.split('/')) > 2 and api_path.split('/')[2] == 'predictions':
                return get_match_predictions(match_id)
            return jsonify({"error": "Invalid match endpoint"}), 404
            
        if api_path.startswith('players/'):
            player_id = api_path.split('/')[1]
            if len(api_path.split('/')) > 2 and api_path.split('/')[2] == 'predictions':
                return get_player_predictions(player_id)
            return jsonify({"error": "Invalid player endpoint"}), 404
            
        # Handle static routes
        if api_path in api_routes:
            return api_routes[api_path]()
            
        return jsonify({"error": "Endpoint not found"}), 404
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    try:
        # Create necessary directories
        Path('data').mkdir(exist_ok=True)
        logger.info("Created data directory")
        
        # Run the Flask app
        port = int(os.environ.get('PORT', 8000))
        logger.info(f"Starting Flask application on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise 