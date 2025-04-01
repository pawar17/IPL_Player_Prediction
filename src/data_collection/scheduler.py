import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List
from web_scraper import CricketWebScraper
from cricket_sources import CricketDataSources

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

class CricketDataScheduler:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data' / 'scraped'
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.web_scraper = CricketWebScraper()
        self.cricket_sources = CricketDataSources()
        
        # Load IPL 2024 schedule
        schedule_path = self.base_path / 'data' / 'processed' / 'ipl2024_schedule_20240401_145632.json'
        with open(schedule_path, 'r') as f:
            self.schedule = json.load(f)

    def update_injury_data(self):
        """Update injury data every 6 hours"""
        logging.info("Starting injury data update")
        try:
            injury_updates = self.cricket_sources.get_player_injury_updates()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save injury updates
            filepath = self.data_path / f"injury_updates_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(injury_updates, f, indent=4)
            
            logging.info(f"Saved {len(injury_updates)} injury updates")
            
        except Exception as e:
            logging.error(f"Error updating injury data: {str(e)}")

    def update_team_compositions(self):
        """Update team compositions every 12 hours"""
        logging.info("Starting team composition update")
        try:
            team_changes = {}
            for team in self.web_scraper.teams:
                changes = self.cricket_sources.get_team_composition_changes(team)
                team_changes[team] = changes
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.data_path / f"team_changes_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(team_changes, f, indent=4)
            
            logging.info(f"Saved team composition changes for {len(team_changes)} teams")
            
        except Exception as e:
            logging.error(f"Error updating team compositions: {str(e)}")

    def update_venue_conditions(self):
        """Update venue conditions every 24 hours"""
        logging.info("Starting venue conditions update")
        try:
            venue_conditions = {}
            venues = set(match['venue'] for match in self.schedule)
            
            for venue in venues:
                conditions = self.cricket_sources.get_venue_conditions(venue)
                venue_conditions[venue] = conditions
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.data_path / f"venue_conditions_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(venue_conditions, f, indent=4)
            
            logging.info(f"Saved conditions for {len(venue_conditions)} venues")
            
        except Exception as e:
            logging.error(f"Error updating venue conditions: {str(e)}")

    def update_player_form(self):
        """Update player form data every 24 hours"""
        logging.info("Starting player form update")
        try:
            player_form = {}
            for team in self.web_scraper.teams:
                team_data = self.web_scraper.get_team_roster(team)
                for player in team_data['players']:
                    form_data = self.cricket_sources.get_player_form(player['name'])
                    player_form[player['name']] = form_data
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.data_path / f"player_form_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(player_form, f, indent=4)
            
            logging.info(f"Saved form data for {len(player_form)} players")
            
        except Exception as e:
            logging.error(f"Error updating player form: {str(e)}")

    def update_match_predictions(self):
        """Update match predictions every 12 hours"""
        logging.info("Starting match predictions update")
        try:
            current_date = datetime.now().date()
            upcoming_matches = [
                match for match in self.schedule
                if datetime.strptime(match['date'], '%Y-%m-%d').date() >= current_date
            ]
            
            predictions = {}
            for match in upcoming_matches:
                match_id = f"ipl2024_{match['match_no']}"
                prediction = self.web_scraper.update_match_predictions(match_id)
                predictions[match_id] = prediction
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = self.data_path / f"match_predictions_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(predictions, f, indent=4)
            
            logging.info(f"Updated predictions for {len(predictions)} matches")
            
        except Exception as e:
            logging.error(f"Error updating match predictions: {str(e)}")

    def run(self):
        """Set up and run the scheduling system"""
        logging.info("Starting cricket data scheduler")
        
        # Schedule tasks
        schedule.every(6).hours.do(self.update_injury_data)
        schedule.every(12).hours.do(self.update_team_compositions)
        schedule.every(12).hours.do(self.update_match_predictions)
        schedule.every(24).hours.do(self.update_venue_conditions)
        schedule.every(24).hours.do(self.update_player_form)
        
        # Run initial updates
        self.update_injury_data()
        self.update_team_compositions()
        self.update_venue_conditions()
        self.update_player_form()
        self.update_match_predictions()
        
        # Keep the script running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    scheduler = CricketDataScheduler()
    scheduler.run() 