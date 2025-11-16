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
from src.data.ipl_2025_data import IPL_2025_MATCHES, get_match_by_id

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
        from src.data.ipl_2025_data import IPL_2025_MATCHES
        logger.info(f"Successfully loaded {len(IPL_2025_MATCHES)} matches")
        return IPL_2025_MATCHES
    except Exception as e:
        logger.error(f"Error loading matches: {str(e)}")
        return []

def get_match(match_no):
    """Get match by match number"""
    try:
        from src.data.ipl_2025_data import get_match_by_id
        return get_match_by_id(match_no)
    except Exception as e:
        logger.error(f"Error getting match {match_no}: {str(e)}")
        return None

def get_team(team_name):
    """Get team data by team name"""
    try:
        from src.data.team_rosters import get_team_roster
        roster = get_team_roster(team_name)
        if roster:
            return {
                'name': team_name,
                'players': roster.get('players', [])
            }
        return None
    except Exception as e:
        logger.error(f"Error getting team {team_name}: {str(e)}")
        return None

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
        import random

        # Get match details
        match = get_match(match_no)
        if not match:
            return jsonify({"error": "Match not found"}), 404

        # Get team rosters
        from src.data.team_rosters import get_team_roster
        team1_roster = get_team_roster(match['team1'])
        team2_roster = get_team_roster(match['team2'])

        if not team1_roster or not team2_roster:
            return jsonify({"error": "Team data not found"}), 404

        # Helper function to generate mock predictions
        def generate_player_prediction(player_name, role):
            # Generate realistic predictions based on role
            if role in ['batsman', 'batsmen']:
                return {
                    'batting': {
                        'value': random.randint(15, 65),
                        'strike_rate': round(random.uniform(110.0, 165.0), 2)
                    },
                    'bowling': {
                        'value': 0,
                        'economy_rate': 0.0
                    }
                }
            elif role in ['bowler', 'bowlers']:
                return {
                    'batting': {
                        'value': random.randint(0, 15),
                        'strike_rate': round(random.uniform(80.0, 130.0), 2)
                    },
                    'bowling': {
                        'value': random.randint(0, 3),
                        'economy_rate': round(random.uniform(6.5, 11.0), 2)
                    }
                }
            else:  # all_rounders
                return {
                    'batting': {
                        'value': random.randint(20, 50),
                        'strike_rate': round(random.uniform(120.0, 150.0), 2)
                    },
                    'bowling': {
                        'value': random.randint(0, 2),
                        'economy_rate': round(random.uniform(7.0, 10.0), 2)
                    }
                }

        # Generate predictions for both teams
        predictions = []

        # Team 1 predictions
        for role_type in ['batsmen', 'bowlers', 'all_rounders']:
            players = team1_roster.get(role_type, [])
            for player_name in players[:11]:  # Limit to likely playing XI
                predictions.append({
                    'player': {
                        'name': player_name,
                        'role': role_type.replace('_', ' ').title()
                    },
                    'team': match['team1'],
                    'prediction': generate_player_prediction(player_name, role_type)
                })

        # Team 2 predictions
        for role_type in ['batsmen', 'bowlers', 'all_rounders']:
            players = team2_roster.get(role_type, [])
            for player_name in players[:11]:  # Limit to likely playing XI
                predictions.append({
                    'player': {
                        'name': player_name,
                        'role': role_type.replace('_', ' ').title()
                    },
                    'team': match['team2'],
                    'prediction': generate_player_prediction(player_name, role_type)
                })

        return jsonify({
            'match': match,
            'predictions': predictions,
            'team_news': {
                match['team1']: [],
                match['team2']: []
            }
        })

    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
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
        from src.data.team_rosters import TEAM_ROSTERS
        teams = []
        for team_name, roster in TEAM_ROSTERS.items():
            teams.append({
                'name': team_name,
                'players': roster.get('players', [])
            })
        return jsonify(teams)
    except Exception as e:
        logger.error(f"Error getting teams: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/team/<team_shortname>/roster')
def get_team_roster_api(team_shortname):
    """Get complete roster for a specific team"""
    try:
        from src.data.team_rosters import TEAM_ROSTERS

        # Map team short names to full names
        team_mapping = {
            'CSK': 'Chennai Super Kings',
            'MI': 'Mumbai Indians',
            'RCB': 'Royal Challengers Bangalore',
            'KKR': 'Kolkata Knight Riders',
            'DC': 'Delhi Capitals',
            'PBKS': 'Punjab Kings',
            'RR': 'Rajasthan Royals',
            'SRH': 'Sunrisers Hyderabad',
            'GT': 'Gujarat Titans'
        }

        team_name = team_mapping.get(team_shortname.upper())
        if not team_name:
            return jsonify({"error": "Team not found"}), 404

        roster = TEAM_ROSTERS.get(team_name)
        if not roster:
            return jsonify({"error": "Roster not found"}), 404

        # Format roster data for frontend
        formatted_roster = []

        # Add batsmen
        for player in roster.get('batsmen', []):
            formatted_roster.append({
                'name': player,
                'role': 'Batsman'
            })

        # Add bowlers
        for player in roster.get('bowlers', []):
            formatted_roster.append({
                'name': player,
                'role': 'Bowler'
            })

        # Add all-rounders
        for player in roster.get('all_rounders', []):
            formatted_roster.append({
                'name': player,
                'role': 'All-Rounder'
            })

        return jsonify(formatted_roster)
    except Exception as e:
        logger.error(f"Error getting team roster: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/team/<team_shortname>/predictions')
def get_team_predictions_api(team_shortname):
    """Get season predictions for a specific team"""
    try:
        import random

        # Map team short names to full names
        team_mapping = {
            'CSK': 'Chennai Super Kings',
            'MI': 'Mumbai Indians',
            'RCB': 'Royal Challengers Bangalore',
            'KKR': 'Kolkata Knight Riders',
            'DC': 'Delhi Capitals',
            'PBKS': 'Punjab Kings',
            'RR': 'Rajasthan Royals',
            'SRH': 'Sunrisers Hyderabad',
            'GT': 'Gujarat Titans'
        }

        team_name = team_mapping.get(team_shortname.upper())
        if not team_name:
            return jsonify({"error": "Team not found"}), 404

        # Generate mock season predictions
        # In production, these would come from ML models
        predictions = {
            'wins': random.randint(6, 12),
            'losses': random.randint(2, 8),
            'position': random.randint(1, 8),
            'totalMatches': 14,
            'topScorer': 'Player TBD',
            'topWicketTaker': 'Player TBD',
            'averageScore': random.randint(160, 190),
            'winPercentage': round(random.uniform(40.0, 80.0), 1)
        }

        return jsonify(predictions)
    except Exception as e:
        logger.error(f"Error getting team predictions: {str(e)}")
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

        if api_path.startswith('team/'):
            parts = api_path.split('/')
            if len(parts) >= 3:
                team_shortname = parts[1]
                endpoint = parts[2]
                if endpoint == 'roster':
                    return get_team_roster_api(team_shortname)
                elif endpoint == 'predictions':
                    return get_team_predictions_api(team_shortname)
            return jsonify({"error": "Invalid team endpoint"}), 404

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
        port = int(os.environ.get('PORT', 5000))  # Changed to 5000 to match frontend expectations
        logger.info(f"Starting Flask application on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)  # Enable debug mode for development
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise 