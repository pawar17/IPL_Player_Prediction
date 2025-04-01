# IPL Player Performance Prediction System

A comprehensive system for predicting IPL player performance using historical data, real-time updates, and weather impact analysis.

## Features

- Real-time data collection from multiple sources
- Advanced feature engineering
- Weather impact analysis on match outcomes
- RESTful API for predictions and statistics
- Automated data synchronization
- Comprehensive logging and monitoring

## Project Structure

```
src/
├── data_collection/
│   ├── cricket_data_scraper.py
│   └── weather_data_collector.py
├── feature_engineering/
│   └── feature_processor.py
├── models/
│   └── prediction_model.py
├── real_time/
│   └── updates_manager.py
├── api/
│   └── prediction_api.py
├── scripts/
│   ├── collect_venue_weather.py
│   ├── analyze_weather_impact.py
│   └── run_weather_pipeline.py
└── tests/
    ├── test_weather_collector.py
    └── run_weather_tests.py
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ipl-player-prediction.git
cd ipl-player-prediction
```

2. Create a virtual environment:
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
# Edit .env with your API keys and configuration
```

## Usage

### Weather Data Collection and Analysis

1. Collect weather data for all IPL venues:
```bash
python src/scripts/collect_venue_weather.py
```

2. Analyze weather impact on match outcomes:
```bash
python src/scripts/analyze_weather_impact.py
```

3. Run the complete weather pipeline:
```bash
python src/scripts/run_weather_pipeline.py
```

### API Server

1. Start the API server:
```bash
uvicorn src.api.prediction_api:app --reload
```

2. Access the API documentation:
```
http://localhost:8000/docs
```

## API Endpoints

### Predictions
- `POST /predict`: Get player performance predictions
- `GET /player/{player_id}/stats`: Get player statistics
- `GET /team/{team_id}/stats`: Get team statistics
- `GET /venue/{venue_id}/stats`: Get venue statistics
- `GET /match/{match_id}`: Get current match data
- `GET /health`: Health check endpoint

## Weather Impact Analysis

The system includes comprehensive weather impact analysis:

1. **Data Collection**
   - Real-time weather data from multiple sources (OpenWeather, WeatherAPI)
   - Historical weather data for past matches
   - Weather forecasts for upcoming matches

2. **Analysis Components**
   - Temperature impact on match outcomes
   - Humidity effects on player performance
   - Wind speed influence on bowling and batting
   - Rain probability impact on match conditions
   - Venue-specific weather patterns

3. **Visualizations**
   - Weather impact charts and graphs
   - Venue-specific weather patterns
   - Historical weather trends
   - Forecast visualizations

## Testing

1. Run weather data collection tests:
```bash
python src/tests/run_weather_tests.py
```

2. Run all tests with coverage:
```bash
pytest --cov=src tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Data sources: ESPNCricinfo, Cricbuzz, IPL official website
- Weather data: OpenWeather API, WeatherAPI
- Contributors and maintainers

## Contact

For support or queries, please open an issue in the repository or contact the maintainers. 