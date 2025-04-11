import logging
from test_match_prediction import MatchPredictor
from data.ipl_2025_data import IPL_2025_MATCHES

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_predictions():
    """Test predictions with the main function"""
    try:
        # Initialize predictor
        predictor = MatchPredictor()
        
        # Get first match from 2025 season
        match_id = list(IPL_2025_MATCHES.keys())[0]
        match = IPL_2025_MATCHES[match_id]
        
        logger.info(f"\nTesting predictions for match: {match['team1']} vs {match['team2']}")
        
        # Get match prediction
        prediction = predictor.predict_match(match_id)
        
        if prediction:
            # Log team 1 predictions
            logger.info(f"\n{prediction['team1']['name']} Predictions:")
            logger.info(f"Win Probability: {prediction['team1']['win_probability']:.2%}")
            logger.info(f"Batting Strength: {prediction['team1']['prediction']['batting']['probability']:.2%}")
            logger.info(f"Bowling Strength: {prediction['team1']['prediction']['bowling']['probability']:.2%}")
            logger.info(f"Fielding Strength: {prediction['team1']['prediction']['fielding']['probability']:.2%}")
            
            # Log team 2 predictions
            logger.info(f"\n{prediction['team2']['name']} Predictions:")
            logger.info(f"Win Probability: {prediction['team2']['win_probability']:.2%}")
            logger.info(f"Batting Strength: {prediction['team2']['prediction']['batting']['probability']:.2%}")
            logger.info(f"Bowling Strength: {prediction['team2']['prediction']['bowling']['probability']:.2%}")
            logger.info(f"Fielding Strength: {prediction['team2']['prediction']['fielding']['probability']:.2%}")
            
            # Log historical stats
            logger.info("\nHistorical Stats:")
            logger.info(f"{prediction['team1']['name']} Win Rate: {prediction['team1']['historical_stats']['win_rate']:.2%}")
            logger.info(f"{prediction['team2']['name']} Win Rate: {prediction['team2']['historical_stats']['win_rate']:.2%}")
        else:
            logger.warning("No prediction available for this match")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in predictions test: {str(e)}")
        return False

if __name__ == "__main__":
    test_predictions() 