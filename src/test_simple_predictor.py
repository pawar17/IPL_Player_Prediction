import logging
from pathlib import Path
import pandas as pd
from src.data_preparation.data_processor import DataProcessor
from src.models.simple_predictor import SimplePredictor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test the simple prediction model"""
    try:
        # Initialize components
        processor = DataProcessor()
        predictor = SimplePredictor()
        
        # Load historical data
        logger.info("Loading historical data...")
        historical_data = processor.prepare_historical_data()
        
        if historical_data is None or historical_data.empty:
            logger.error("No historical data available for testing")
            return
        
        # Make predictions for a few sample players
        logger.info("\nTesting predictions for sample players:")
        for _, player_data in historical_data.head(5).iterrows():
            player_dict = player_data.to_dict()
            predictions = predictor.predict(player_dict)
            
            logger.info(f"\nPredictions for {player_dict['player_name']}:")
            logger.info(f"Form: {predictions['form']}")
            logger.info(f"Confidence: {predictions['confidence']:.2f}")
            
            # Display data quality assessment
            quality = predictions['data_quality']
            logger.info("\nData Quality Assessment:")
            logger.info(f"Recent Data: {'✓' if quality['recent_data'] else '✗'}")
            logger.info(f"Historical Data: {'✓' if quality['historical_data'] else '✗'}")
            logger.info(f"Context Data: {'✓' if quality['context_data'] else '✗'}")
            if quality['issues']:
                logger.info("Issues:")
                for issue in quality['issues']:
                    logger.info(f"- {issue}")
            
            logger.info("\nPredictions:")
            logger.info(f"Runs: {predictions['runs']} (CI: {predictions['runs_ci']})")
            logger.info(f"Wickets: {predictions['wickets']} (CI: {predictions['wickets_ci']})")
            logger.info(f"Strike Rate: {predictions['strike_rate']} (CI: {predictions['strike_rate_ci']})")
            logger.info(f"Economy Rate: {predictions['economy_rate']} (CI: {predictions['economy_rate_ci']})")
        
        # Calculate accuracy metrics
        logger.info("\nCalculating prediction accuracy:")
        total_predictions = len(historical_data)
        accurate_predictions = 0
        
        for _, player_data in historical_data.iterrows():
            player_dict = player_data.to_dict()
            predictions = predictor.predict(player_dict)
            
            # Check if actual values fall within confidence intervals
            if (player_dict['runs'] >= predictions['runs_ci'][0] and 
                player_dict['runs'] <= predictions['runs_ci'][1]):
                accurate_predictions += 1
        
        accuracy = accurate_predictions / total_predictions
        logger.info(f"Prediction accuracy (runs within CI): {accuracy:.2%}")
        
    except Exception as e:
        logger.error(f"Error testing simple predictor: {str(e)}")
        raise

if __name__ == "__main__":
    main() 