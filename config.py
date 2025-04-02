import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# API Keys
API_KEYS = {
    'cricbuzz': os.getenv('CRICBUZZ_RAPIDAPI_KEY', 'e25a618be3msh09379c7fc6ba226p187977jsnd56e4bd0e1c4')
}

# Cricbuzz API Configuration
CRICBUZZ_API = {
    'base_url': 'https://cricbuzz-cricket.p.rapidapi.com',
    'host': 'cricbuzz-cricket.p.rapidapi.com'
}

# Cache settings
CACHE_DURATION = 3600  # 1 hour in seconds
CACHE_UPDATE_INTERVAL = 300  # 5 minutes in seconds

# Data collection settings
DATA_COLLECTION_INTERVAL = 300  # 5 minutes in seconds
MAX_RETRIES = 3
RETRY_DELAY = 60  # 1 minute in seconds

# File paths
HISTORICAL_DATA_FILE = DATA_DIR / "historical_matches.csv"
PLAYER_STATS_FILE = DATA_DIR / "player_stats.json"
LIVE_MATCHES_CACHE = CACHE_DIR / "live_matches.json"

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "data_collection.log"

# Data validation rules
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
    "Mumbai Indians": {
        "id": "9",
        "home_ground": "Wankhede Stadium",
        "coach": "Mahela Jayawardene"
    },
    "Chennai Super Kings": {
        "id": "4",
        "home_ground": "M. A. Chidambaram Stadium",
        "coach": "Stephen Fleming"
    }
}

# Player roles
PLAYER_ROLES = [
    "Batsman",
    "Bowler",
    "All-Rounder",
    "Wicket Keeper"
]

# Match importance levels
MATCH_IMPORTANCE = {
    "group_stage": 1,
    "playoff": 2,
    "semi_final": 3,
    "final": 4
}

# Pressure index factors
PRESSURE_FACTORS = {
    "high_stakes": 1.5,
    "rivalry": 1.3,
    "home_advantage": 1.2,
    "away_disadvantage": 0.8,
    "must_win": 1.4
} 