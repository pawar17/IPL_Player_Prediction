from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from src.data_collection.data_collector import DataCollector
from src.data_collection.data_processor import DataProcessor
from src.predict_player_performance import predict_player_performance
import os
from logging_config import logger

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Log startup information
logger.info("Starting application...")
logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir('.')}")

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
    matches = load_ipl_matches()
    return jsonify(matches)

@app.route('/api/matches/<match_id>/predictions')
def get_match_predictions(match_id):
    """Get predictions for all players in a specific match"""
    try:
        # Get match details
        matches = load_ipl_matches()
        match = next((m for m in matches if m['match_id'] == match_id), None)
        
        if not match:
            return jsonify({"error": "Match not found"}), 404
            
        # Get predictions for each player
        predictions = []
        for team in [match['team1'], match['team2']]:
            team_data = next((t for t in collector.teams if t['name'] == team), None)
            if team_data:
                for player in team_data['players']:
                    # Get player prediction
                    prediction = predict_player_performance(
                        player_id=player['id'],
                        match_id=match_id,
                        historical_data=processor.get_historical_data(),
                        current_form=processor.get_player_form(player['id'])
                    )
                    predictions.append({
                        'player': player,
                        'prediction': prediction
                    })
        
        return jsonify(predictions)
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
            prediction = predict_player_performance(
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
    """Get all teams and their players"""
    teams = collector.teams
    return jsonify(teams)

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
            "environment": os.environ.get('FLASK_ENV', 'production')
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    try:
        # Create necessary directories
        Path('data').mkdir(exist_ok=True)
        logger.info("Created data directory")
        
        # Run the Flask app
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting Flask application on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise 