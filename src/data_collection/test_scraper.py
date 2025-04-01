import logging
import json
from datetime import datetime
import os
import time
from web_scraper import CricketWebScraper

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_scraper.log'),
            logging.StreamHandler()
        ]
    )

def retry_with_backoff(func, *args, max_retries=3, initial_delay=1, **kwargs):
    """Retry a function with exponential backoff"""
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            time.sleep(delay)
            delay *= 2

def test_web_scraper():
    """Test the web scraper functionality"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize scraper
        scraper = CricketWebScraper()
        
        # Test match schedule retrieval
        logger.info("Testing match schedule retrieval...")
        match_schedule = retry_with_backoff(scraper.get_match_schedule)
        logger.info(f"Retrieved {len(match_schedule.get('matches', []))} matches")
        
        # Test team roster retrieval
        logger.info("Testing team roster retrieval...")
        team_rosters = {}
        for team in scraper.teams:
            logger.info(f"Getting roster for {team}...")
            roster = retry_with_backoff(scraper.get_team_roster, team)
            team_rosters[team] = roster
            logger.info(f"Found {len(roster.get('players', []))} players")
        
        # Test team news retrieval
        logger.info("Testing team news retrieval...")
        team_news = {}
        for team in scraper.teams:
            logger.info(f"Getting news for {team}...")
            news = retry_with_backoff(scraper.get_team_news, team)
            team_news[team] = news
            logger.info(f"Found {len(news.get('news', []))} news items")
        
        # Save test results
        results = {
            "timestamp": datetime.now().isoformat(),
            "match_schedule": match_schedule,
            "team_rosters": team_rosters,
            "team_news": team_news
        }
        
        # Create results directory if it doesn't exist
        results_dir = os.path.join("data", "test_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(results_dir, f"test_results_{timestamp}.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=4)
        
        logger.info(f"Test results saved to {results_file}")
        
        # Print summary
        print("\nTest Summary:")
        print(f"Total matches: {len(match_schedule.get('matches', []))}")
        print(f"Teams tested: {len(team_rosters)}")
        print(f"Total players found: {sum(len(roster.get('players', [])) for roster in team_rosters.values())}")
        print(f"Total news items: {sum(len(news.get('news', [])) for news in team_news.values())}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_web_scraper()
    if success:
        print("\nAll tests completed successfully!")
    else:
        print("\nTests failed. Check the logs for details.") 