import asyncio
import logging
from pathlib import Path
from datetime import datetime
import json
from data_collector import DataCollector
from data_processor import DataProcessor
from config import (
    DATA_DIR, LOG_FILE, LOG_LEVEL,
    DATA_COLLECTION_INTERVAL, MAX_RETRIES, RETRY_DELAY
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPLDataSystem:
    def __init__(self):
        self.collector = DataCollector()
        self.processor = DataProcessor()
        self.running = False

    async def start(self):
        """Start the data collection and processing system"""
        self.running = True
        logger.info("Starting IPL Data System")
        
        while self.running:
            try:
                # Collect live match data
                live_matches = await self.collector.fetch_live_matches()
                
                # Process each match
                for match in live_matches:
                    try:
                        # Process match data
                        processed_match = self.processor.process_match_data(match)
                        
                        # Process player data for each team
                        for team in [match['team1'], match['team2']]:
                            team_data = next(
                                (t for t in self.collector.teams if t['name'] == team),
                                None
                            )
                            if team_data:
                                for player in team_data['players']:
                                    # Process player data
                                    processed_player = self.processor.process_player_data(player)
                                    
                                    # Save processed data
                                    self.processor.save_processed_data(
                                        processed_match,
                                        processed_player
                                    )
                                    
                                    # Update player statistics
                                    self.processor.update_player_stats(processed_player)
                        
                        # Update historical data
                        self.processor.update_historical_data(processed_match)
                        
                    except Exception as e:
                        logger.error(f"Error processing match {match.get('match_id', 'unknown')}: {e}")
                
                # Wait before next update
                await asyncio.sleep(DATA_COLLECTION_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(RETRY_DELAY)

    def stop(self):
        """Stop the data collection and processing system"""
        self.running = False
        logger.info("Stopping IPL Data System")

    async def run_once(self):
        """Run a single iteration of data collection and processing"""
        try:
            # Collect live match data
            live_matches = await self.collector.fetch_live_matches()
            
            # Process each match
            for match in live_matches:
                try:
                    # Process match data
                    processed_match = self.processor.process_match_data(match)
                    
                    # Process player data for each team
                    for team in [match['team1'], match['team2']]:
                        team_data = next(
                            (t for t in self.collector.teams if t['name'] == team),
                            None
                        )
                        if team_data:
                            for player in team_data['players']:
                                # Process player data
                                processed_player = self.processor.process_player_data(player)
                                
                                # Save processed data
                                self.processor.save_processed_data(
                                    processed_match,
                                    processed_player
                                )
                                
                                # Update player statistics
                                self.processor.update_player_stats(processed_player)
                    
                    # Update historical data
                    self.processor.update_historical_data(processed_match)
                    
                except Exception as e:
                    logger.error(f"Error processing match {match.get('match_id', 'unknown')}: {e}")
            
            logger.info("Completed single run successfully")
            
        except Exception as e:
            logger.error(f"Error in single run: {e}")

async def main():
    """Main entry point"""
    system = IPLDataSystem()
    
    try:
        # Run the system
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping system")
        system.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        system.stop()

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Run the system
    asyncio.run(main()) 