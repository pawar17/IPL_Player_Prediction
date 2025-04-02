import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            RotatingFileHandler(
                'logs/app.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
        ]
    )

    # Create logger
    logger = logging.getLogger('ipl_prediction')
    logger.setLevel(logging.INFO)

    # Add Azure-specific logging
    if os.environ.get('WEBSITE_HOSTNAME'):
        logger.info(f"Running on Azure App Service: {os.environ.get('WEBSITE_HOSTNAME')}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Directory contents: {os.listdir('.')}")

    return logger

# Create logger instance
logger = setup_logging() 