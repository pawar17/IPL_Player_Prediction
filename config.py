import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# API Keys (load from environment variables)
API_KEYS = {
    'cricapi': os.getenv('CRICAPI_KEY', 'YOUR_CRICAPI_KEY'),
    'espn': os.getenv('ESPN_API_KEY', 'YOUR_ESPN_API_KEY'),
    'cricbuzz': os.getenv('CRICBUZZ_API_KEY', 'YOUR_CRICBUZZ_API_KEY')
}

# API Endpoints
API_ENDPOINTS = {
    'cricbuzz': 'https://www.cricbuzz.com/api/cricket/match/',
    'espn': 'https://site.api.espn.com/apis/site/v2/sports/cricket/',
    'cricapi': 'https://api.cricapi.com/v1/'
}

# Cache settings
CACHE_DURATION = 3600  # 1 hour in seconds
CACHE_UPDATE_INTERVAL = 300  # 5 minutes

# Data collection settings
DATA_COLLECTION_INTERVAL = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 60  # 1 minute

# File paths
HISTORICAL_DATA_FILE = DATA_DIR / "historical_matches.csv"
PLAYER_STATS_FILE = DATA_DIR / "player_statistics.csv"
LIVE_MATCHES_CACHE = CACHE_DIR / "live_matches.json"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "data_collection.log"

# Data validation settings
VALIDATION_RULES = {
    'min_runs': 0,
    'max_runs': 500,
    'min_wickets': 0,
    'max_wickets': 10,
    'min_strike_rate': 0,
    'max_strike_rate': 300,
    'min_economy_rate': 0,
    'max_economy_rate': 20
}

# Team configurations
TEAMS = {
    'Mumbai Indians': {
        'id': 'MI',
        'home_ground': 'Wankhede Stadium',
        'coach': 'Mark Boucher'
    },
    'Chennai Super Kings': {
        'id': 'CSK',
        'home_ground': 'M. A. Chidambaram Stadium',
        'coach': 'Stephen Fleming'
    }
}

# Player roles
PLAYER_ROLES = [
    'Batsman',
    'Bowler',
    'All-Rounder',
    'Wicket Keeper',
    'Captain'
]

# Match importance levels
MATCH_IMPORTANCE = {
    'group_stage': 0.5,
    'playoff': 0.7,
    'semi_final': 0.8,
    'final': 1.0
}

# Pressure index factors
PRESSURE_FACTORS = {
    'home_match': 1.2,
    'away_match': 0.8,
    'rivalry_match': 1.3,
    'must_win': 1.4,
    'dead_rubber': 0.6
} 