import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
from data_collector import DataCollector
from data_processor import DataProcessor
from config import DATA_COLLECTION_INTERVAL, CACHE_UPDATE_INTERVAL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.collector = DataCollector(data_dir=data_dir)
        self.processor = DataProcessor(data_dir=data_dir)
        self.running = False

    def start(self):
        """Start the data collection and processing schedule"""
        self.running = True
        logger.info("Starting data collection schedule")

        # Schedule regular data collection
        schedule.every(DATA_COLLECTION_INTERVAL).seconds.do(self.collect_and_process_data)
        
        # Schedule cache updates
        schedule.every(CACHE_UPDATE_INTERVAL).seconds.do(self.update_cache)

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def stop(self):
        """Stop the data collection schedule"""
        self.running = False
        logger.info("Stopping data collection schedule")

    def collect_and_process_data(self):
        """Collect and process new data"""
        try:
            logger.info("Starting data collection cycle")
            
            # Collect live match data
            live_matches = self.collector.fetch_live_matches()
            if live_matches:
                logger.info(f"Collected {len(live_matches)} live matches")
                
                # Process each match
                for match in live_matches:
                    try:
                        # Process match data
                        processed_data = self.processor.process_match_data(match)
                        
                        # Validate processed data
                        if self.processor.validate_data(processed_data):
                            # Save processed data
                            self.processor.save_processed_data(
                                processed_data,
                                match.get('match_id', 'unknown')
                            )
                            logger.info(f"Processed and saved data for match {match.get('match_id')}")
                        else:
                            logger.warning(f"Invalid data for match {match.get('match_id')}")
                    
                    except Exception as e:
                        logger.error(f"Error processing match {match.get('match_id')}: {e}")
                        continue
            
            # Collect trending players
            trending_players = self.collector.get_trending_players()
            if trending_players:
                logger.info("Collected trending players data")
            
            # Collect team rankings
            team_rankings = self.collector.get_team_rankings()
            if team_rankings:
                logger.info("Collected team rankings")
            
            # Collect batsmen rankings
            batsmen_rankings = self.collector.get_batsmen_rankings()
            if batsmen_rankings:
                logger.info("Collected batsmen rankings")
            
            # Collect top stats
            top_stats = self.collector.get_top_stats()
            if top_stats:
                logger.info("Collected top stats")
            
            logger.info("Completed data collection cycle")
            
        except Exception as e:
            logger.error(f"Error in data collection cycle: {e}")

    def update_cache(self):
        """Update cached data"""
        try:
            logger.info("Starting cache update")
            
            # Update live matches cache
            live_matches = self.collector.fetch_live_matches()
            if live_matches:
                self.collector.save_to_cache(live_matches, 'live_matches')
                logger.info("Updated live matches cache")
            
            # Update trending players cache
            trending_players = self.collector.get_trending_players()
            if trending_players:
                self.collector.save_to_cache(trending_players, 'trending_players')
                logger.info("Updated trending players cache")
            
            # Update team rankings cache
            team_rankings = self.collector.get_team_rankings()
            if team_rankings:
                self.collector.save_to_cache(team_rankings, 'team_rankings')
                logger.info("Updated team rankings cache")
            
            # Update batsmen rankings cache
            batsmen_rankings = self.collector.get_batsmen_rankings()
            if batsmen_rankings:
                self.collector.save_to_cache(batsmen_rankings, 'batsmen_rankings')
                logger.info("Updated batsmen rankings cache")
            
            # Update top stats cache
            top_stats = self.collector.get_top_stats()
            if top_stats:
                self.collector.save_to_cache(top_stats, 'top_stats')
                logger.info("Updated top stats cache")
            
            logger.info("Completed cache update")
            
        except Exception as e:
            logger.error(f"Error updating cache: {e}")

    def run_once(self):
        """Run a single data collection and processing cycle"""
        try:
            logger.info("Running single data collection cycle")
            self.collect_and_process_data()
            logger.info("Completed single data collection cycle")
        except Exception as e:
            logger.error(f"Error in single data collection cycle: {e}")

if __name__ == "__main__":
    scheduler = DataScheduler()
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping scheduler")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Fatal error in scheduler: {e}")
        scheduler.stop() 