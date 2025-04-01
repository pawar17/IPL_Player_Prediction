import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import json
from src.data_collection.weather_data_collector import WeatherDataCollector

@pytest.fixture
def weather_collector():
    return WeatherDataCollector()

@pytest.fixture
def sample_venue_id():
    return "wankhede"

@pytest.fixture
def sample_date():
    return datetime.now()

@pytest.mark.asyncio
async def test_collect_venue_weather(weather_collector, sample_venue_id, sample_date):
    """Test collecting weather data for a venue"""
    weather_data = await weather_collector.collect_venue_weather(sample_venue_id, sample_date)
    
    # Check if weather data was collected
    assert weather_data is not None
    assert isinstance(weather_data, dict)
    
    # Check if data was saved
    date_str = sample_date.strftime('%Y%m%d')
    file_path = weather_collector.weather_path / f'venue_{sample_venue_id}_{date_str}.json'
    assert file_path.exists()
    
    # Load and verify saved data
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data == weather_data

@pytest.mark.asyncio
async def test_collect_forecast(weather_collector, sample_venue_id):
    """Test collecting weather forecast for a venue"""
    forecast_data = await weather_collector.collect_forecast(sample_venue_id, days=5)
    
    # Check if forecast data was collected
    assert forecast_data is not None
    assert isinstance(forecast_data, dict)
    
    # Check if data was saved
    file_path = weather_collector.weather_path / f'venue_{sample_venue_id}_forecast.json'
    assert file_path.exists()
    
    # Load and verify saved data
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    assert saved_data == forecast_data

@pytest.mark.asyncio
async def test_get_venue_coordinates(weather_collector, sample_venue_id):
    """Test getting venue coordinates"""
    coordinates = await weather_collector._get_venue_coordinates(sample_venue_id)
    
    # Check if coordinates were retrieved
    assert coordinates is not None
    assert isinstance(coordinates, dict)
    assert 'lat' in coordinates
    assert 'lon' in coordinates
    assert isinstance(coordinates['lat'], float)
    assert isinstance(coordinates['lon'], float)

@pytest.mark.asyncio
async def test_geocode_venue(weather_collector):
    """Test geocoding venue name"""
    venue_name = "Wankhede Stadium, Mumbai"
    coordinates = await weather_collector._geocode_venue(venue_name)
    
    # Check if coordinates were retrieved
    assert coordinates is not None
    assert isinstance(coordinates, dict)
    assert 'lat' in coordinates
    assert 'lon' in coordinates
    assert isinstance(coordinates['lat'], float)
    assert isinstance(coordinates['lon'], float)

@pytest.mark.asyncio
async def test_collect_openweather_data(weather_collector):
    """Test collecting data from OpenWeather API"""
    lat, lon = 19.0896, 72.8278  # Wankhede Stadium coordinates
    date = datetime.now()
    
    data = await weather_collector._collect_openweather_data(lat, lon, date)
    
    # Check if data was collected
    assert data is not None
    assert isinstance(data, dict)
    
    # Check required fields
    required_fields = [
        'temperature', 'humidity', 'wind_speed', 'wind_direction',
        'pressure', 'visibility', 'clouds', 'rain_probability',
        'weather_description', 'timestamp'
    ]
    for field in required_fields:
        assert field in data

@pytest.mark.asyncio
async def test_collect_weatherapi_data(weather_collector):
    """Test collecting data from WeatherAPI"""
    lat, lon = 19.0896, 72.8278  # Wankhede Stadium coordinates
    date = datetime.now()
    
    data = await weather_collector._collect_weatherapi_data(lat, lon, date)
    
    # Check if data was collected
    assert data is not None
    assert isinstance(data, dict)
    
    # Check required fields
    required_fields = [
        'temperature', 'humidity', 'wind_speed', 'wind_direction',
        'pressure', 'visibility', 'clouds', 'rain_probability',
        'weather_description', 'timestamp'
    ]
    for field in required_fields:
        assert field in data

@pytest.mark.asyncio
async def test_collect_openweather_forecast(weather_collector):
    """Test collecting forecast from OpenWeather API"""
    lat, lon = 19.0896, 72.8278  # Wankhede Stadium coordinates
    days = 5
    
    data = await weather_collector._collect_openweather_forecast(lat, lon, days)
    
    # Check if data was collected
    assert data is not None
    assert isinstance(data, dict)
    assert 'daily_forecast' in data
    
    # Check forecast data structure
    forecast = data['daily_forecast']
    assert isinstance(forecast, list)
    assert len(forecast) == days
    
    for day in forecast:
        assert 'date' in day
        assert 'temperature' in day
        assert 'min' in day['temperature']
        assert 'max' in day['temperature']
        assert 'humidity' in day
        assert 'wind_speed' in day
        assert 'rain_probability' in day
        assert 'weather_description' in day

@pytest.mark.asyncio
async def test_collect_weatherapi_forecast(weather_collector):
    """Test collecting forecast from WeatherAPI"""
    lat, lon = 19.0896, 72.8278  # Wankhede Stadium coordinates
    days = 5
    
    data = await weather_collector._collect_weatherapi_forecast(lat, lon, days)
    
    # Check if data was collected
    assert data is not None
    assert isinstance(data, dict)
    assert 'daily_forecast' in data
    
    # Check forecast data structure
    forecast = data['daily_forecast']
    assert isinstance(forecast, list)
    assert len(forecast) == days
    
    for day in forecast:
        assert 'date' in day
        assert 'temperature' in day
        assert 'min' in day['temperature']
        assert 'max' in day['temperature']
        assert 'humidity' in day
        assert 'wind_speed' in day
        assert 'rain_probability' in day
        assert 'weather_description' in day

@pytest.mark.asyncio
async def test_error_handling(weather_collector):
    """Test error handling for invalid inputs"""
    # Test with invalid venue ID
    weather_data = await weather_collector.collect_venue_weather("invalid_venue", datetime.now())
    assert weather_data == {}
    
    # Test with invalid coordinates
    data = await weather_collector._collect_openweather_data(0, 0, datetime.now())
    assert data == {}
    
    # Test with invalid date
    data = await weather_collector._collect_weatherapi_data(0, 0, datetime.now() + timedelta(days=365))
    assert data == {} 