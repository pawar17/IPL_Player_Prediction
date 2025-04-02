# IPL Player Performance Prediction

A machine learning application that predicts player performance in IPL matches using historical data and real-time statistics.

## Features

- Live match data collection from Cricbuzz API
- Player performance prediction
- Historical data analysis
- Interactive dashboard
- Real-time updates

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- PostgreSQL (if running locally)
- Cricbuzz RapidAPI key

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ipl-player-prediction
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Running Locally

1. Start the database:
```bash
# If using Docker
docker-compose up -d db

# If running PostgreSQL locally
# Make sure PostgreSQL is running and create the database
createdb ipl_prediction
```

2. Initialize the database:
```bash
python init_db.py
```

3. Start the backend API:
```bash
python app.py
```

4. Start the frontend:
```bash
streamlit run frontend.py
```

## Docker Deployment

1. Build and start the containers:
```bash
docker-compose up -d
```

2. Initialize the database:
```bash
docker-compose exec app python init_db.py
```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Project Structure

```
ipl-player-prediction/
├── app.py                 # FastAPI backend
├── frontend.py           # Streamlit frontend
├── data_collector.py     # Data collection module
├── data_processor.py     # Data processing module
├── models.py             # Database models
├── database.py           # Database configuration
├── config.py             # Application configuration
├── migrations/           # Database migrations
├── data/                 # Data storage
│   ├── cache/           # Cache directory
│   ├── historical_matches/  # Historical match data
│   └── player_stats/    # Player statistics
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
└── .env                 # Environment variables
```

## API Endpoints

- `GET /matches` - Get all matches
- `GET /matches/{match_id}` - Get match details
- `GET /teams` - Get all teams
- `GET /teams/{team_id}` - Get team details
- `GET /players` - Get all players
- `GET /players/{player_id}` - Get player details
- `GET /predictions` - Get all predictions
- `POST /predict` - Make a new prediction
- `GET /live-data` - Get live match data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.