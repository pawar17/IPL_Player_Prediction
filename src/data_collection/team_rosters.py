import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('team_rosters.log'),
        logging.StreamHandler()
    ]
)

class IPLTeamDataCollector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.processed_data_path = self.base_path / 'data' / 'processed'
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # IPL 2024 Teams
        self.teams = {
            'Chennai Super Kings': 'csk',
            'Delhi Capitals': 'dc',
            'Gujarat Titans': 'gt',
            'Kolkata Knight Riders': 'kkr',
            'Lucknow Super Giants': 'lsg',
            'Mumbai Indians': 'mi',
            'Punjab Kings': 'pbks',
            'Rajasthan Royals': 'rr',
            'Royal Challengers Bangalore': 'rcb',
            'Sunrisers Hyderabad': 'srh'
        }
        
        # Base URLs for scraping
        self.iplt20_base_url = "https://www.iplt20.com"
        self.cricbuzz_base_url = "https://www.cricbuzz.com"

    def get_team_roster(self, team_name: str) -> Dict:
        """Scrape team roster from IPL official website."""
        try:
            team_id = self.teams[team_name]
            url = f"{self.iplt20_base_url}/teams/{team_id}/squad"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            
            # Find player elements (adjust selectors based on actual website structure)
            player_elements = soup.find_all('div', class_='player-card')
            
            for player in player_elements:
                player_data = {
                    'name': player.find('h3', class_='player-name').text.strip(),
                    'role': player.find('div', class_='player-role').text.strip(),
                    'country': player.find('div', class_='player-country').text.strip(),
                    'price': player.find('div', class_='player-price').text.strip(),
                    'team': team_name
                }
                players.append(player_data)
            
            return {
                'team': team_name,
                'players': players
            }
            
        except Exception as e:
            logging.error(f"Error scraping roster for {team_name}: {str(e)}")
            return {'team': team_name, 'players': []}

    def get_match_schedule(self) -> List[Dict]:
        """Scrape match schedule from IPL official website."""
        try:
            url = f"{self.iplt20_base_url}/schedule"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            matches = []
            
            # Find match elements (adjust selectors based on actual website structure)
            match_elements = soup.find_all('div', class_='match-card')
            
            for match in match_elements:
                match_data = {
                    'match_id': match.get('data-match-id'),
                    'date': match.find('div', class_='match-date').text.strip(),
                    'time': match.find('div', class_='match-time').text.strip(),
                    'venue': match.find('div', class_='match-venue').text.strip(),
                    'team1': match.find('div', class_='team1-name').text.strip(),
                    'team2': match.find('div', class_='team2-name').text.strip(),
                    'status': match.find('div', class_='match-status').text.strip()
                }
                matches.append(match_data)
            
            return matches
            
        except Exception as e:
            logging.error(f"Error scraping match schedule: {str(e)}")
            return []

    def get_team_stats(self, team_name: str) -> Dict:
        """Scrape team statistics from Cricbuzz."""
        try:
            team_id = self.teams[team_name]
            url = f"{self.cricbuzz_base_url}/cricket-team/{team_id}/stats"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract team statistics (adjust selectors based on actual website structure)
            stats = {
                'team': team_name,
                'matches_played': soup.find('div', class_='matches-played').text.strip(),
                'wins': soup.find('div', class_='wins').text.strip(),
                'losses': soup.find('div', class_='losses').text.strip(),
                'win_percentage': soup.find('div', class_='win-percentage').text.strip(),
                'home_record': soup.find('div', class_='home-record').text.strip(),
                'away_record': soup.find('div', class_='away-record').text.strip()
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"Error scraping stats for {team_name}: {str(e)}")
            return {'team': team_name}

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file."""
        try:
            filepath = self.processed_data_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Successfully saved data to {filename}")
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            raise

    def run(self):
        """Run the complete data collection pipeline."""
        try:
            logging.info("Starting IPL 2024 team data collection...")
            
            # Collect team rosters
            rosters = {}
            for team in self.teams:
                logging.info(f"Collecting roster for {team}...")
                rosters[team] = self.get_team_roster(team)
            
            # Collect match schedule
            logging.info("Collecting match schedule...")
            schedule = self.get_match_schedule()
            
            # Collect team statistics
            team_stats = {}
            for team in self.teams:
                logging.info(f"Collecting stats for {team}...")
                team_stats[team] = self.get_team_stats(team)
            
            # Save all data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_data(rosters, f"team_rosters_{timestamp}.json")
            self.save_data(schedule, f"match_schedule_{timestamp}.json")
            self.save_data(team_stats, f"team_stats_{timestamp}.json")
            
            # Create a summary DataFrame
            summary_data = []
            for team in self.teams:
                roster = rosters[team]
                stats = team_stats[team]
                summary_data.append({
                    'team': team,
                    'total_players': len(roster['players']),
                    'matches_played': stats.get('matches_played', 'N/A'),
                    'wins': stats.get('wins', 'N/A'),
                    'losses': stats.get('losses', 'N/A'),
                    'win_percentage': stats.get('win_percentage', 'N/A')
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(self.processed_data_path / f"team_summary_{timestamp}.csv", index=False)
            
            logging.info("Successfully completed team data collection")
            
        except Exception as e:
            logging.error(f"Error in data collection pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    collector = IPLTeamDataCollector()
    collector.run() 