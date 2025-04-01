import pandas as pd
import requests
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_ipl_data():
    """Download IPL historical data"""
    try:
        # Create data directory if it doesn't exist
        data_path = Path(__file__).parent.parent.parent / 'data' / 'raw'
        data_path.mkdir(parents=True, exist_ok=True)
        
        # URLs for IPL data
        urls = {
            'matches': 'https://raw.githubusercontent.com/amanthedorkknight/IPL-Dataset-2022/master/matches.csv',
            'deliveries': 'https://raw.githubusercontent.com/amanthedorkknight/IPL-Dataset-2022/master/deliveries.csv'
        }
        
        # Download files
        for name, url in urls.items():
            logger.info(f"Downloading {name} data...")
            response = requests.get(url)
            response.raise_for_status()
            
            # Save to file
            file_path = data_path / f"{name}.csv"
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded {name} data")
        
        # Load and validate data
        matches_df = pd.read_csv(data_path / 'matches.csv')
        deliveries_df = pd.read_csv(data_path / 'deliveries.csv')
        
        logger.info(f"Loaded {len(matches_df)} matches and {len(deliveries_df)} deliveries")
        
        return True
        
    except Exception as e:
        logger.error(f"Error downloading data: {str(e)}")
        return False

if __name__ == "__main__":
    download_ipl_data() 