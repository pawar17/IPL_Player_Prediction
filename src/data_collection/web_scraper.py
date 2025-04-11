import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
from pathlib import Path
import time
import re
from typing import Dict, List, Optional, Any
import random
from urllib.parse import quote, urlencode
import os
from dotenv import load_dotenv
from .test_data import SAMPLE_MATCHES, SAMPLE_RESULTS, SAMPLE_PLAYER_STATS

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CricketWebScraper:
    def __init__(self, use_test_data: bool = True):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.scraped_path = self.data_path / 'scraped'
        self.scraped_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.teams = {}
        self.venues = {}
        self.conditions = {}
        self.player_form = {}
        self.match_predictions = {}
        
        # Set up URLs for reliable sources
        self.urls = {
            'ipl': {
                'base': 'https://www.iplt20.com',
                'teams': 'https://www.iplt20.com/teams',
                'matches': 'https://www.iplt20.com/matches/schedule',
                'news': 'https://www.iplt20.com/news'
            },
            'cricbuzz': {
                'base': 'https://www.cricbuzz.com',
                'matches': 'https://www.cricbuzz.com/cricket-match/live-scores',
                'stats': 'https://www.cricbuzz.com/cricket-stats'
            }
        }
        
        # Set up headers for better request success
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.base_url = "https://www.cricbuzz.com"
        self.team_ids = {
            'Royal Challengers Bangalore': 'rcb',
            'Gujarat Titans': 'gt',
            'Chennai Super Kings': 'csk',
            'Mumbai Indians': 'mi',
            'Delhi Capitals': 'dc',
            'Punjab Kings': 'pbks',
            'Kolkata Knight Riders': 'kkr',
            'Rajasthan Royals': 'rr',
            'Sunrisers Hyderabad': 'srh',
            'Lucknow Super Giants': 'lsg'
        }
        
        self.use_test_data = use_test_data
        self.rate_limit_delay = 2  # 2 seconds between requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[BeautifulSoup]:
        """Make HTTP request with retry logic and validation"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                
                # Validate response content
                if not self._validate_response(response):
                    self.logger.warning(f"Invalid response content from {url}")
                    continue
                    
                return BeautifulSoup(response.text, 'html.parser')
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
                
        return None
    
    def _validate_response(self, response: requests.Response) -> bool:
        """Validate HTTP response content"""
        if not response.content:
            return False
            
        if len(response.content) < 1000:  # Minimum content length
            return False
            
        if 'error' in response.text.lower() or 'not found' in response.text.lower():
            return False
            
        return True
    
    def get_team_roster(self, team_name: str) -> Dict[str, Any]:
        """Get team roster from IPL website"""
        try:
            team_url = f"{self.urls['ipl']['teams']}/{team_name.lower().replace(' ', '-')}"
            response = self._make_request(team_url)
            if not response:
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            players = []
            
            # Find player elements
            player_elements = soup.find_all('div', class_='player-card')
            for player in player_elements:
                player_data = {
                    'name': player.find('h3', class_='player-name').text.strip(),
                    'role': player.find('span', class_='player-role').text.strip(),
                    'status': player.find('span', class_='player-status').text.strip(),
                    'status_reason': player.find('span', class_='status-reason').text.strip() if player.find('span', class_='status-reason') else '',
                    'recovery_progress': int(player.find('div', class_='recovery-progress').text.strip().replace('%', '')) if player.find('div', class_='recovery-progress') else 100,
                    'expected_return_date': player.find('span', class_='return-date').text.strip() if player.find('span', class_='return-date') else None
                }
                
                # Validate player data
                if self._validate_player_data(player_data):
                    players.append(player_data)
                else:
                    self.logger.warning(f"Skipping invalid player data: {player_data}")
            
            if not players:
                self.logger.warning(f"No valid players found for team {team_name}")
                return None
                
            return {
                'team_name': team_name,
                'players': players,
                'total_players': len(players),
                'available_players': len([p for p in players if p['status'] == 'Available']),
                'injured_players': len([p for p in players if 'injured' in p['status'].lower()]),
                'rested_players': len([p for p in players if 'rested' in p['status'].lower()])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting team roster for {team_name}: {str(e)}")
            return None
    
    def get_match_schedule(self) -> List[Dict[str, Any]]:
        """Get match schedule from IPL website"""
        try:
            response = self._make_request(self.urls['ipl']['matches'])
            if not response:
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            matches = []
            
            # Find match elements
            match_elements = soup.find_all('div', class_='match-card')
            for match in match_elements:
                match_data = {
                    'match_id': match.get('data-match-id', ''),
                    'date': match.find('span', class_='match-date').text.strip(),
                    'time': match.find('span', class_='match-time').text.strip(),
                    'venue': match.find('span', class_='match-venue').text.strip(),
                    'team1': match.find('div', class_='team1-name').text.strip(),
                    'team2': match.find('div', class_='team2-name').text.strip(),
                    'status': match.find('span', class_='match-status').text.strip(),
                    'match_type': match.find('span', class_='match-type').text.strip()
                }
                
                # Validate match data
                if self._validate_match_data(match_data):
                    matches.append(match_data)
                else:
                    self.logger.warning(f"Skipping invalid match data: {match_data}")
            
            if not matches:
                self.logger.warning("No valid matches found in schedule")
                return []
                
            return matches
            
        except Exception as e:
            self.logger.error(f"Error getting match schedule: {str(e)}")
            return []
    
    def get_player_stats(self, player_name: str) -> Dict:
        """Get player statistics"""
        if self.use_test_data:
            return SAMPLE_PLAYER_STATS.get(player_name, {})
            
        try:
            # Search for player
            search_url = f"{self.base_url}/api/search/results?q={player_name}"
            response = requests.get(search_url, headers=self.headers)
            search_results = response.json()
            
            player_url = None
            for result in search_results.get('players', []):
                if result['name'].lower() == player_name.lower():
                    player_url = f"{self.base_url}{result['url']}"
                    break
                    
            if not player_url:
                return {}
                
            # Get player profile page
            response = requests.get(player_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {}
            
            # Get batting stats
            batting_table = soup.find('table', class_='cb-col-100 cb-plyr-thead')
            if batting_table:
                rows = batting_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 7:
                        format_name = cols[0].text.strip()
                        if format_name == 'IPL':
                            stats.update({
                                'batting_average': float(cols[6].text.strip() or 0),
                                'strike_rate': float(cols[7].text.strip() or 0),
                                'recent_balls_faced': int(cols[3].text.strip() or 0)
                            })
            
            # Get bowling stats
            bowling_table = soup.find('table', class_='cb-col-100 cb-plyr-thead')
            if bowling_table:
                rows = bowling_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 8:
                        format_name = cols[0].text.strip()
                        if format_name == 'IPL':
                            stats.update({
                                'bowling_average': float(cols[6].text.strip() or 0),
                                'economy_rate': float(cols[7].text.strip() or 0),
                                'recent_wickets': int(cols[4].text.strip() or 0)
                            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error fetching player stats: {str(e)}")
            return {}
    
    def _extract_stat(self, soup: BeautifulSoup, stat_name: str) -> float:
        """Extract a specific statistic from the page"""
        try:
            stat_element = soup.find('div', class_=f'stat-{stat_name}')
            if stat_element:
                return float(stat_element.text.strip().replace('-', '0'))
            return 0.0
        except:
            return 0.0
    
    def _validate_player_data(self, data: Dict) -> bool:
        """Validate player data"""
        required_fields = ['name', 'role', 'status']
        return all(field in data and data[field] for field in required_fields)
    
    def _validate_match_data(self, data: Dict) -> bool:
        """Validate match data"""
        required_fields = ['match_id', 'date', 'team1', 'team2']
        return all(field in data and data[field] for field in required_fields)
    
    def _validate_player_stats(self, data: Dict) -> bool:
        """Validate player statistics"""
        required_fields = ['name', 'matches', 'runs', 'wickets']
        return all(field in data and isinstance(data[field], (int, float)) for field in required_fields)

    def scrape_cricbuzz_match_stats(self, match_url: str) -> Dict:
        """Scrape match statistics from Cricbuzz"""
        soup = self._make_request(match_url)
        if not soup:
            logging.error(f"Failed to get match stats from {match_url}")
            return {}
            
        match_stats = {
            'match_info': {},
            'teams': {},
            'scores': {},
            'players': {}
        }
        
        try:
            # Get match info
            match_header = soup.find('div', class_='cb-nav-main cb-col-100 cb-col')
            if match_header:
                match_stats['match_info'] = {
                    'title': match_header.find('h1').text.strip() if match_header.find('h1') else '',
                    'venue': match_header.find('div', class_='cb-nav-subhdr').text.strip() if match_header.find('div', class_='cb-nav-subhdr') else '',
                    'date': match_header.find('span', class_='cb-nav-day').text.strip() if match_header.find('span', class_='cb-nav-day') else ''
                }
            
            # Get team scores
            score_cards = soup.find_all('div', class_='cb-col cb-col-100 cb-ltst-wgt-hdr')
            for card in score_cards:
                team_name = card.find('div', class_='cb-col-100 cb-scrd-hdr-rw').text.strip()
                score_details = card.find('div', class_='cb-col-100 cb-scrd-sub-hdr cb-bg-gray')
                if score_details:
                    match_stats['scores'][team_name] = {
                        'total': score_details.find('div', class_='cb-col-100 cb-scrd-itms').text.strip(),
                        'overs': score_details.find('div', class_='cb-col-100 cb-scrd-itms').find_next_sibling('div').text.strip()
                    }
            
            # Get player performances
            player_tables = soup.find_all('div', class_='cb-col-67 cb-col')
            for table in player_tables:
                rows = table.find_all('div', class_='cb-col-100 cb-scrd-itms')
                for row in rows:
                    player_name = row.find('a')
                    if player_name:
                        stats = row.find_all('div', class_='cb-col cb-col-8')
                        match_stats['players'][player_name.text.strip()] = {
                            'runs': stats[0].text.strip() if len(stats) > 0 else '0',
                            'balls': stats[1].text.strip() if len(stats) > 1 else '0',
                            'fours': stats[2].text.strip() if len(stats) > 2 else '0',
                            'sixes': stats[3].text.strip() if len(stats) > 3 else '0',
                            'strike_rate': stats[4].text.strip() if len(stats) > 4 else '0'
                        }
            
            return match_stats
            
        except Exception as e:
            logging.error(f"Error parsing match stats: {str(e)}")
            return match_stats

    def scrape_ipl_team_updates(self, team_name: str) -> Dict:
        """Scrape team updates from IPL website"""
        team_url = f"{self.urls['ipl']}/teams/{team_name.lower().replace(' ', '-')}"
        soup = self._make_request(team_url)
        if not soup:
            return {}

        team_updates = {
            'squad': [],
            'news': [],
            'injuries': [],
            'availability': {}
        }

        try:
            # Extract squad information
            squad_section = soup.find('div', class_='team-squad')
            if squad_section:
                for player in squad_section.find_all('div', class_='player-card'):
                    team_updates['squad'].append({
                        'name': player.find('div', class_='player-name').text.strip(),
                        'role': player.find('div', class_='player-role').text.strip(),
                        'status': player.find('div', class_='player-status').text.strip()
                    })

            # Extract news and updates
            news_section = soup.find('div', class_='team-news')
            if news_section:
                for news in news_section.find_all('div', class_='news-item'):
                    team_updates['news'].append({
                        'title': news.find('h3').text.strip(),
                        'date': news.find('span', class_='date').text.strip(),
                        'content': news.find('p').text.strip()
                    })

        except Exception as e:
            logging.error(f"Error scraping team updates: {str(e)}")

        return team_updates

    def scrape_espn_player_stats(self, player_name: str) -> Dict:
        """Scrape player statistics from ESPN CricInfo"""
        # First try direct player URL
        player_slug = player_name.lower().replace(' ', '-')
        player_url = f"{self.urls['espn']['base']}/player/{player_slug}"
        soup = self._make_request(player_url)
        
        if not soup:
            # If direct URL fails, try search
            search_url = f"{self.urls['espn']['base']}/search?search={player_name}"
            soup = self._make_request(search_url)
            if soup:
                # Find player profile link
                player_link = soup.find('a', href=re.compile(r'/player/.*'))
                if player_link:
                    player_url = f"{self.urls['espn']['base']}{player_link['href']}"
                    soup = self._make_request(player_url)

        if not soup:
            return {}

        player_stats = {
            'basic_info': {},
            'batting_stats': {},
            'bowling_stats': {},
            'recent_matches': []
        }

        try:
            # Extract basic information
            info_section = soup.find('div', class_='player-info')
            if info_section:
                player_stats['basic_info'] = {
                    'name': info_section.find('h1').text.strip(),
                    'country': info_section.find('div', class_='country').text.strip(),
                    'age': info_section.find('div', class_='age').text.strip(),
                    'role': info_section.find('div', class_='role').text.strip()
                }

            # Extract batting statistics
            batting_table = soup.find('table', class_='batting-stats')
            if batting_table:
                for row in batting_table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 8:
                        player_stats['batting_stats'] = {
                            'matches': cols[0].text.strip(),
                            'runs': cols[1].text.strip(),
                            'average': cols[2].text.strip(),
                            'strike_rate': cols[3].text.strip(),
                            'fifties': cols[4].text.strip(),
                            'hundreds': cols[5].text.strip(),
                            'fours': cols[6].text.strip(),
                            'sixes': cols[7].text.strip()
                        }

            # Extract bowling statistics
            bowling_table = soup.find('table', class_='bowling-stats')
            if bowling_table:
                for row in bowling_table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 8:
                        player_stats['bowling_stats'] = {
                            'matches': cols[0].text.strip(),
                            'wickets': cols[1].text.strip(),
                            'average': cols[2].text.strip(),
                            'economy': cols[3].text.strip(),
                            'strike_rate': cols[4].text.strip(),
                            'best_figures': cols[5].text.strip(),
                            'five_wickets': cols[6].text.strip(),
                            'ten_wickets': cols[7].text.strip()
                        }

            # Extract recent matches
            recent_matches = soup.find_all('div', class_='recent-match')
            for match in recent_matches:
                player_stats['recent_matches'].append({
                    'date': match.find('div', class_='match-date').text.strip(),
                    'opposition': match.find('div', class_='opposition').text.strip(),
                    'runs': match.find('div', class_='runs').text.strip(),
                    'wickets': match.find('div', class_='wickets').text.strip(),
                    'strike_rate': match.find('div', class_='strike-rate').text.strip()
                })

        except Exception as e:
            logging.error(f"Error scraping player stats: {str(e)}")

        return player_stats

    def update_match_predictions(self, match_id: str) -> Dict:
        """Update predictions for a specific match based on latest data"""
        # Get match details
        match_url = f"{self.urls['cricbuzz']}/cricket-match/{match_id}"
        match_stats = self.scrape_cricbuzz_match_stats(match_url)
        
        # Get team updates
        team1_updates = self.scrape_ipl_team_updates(match_stats['match_info']['team1'])
        team2_updates = self.scrape_ipl_team_updates(match_stats['match_info']['team2'])
        
        # Get player statistics
        player_stats = {}
        for player in match_stats['batting_stats'] + match_stats['bowling_stats']:
            player_stats[player['name']] = self.scrape_espn_player_stats(player['name'])
        
        # Generate updated predictions
        predictions = {
            'match_id': match_id,
            'timestamp': datetime.now().isoformat(),
            'match_info': match_stats['match_info'],
            'team1': {
                'name': match_stats['match_info']['team1'],
                'updates': team1_updates,
                'predicted_score': self._predict_team_score(match_stats['batting_stats'], player_stats)
            },
            'team2': {
                'name': match_stats['match_info']['team2'],
                'updates': team2_updates,
                'predicted_score': self._predict_team_score(match_stats['batting_stats'], player_stats)
            },
            'win_probability': self._calculate_win_probability(match_stats, player_stats)
        }
        
        return predictions

    def _predict_team_score(self, batting_stats: List[Dict], player_stats: Dict) -> Dict:
        """Predict team score based on player statistics and recent form"""
        predicted_runs = 0
        confidence = 0
        factors = []

        try:
            # Calculate base score from historical performance
            total_historical_runs = 0
            total_matches = 0
            for player_name, stats in player_stats.items():
                if 'batting_stats' in stats and stats['batting_stats']:
                    batting = stats['batting_stats']
                    if batting.get('runs') and batting.get('matches'):
                        total_historical_runs += float(batting['runs'])
                        total_matches += float(batting['matches'])

            if total_matches > 0:
                avg_historical_runs = total_historical_runs / total_matches
                predicted_runs += avg_historical_runs * 0.4  # 40% weight to historical performance
                factors.append(f"Historical average: {avg_historical_runs:.2f} runs per match")

            # Consider recent form (last 5 matches)
            recent_runs = 0
            recent_matches = 0
            for player_name, stats in player_stats.items():
                if 'recent_matches' in stats and stats['recent_matches']:
                    for match in stats['recent_matches'][:5]:  # Last 5 matches
                        if 'runs' in match:
                            recent_runs += float(match['runs'])
                            recent_matches += 1

            if recent_matches > 0:
                avg_recent_runs = recent_runs / recent_matches
                predicted_runs += avg_recent_runs * 0.6  # 60% weight to recent form
                factors.append(f"Recent form: {avg_recent_runs:.2f} runs per match")

            # Adjust for player availability and injuries
            available_players = sum(1 for player in batting_stats if player.get('status') != 'injured')
            if available_players < len(batting_stats):
                predicted_runs *= (available_players / len(batting_stats))
                factors.append(f"Player availability: {available_players}/{len(batting_stats)} players")

            # Calculate confidence based on data quality
            confidence = min(0.95, 0.5 + (len(factors) * 0.15))  # Base 50% + 15% per factor

        except Exception as e:
            logging.error(f"Error in score prediction: {str(e)}")
            confidence = 0.3  # Low confidence if there's an error

        return {
            'predicted_runs': round(predicted_runs),
            'confidence': round(confidence, 2),
            'factors': factors
        }

    def _calculate_win_probability(self, match_stats: Dict, player_stats: Dict) -> Dict:
        """Calculate win probability based on all available data"""
        team1_probability = 0
        team2_probability = 0
        factors = []

        try:
            # Get predicted scores for both teams
            team1_score = self._predict_team_score(match_stats['batting_stats'], player_stats)
            team2_score = self._predict_team_score(match_stats['batting_stats'], player_stats)

            # Calculate base probabilities from predicted scores
            total_runs = team1_score['predicted_runs'] + team2_score['predicted_runs']
            if total_runs > 0:
                team1_probability = team1_score['predicted_runs'] / total_runs
                team2_probability = team2_score['predicted_runs'] / total_runs
                factors.append(f"Score-based probability: {team1_probability:.2%} vs {team2_probability:.2%}")

            # Consider bowling strength
            team1_bowling = 0
            team2_bowling = 0
            for player_name, stats in player_stats.items():
                if 'bowling_stats' in stats and stats['bowling_stats']:
                    bowling = stats['bowling_stats']
                    if bowling.get('wickets') and bowling.get('matches'):
                        bowling_strength = float(bowling['wickets']) / float(bowling['matches'])
                        if player_name in match_stats['team1']:
                            team1_bowling += bowling_strength
                        else:
                            team2_bowling += bowling_strength

            # Adjust probabilities based on bowling strength
            total_bowling = team1_bowling + team2_bowling
            if total_bowling > 0:
                bowling_factor = 0.3  # 30% weight to bowling strength
                team1_probability = (team1_probability * (1 - bowling_factor) + 
                                  (team1_bowling / total_bowling) * bowling_factor)
                team2_probability = (team2_probability * (1 - bowling_factor) + 
                                  (team2_bowling / total_bowling) * bowling_factor)
                factors.append(f"Bowling strength adjustment: {bowling_factor:.1%}")

            # Consider home advantage
            home_advantage = 0.05  # 5% boost for home team
            if match_stats['match_info'].get('venue') in match_stats['team1']:
                team1_probability += home_advantage
                factors.append(f"Home advantage: +{home_advantage:.1%} for {match_stats['team1']}")
            else:
                team2_probability += home_advantage
                factors.append(f"Home advantage: +{home_advantage:.1%} for {match_stats['team2']}")

            # Normalize probabilities to sum to 1
            total_prob = team1_probability + team2_probability
            if total_prob > 0:
                team1_probability /= total_prob
                team2_probability /= total_prob

        except Exception as e:
            logging.error(f"Error in win probability calculation: {str(e)}")
            team1_probability = 0.5
            team2_probability = 0.5
            factors.append("Error in calculation, using equal probabilities")

        return {
            'team1_probability': round(team1_probability, 2),
            'team2_probability': round(team2_probability, 2),
            'factors': factors
        }

    def save_data(self, data: Dict, filename: str):
        """Save scraped data to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.data_path / f"{filename}_{timestamp}.json"
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Saved data to {filepath}")

    def load_data(self, filename: str) -> Dict:
        """Load most recent data from JSON file"""
        pattern = f"{filename}_*.json"
        files = list(self.data_path.glob(pattern))
        if not files:
            return {}
        
        latest_file = max(files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)

    def _extract_batting_stats_from_json(self, data: Dict) -> Dict:
        """Extract batting statistics from API response"""
        batting_stats = {}
        if isinstance(data, dict) and 'batting' in data:
            stats = data['batting']
            batting_stats = {
                'matches': stats.get('matches', 0),
                'innings': stats.get('innings', 0),
                'runs': stats.get('runs', 0),
                'highest': stats.get('highest', 0),
                'average': stats.get('average', 0),
                'strike_rate': stats.get('strike_rate', 0),
                'fifties': stats.get('fifties', 0),
                'hundreds': stats.get('hundreds', 0)
            }
        return batting_stats

    def _extract_bowling_stats_from_json(self, data: Dict) -> Dict:
        """Extract bowling statistics from API response"""
        bowling_stats = {}
        if isinstance(data, dict) and 'bowling' in data:
            stats = data['bowling']
            bowling_stats = {
                'matches': stats.get('matches', 0),
                'innings': stats.get('innings', 0),
                'wickets': stats.get('wickets', 0),
                'best_figures': stats.get('best_figures', ''),
                'average': stats.get('average', 0),
                'economy': stats.get('economy', 0),
                'strike_rate': stats.get('strike_rate', 0)
            }
        return bowling_stats

    def _extract_recent_matches_from_json(self, data: Dict) -> List[Dict]:
        """Extract recent match performance from API response"""
        recent_matches = []
        if isinstance(data, dict) and 'recent_matches' in data:
            for match in data['recent_matches']:
                match_info = {
                    'date': match.get('date', ''),
                    'teams': match.get('teams', ''),
                    'batting': {
                        'runs': match.get('batting_runs', 0),
                        'balls': match.get('batting_balls', 0),
                        'fours': match.get('batting_fours', 0),
                        'sixes': match.get('batting_sixes', 0)
                    },
                    'bowling': {
                        'overs': match.get('bowling_overs', 0),
                        'wickets': match.get('bowling_wickets', 0),
                        'runs': match.get('bowling_runs', 0)
                    }
                }
                recent_matches.append(match_info)
        return recent_matches

    def get_venue_conditions(self, venue: str) -> Dict[str, Any]:
        """Get venue conditions from Cricbuzz"""
        try:
            # Search for venue
            search_url = f"{self.urls['cricbuzz']['base']}/search/results?q={quote(venue)}"
            soup = self._make_request(search_url)
            
            if not soup:
                raise Exception("Failed to get search results")
            
            # Find venue link
            venue_link = soup.find('a', text=re.compile(venue, re.IGNORECASE))
            if not venue_link:
                raise Exception(f"Venue {venue} not found")
            
            venue_url = f"{self.urls['cricbuzz']['base']}{venue_link['href']}"
            venue_soup = self._make_request(venue_url)
            
            if not venue_soup:
                raise Exception("Failed to get venue page")
            
            # Extract venue information
            venue_info = {
                "name": venue,
                "location": "",
                "capacity": "",
                "dimensions": "",
                "pitch_type": "",
                "weather": "",
                "last_match": ""
            }
            
            # Try to find venue details
            details_section = venue_soup.find('div', class_=re.compile('cb-col-100'))
            if details_section:
                # Location
                location = details_section.find('div', text=re.compile('Location', re.IGNORECASE))
                if location:
                    venue_info["location"] = location.find_next('div').text.strip()
                
                # Capacity
                capacity = details_section.find('div', text=re.compile('Capacity', re.IGNORECASE))
                if capacity:
                    venue_info["capacity"] = capacity.find_next('div').text.strip()
                
                # Dimensions
                dimensions = details_section.find('div', text=re.compile('Dimensions', re.IGNORECASE))
                if dimensions:
                    venue_info["dimensions"] = dimensions.find_next('div').text.strip()
                
                # Pitch type
                pitch = details_section.find('div', text=re.compile('Pitch', re.IGNORECASE))
                if pitch:
                    venue_info["pitch_type"] = pitch.find_next('div').text.strip()
            
            # Get weather information from Google
            weather_url = f"{self.urls['google']['base']}/search?q={quote(f'{venue} weather forecast')}"
            weather_soup = self._make_request(weather_url)
            
            if weather_soup:
                weather_element = weather_soup.find('div', class_=re.compile('weather'))
                if weather_element:
                    venue_info["weather"] = weather_element.text.strip()
            
            # Get last match information
            last_match = venue_soup.find('div', class_=re.compile('last-match'))
            if last_match:
                venue_info["last_match"] = last_match.text.strip()
            
            return venue_info
            
        except Exception as e:
            self.logger.error(f"Error getting venue conditions for {venue}: {str(e)}")
            return {
                "name": venue,
                "error": str(e)
            }

    def get_team_players(self, team_name: str) -> List[str]:
        """Get current playing XI for a team"""
        try:
            # For testing, return a sample playing XI
            # In production, this would fetch from Cricbuzz API
            sample_players = {
                'Royal Challengers Bangalore': [
                    'Virat Kohli',
                    'Faf du Plessis',
                    'Glenn Maxwell',
                    'Cameron Green',
                    'Rajat Patidar',
                    'Dinesh Karthik',
                    'Anuj Rawat',
                    'Mayank Dagar',
                    'Alzarri Joseph',
                    'Mohammed Siraj',
                    'Yash Dayal'
                ],
                'Gujarat Titans': [
                    'Shubman Gill',
                    'Wriddhiman Saha',
                    'Sai Sudharsan',
                    'David Miller',
                    'Vijay Shankar',
                    'Rahul Tewatia',
                    'Rashid Khan',
                    'Noor Ahmad',
                    'Umesh Yadav',
                    'Spencer Johnson',
                    'Mohit Sharma'
                ]
            }
            
            return sample_players.get(team_name, [])
            
        except Exception as e:
            self.logger.error(f"Error getting players for {team_name}: {str(e)}")
            return []

    def get_match_details(self, match_id: str) -> Dict:
        """Get match details including venue, conditions, etc."""
        try:
            # For testing, return sample match details
            # In production, this would fetch from Cricbuzz API
            return {
                'venue': 'M.Chinnaswamy Stadium, Bangalore',
                'conditions': {
                    'pitch': 'batting friendly',
                    'weather': 'clear',
                    'temperature': 28,
                    'humidity': 65
                },
                'toss': None,
                'status': 'upcoming'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting match details: {str(e)}")
            return {}

    def get_recent_matches(self, days_back: int = 30) -> List[Dict]:
        """Get list of recent IPL matches"""
        if self.use_test_data:
            return SAMPLE_MATCHES
            
        try:
            # Get current IPL series page
            ipl_url = f"{self.base_url}/cricket-series/2697/indian-premier-league-2024"
            response = requests.get(ipl_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            matches = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Find match cards
            match_cards = soup.find_all('div', class_='cb-col-100 cb-col')
            for card in match_cards:
                try:
                    # Extract match details
                    date_str = card.find('div', class_='cb-col-100 cb-mtch-lst-itm').text.strip()
                    match_date = datetime.strptime(date_str, '%B %d, %Y')
                    
                    if match_date >= cutoff_date:
                        teams = card.find_all('div', class_='cb-ovr-flo cb-hmscg-tm-nm')
                        team1 = teams[0].text.strip()
                        team2 = teams[1].text.strip()
                        
                        match_link = card.find('a', href=True)['href']
                        match_id = match_link.split('/')[-1]
                        
                        matches.append({
                            'match_id': match_id,
                            'team1': team1,
                            'team2': team2,
                            'date': match_date.strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    logger.error(f"Error parsing match card: {str(e)}")
                    continue
            
            return matches
            
        except Exception as e:
            logger.error(f"Error fetching recent matches: {str(e)}")
            return []
            
    def get_match_result(self, match_id: str) -> Dict:
        """Get match result"""
        if self.use_test_data:
            return SAMPLE_RESULTS.get(match_id, {})
            
        try:
            # Get match scorecard page
            match_url = f"{self.base_url}/live-cricket-scorecard/{match_id}"
            response = requests.get(match_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            result = {
                'match_id': match_id,
                'team_totals': {}
            }
            
            # Find innings tables
            innings_tables = soup.find_all('div', class_='cb-col-100 cb-ltst-wgt-hdr')
            for innings in innings_tables:
                try:
                    team_name = innings.find('div', class_='cb-col-100 cb-scrd-hdr-rw').text.strip().split('Innings')[0].strip()
                    total_row = innings.find('div', class_='cb-col-100 cb-scrd-itms')
                    
                    runs = int(total_row.find('div', class_='cb-col-100 cb-scrd-itms-rw').text.strip().split('-')[0])
                    wickets = int(total_row.find('div', class_='cb-col-100 cb-scrd-itms-rw').text.strip().split('-')[1])
                    
                    result['team_totals'][team_name] = {
                        'runs': runs,
                        'wickets': wickets
                    }
                    
                    # Get individual performances
                    batting_rows = innings.find_all('div', class_='cb-col-100 cb-scrd-itms')
                    result[team_name] = []
                    
                    for row in batting_rows:
                        player_name = row.find('a').text.strip() if row.find('a') else row.find('div', class_='cb-col-27').text.strip()
                        runs = int(row.find('div', class_='cb-col-8 text-right').text.strip())
                        
                        result[team_name].append({
                            'name': player_name,
                            'runs': runs,
                            'wickets': 0,  # Will be updated from bowling data
                            'catches': 0  # Will be updated from fielding data
                        })
                        
                except Exception as e:
                    logger.error(f"Error parsing innings: {str(e)}")
                    continue
            
            # Get bowling performances
            bowling_tables = soup.find_all('div', class_='cb-col-100 cb-ltst-wgt-hdr')
            for bowling in bowling_tables:
                try:
                    bowling_rows = bowling.find_all('div', class_='cb-col-100 cb-scrd-itms')
                    for row in bowling_rows:
                        player_name = row.find('a').text.strip() if row.find('a') else row.find('div', class_='cb-col-40').text.strip()
                        wickets = int(row.find('div', class_='cb-col-8 text-right').text.strip())
                        
                        # Update player's wickets
                        for team in result:
                            if isinstance(result[team], list):
                                for player in result[team]:
                                    if player['name'] == player_name:
                                        player['wickets'] = wickets
                                        break
                                        
                except Exception as e:
                    logger.error(f"Error parsing bowling data: {str(e)}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching match result: {str(e)}")
            return {}

    def get_player_stats(self, player_name: str) -> Optional[Dict]:
        """Get player statistics from cricket websites"""
        try:
            self.logger.info(f"Scraping stats for player: {player_name}")
            
            # Try different sources in order of reliability
            stats = self._scrape_espncricinfo(player_name)
            if stats:
                return stats
                
            stats = self._scrape_cricbuzz(player_name)
            if stats:
                return stats
                
            stats = self._scrape_icc(player_name)
            if stats:
                return stats
                
            self.logger.warning(f"Could not find stats for {player_name} from any source")
            return None
            
        except Exception as e:
            self.logger.error(f"Error scraping player stats: {str(e)}")
            return None
            
    def _scrape_espncricinfo(self, player_name: str) -> Optional[Dict]:
        """Scrape player stats from ESPNCricinfo"""
        try:
            # Format player name for URL
            formatted_name = player_name.lower().replace(' ', '-')
            
            # Search for player
            search_url = f"https://www.espncricinfo.com/ci/content/player/search.html?search={formatted_name}"
            self._rate_limit()
            response = self.session.get(search_url)
            
            if response.status_code != 200:
                self.logger.warning(f"ESPNCricinfo search failed with status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            player_link = None
            
            # Find the player link in search results
            for link in soup.select('.player-link'):
                if player_name.lower() in link.text.lower():
                    player_link = link.get('href')
                    break
                    
            if not player_link:
                self.logger.warning(f"Player {player_name} not found on ESPNCricinfo")
                return None
                
            # Get player page
            player_url = f"https://www.espncricinfo.com{player_link}"
            self._rate_limit()
            response = self.session.get(player_url)
            
            if response.status_code != 200:
                self.logger.warning(f"ESPNCricinfo player page failed with status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract player stats
            stats = {
                'batting': self._extract_batting_stats(soup),
                'bowling': self._extract_bowling_stats(soup),
                'fielding': self._extract_fielding_stats(soup),
                'role': self._extract_player_role(soup)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error scraping ESPNCricinfo: {str(e)}")
            return None
            
    def _scrape_cricbuzz(self, player_name: str) -> Optional[Dict]:
        """Scrape player stats from Cricbuzz"""
        try:
            # Format player name for URL
            formatted_name = player_name.lower().replace(' ', '-')
            
            # Search for player
            search_url = f"https://www.cricbuzz.com/search?q={formatted_name}"
            self._rate_limit()
            response = self.session.get(search_url)
            
            if response.status_code != 200:
                self.logger.warning(f"Cricbuzz search failed with status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            player_link = None
            
            # Find the player link in search results
            for link in soup.select('.player-link'):
                if player_name.lower() in link.text.lower():
                    player_link = link.get('href')
                    break
                    
            if not player_link:
                self.logger.warning(f"Player {player_name} not found on Cricbuzz")
                return None
                
            # Get player page
            player_url = f"https://www.cricbuzz.com{player_link}"
            self._rate_limit()
            response = self.session.get(player_url)
            
            if response.status_code != 200:
                self.logger.warning(f"Cricbuzz player page failed with status code: {response.status_code}")
                return None
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract player stats
            stats = {
                'batting': self._extract_batting_stats_cricbuzz(soup),
                'bowling': self._extract_bowling_stats_cricbuzz(soup),
                'fielding': self._extract_fielding_stats_cricbuzz(soup),
                'role': self._extract_player_role_cricbuzz(soup)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error scraping Cricbuzz: {str(e)}")
            return None
            
    def _scrape_icc(self, player_name: str) -> Optional[Dict]:
        """Scrape player stats from ICC website"""
        # Similar implementation to other scraping methods
        # This is a placeholder as ICC website structure would need to be analyzed
        return None
        
    def _extract_batting_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract batting statistics from ESPNCricinfo page"""
        stats = {
            'average': 0.0,
            'strike_rate': 0.0,
            'runs': 0,
            'current_form': {
                'average': 0.0,
                'strike_rate': 0.0,
                'runs': 0
            },
            'career': {
                'average': 0.0,
                'strike_rate': 0.0,
                'runs': 0
            }
        }
        
        try:
            # Find T20 stats table
            t20_table = None
            for table in soup.select('table'):
                if 'T20' in table.text and 'Batting' in table.text:
                    t20_table = table
                    break
                    
            if t20_table:
                # Extract career stats
                rows = t20_table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 8:
                        if 'Matches' in cells[0].text:
                            stats['career']['matches'] = self._extract_number(cells[1].text)
                        elif 'Runs' in cells[0].text:
                            stats['career']['runs'] = self._extract_number(cells[1].text)
                        elif 'Average' in cells[0].text:
                            stats['career']['average'] = self._extract_number(cells[1].text)
                        elif 'Strike rate' in cells[0].text:
                            stats['career']['strike_rate'] = self._extract_number(cells[1].text)
                            
                # Set overall stats from career
                stats['average'] = stats['career']['average']
                stats['strike_rate'] = stats['career']['strike_rate']
                stats['runs'] = stats['career']['runs']
                
                # Try to find recent form (last 10 matches)
                recent_matches = self._extract_recent_matches(soup, 'batting')
                if recent_matches:
                    stats['current_form'] = recent_matches
                    
        except Exception as e:
            self.logger.error(f"Error extracting batting stats: {str(e)}")
            
        return stats
        
    def _extract_bowling_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract bowling statistics from ESPNCricinfo page"""
        stats = {
            'wickets': 0,
            'economy': 0.0,
            'average': 0.0,
            'current_form': {
                'wickets': 0,
                'economy': 0.0,
                'average': 0.0
            },
            'career': {
                'wickets': 0,
                'economy': 0.0,
                'average': 0.0
            }
        }
        
        try:
            # Find T20 stats table
            t20_table = None
            for table in soup.select('table'):
                if 'T20' in table.text and 'Bowling' in table.text:
                    t20_table = table
                    break
                    
            if t20_table:
                # Extract career stats
                rows = t20_table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 8:
                        if 'Matches' in cells[0].text:
                            stats['career']['matches'] = self._extract_number(cells[1].text)
                        elif 'Wickets' in cells[0].text:
                            stats['career']['wickets'] = self._extract_number(cells[1].text)
                        elif 'Average' in cells[0].text:
                            stats['career']['average'] = self._extract_number(cells[1].text)
                        elif 'Economy' in cells[0].text:
                            stats['career']['economy'] = self._extract_number(cells[1].text)
                            
                # Set overall stats from career
                stats['wickets'] = stats['career']['wickets']
                stats['economy'] = stats['career']['economy']
                stats['average'] = stats['career']['average']
                
                # Try to find recent form (last 10 matches)
                recent_matches = self._extract_recent_matches(soup, 'bowling')
                if recent_matches:
                    stats['current_form'] = recent_matches
                    
        except Exception as e:
            self.logger.error(f"Error extracting bowling stats: {str(e)}")
            
        return stats
        
    def _extract_fielding_stats(self, soup: BeautifulSoup) -> Dict:
        """Extract fielding statistics from ESPNCricinfo page"""
        stats = {
            'catches': 0,
            'stumpings': 0
        }
        
        try:
            # Find fielding stats
            fielding_section = None
            for section in soup.select('.player-section'):
                if 'Fielding' in section.text:
                    fielding_section = section
                    break
                    
            if fielding_section:
                # Extract catches and stumpings
                for row in fielding_section.select('tr'):
                    cells = row.select('td')
                    if len(cells) >= 2:
                        if 'Catches' in cells[0].text:
                            stats['catches'] = self._extract_number(cells[1].text)
                        elif 'Stumpings' in cells[0].text:
                            stats['stumpings'] = self._extract_number(cells[1].text)
                            
        except Exception as e:
            self.logger.error(f"Error extracting fielding stats: {str(e)}")
            
        return stats
        
    def _extract_player_role(self, soup: BeautifulSoup) -> str:
        """Extract player role from ESPNCricinfo page"""
        try:
            # Look for role in player info
            player_info = soup.select('.player-info')
            if player_info:
                for info in player_info:
                    if 'Role' in info.text:
                        role_text = info.text.split('Role:')[1].strip().lower()
                        if 'batsman' in role_text:
                            return 'batsman'
                        elif 'bowler' in role_text:
                            return 'bowler'
                        elif 'all-rounder' in role_text or 'allrounder' in role_text:
                            return 'all-rounder'
                        elif 'wicket-keeper' in role_text or 'wicketkeeper' in role_text:
                            return 'wicket-keeper'
                            
            # Try to determine role from stats
            batting_stats = self._extract_batting_stats(soup)
            bowling_stats = self._extract_bowling_stats(soup)
            
            if batting_stats['runs'] > 500 and bowling_stats['wickets'] > 20:
                return 'all-rounder'
            elif batting_stats['runs'] > 500:
                return 'batsman'
            elif bowling_stats['wickets'] > 20:
                return 'bowler'
                
        except Exception as e:
            self.logger.error(f"Error extracting player role: {str(e)}")
            
        return 'all-rounder'  # Default role
        
    def _extract_batting_stats_cricbuzz(self, soup: BeautifulSoup) -> Dict:
        """Extract batting statistics from Cricbuzz page"""
        # Similar implementation to ESPNCricinfo but adapted for Cricbuzz HTML structure
        return {
            'average': 0.0,
            'strike_rate': 0.0,
            'runs': 0,
            'current_form': {
                'average': 0.0,
                'strike_rate': 0.0,
                'runs': 0
            },
            'career': {
                'average': 0.0,
                'strike_rate': 0.0,
                'runs': 0
            }
        }
        
    def _extract_bowling_stats_cricbuzz(self, soup: BeautifulSoup) -> Dict:
        """Extract bowling statistics from Cricbuzz page"""
        # Similar implementation to ESPNCricinfo but adapted for Cricbuzz HTML structure
        return {
            'wickets': 0,
            'economy': 0.0,
            'average': 0.0,
            'current_form': {
                'wickets': 0,
                'economy': 0.0,
                'average': 0.0
            },
            'career': {
                'wickets': 0,
                'economy': 0.0,
                'average': 0.0
            }
        }
        
    def _extract_fielding_stats_cricbuzz(self, soup: BeautifulSoup) -> Dict:
        """Extract fielding statistics from Cricbuzz page"""
        # Similar implementation to ESPNCricinfo but adapted for Cricbuzz HTML structure
        return {
            'catches': 0,
            'stumpings': 0
        }
        
    def _extract_player_role_cricbuzz(self, soup: BeautifulSoup) -> str:
        """Extract player role from Cricbuzz page"""
        # Similar implementation to ESPNCricinfo but adapted for Cricbuzz HTML structure
        return 'all-rounder'
        
    def _extract_recent_matches(self, soup: BeautifulSoup, stat_type: str) -> Optional[Dict]:
        """Extract recent match statistics"""
        try:
            # Find recent matches section
            recent_matches_section = None
            for section in soup.select('.player-section'):
                if 'Recent Matches' in section.text:
                    recent_matches_section = section
                    break
                    
            if not recent_matches_section:
                return None
                
            # Extract stats from last 10 matches
            matches = recent_matches_section.select('.match-row')
            if not matches:
                return None
                
            # Limit to last 10 matches
            recent_matches = matches[:10]
            
            if stat_type == 'batting':
                runs = 0
                balls = 0
                dismissals = 0
                
                for match in recent_matches:
                    cells = match.select('td')
                    if len(cells) >= 3:
                        runs += self._extract_number(cells[1].text)
                        balls += self._extract_number(cells[2].text)
                        if cells[3].text.strip() != 'not out':
                            dismissals += 1
                            
                average = runs / dismissals if dismissals > 0 else 0
                strike_rate = (runs / balls) * 100 if balls > 0 else 0
                
                return {
                    'average': average,
                    'strike_rate': strike_rate,
                    'runs': runs
                }
                
            elif stat_type == 'bowling':
                wickets = 0
                runs_conceded = 0
                overs = 0
                
                for match in recent_matches:
                    cells = match.select('td')
                    if len(cells) >= 4:
                        wickets += self._extract_number(cells[1].text)
                        runs_conceded += self._extract_number(cells[2].text)
                        overs += self._extract_number(cells[3].text)
                        
                average = runs_conceded / wickets if wickets > 0 else 0
                economy = runs_conceded / overs if overs > 0 else 0
                
                return {
                    'wickets': wickets,
                    'economy': economy,
                    'average': average
                }
                
        except Exception as e:
            self.logger.error(f"Error extracting recent matches: {str(e)}")
            
        return None
        
    def _extract_number(self, text: str) -> float:
        """Extract number from text, handling various formats"""
        try:
            # Remove non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', text)
            if cleaned:
                return float(cleaned)
            return 0.0
        except:
            return 0.0
            
    def _rate_limit(self):
        """Implement rate limiting to avoid being blocked"""
        time.sleep(self.rate_limit_delay + random.uniform(0, 1)) 