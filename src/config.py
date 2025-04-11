from pathlib import Path

# Directory paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
HISTORICAL_DATA_FILE = DATA_DIR / 'historical' / 'matches.csv'
PLAYER_STATS_FILE = DATA_DIR / 'processed' / 'player_stats.csv'

# Validation rules
VALIDATION_RULES = {
    'batting': {
        'min_average': 0,
        'max_average': 100,
        'min_strike_rate': 0,
        'max_strike_rate': 300
    },
    'bowling': {
        'min_average': 0,
        'max_average': 100,
        'min_economy': 0,
        'max_economy': 20
    }
}

# Team names
TEAMS = [
    'Royal Challengers Bangalore',
    'Mumbai Indians',
    'Chennai Super Kings',
    'Kolkata Knight Riders',
    'Delhi Capitals',
    'Punjab Kings',
    'Rajasthan Royals',
    'Sunrisers Hyderabad',
    'Gujarat Titans',
    'Lucknow Super Giants'
]

# Player roles
PLAYER_ROLES = ['batsman', 'bowler', 'all_rounder', 'wicket_keeper'] 