import logging
import sys
from pathlib import Path
import pandas as pd
import os

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_collection.ipl_dataset_collector import IPLDatasetCollector
from src.data_collection.data_processor import DataProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Set up data directory
    base_path = Path(__file__).parent.parent
    ipl_dataset_path = base_path / 'IPL-DATASET-main' / 'IPL-DATASET-main' / 'csv'
    data_dir = base_path / 'data'
    
    # Create data directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Using data directory: {data_dir}")

    # Initialize collectors
    ipl_collector = IPLDatasetCollector(ipl_dataset_path)
    data_processor = DataProcessor(data_dir)

    # Test players
    players = ["Virat Kohli", "MS Dhoni", "Rohit Sharma"]
    successful_loads = 0

    for player in players:
        logger.info(f"\nTesting data loading for player: {player}")
        
        # Test IPL data
        try:
            ipl_stats = ipl_collector.get_player_stats(player)
            logger.info(f"IPL data loaded successfully for {player}")
            logger.info(f"Stats: {ipl_stats}")
            successful_loads += 1
        except Exception as e:
            logger.error(f"Failed to load IPL data for {player}: {str(e)}")

        # Test Form data
        logger.info("Testing Form data:")
        try:
            form_data = data_processor.get_player_form(player)
            logger.info(f"Form data loaded successfully for {player}")
            logger.info(f"Form data: {form_data}")
        except Exception as e:
            logger.error(f"Failed to load form data for {player}: {str(e)}")

    logger.info(f"Successfully loaded data for {successful_loads} out of {len(players)} players")

if __name__ == "__main__":
    main() 