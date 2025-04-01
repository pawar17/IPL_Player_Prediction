import logging
from pathlib import Path
import pandas as pd
from src.data_preparation.data_processor import DataProcessor
from src.models.player_predictor import PlayerPredictor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the model training pipeline"""
    try:
        # Initialize paths
        base_path = Path(__file__).parent.parent
        data_path = base_path / 'data' / 'raw'
        processed_path = base_path / 'data' / 'processed'
        models_path = base_path / 'models' / 'saved'
        
        # Create necessary directories
        processed_path.mkdir(parents=True, exist_ok=True)
        models_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        processor = DataProcessor()
        predictor = PlayerPredictor()
        
        # Load and prepare data
        logger.info("Loading historical data...")
        historical_data = processor.prepare_historical_data()
        
        if historical_data is None or historical_data.empty:
            logger.error("No historical data available for training")
            return
        
        # Split data into training and validation sets
        logger.info("Splitting data into training and validation sets...")
        train_data = historical_data.sample(frac=0.8, random_state=42)
        val_data = historical_data.drop(train_data.index)
        
        # Train models
        logger.info("Training models...")
        predictor.train(train_data)
        
        # Validate models
        logger.info("Validating models...")
        val_predictions = predictor.predict_batch(val_data)
        
        # Calculate validation metrics
        metrics = predictor.calculate_metrics(val_data, val_predictions)
        logger.info("Validation metrics:")
        for metric, value in metrics.items():
            logger.info(f"{metric}: {value:.3f}")
        
        # Save models
        logger.info("Saving trained models...")
        predictor.save_models()
        
        logger.info("Model training completed successfully")
        
    except Exception as e:
        logger.error(f"Error in model training pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main() 