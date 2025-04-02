import requests
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional
from pathlib import Path
import json
import time
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # API endpoints and configurations
        self.config = {
            'cricbuzz_api': 'https://www.cricbuzz.com/api/cricket/match/',
            'espn_api': 'https://site.api.espn.com/apis/site/v2/sports/cricket/',
            'cricket_api': 'https://api.cricapi.com/v1/',
            'cache_duration': 3600  # 1 hour in seconds
        }
        
        # API keys (should be loaded from environment variables)
        self.api_keys = {
            'cricapi': 'YOUR_CRICAPI_KEY',
            'espn': 'YOUR_ESPN_API_KEY'
        }

    async def fetch_live_matches(self) -> List[Dict]:
        """Fetch live match data from multiple sources"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_cricbuzz_live(session),
                self._fetch_espn_live(session),
                self._fetch_cricapi_live(session)
            ]
            results = await asyncio.gather(*tasks)
            
            # Merge and deduplicate results
            all_matches = []
            seen_match_ids = set()
            
            for source_matches in results:
                for match in source_matches:
                    if match['match_id'] not in seen_match_ids:
                        seen_match_ids.add(match['match_id'])
                        all_matches.append(match)
            
            return all_matches

    async def _fetch_cricbuzz_live(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch live match data from Cricbuzz"""
        try:
            url = f"{self.config['cricbuzz_api']}live"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_cricbuzz_data(data)
                return []
        except Exception as e:
            logger.error(f"Error fetching Cricbuzz data: {e}")
            return []

    async def _fetch_espn_live(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch live match data from ESPN"""
        try:
            url = f"{self.config['espn_api']}matches"
            headers = {'Authorization': f"Bearer {self.api_keys['espn']}"}
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_espn_data(data)
                return []
        except Exception as e:
            logger.error(f"Error fetching ESPN data: {e}")
            return []

    async def _fetch_cricapi_live(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch live match data from CricAPI"""
        try:
            url = f"{self.config['cricket_api']}matches"
            params = {'apikey': self.api_keys['cricapi']}
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_cricapi_data(data)
                return []
        except Exception as e:
            logger.error(f"Error fetching CricAPI data: {e}")
            return []

    def _process_cricbuzz_data(self, data: Dict) -> List[Dict]:
        """Process and standardize Cricbuzz data"""
        processed_matches = []
        for match in data.get('matches', []):
            processed_match = {
                'match_id': match.get('id'),
                'date': match.get('startTime'),
                'venue': match.get('venue', {}).get('name'),
                'team1': match.get('team1', {}).get('name'),
                'team2': match.get('team2', {}).get('name'),
                'status': match.get('status'),
                'score': match.get('score'),
                'players': self._extract_players(match)
            }
            processed_matches.append(processed_match)
        return processed_matches

    def _process_espn_data(self, data: Dict) -> List[Dict]:
        """Process and standardize ESPN data"""
        processed_matches = []
        for match in data.get('events', []):
            processed_match = {
                'match_id': match.get('id'),
                'date': match.get('date'),
                'venue': match.get('location', {}).get('name'),
                'team1': match.get('competitions', [{}])[0].get('competitors', [{}])[0].get('team', {}).get('name'),
                'team2': match.get('competitions', [{}])[0].get('competitors', [{}])[1].get('team', {}).get('name'),
                'status': match.get('status', {}).get('type', {}).get('name'),
                'score': match.get('status', {}).get('displayClock'),
                'players': self._extract_players(match)
            }
            processed_matches.append(processed_match)
        return processed_matches

    def _process_cricapi_data(self, data: Dict) -> List[Dict]:
        """Process and standardize CricAPI data"""
        processed_matches = []
        for match in data.get('data', []):
            processed_match = {
                'match_id': match.get('id'),
                'date': match.get('dateTimeGMT'),
                'venue': match.get('venue'),
                'team1': match.get('teams', [{}])[0],
                'team2': match.get('teams', [{}])[1],
                'status': match.get('status'),
                'score': match.get('score', [{}])[0].get('r'),
                'players': self._extract_players(match)
            }
            processed_matches.append(processed_match)
        return processed_matches

    def _extract_players(self, match_data: Dict) -> List[Dict]:
        """Extract player information from match data"""
        players = []
        # Implementation depends on the data structure of each source
        # This is a placeholder that should be customized for each API
        return players

    def update_historical_data(self):
        """Update historical match data"""
        try:
            # Load existing historical data
            historical_file = self.data_dir / "historical_matches.csv"
            if historical_file.exists():
                historical_data = pd.read_csv(historical_file)
            else:
                historical_data = pd.DataFrame()

            # Fetch new historical data
            new_data = self._fetch_historical_data()
            
            # Merge and deduplicate
            combined_data = pd.concat([historical_data, new_data])
            combined_data = combined_data.drop_duplicates(subset=['match_id'])
            
            # Save updated data
            combined_data.to_csv(historical_file, index=False)
            logger.info(f"Updated historical data with {len(new_data)} new matches")
            
        except Exception as e:
            logger.error(f"Error updating historical data: {e}")

    def _fetch_historical_data(self) -> pd.DataFrame:
        """Fetch historical match data"""
        # Implementation for fetching historical data
        # This could involve web scraping or API calls to cricket statistics websites
        return pd.DataFrame()

    def update_player_statistics(self):
        """Update player statistics"""
        try:
            # Load existing player stats
            stats_file = self.data_dir / "player_statistics.csv"
            if stats_file.exists():
                player_stats = pd.read_csv(stats_file)
            else:
                player_stats = pd.DataFrame()

            # Fetch new player stats
            new_stats = self._fetch_player_stats()
            
            # Update existing stats
            updated_stats = self._merge_player_stats(player_stats, new_stats)
            
            # Save updated stats
            updated_stats.to_csv(stats_file, index=False)
            logger.info("Updated player statistics")
            
        except Exception as e:
            logger.error(f"Error updating player statistics: {e}")

    def _fetch_player_stats(self) -> pd.DataFrame:
        """Fetch player statistics from various sources"""
        # Implementation for fetching player statistics
        return pd.DataFrame()

    def _merge_player_stats(self, existing_stats: pd.DataFrame, new_stats: pd.DataFrame) -> pd.DataFrame:
        """Merge existing and new player statistics"""
        # Implementation for merging player statistics
        return pd.DataFrame()

    def validate_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean the data"""
        # Remove duplicates
        data = data.drop_duplicates()
        
        # Handle missing values
        data = data.fillna({
            'runs': 0,
            'wickets': 0,
            'strike_rate': 0,
            'economy_rate': 0
        })
        
        # Validate numeric columns
        numeric_columns = ['runs', 'wickets', 'strike_rate', 'economy_rate']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        return data

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
                if (datetime.now() - cache_time).total_seconds() < self.config['cache_duration']:
                    return cache_data['data']
        return None

    async def run_data_collection(self):
        """Main method to run all data collection tasks"""
        while True:
            try:
                # Collect live match data
                live_matches = await self.fetch_live_matches()
                self.save_to_cache(live_matches, 'live_matches')
                
                # Update historical data
                self.update_historical_data()
                
                # Update player statistics
                self.update_player_statistics()
                
                # Wait before next update
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in data collection: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    collector = DataCollector()
    asyncio.run(collector.run_data_collection()) 