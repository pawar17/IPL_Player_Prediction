import aiohttp
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import os
from dotenv import load_dotenv

class WeatherDataCollector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.weather_path = self.data_path / 'weather'
        self.weather_path.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize API keys
        self.openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
        self.weatherapi_key = os.getenv('WEATHERAPI_KEY')
        
        # Define weather API endpoints
        self.weather_apis = {
            'openweather': 'https://api.openweathermap.org/data/2.5',
            'weatherapi': 'http://api.weatherapi.com/v1'
        }
        
        # Rate limiting
        self.request_delay = 1  # seconds between requests
        self.last_request_time = 0
    
    async def collect_venue_weather(self, venue_id: str, date: datetime) -> Dict[str, Any]:
        """Collect weather data for a venue on a specific date"""
        try:
            # Get venue coordinates
            coordinates = await self._get_venue_coordinates(venue_id)
            if not coordinates:
                return {}
            
            # Collect weather data from multiple sources
            weather_data = {}
            
            # OpenWeather data
            openweather_data = await self._collect_openweather_data(
                coordinates['lat'],
                coordinates['lon'],
                date
            )
            if openweather_data:
                weather_data['openweather'] = openweather_data
            
            # WeatherAPI data
            weatherapi_data = await self._collect_weatherapi_data(
                coordinates['lat'],
                coordinates['lon'],
                date
            )
            if weatherapi_data:
                weather_data['weatherapi'] = weatherapi_data
            
            # Save weather data
            self._save_weather_data(venue_id, date, weather_data)
            
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Error collecting weather data: {str(e)}")
            return {}
    
    async def collect_forecast(self, venue_id: str, days: int = 5) -> Dict[str, Any]:
        """Collect weather forecast for a venue"""
        try:
            # Get venue coordinates
            coordinates = await self._get_venue_coordinates(venue_id)
            if not coordinates:
                return {}
            
            # Collect forecast data
            forecast_data = {}
            
            # OpenWeather forecast
            openweather_forecast = await self._collect_openweather_forecast(
                coordinates['lat'],
                coordinates['lon'],
                days
            )
            if openweather_forecast:
                forecast_data['openweather'] = openweather_forecast
            
            # WeatherAPI forecast
            weatherapi_forecast = await self._collect_weatherapi_forecast(
                coordinates['lat'],
                coordinates['lon'],
                days
            )
            if weatherapi_forecast:
                forecast_data['weatherapi'] = weatherapi_forecast
            
            # Save forecast data
            self._save_forecast_data(venue_id, forecast_data)
            
            return forecast_data
            
        except Exception as e:
            self.logger.error(f"Error collecting weather forecast: {str(e)}")
            return {}
    
    async def _get_venue_coordinates(self, venue_id: str) -> Optional[Dict[str, float]]:
        """Get venue coordinates from venue data"""
        try:
            # Load venue data
            venue_file = self.base_path / 'data' / 'scraped' / f'venue_{venue_id}_stats.json'
            if not venue_file.exists():
                return None
            
            with open(venue_file, 'r') as f:
                venue_data = json.load(f)
            
            # Extract coordinates from venue data
            if 'coordinates' in venue_data:
                return venue_data['coordinates']
            
            # If coordinates not found, try to get from venue name
            venue_name = venue_data.get('name', '')
            if venue_name:
                return await self._geocode_venue(venue_name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting venue coordinates: {str(e)}")
            return None
    
    async def _geocode_venue(self, venue_name: str) -> Optional[Dict[str, float]]:
        """Geocode venue name to get coordinates"""
        try:
            # Use OpenWeather geocoding API
            url = f"{self.weather_apis['openweather']}/weather"
            params = {
                'q': venue_name,
                'appid': self.openweather_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'lat': data['coord']['lat'],
                            'lon': data['coord']['lon']
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error geocoding venue: {str(e)}")
            return None
    
    async def _collect_openweather_data(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """Collect weather data from OpenWeather API"""
        try:
            # Calculate timestamp
            timestamp = int(date.timestamp())
            
            url = f"{self.weather_apis['openweather']}/onecall/timemachine"
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_openweather_data(data)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting OpenWeather data: {str(e)}")
            return {}
    
    async def _collect_weatherapi_data(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """Collect weather data from WeatherAPI"""
        try:
            url = self.weather_apis['weatherapi']
            params = {
                'key': self.weatherapi_key,
                'q': f"{lat},{lon}",
                'dt': date.strftime('%Y-%m-%d'),
                'aqi': 'no'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_weatherapi_data(data)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting WeatherAPI data: {str(e)}")
            return {}
    
    async def _collect_openweather_forecast(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Collect weather forecast from OpenWeather API"""
        try:
            url = f"{self.weather_apis['openweather']}/onecall"
            params = {
                'lat': lat,
                'lon': lon,
                'exclude': 'minutely,hourly,alerts',
                'appid': self.openweather_api_key,
                'units': 'metric'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_openweather_forecast(data)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting OpenWeather forecast: {str(e)}")
            return {}
    
    async def _collect_weatherapi_forecast(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Collect weather forecast from WeatherAPI"""
        try:
            url = f"{self.weather_apis['weatherapi']}/forecast.json"
            params = {
                'key': self.weatherapi_key,
                'q': f"{lat},{lon}",
                'days': days,
                'aqi': 'no'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_weatherapi_forecast(data)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error collecting WeatherAPI forecast: {str(e)}")
            return {}
    
    def _process_openweather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenWeather API response"""
        try:
            current = data['current']
            
            return {
                'temperature': current['temp'],
                'humidity': current['humidity'],
                'wind_speed': current['wind_speed'],
                'wind_direction': current['wind_deg'],
                'pressure': current['pressure'],
                'visibility': current['visibility'],
                'clouds': current['clouds'],
                'rain_probability': current.get('rain', {}).get('1h', 0) / 100,
                'weather_description': current['weather'][0]['description'],
                'timestamp': current['dt']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing OpenWeather data: {str(e)}")
            return {}
    
    def _process_weatherapi_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WeatherAPI response"""
        try:
            current = data['current']
            
            return {
                'temperature': current['temp_c'],
                'humidity': current['humidity'],
                'wind_speed': current['wind_kph'],
                'wind_direction': current['wind_degree'],
                'pressure': current['pressure_mb'],
                'visibility': current['vis_km'],
                'clouds': current['cloud'],
                'rain_probability': current.get('chance_of_rain', 0) / 100,
                'weather_description': current['condition']['text'],
                'timestamp': current['last_updated_epoch']
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WeatherAPI data: {str(e)}")
            return {}
    
    def _process_openweather_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process OpenWeather forecast response"""
        try:
            daily = data['daily']
            
            return {
                'daily_forecast': [
                    {
                        'date': day['dt'],
                        'temperature': {
                            'min': day['temp']['min'],
                            'max': day['temp']['max']
                        },
                        'humidity': day['humidity'],
                        'wind_speed': day['wind_speed'],
                        'rain_probability': day.get('rain', 0) / 100,
                        'weather_description': day['weather'][0]['description']
                    }
                    for day in daily
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing OpenWeather forecast: {str(e)}")
            return {}
    
    def _process_weatherapi_forecast(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process WeatherAPI forecast response"""
        try:
            forecast = data['forecast']['forecastday']
            
            return {
                'daily_forecast': [
                    {
                        'date': day['date_epoch'],
                        'temperature': {
                            'min': day['day']['mintemp_c'],
                            'max': day['day']['maxtemp_c']
                        },
                        'humidity': day['day']['avghumidity'],
                        'wind_speed': day['day']['maxwind_kph'],
                        'rain_probability': day['day']['daily_chance_of_rain'] / 100,
                        'weather_description': day['day']['condition']['text']
                    }
                    for day in forecast
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing WeatherAPI forecast: {str(e)}")
            return {}
    
    def _save_weather_data(self, venue_id: str, date: datetime, data: Dict[str, Any]):
        """Save weather data to file"""
        try:
            date_str = date.strftime('%Y%m%d')
            file_path = self.weather_path / f'venue_{venue_id}_{date_str}.json'
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved weather data for venue {venue_id} on {date_str}")
            
        except Exception as e:
            self.logger.error(f"Error saving weather data: {str(e)}")
    
    def _save_forecast_data(self, venue_id: str, data: Dict[str, Any]):
        """Save forecast data to file"""
        try:
            file_path = self.weather_path / f'venue_{venue_id}_forecast.json'
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Saved forecast data for venue {venue_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving forecast data: {str(e)}") 