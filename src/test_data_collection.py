import logging
from pathlib import Path
from src.data_collection.data_collector import DataCollector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test the data collection system"""
    try:
        # Initialize collector
        collector = DataCollector()
        
        # Test data collection
        logger.info("Starting data collection...")
        success = collector.collect_all_data()
        
        if success:
            logger.info("Data collection completed successfully")
            
            # Verify collected data
            data_path = Path(__file__).parent.parent / 'data' / 'scraped'
            required_files = [
                'processed_player_stats.json',
                'processed_team_stats.json',
                'processed_venue_stats.json',
                'match_schedules.json',
                'team_rosters.json',
                'player_statistics.json',
                'player_availability.json',
                'venue_data.json'
            ]
            
            logger.info("\nVerifying collected data files:")
            for file in required_files:
                file_path = data_path / file
                if file_path.exists():
                    logger.info(f"✓ {file}")
                else:
                    logger.warning(f"✗ {file} (missing)")
            
        else:
            logger.error("Data collection failed")
        
    except Exception as e:
        logger.error(f"Error testing data collection: {str(e)}")
        raise

if __name__ == "__main__":
    main() 