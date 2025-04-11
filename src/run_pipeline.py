import logging
from src.data_collection.data_pipeline import DataPipeline
from src.training.train_models import ModelTrainer

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize data pipeline
        logger.info("Initializing data pipeline...")
        pipeline = DataPipeline()
        
        # Run data pipeline
        logger.info("Running data pipeline...")
        if pipeline.run_pipeline():
            logger.info("Data pipeline completed successfully")
        else:
            logger.error("Data pipeline failed")
            return
        
        # Initialize model trainer
        logger.info("Initializing model trainer...")
        trainer = ModelTrainer()
        
        # Train models
        logger.info("Training models...")
        metrics = trainer.train_models(perform_grid_search=True)
        
        # Print results
        logger.info("\nModel Performance Metrics:")
        logger.info("\nBatting Model:")
        for metric, value in metrics["batting"].items():
            if metric != "feature_importance":
                logger.info(f"{metric.upper()}: {value:.4f}")
        
        logger.info("\nBowling Model:")
        for metric, value in metrics["bowling"].items():
            if metric != "feature_importance":
                logger.info(f"{metric.upper()}: {value:.4f}")
        
        logger.info("\nFeature Importance:")
        logger.info("\nBatting Model:")
        for feature, importance in metrics["batting"]["feature_importance"].items():
            logger.info(f"{feature}: {importance:.4f}")
        
        logger.info("\nBowling Model:")
        for feature, importance in metrics["bowling"]["feature_importance"].items():
            logger.info(f"{feature}: {importance:.4f}")
        
    except Exception as e:
        logger.error(f"Error running pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main() 