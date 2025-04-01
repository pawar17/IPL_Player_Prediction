import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv
import os

# Import collectors
from collect_historical_data import HistoricalDataCollector
from collect_venue_weather import WeatherDataCollector
from collect_venue_stats import VenueStatsCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCollectionOrchestrator:
    def __init__(self):
        load_dotenv()
        self.historical_collector = HistoricalDataCollector()
        self.weather_collector = WeatherDataCollector()
        self.venue_stats_collector = VenueStatsCollector()
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def collect_historical_data(self, start_season: int, end_season: int):
        """Collect historical match and player data."""
        try:
            logger.info("Starting historical data collection...")
            await self.historical_collector.collect_all_data(start_season, end_season)
            logger.info("Historical data collection completed")
        except Exception as e:
            logger.error(f"Error in historical data collection: {str(e)}")

    async def collect_weather_data(self):
        """Collect weather data for all venues."""
        try:
            logger.info("Starting weather data collection...")
            await self.weather_collector.collect_all_venue_weather()
            logger.info("Weather data collection completed")
        except Exception as e:
            logger.error(f"Error in weather data collection: {str(e)}")

    def analyze_venue_stats(self):
        """Analyze venue-specific statistics."""
        try:
            logger.info("Starting venue statistics analysis...")
            matches = self.venue_stats_collector.load_match_data()
            
            if not matches:
                logger.error("No match data found for venue analysis")
                return
            
            venue_stats = self.venue_stats_collector.analyze_venue_stats(matches)
            self.venue_stats_collector.save_venue_stats(venue_stats)
            self.venue_stats_collector.generate_venue_report(venue_stats)
            logger.info("Venue statistics analysis completed")
        except Exception as e:
            logger.error(f"Error in venue statistics analysis: {str(e)}")

    def generate_collection_report(self):
        """Generate a summary report of the data collection process."""
        report = []
        report.append("Data Collection Report")
        report.append("=" * 50)
        report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Count files in each directory
        historical_dir = Path("data/historical")
        weather_dir = Path("data/weather")
        venue_stats_dir = Path("data/venue_stats")
        
        report.append("\nHistorical Data:")
        if historical_dir.exists():
            match_files = list(historical_dir.glob("match_*.json"))
            player_files = list(historical_dir.glob("player_*.json"))
            report.append(f"Total Matches: {len(match_files)}")
            report.append(f"Total Players: {len(player_files)}")
        
        report.append("\nWeather Data:")
        if weather_dir.exists():
            weather_files = list(weather_dir.glob("*.json"))
            report.append(f"Total Venues with Weather Data: {len(weather_files)}")
        
        report.append("\nVenue Statistics:")
        if venue_stats_dir.exists():
            venue_files = list(venue_stats_dir.glob("venue_*.json"))
            report.append(f"Total Venues Analyzed: {len(venue_files)}")
        
        # Save report
        report_file = self.data_dir / "collection_report.txt"
        with open(report_file, 'w') as f:
            f.write("\n".join(report))
        logger.info(f"Saved collection report to {report_file}")

async def main():
    orchestrator = DataCollectionOrchestrator()
    
    # Collect historical data
    await orchestrator.collect_historical_data(2008, 2023)
    
    # Collect weather data
    await orchestrator.collect_weather_data()
    
    # Analyze venue statistics
    orchestrator.analyze_venue_stats()
    
    # Generate report
    orchestrator.generate_collection_report()

if __name__ == "__main__":
    asyncio.run(main()) 