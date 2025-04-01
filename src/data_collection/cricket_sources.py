import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from typing import Dict, List, Optional
import time
import re
import random
from fake_useragent import UserAgent
from requests.exceptions import RequestException
import json
from pathlib import Path

class CricketDataSources:
    def __init__(self):
        self.ua = UserAgent()
        self.base_path = Path(__file__).parent.parent.parent
        self.config_path = self.base_path / 'config'
        self.config_path.mkdir(parents=True, exist_ok=True)
        
        # Load proxy list if available
        self.proxies = self._load_proxies()
        
        # Updated URLs with correct paths for IPL 2025
        self.urls = {
            'cricinfo': {
                'base': 'https://www.espncricinfo.com',
                'news': '/cricket-news',
                'player': '/player',
                'venue': '/ground',
                'match': '/series/indian-premier-league-2025'
            },
            'cricbuzz': {
                'base': 'https://www.cricbuzz.com',
                'series': '/cricket-series/9237/Indian-Premier-League-2025',
                'matches': '/cricket-series/9237/indian-premier-league-2025/matches',
                'news': '/cricket-series/9237/indian-premier-league-2025/news',
                'points_table': '/cricket-series/9237/indian-premier-league-2025/points-table',
                'stats': '/cricket-series/9237/indian-premier-league-2025/stats',
                'wicket_zone': '/special-content/wicket-zone/9237/indian-premier-league-2025',
                'player': '/profiles',
                'venue': '/cricket-stadium'
            },
            'iplt20': {
                'base': 'https://www.iplt20.com',
                'teams': '/teams',
                'stats': '/stats',
                'news': '/news'
            }
        }

    def _load_proxies(self) -> List[str]:
        """Load proxy list from config file"""
        proxy_file = self.config_path / 'proxies.json'
        if proxy_file.exists():
            with open(proxy_file, 'r') as f:
                return json.load(f)
        return []

    def _get_headers(self) -> Dict:
        """Get randomized headers to mimic different browsers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1'
        }

    def _make_request(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Make HTTP request with retry mechanism, rotating user agents and proxies"""
        for attempt in range(retries):
            try:
                # Add random delay between requests
                time.sleep(random.uniform(2, 5))
                
                # Get random proxy if available
                proxy = None
                if self.proxies:
                    proxy = {'http': random.choice(self.proxies), 'https': random.choice(self.proxies)}
                
                # Make request with current configuration
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    proxies=proxy,
                    timeout=15,
                    allow_redirects=True
                )
                
                # Check response
                response.raise_for_status()
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    logging.warning(f"Received non-HTML response from {url}")
                    continue
                
                # Parse and validate HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                if not soup.find():  # Check if parsed HTML is empty
                    logging.warning(f"Received empty HTML from {url}")
                    continue
                    
                return soup
                
            except RequestException as e:
                logging.error(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(1, 3)
                    time.sleep(delay)
                continue
            except Exception as e:
                logging.error(f"Unexpected error for {url}: {str(e)}")
                continue
        return None

    def get_player_injury_updates(self) -> List[Dict]:
        """Get injury updates from multiple sources"""
        injury_updates = []
        
        # Try CricInfo
        urls = [
            f"{self.urls['cricinfo']['base']}{self.urls['cricinfo']['news']}/topic/injury-updates",
            f"{self.urls['cricbuzz']['base']}{self.urls['cricbuzz']['news']}/injury-updates",
            f"{self.urls['iplt20']['base']}{self.urls['iplt20']['news']}/medical-updates"
        ]
        
        for url in urls:
            soup = self._make_request(url)
            if soup:
                try:
                    # Look for news items with different possible class names
                    news_items = (
                        soup.find_all('div', class_='news-item') or
                        soup.find_all('article', class_='story') or
                        soup.find_all('div', class_='article-item')
                    )
                    
                    for news in news_items:
                        title = (
                            news.find('h3') or 
                            news.find('h2') or 
                            news.find('div', class_='title')
                        )
                        content = (
                            news.find('p') or 
                            news.find('div', class_='description') or
                            news.find('div', class_='content')
                        )
                        
                        if title and content and any(kw in title.text.lower() for kw in ['injury', 'medical', 'fitness']):
                            injury_updates.append({
                                'source': url.split('/')[2],
                                'player': title.text.strip(),
                                'status': content.text.strip(),
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'url': url
                            })
                except Exception as e:
                    logging.error(f"Error parsing injury updates from {url}: {str(e)}")

        return injury_updates

    def get_team_composition_changes(self, team_name: str) -> List[Dict]:
        """Get team composition changes from multiple sources"""
        changes = []
        
        # Try multiple URL patterns
        team_slug = team_name.lower().replace(' ', '-')
        urls = [
            f"{self.urls['iplt20']['base']}{self.urls['iplt20']['teams']}/{team_slug}",
            f"{self.urls['cricbuzz']['base']}/teams/{team_slug}",
            f"{self.urls['cricinfo']['base']}/team/{team_slug}"
        ]
        
        for url in urls:
            soup = self._make_request(url)
            if soup:
                try:
                    # Look for updates with different possible class names
                    update_items = (
                        soup.find_all('div', class_='squad-update') or
                        soup.find_all('div', class_='team-news') or
                        soup.find_all('div', class_='update-item')
                    )
                    
                    for update in update_items:
                        type_elem = (
                            update.find('div', class_='update-type') or
                            update.find('div', class_='news-type') or
                            update.find('span', class_='category')
                        )
                        details_elem = (
                            update.find('div', class_='update-details') or
                            update.find('div', class_='news-content') or
                            update.find('p')
                        )
                        
                        if type_elem and details_elem:
                            changes.append({
                                'source': url.split('/')[2],
                                'team': team_name,
                                'type': type_elem.text.strip(),
                                'details': details_elem.text.strip(),
                                'date': datetime.now().strftime('%Y-%m-%d'),
                                'url': url
                            })
                except Exception as e:
                    logging.error(f"Error parsing team changes from {url}: {str(e)}")

        return changes

    def get_venue_conditions(self, venue: str) -> Dict:
        """Get venue conditions and pitch reports from multiple sources"""
        conditions = {
            'venue': venue,
            'pitch_report': {},
            'weather': {},
            'historical_stats': {}
        }

        venue_slug = venue.lower().replace(' ', '-').replace('.', '')
        urls = {
            'pitch': [
                f"{self.urls['cricinfo']['base']}{self.urls['cricinfo']['venue']}/{venue_slug}/pitch-report",
                f"{self.urls['cricbuzz']['base']}/cricket-stadium/{venue_slug}/pitch-report"
            ],
            'weather': [
                f"{self.urls['cricbuzz']['base']}/cricket-stadium/{venue_slug}/weather",
                f"{self.urls['cricinfo']['base']}{self.urls['cricinfo']['venue']}/{venue_slug}/weather"
            ],
            'stats': [
                f"{self.urls['cricinfo']['base']}{self.urls['cricinfo']['venue']}/{venue_slug}/stats",
                f"{self.urls['cricbuzz']['base']}/cricket-stadium/{venue_slug}/stats"
            ]
        }

        # Get pitch report
        for url in urls['pitch']:
            soup = self._make_request(url)
            if soup:
                try:
                    pitch_info = (
                        soup.find('div', class_='pitch-report') or
                        soup.find('div', class_='venue-pitch') or
                        soup.find('section', class_='pitch-conditions')
                    )
                    if pitch_info:
                        conditions['pitch_report'] = {
                            'type': (pitch_info.find('div', class_='pitch-type') or pitch_info.find('span', class_='type')).text.strip(),
                            'description': (pitch_info.find('div', class_='pitch-description') or pitch_info.find('p')).text.strip(),
                            'last_updated': datetime.now().strftime('%Y-%m-%d'),
                            'source': url
                        }
                        break
                except Exception as e:
                    logging.error(f"Error parsing pitch report from {url}: {str(e)}")

        # Get weather data
        for url in urls['weather']:
            soup = self._make_request(url)
            if soup:
                try:
                    weather_info = (
                        soup.find('div', class_='weather-forecast') or
                        soup.find('div', class_='weather-info') or
                        soup.find('section', class_='weather-conditions')
                    )
                    if weather_info:
                        conditions['weather'] = {
                            'temperature': self._extract_text(weather_info, ['temperature', 'temp']),
                            'humidity': self._extract_text(weather_info, ['humidity', 'humid']),
                            'wind_speed': self._extract_text(weather_info, ['wind-speed', 'wind']),
                            'forecast': self._extract_text(weather_info, ['forecast', 'prediction']),
                            'source': url
                        }
                        break
                except Exception as e:
                    logging.error(f"Error parsing weather info from {url}: {str(e)}")

        # Get historical statistics
        for url in urls['stats']:
            soup = self._make_request(url)
            if soup:
                try:
                    stats = (
                        soup.find('div', class_='venue-stats') or
                        soup.find('div', class_='ground-stats') or
                        soup.find('section', class_='stadium-statistics')
                    )
                    if stats:
                        conditions['historical_stats'] = {
                            'total_matches': self._extract_text(stats, ['total-matches', 'matches-played']),
                            'avg_first_innings': self._extract_text(stats, ['avg-first-innings', 'first-inns-avg']),
                            'avg_second_innings': self._extract_text(stats, ['avg-second-innings', 'second-inns-avg']),
                            'highest_total': self._extract_text(stats, ['highest-total', 'highest-score']),
                            'lowest_total': self._extract_text(stats, ['lowest-total', 'lowest-score']),
                            'source': url
                        }
                        break
                except Exception as e:
                    logging.error(f"Error parsing venue stats from {url}: {str(e)}")

        return conditions

    def _extract_text(self, soup_element: BeautifulSoup, possible_classes: List[str]) -> str:
        """Helper method to extract text from elements with different possible class names"""
        for class_name in possible_classes:
            element = soup_element.find('div', class_=class_name)
            if element:
                return element.text.strip()
        return "N/A"

    def get_player_form(self, player_name: str) -> Dict:
        """Get detailed player form and statistics from multiple sources"""
        player_data = {
            'name': player_name,
            'recent_performance': [],
            'head_to_head': {},
            'venue_stats': {},
            'fitness_status': {}
        }

        # Get recent performance from CricInfo
        soup = self._make_request(f"{self.urls['cricinfo']['base']}{self.urls['cricinfo']['player']}/{player_name.lower().replace(' ', '-')}")
        if soup:
            recent_matches = soup.find_all('div', class_='recent-match')
            for match in recent_matches:
                player_data['recent_performance'].append({
                    'date': match.find('div', class_='match-date').text.strip(),
                    'opposition': match.find('div', class_='opposition').text.strip(),
                    'runs': match.find('div', class_='runs').text.strip(),
                    'wickets': match.find('div', class_='wickets').text.strip(),
                    'strike_rate': match.find('div', class_='strike-rate').text.strip()
                })

        # Get head-to-head statistics
        soup = self._make_request(f"{self.urls['cricbuzz']['base']}{self.urls['cricbuzz']['player']}/{player_name.lower().replace(' ', '-')}/head-to-head")
        if soup:
            h2h_stats = soup.find('div', class_='head-to-head-stats')
            if h2h_stats:
                player_data['head_to_head'] = {
                    'opposition': h2h_stats.find('div', class_='opposition').text.strip(),
                    'matches': h2h_stats.find('div', class_='matches').text.strip(),
                    'runs': h2h_stats.find('div', class_='runs').text.strip(),
                    'wickets': h2h_stats.find('div', class_='wickets').text.strip(),
                    'average': h2h_stats.find('div', class_='average').text.strip()
                }

        # Get venue-specific statistics
        soup = self._make_request(f"{self.urls['cricbuzz']['base']}/cricket-stadium/{player_name.lower().replace(' ', '-')}/venue-stats")
        if soup:
            venue_stats = soup.find_all('div', class_='venue-stat')
            for stat in venue_stats:
                venue = stat.find('div', class_='venue-name').text.strip()
                player_data['venue_stats'][venue] = {
                    'matches': stat.find('div', class_='matches').text.strip(),
                    'runs': stat.find('div', class_='runs').text.strip(),
                    'wickets': stat.find('div', class_='wickets').text.strip(),
                    'average': stat.find('div', class_='average').text.strip()
                }

        return player_data 