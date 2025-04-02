import requests
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
import time
from config import API_KEYS, CRICBUZZ_API

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cricbuzz RapidAPI configuration
        self.headers = {
            "x-rapidapi-key": API_KEYS['cricbuzz'],
            "x-rapidapi-host": CRICBUZZ_API['host']
        }
        
        # API endpoints
        self.endpoints = {
            # IPL specific endpoints
            'ipl_schedule': '/schedule/v1/series/2',  # IPL series ID
            'ipl_points_table': '/stats/v1/series/2/points-table',
            'ipl_stats': '/stats/v1/series/2',
            'ipl_teams': '/series/v1/2/teams',
            'ipl_team_stats': '/stats/v1/series/2/team/{team_id}',
            'ipl_player_stats': '/stats/v1/series/2/player/{player_id}',
            'ipl_venue_stats': '/stats/v1/series/2/venue/{venue_id}',
            
            # Match related endpoints
            'recent_matches': '/matches/v1/recent',
            'match_details': '/mcenter/v1/{match_id}',
            'match_team': '/mcenter/v1/{match_id}/team/{team_id}',
            'match_comments': '/mcenter/v1/{match_id}/comm',
            'match_overs': '/mcenter/v1/{match_id}/overs',
            'match_scorecard': '/mcenter/v1/{match_id}/scard',
            'match_highlights': '/mcenter/v1/{match_id}/hscard',
            'match_leanback': '/mcenter/v1/{match_id}/leanback',
            
            # Player related endpoints
            'trending_players': '/stats/v1/player/trending',
            'player_career': '/stats/v1/player/{player_id}/career',
            'player_news': '/news/v1/player/{player_id}',
            'player_bowling': '/stats/v1/player/{player_id}/bowling',
            'player_batting': '/stats/v1/player/{player_id}/batting',
            'player_stats': '/stats/v1/player/{player_id}',
            'player_search': '/stats/v1/player/search',
            
            # Rankings and stats endpoints
            'batsmen_rankings': '/stats/v1/rankings/batsmen',
            'team_rankings': '/stats/v1/iccstanding/team/matchtype/{match_type}',
            'top_stats': '/stats/v1/topstats/{category}'
        }

    def get_ipl_schedule(self) -> Dict:
        """Fetch IPL schedule"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_schedule']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL schedule: {e}")
            return {}

    def get_ipl_points_table(self) -> Dict:
        """Fetch IPL points table"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_points_table']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL points table: {e}")
            return {}

    def get_ipl_stats(self) -> Dict:
        """Fetch IPL statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_stats']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL stats: {e}")
            return {}

    def get_ipl_teams(self) -> Dict:
        """Fetch IPL teams"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_teams']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL teams: {e}")
            return {}

    def get_ipl_team_stats(self, team_id: str) -> Dict:
        """Fetch IPL team statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_team_stats'].format(team_id=team_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL team stats: {e}")
            return {}

    def get_ipl_player_stats(self, player_id: str) -> Dict:
        """Fetch IPL player statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_player_stats'].format(player_id=player_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL player stats: {e}")
            return {}

    def get_ipl_venue_stats(self, venue_id: str) -> Dict:
        """Fetch IPL venue statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['ipl_venue_stats'].format(venue_id=venue_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching IPL venue stats: {e}")
            return {}

    def fetch_live_matches(self) -> List[Dict]:
        """Fetch live match data from Cricbuzz"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['recent_matches']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return self._process_cricbuzz_data(data)
            else:
                logger.error(f"Error fetching live matches: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
            return []

    def get_match_details(self, match_id: str) -> Dict:
        """Fetch detailed match information"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['match_details'].format(match_id=match_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching match details: {e}")
            return {}

    def get_match_team(self, match_id: str, team_id: str) -> Dict:
        """Fetch team information for a specific match"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['match_team'].format(match_id=match_id, team_id=team_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching match team: {e}")
            return {}

    def get_match_comments(self, match_id: str) -> Dict:
        """Fetch match commentary"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['match_comments'].format(match_id=match_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching match comments: {e}")
            return {}

    def get_match_scorecard(self, match_id: str) -> Dict:
        """Fetch match scorecard"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['match_scorecard'].format(match_id=match_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching match scorecard: {e}")
            return {}

    def get_player_stats(self, player_id: str) -> Dict:
        """Fetch player statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['player_stats'].format(player_id=player_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return {}

    def get_player_career(self, player_id: str) -> Dict:
        """Fetch player career statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['player_career'].format(player_id=player_id)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching player career: {e}")
            return {}

    def get_trending_players(self) -> Dict:
        """Fetch trending players"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['trending_players']}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching trending players: {e}")
            return {}

    def get_player_search(self, player_name: str) -> Dict:
        """Search for players by name"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['player_search']}"
            params = {"plrN": player_name}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error searching for players: {e}")
            return {}

    def get_batsmen_rankings(self, format_type: str = "test") -> Dict:
        """Fetch batsmen rankings"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['batsmen_rankings']}"
            params = {"formatType": format_type}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching batsmen rankings: {e}")
            return {}

    def get_team_rankings(self, match_type: str = "1") -> Dict:
        """Fetch team rankings"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['team_rankings'].format(match_type=match_type)}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching team rankings: {e}")
            return {}

    def get_top_stats(self, category: str = "0", stats_type: str = "mostRuns") -> Dict:
        """Fetch top statistics"""
        try:
            url = f"{CRICBUZZ_API['base_url']}{self.endpoints['top_stats'].format(category=category)}"
            params = {"statsType": stats_type}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error fetching top stats: {e}")
            return {}

    def _process_cricbuzz_data(self, data: Dict) -> List[Dict]:
        """Process and standardize Cricbuzz data"""
        processed_matches = []
        for match in data.get('matchList', []):
            try:
                processed_match = {
                    'match_id': match.get('matchInfo', {}).get('id'),
                    'date': match.get('matchInfo', {}).get('startDate'),
                    'venue': match.get('matchInfo', {}).get('venueInfo', {}).get('name'),
                    'team1': match.get('matchInfo', {}).get('team1', {}).get('name'),
                    'team2': match.get('matchInfo', {}).get('team2', {}).get('name'),
                    'status': match.get('matchInfo', {}).get('status'),
                    'score': match.get('matchScore', {}).get('team1Score', {}).get('inngs1', {}).get('score'),
                    'players': self._extract_players(match)
                }
                processed_matches.append(processed_match)
            except Exception as e:
                logger.error(f"Error processing match: {e}")
                continue
        return processed_matches

    def _extract_players(self, match_data: Dict) -> List[Dict]:
        """Extract player information from match data"""
        players = []
        try:
            # Extract players from both teams
            for team in ['team1', 'team2']:
                team_data = match_data.get('matchInfo', {}).get(team, {})
                for player in team_data.get('players', []):
                    player_info = {
                        'id': player.get('id'),
                        'name': player.get('name'),
                        'role': player.get('role'),
                        'recent_stats': self.get_player_stats(player.get('id')),
                        'career_stats': self.get_player_career(player.get('id'))
                    }
                    players.append(player_info)
        except Exception as e:
            logger.error(f"Error extracting players: {e}")
        return players

    def save_to_cache(self, data: Dict, cache_key: str):
        """Save data to cache with timestamp"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

    def load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache if it's still valid"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if (datetime.now() - cache_time).total_seconds() < 3600:  # 1 hour cache
                    return cache_data['data']
        return None

    def run_data_collection(self):
        """Main method to run all data collection tasks"""
        while True:
            try:
                # Collect IPL specific data
                ipl_schedule = self.get_ipl_schedule()
                self.save_to_cache(ipl_schedule, 'ipl_schedule')
                
                ipl_points_table = self.get_ipl_points_table()
                self.save_to_cache(ipl_points_table, 'ipl_points_table')
                
                ipl_stats = self.get_ipl_stats()
                self.save_to_cache(ipl_stats, 'ipl_stats')
                
                ipl_teams = self.get_ipl_teams()
                self.save_to_cache(ipl_teams, 'ipl_teams')
                
                # Collect live match data
                live_matches = self.fetch_live_matches()
                self.save_to_cache(live_matches, 'live_matches')
                
                # Collect trending players
                trending_players = self.get_trending_players()
                self.save_to_cache(trending_players, 'trending_players')
                
                # Collect team rankings
                team_rankings = self.get_team_rankings()
                self.save_to_cache(team_rankings, 'team_rankings')
                
                # Collect top stats
                top_stats = self.get_top_stats()
                self.save_to_cache(top_stats, 'top_stats')
                
                # Wait before next update
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    collector = DataCollector()
    collector.run_data_collection() 