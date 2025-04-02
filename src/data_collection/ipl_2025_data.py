"""
IPL 2025 data including schedule and team rosters
"""

import numpy as np
from datetime import datetime, timedelta

__all__ = ['schedule', 'teams', 'get_match', 'get_team', 'get_player']

# Sample schedule data
schedule = [
    {
        'match_id': 1,
        'date': '2025-03-23',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'venue': 'Wankhede Stadium',
        'match_type': 'league',
        'match_importance': 0.8
    },
    {
        'match_id': 2,
        'date': '2025-03-24',
        'team1': 'Royal Challengers Bangalore',
        'team2': 'Kolkata Knight Riders',
        'venue': 'M. Chinnaswamy Stadium',
        'match_type': 'league',
        'match_importance': 0.7
    }
]

# Sample team data with current rosters and recent performance
teams = [
    {
        'name': 'Mumbai Indians',
        'players': [
            {
                'name': 'Rohit Sharma',
                'id': 'RS001',
                'role': 'Batsman',
                'recent_stats': {
                    'batting_average': 45.5,
                    'strike_rate': 145.8,
                    'form': 0.85,
                    'consistency': 0.78
                },
                'recent_matches': [
                    {'runs': 65, 'wickets': 0, 'strike_rate': 155.2},
                    {'runs': 48, 'wickets': 0, 'strike_rate': 142.8},
                    {'runs': 12, 'wickets': 0, 'strike_rate': 120.0},
                    {'runs': 82, 'wickets': 0, 'strike_rate': 168.5},
                    {'runs': 34, 'wickets': 0, 'strike_rate': 138.2}
                ]
            },
            {
                'name': 'Jasprit Bumrah',
                'id': 'JB001',
                'role': 'Bowler',
                'recent_stats': {
                    'bowling_average': 22.4,
                    'economy_rate': 7.2,
                    'form': 0.92,
                    'consistency': 0.85
                },
                'recent_matches': [
                    {'wickets': 3, 'economy_rate': 6.8},
                    {'wickets': 2, 'economy_rate': 7.5},
                    {'wickets': 1, 'economy_rate': 8.2},
                    {'wickets': 4, 'economy_rate': 6.2},
                    {'wickets': 2, 'economy_rate': 7.4}
                ]
            }
        ]
    },
    {
        'name': 'Chennai Super Kings',
        'players': [
            {
                'name': 'MS Dhoni',
                'id': 'MSD001',
                'role': 'Wicket Keeper Batsman',
                'recent_stats': {
                    'batting_average': 38.2,
                    'strike_rate': 152.4,
                    'form': 0.78,
                    'consistency': 0.72
                },
                'recent_matches': [
                    {'runs': 45, 'wickets': 0, 'strike_rate': 180.0},
                    {'runs': 28, 'wickets': 0, 'strike_rate': 155.5},
                    {'runs': 18, 'wickets': 0, 'strike_rate': 138.4},
                    {'runs': 35, 'wickets': 0, 'strike_rate': 145.8},
                    {'runs': 42, 'wickets': 0, 'strike_rate': 162.5}
                ]
            },
            {
                'name': 'Ravindra Jadeja',
                'id': 'RJ001',
                'role': 'All-rounder',
                'recent_stats': {
                    'batting_average': 32.5,
                    'bowling_average': 24.8,
                    'strike_rate': 142.5,
                    'economy_rate': 7.8,
                    'form': 0.88,
                    'consistency': 0.82
                },
                'recent_matches': [
                    {'runs': 35, 'wickets': 2, 'strike_rate': 145.8, 'economy_rate': 7.2},
                    {'runs': 28, 'wickets': 1, 'strike_rate': 140.0, 'economy_rate': 8.4},
                    {'runs': 42, 'wickets': 3, 'strike_rate': 150.0, 'economy_rate': 6.8},
                    {'runs': 18, 'wickets': 2, 'strike_rate': 128.5, 'economy_rate': 7.5},
                    {'runs': 25, 'wickets': 1, 'strike_rate': 138.8, 'economy_rate': 8.2}
                ]
            }
        ]
    }
]

def get_match(match_id):
    """Get match data by match ID"""
    return next((m for m in schedule if m['match_id'] == match_id), None)

def get_team(team_name):
    """Get team data by team name"""
    return next((t for t in teams if t['name'] == team_name), None)

def get_player(player_id):
    """Get player data by player ID"""
    for team in teams:
        for player in team['players']:
            if player['id'] == player_id:
                return player
    return None 