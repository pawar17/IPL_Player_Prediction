import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IPLWebsiteScraper:
    def __init__(self):
        self.base_url = "https://www.iplt20.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Get BeautifulSoup object from URL."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None

    def get_team_stats(self) -> List[Dict]:
        """Get team statistics from IPL website."""
        try:
            url = f"{self.base_url}/stats/team"
            soup = self.get_soup(url)
            if not soup:
                return []

            team_stats = []
            stats_table = soup.find('table', {'class': 'table'})
            if stats_table:
                for row in stats_table.find_all('tr')[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if len(cols) >= 8:
                        team_stats.append({
                            'team': cols[0].text.strip(),
                            'matches': cols[1].text.strip(),
                            'won': cols[2].text.strip(),
                            'lost': cols[3].text.strip(),
                            'points': cols[4].text.strip(),
                            'nrr': cols[5].text.strip(),
                            'last_updated': datetime.now().strftime('%Y-%m-%d')
                        })
            return team_stats
        except Exception as e:
            logger.error(f"Error getting team stats: {str(e)}")
            return []

    def get_player_stats(self) -> List[Dict]:
        """Get player statistics from IPL website."""
        try:
            url = f"{self.base_url}/stats/player"
            soup = self.get_soup(url)
            if not soup:
                return []

            player_stats = []
            stats_table = soup.find('table', {'class': 'table'})
            if stats_table:
                for row in stats_table.find_all('tr')[1:]:  # Skip header row
                    cols = row.find_all('td')
                    if len(cols) >= 8:
                        player_stats.append({
                            'player_id': cols[0].find('a')['href'].split('/')[-1],
                            'name': cols[0].text.strip(),
                            'team': cols[1].text.strip(),
                            'matches': cols[2].text.strip(),
                            'runs': cols[3].text.strip(),
                            'wickets': cols[4].text.strip(),
                            'last_updated': datetime.now().strftime('%Y-%m-%d')
                        })
            return player_stats
        except Exception as e:
            logger.error(f"Error getting player stats: {str(e)}")
            return []

    def get_match_schedule(self) -> List[Dict]:
        """Get match schedule from IPL website."""
        try:
            url = f"{self.base_url}/schedule"
            soup = self.get_soup(url)
            if not soup:
                return []

            matches = []
            match_cards = soup.find_all('div', {'class': 'match-card'})
            for card in match_cards:
                try:
                    match = {
                        'match_id': card.get('data-match-id', ''),
                        'date': card.find('div', {'class': 'date'}).text.strip(),
                        'time': card.find('div', {'class': 'time'}).text.strip(),
                        'venue': card.find('div', {'class': 'venue'}).text.strip(),
                        'team1': card.find('div', {'class': 'team1'}).text.strip(),
                        'team2': card.find('div', {'class': 'team2'}).text.strip(),
                        'status': card.find('div', {'class': 'status'}).text.strip(),
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
                    matches.append(match)
                except Exception as e:
                    logger.error(f"Error processing match card: {str(e)}")
                    continue
            return matches
        except Exception as e:
            logger.error(f"Error getting match schedule: {str(e)}")
            return []

    def get_team_squads(self) -> List[Dict]:
        """Get team squads from IPL website."""
        try:
            url = f"{self.base_url}/teams"
            soup = self.get_soup(url)
            if not soup:
                return []

            squads = []
            team_cards = soup.find_all('div', {'class': 'team-card'})
            for card in team_cards:
                try:
                    team_name = card.find('div', {'class': 'team-name'}).text.strip()
                    players = []
                    player_list = card.find_all('div', {'class': 'player'})
                    for player in player_list:
                        players.append({
                            'player_id': player.find('a')['href'].split('/')[-1],
                            'name': player.text.strip(),
                            'role': player.get('data-role', ''),
                            'status': player.get('data-status', 'active')
                        })
                    squads.append({
                        'team': team_name,
                        'players': players,
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
                except Exception as e:
                    logger.error(f"Error processing team card: {str(e)}")
                    continue
            return squads
        except Exception as e:
            logger.error(f"Error getting team squads: {str(e)}")
            return []

    def save_data(self, data: List[Dict], filename: str):
        """Save data to JSON file."""
        try:
            filepath = self.data_dir / f"ipl_website_{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(data)} records to {filepath}")
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")

    def update_all_data(self):
        """Update all data from IPL website."""
        try:
            logger.info("Starting IPL website data update...")

            # Get and save team stats
            team_stats = self.get_team_stats()
            self.save_data(team_stats, "team_stats")

            # Get and save player stats
            player_stats = self.get_player_stats()
            self.save_data(player_stats, "player_stats")

            # Get and save match schedule
            match_schedule = self.get_match_schedule()
            self.save_data(match_schedule, "match_schedule")

            # Get and save team squads
            team_squads = self.get_team_squads()
            self.save_data(team_squads, "team_squads")

            logger.info("IPL website data update completed")
        except Exception as e:
            logger.error(f"Error updating IPL website data: {str(e)}")

def main():
    scraper = IPLWebsiteScraper()
    scraper.update_all_data()

if __name__ == "__main__":
    main() 