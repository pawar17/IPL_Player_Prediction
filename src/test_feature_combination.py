import logging
from test_match_prediction import MatchPredictor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_feature_combination():
    """Test feature combination from all sources"""
    try:
        # Initialize predictor
        predictor = MatchPredictor()
        
        # Test players
        test_players = ["Virat Kohli", "MS Dhoni", "Rohit Sharma"]
        
        for player in test_players:
            logger.info(f"\nTesting feature combination for player: {player}")
            
            # Get combined features
            features = predictor.get_player_features(player, "RCB")  # Using RCB as example team
            
            if features:
                # Log batting features
                logger.info("\nBatting Features:")
                logger.info(f"Average: {features['batting'][0]:.2f}")
                logger.info(f"Strike Rate: {features['batting'][1]:.2f}")
                logger.info(f"Runs: {features['batting'][2]:.2f}")
                
                # Log bowling features
                logger.info("\nBowling Features:")
                logger.info(f"Wickets: {features['bowling'][0]:.2f}")
                logger.info(f"Economy: {features['bowling'][1]:.2f}")
                logger.info(f"Average: {features['bowling'][2]:.2f}")
                
                # Log fielding features
                logger.info("\nFielding Features:")
                logger.info(f"Catches: {features['fielding'][0]:.2f}")
                logger.info(f"Stumpings: {features['fielding'][1]:.2f}")
            else:
                logger.warning(f"No features available for {player}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in feature combination test: {str(e)}")
        return False

if __name__ == "__main__":
    test_feature_combination() 