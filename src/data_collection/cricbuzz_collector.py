import requests
import json
from datetime import datetime
import logging
from typing import Dict, List, Optional
import time
from pathlib import Path

class CricbuzzCollector:
    def __init__(self):
        self.base_url = "https://cricbuzz-cricket.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": "e25a618be3msh09379c7fc6ba226p187977jsnd56e4bd0e1c4",
            "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
        }
        self.logger = logging.getLogger(__name__)
        self._cache = {}
        self._cache_duration = 3600  # Cache for 1 hour
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests

    def _make_request(self, url: str, headers: Dict) -> Optional[Dict]:
        """Make a rate-limited request to Cricbuzz API"""
        # Ensure minimum time between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        
        try:
            response = requests.get(url, headers=headers)
            self._last_request_time = time.time()
            
            if response.status_code == 429:
                self.logger.warning("Rate limit hit, waiting 5 seconds...")
                time.sleep(5)
                return self._make_request(url, headers)  # Retry after waiting
                
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Request failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error making request: {str(e)}")
            return None

    def get_player_stats(self, player_name: str) -> Dict:
        """Get player's recent stats and form from Cricbuzz"""
        try:
            # Check cache first
            cache_key = f"player_stats_{player_name}"
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if (datetime.now() - cached_data['timestamp']).total_seconds() < self._cache_duration:
                    self.logger.info(f"Using cached stats for {player_name}")
                    return cached_data['data']
            
            # First search for player ID
            search_url = f"{self.base_url}/stats/v1/player/search"
            params = {"plrN": player_name}
            
            response = self._make_request(search_url, self.headers)
            if response is None:
                self.logger.warning(f"Failed to search for player {player_name}")
                return self._get_fallback_stats(player_name)
                
            search_data = response
            if not search_data.get('player'):
                self.logger.warning(f"No player found for {player_name}")
                return self._get_fallback_stats(player_name)
                
            player_id = search_data['player'][0]['id']
            
            # Get player's batting stats
            batting_url = f"{self.base_url}/stats/v1/player/{player_id}/batting"
            batting_response = self._make_request(batting_url, self.headers)
            batting_stats = batting_response if batting_response else {}
            
            # Get player's bowling stats
            bowling_url = f"{self.base_url}/stats/v1/player/{player_id}/bowling"
            bowling_response = self._make_request(bowling_url, self.headers)
            bowling_stats = bowling_response if bowling_response else {}
            
            # Get player's career stats
            career_url = f"{self.base_url}/stats/v1/player/{player_id}/career"
            career_response = self._make_request(career_url, self.headers)
            career_stats = career_response if career_response else {}
            
            # Combine all stats
            combined_stats = {
                'batting': {
                    'current_form': {
                        'average': batting_stats.get('average', 0),
                        'strike_rate': batting_stats.get('strike_rate', 0),
                        'runs': batting_stats.get('runs', 0)
                    },
                    'career': {
                        'average': career_stats.get('batting_average', 0),
                        'strike_rate': career_stats.get('batting_strike_rate', 0),
                        'runs': career_stats.get('runs_scored', 0)
                    }
                },
                'bowling': {
                    'current_form': {
                        'wickets': bowling_stats.get('wickets', 0),
                        'economy': bowling_stats.get('economy', 0),
                        'average': bowling_stats.get('average', 0)
                    },
                    'career': {
                        'wickets': career_stats.get('wickets_taken', 0),
                        'economy': career_stats.get('economy_rate', 0),
                        'average': career_stats.get('bowling_average', 0)
                    }
                }
            }
            
            # Cache the results
            self._cache[cache_key] = {
                'data': combined_stats,
                'timestamp': datetime.now()
            }
            
            return combined_stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats for {player_name}: {str(e)}")
            return self._get_fallback_stats(player_name)
    
    def _get_fallback_stats(self, player_name: str) -> Dict:
        """Get fallback stats when API fails"""
        # Try to get data from local cache first
        cache_file = Path(__file__).parent.parent.parent / 'data' / 'cache' / 'player_stats.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_stats = json.load(f)
                    if player_name in cached_stats:
                        return cached_stats[player_name]
            except Exception as e:
                self.logger.error(f"Error reading cache file: {str(e)}")
        
        # Return default stats based on player role
        role = self._guess_player_role(player_name)
        if role == "batsman":
            return {
                'batting': {
                    'current_form': {'average': 25.0, 'strike_rate': 130.0, 'runs': 100},
                    'career': {'average': 30.0, 'strike_rate': 140.0, 'runs': 1000}
                },
                'bowling': {
                    'current_form': {'wickets': 0, 'economy': 0, 'average': 0},
                    'career': {'wickets': 0, 'economy': 0, 'average': 0}
                }
            }
        elif role == "bowler":
            return {
                'batting': {
                    'current_form': {'average': 0, 'strike_rate': 0, 'runs': 0},
                    'career': {'average': 0, 'strike_rate': 0, 'runs': 0}
                },
                'bowling': {
                    'current_form': {'wickets': 15, 'economy': 8.0, 'average': 25.0},
                    'career': {'wickets': 50, 'economy': 7.5, 'average': 28.0}
                }
            }
        else:  # all-rounder
            return {
                'batting': {
                    'current_form': {'average': 20.0, 'strike_rate': 120.0, 'runs': 50},
                    'career': {'average': 25.0, 'strike_rate': 130.0, 'runs': 500}
                },
                'bowling': {
                    'current_form': {'wickets': 10, 'economy': 8.5, 'average': 30.0},
                    'career': {'wickets': 30, 'economy': 8.0, 'average': 32.0}
                }
            }
    
    def _guess_player_role(self, player_name: str) -> str:
        """Guess player role based on name or team roster"""
        # Try to get role from team roster
        roster_file = Path(__file__).parent.parent.parent / 'data' / 'team_rosters.json'
        if roster_file.exists():
            try:
                with open(roster_file, 'r') as f:
                    rosters = json.load(f)
                    for team in rosters.values():
                        for player in team:
                            if player['name'].lower() == player_name.lower():
                                return player.get('role', 'all-rounder')
            except Exception as e:
                self.logger.error(f"Error reading roster file: {str(e)}")
        
        # Default to all-rounder if can't determine
        return 'all-rounder'

    def get_team_stats(self, team_name: str) -> List[Dict]:
        """Get team's recent performance and player stats"""
        try:
            # Get recent matches
            matches_url = f"{self.base_url}/matches/v1/recent"
            response = self._make_request(matches_url, self.headers)
            if response is None:
                return []
                
            matches_data = response
            team_matches = [
                match for match in matches_data.get('matches', [])
                if team_name in [match.get('team1', {}).get('name'), match.get('team2', {}).get('name')]
            ]
            
            # Get team's players from recent matches
            team_players = []
            for match in team_matches[:5]:  # Get last 5 matches
                match_id = match.get('id')
                if not match_id:
                    continue
                    
                # Get match details
                match_url = f"{self.base_url}/mcenter/v1/{match_id}"
                match_response = self._make_request(match_url, self.headers)
                if match_response is None:
                    continue
                    
                match_data = match_response
                team_players.extend(self._extract_team_players(match_data, team_name))
            
            # Get stats for each player
            player_stats = []
            for player in team_players:
                stats = self.get_player_stats(player['name'])
                if stats:
                    player_stats.append(stats)
            
            return player_stats
            
        except Exception as e:
            self.logger.error(f"Error fetching team stats for {team_name}: {str(e)}")
            return []

    def get_match_details(self, match_id: int) -> Dict:
        """Get detailed match information"""
        try:
            # Get basic match info
            match_url = f"{self.base_url}/mcenter/v1/{match_id}"
            response = self._make_request(match_url, self.headers)
            if response is None:
                return {}
                
            match_data = response
            
            # Get scorecard
            scorecard_url = f"{self.base_url}/mcenter/v1/{match_id}/scard"
            scorecard_response = self._make_request(scorecard_url, self.headers)
            scorecard_data = scorecard_response if scorecard_response else {}
            
            # Get commentary
            commentary_url = f"{self.base_url}/mcenter/v1/{match_id}/comm"
            commentary_response = self._make_request(commentary_url, self.headers)
            commentary_data = commentary_response if commentary_response else {}
            
            return {
                "match_info": match_data,
                "scorecard": scorecard_data,
                "commentary": commentary_data
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching match details for {match_id}: {str(e)}")
            return {}

    def _process_batting_stats(self, stats: Dict) -> Dict:
        """Process and format batting statistics"""
        try:
            return {
                "recent_matches": stats.get('recentMatches', []),
                "current_form": {
                    "runs": stats.get('recentRuns', 0),
                    "average": stats.get('recentAverage', 0),
                    "strike_rate": stats.get('recentStrikeRate', 0)
                },
                "career": {
                    "matches": stats.get('matches', 0),
                    "runs": stats.get('runs', 0),
                    "average": stats.get('average', 0),
                    "strike_rate": stats.get('strikeRate', 0)
                }
            }
        except:
            return {}

    def _process_bowling_stats(self, stats: Dict) -> Dict:
        """Process and format bowling statistics"""
        try:
            return {
                "recent_matches": stats.get('recentMatches', []),
                "current_form": {
                    "wickets": stats.get('recentWickets', 0),
                    "economy": stats.get('recentEconomy', 0),
                    "average": stats.get('recentAverage', 0)
                },
                "career": {
                    "matches": stats.get('matches', 0),
                    "wickets": stats.get('wickets', 0),
                    "economy": stats.get('economy', 0),
                    "average": stats.get('average', 0)
                }
            }
        except:
            return {}

    def _process_career_stats(self, stats: Dict) -> Dict:
        """Process and format career statistics"""
        try:
            return {
                "format_stats": stats.get('formatStats', {}),
                "recent_form": stats.get('recentForm', {}),
                "achievements": stats.get('achievements', [])
            }
        except:
            return {}

    def _extract_team_players(self, match_data: Dict, team_name: str) -> List[Dict]:
        """Extract player information from match data"""
        players = []
        try:
            for team in match_data.get('teams', []):
                if team.get('name') == team_name:
                    for player in team.get('players', []):
                        players.append({
                            'id': player.get('id'),
                            'name': player.get('name'),
                            'role': player.get('role')
                        })
        except:
            pass
        return players

    def get_team_news(self, team_name: str) -> List[Dict]:
        """Get latest news about team and players"""
        try:
            # Search for team news
            search_url = f"{self.base_url}/search?q={team_name}"
            response = self._make_request(search_url, self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            news_items = []
            news_articles = soup.find_all('div', class_='news-item')
            
            for article in news_articles[:5]:  # Get latest 5 news items
                title = article.find('h3')
                date = article.find('span', class_='date')
                if title and date:
                    news_items.append({
                        "title": title.text.strip(),
                        "date": date.text.strip(),
                        "url": f"{self.base_url}{article.find('a')['href']}"
                    })
            
            return news_items
            
        except Exception as e:
            self.logger.error(f"Error fetching team news for {team_name}: {str(e)}")
            return []

    def get_match_squads(self, match_id: int) -> Dict:
        """Get playing XI and squad information for a match"""
        try:
            match_url = f"{self.base_url}/matches/{match_id}"
            response = self._make_request(match_url, self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            squads = {
                "team1": {"playing_xi": [], "bench": []},
                "team2": {"playing_xi": [], "bench": []}
            }
            
            # Find squad sections
            squad_sections = soup.find_all('div', class_='squad-section')
            for i, section in enumerate(squad_sections[:2]):
                team_key = f"team{i+1}"
                playing_xi = section.find('div', class_='playing-xi')
                bench = section.find('div', class_='bench')
                
                if playing_xi:
                    squads[team_key]["playing_xi"] = [
                        player.text.strip() for player in playing_xi.find_all('div', class_='player')
                    ]
                
                if bench:
                    squads[team_key]["bench"] = [
                        player.text.strip() for player in bench.find_all('div', class_='player')
                    ]
            
            return squads
            
        except Exception as e:
            self.logger.error(f"Error fetching match squads for match {match_id}: {str(e)}")
            return {"team1": {"playing_xi": [], "bench": []}, "team2": {"playing_xi": [], "bench": []}}

    def _parse_number(self, text: str) -> float:
        """Parse number from text, handling special cases"""
        try:
            # Remove any non-numeric characters except decimal point
            cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0 