# IPL Player Performance Prediction

A machine learning system that predicts player performance in IPL matches using historical data and real-time match conditions.

## Features

- Historical IPL data collection and processing
- Real-time match data collection from Cricbuzz API
- Player performance prediction using machine learning
- Interactive web interface for predictions
- Automated data collection and model updates

## Project Structure

```
IPL_Player_Prediction/
├── src/                      # Source code
│   ├── data_collection/      # Data collection modules
│   └── prediction/           # Prediction models
├── data/                     # Data storage
│   ├── historical/           # Historical IPL data
│   └── processed/           # Processed datasets
├── models/                   # Trained ML models
├── frontend/                 # React frontend
├── static/                   # Static files
├── app.py                    # Flask application
├── config.py                # Configuration
└── requirements.txt         # Python dependencies
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/IPL_Player_Prediction.git
cd IPL_Player_Prediction
```

2. Create and activate virtual environment:
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

5. Install frontend dependencies:
```bash
cd frontend
npm install
npm run build
cd ..
```

## Usage

1. Start the Flask backend:
```bash
python app.py
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Access the application at http://localhost:3000

## Data Collection

The system collects data from two main sources:
1. Historical IPL data (2008-2024)
2. Real-time match data from Cricbuzz API

Data collection is automated using the scheduler module:
```bash
python src/data_collection/scheduler.py
```

## Prediction System

The prediction system uses various features:
- Historical player performance
- Recent form
- Venue statistics
- Team composition
- Opposition strength
- Match conditions
- Player role and position

## API Endpoints

- `/api/matches`: Get upcoming matches
- `/api/match/<id>/teams`: Get teams for a match
- `/api/predict/team`: Get team predictions
- `/api/predict/player`: Get player predictions

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.