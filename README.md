# IPL Player Performance Prediction System

A full-stack web application that predicts player performance in IPL matches using historical data, real-time statistics, and machine learning models.

## Project Overview

This system combines historical IPL data with real-time statistics from Cricbuzz to predict player performance in upcoming matches. The application features a Flask backend API and a React frontend interface.

### Key Features

- Real-time data collection from Cricbuzz API
- Historical data analysis from IPL datasets
- Player performance prediction using machine learning
- Interactive web interface for match selection and prediction viewing
- Automated data collection and processing pipeline
- Regular updates of player statistics and team information

## Technology Stack

### Backend
- Python 3.9
- Flask (Web Framework)
- Pandas (Data Processing)
- Scikit-learn (Machine Learning)
- Gunicorn (Production Server)

### Frontend
- React.js
- Material-UI
- Axios (API Client)

### Data Sources
- Cricbuzz RapidAPI
- Historical IPL datasets (CSV files)
- Real-time match statistics

## Project Structure

```
IPL_Player_Prediction/
├── app.py                 # Flask backend application
├── frontend/             # React frontend application
│   ├── src/
│   │   ├── api.js       # API client
│   │   └── components/  # React components
│   └── package.json
├── src/
│   ├── data_collection/  # Data collection modules
│   │   └── ipl_2025_data.py
│   └── predict_player_performance.py
├── data/                 # Data storage
│   ├── historical/      # Historical IPL data
│   └── processed/       # Processed data for predictions
├── requirements.txt     # Python dependencies
└── Procfile            # Production configuration
```

## Data Sources and Processing

### Historical Data
- IPL match results (2008-2024)
- Player statistics
- Team performance metrics
- Venue information

### Real-time Data (Cricbuzz API)
- Live match statistics
- Player rankings
- Team rankings
- Trending players
- Recent match data

### Data Processing Pipeline
1. Data Collection
   - Historical data loading
   - Real-time data fetching
   - Data validation and cleaning

2. Feature Engineering
   - Match importance calculation
   - Pressure index computation
   - Venue factor analysis
   - Team and player form calculation
   - Consistency scoring

3. Prediction Model
   - Player performance prediction
   - Match outcome analysis
   - Team composition optimization

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/IPL_Player_Prediction.git
cd IPL_Player_Prediction
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up frontend:
```bash
cd frontend
npm install
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Cricbuzz API key and other configurations
```

## Running the Application

### Development Mode

1. Start the Flask backend:
```bash
python app.py
```

2. Start the React frontend:
```bash
cd frontend
npm start
```

### Production Mode

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Start the production server:
```bash
gunicorn app:app
```

## Deployment

The application is configured for deployment on Azure App Service. See `deploy_azure.ps1` for deployment instructions.

## API Endpoints

### Match Endpoints
- `GET /api/matches` - Get all IPL 2025 matches
- `GET /api/matches/<match_id>/predictions` - Get predictions for a specific match

### Player Endpoints
- `GET /api/players` - Get all players with statistics
- `GET /api/players/<player_id>/predictions` - Get predictions for a specific player

### Team Endpoints
- `GET /api/teams` - Get all teams and their players

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Cricbuzz API for providing real-time cricket data
- IPL datasets for historical data
- Contributors and maintainers of all used libraries and frameworks