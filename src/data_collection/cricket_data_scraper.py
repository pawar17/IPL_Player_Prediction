import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
import json
from pathlib import Path
import aiohttp
import asyncio
from fake_useragent import UserAgent

class CricketDataScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.scraped_path = self.data_path / 'scraped'
        self.scraped_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize user agent
        self.ua = UserAgent()
        
        # Define data sources
        self.sources = {
            'cricbuzz': 'https://www.cricbuzz.com',
            'espncricinfo': 'https://www.espncricinfo.com',
            'iplt20': 'https://www.iplt20.com'
        }
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
    
    async def collect_historical_data(self, start_year: int = 2008, end_year: int = 2024):
        """Collect historical IPL data"""
        try:
            all_matches = []
            
            for year in range(start_year, end_year + 1):
                self.logger.info(f"Collecting data for IPL {year}")
                
                # Collect match data
                matches = await self._collect_season_matches(year)
                all_matches.extend(matches)
                
                # Save yearly data
                self._save_season_data(year, matches)
                
                # Rate limiting
                await asyncio.sleep(self.request_delay)
            
            # Save complete historical data
            self._save_historical_data(all_matches)
            
            return all_matches
            
        except Exception as e:
            self.logger.error(f"Error collecting historical data: {str(e)}")
            return []
    
    async def collect_current_season_data(self):
        """Collect current season data"""
        try:
            current_year = datetime.now().year
            matches = await self._collect_season_matches(current_year)
            
            # Save current season data
            self._save_season_data(current_year, matches)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error collecting current season data: {str(e)}")
            return []
    
    async def collect_player_stats(self, player_id: str) -> Dict[str, Any]:
        """Collect detailed player statistics"""
        try:
            # Collect from multiple sources for comprehensive data
            stats = {}
            
            # Cricbuzz stats
            cricbuzz_stats = await self._collect_cricbuzz_player_stats(player_id)
            if cricbuzz_stats:
                stats['cricbuzz'] = cricbuzz_stats
            
            # ESPNCricinfo stats
            espn_stats = await self._collect_espn_player_stats(player_id)
            if espn_stats:
                stats['espn'] = espn_stats
            
            # IPL official stats
            ipl_stats = await self._collect_ipl_player_stats(player_id)
            if ipl_stats:
                stats['ipl'] = ipl_stats
            
            # Save player stats
            self._save_player_stats(player_id, stats)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error collecting player stats: {str(e)}")
            return {}
    
    async def collect_team_stats(self, team_id: str) -> Dict[str, Any]:
        """Collect team statistics"""
        try:
            stats = {}
            
            # Collect from multiple sources
            cricbuzz_stats = await self._collect_cricbuzz_team_stats(team_id)
            if cricbuzz_stats:
                stats['cricbuzz'] = cricbuzz_stats
            
            espn_stats = await self._collect_espn_team_stats(team_id)
            if espn_stats:
                stats['espn'] = espn_stats
            
            ipl_stats = await self._collect_ipl_team_stats(team_id)
            if ipl_stats:
                stats['ipl'] = ipl_stats
            
            # Save team stats
            self._save_team_stats(team_id, stats)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error collecting team stats: {str(e)}")
            return {}
    
    async def collect_venue_stats(self, venue_id: str) -> Dict[str, Any]:
        """Collect venue statistics"""
        try:
            stats = {}
            
            # Collect from multiple sources
            cricbuzz_stats = await self._collect_cricbuzz_venue_stats(venue_id)
            if cricbuzz_stats:
                stats['cricbuzz'] = cricbuzz_stats
            
            espn_stats = await self._collect_espn_venue_stats(venue_id)
            if espn_stats:
                stats['espn'] = espn_stats
            
            ipl_stats = await self._collect_ipl_venue_stats(venue_id)
            if ipl_stats:
                stats['ipl'] = ipl_stats
            
            # Save venue stats
            self._save_venue_stats(venue_id, stats)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error collecting venue stats: {str(e)}")
            return {}
    
    async def _collect_season_matches(self, year: int) -> List[Dict[str, Any]]:
        """Collect matches for a specific season"""
        matches = []
        
        try:
            # Collect from multiple sources
            cricbuzz_matches = await self._collect_cricbuzz_season_matches(year)
            if cricbuzz_matches:
                matches.extend(cricbuzz_matches)
            
            espn_matches = await self._collect_espn_season_matches(year)
            if espn_matches:
                matches.extend(espn_matches)
            
            ipl_matches = await self._collect_ipl_season_matches(year)
            if ipl_matches:
                matches.extend(ipl_matches)
            
            # Deduplicate matches
            matches = self._deduplicate_matches(matches)
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Error collecting season matches: {str(e)}")
            return []
    
    async def _collect_cricbuzz_season_matches(self, year: int) -> List[Dict[str, Any]]:
        """Collect matches from Cricbuzz"""
        matches = []
        
        try:
            url = f"{self.sources['cricbuzz']}/cricket-series/ipl-{year}"
            headers = {'User-Agent': self.ua.random}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Parse match data
                        match_elements = soup.find_all('div', class_='match-item')
                        for element in match_elements:
                            match_data = self._parse_cricbuzz_match(element)
                            if match_data:
                                matches.append(match_data)
        
        except Exception as e:
            self.logger.error(f"Error collecting Cricbuzz matches: {str(e)}")
        
        return matches
    
    async def _collect_espn_season_matches(self, year: int) -> List[Dict[str, Any]]:
        """Collect matches from ESPNCricinfo"""
        matches = []
        
        try:
            url = f"{self.sources['espncricinfo']}/series/indian-premier-league-{year}"
            headers = {'User-Agent': self.ua.random}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Parse match data
                        match_elements = soup.find_all('div', class_='match-info')
                        for element in match_elements:
                            match_data = self._parse_espn_match(element)
                            if match_data:
                                matches.append(match_data)
        
        except Exception as e:
            self.logger.error(f"Error collecting ESPNCricinfo matches: {str(e)}")
        
        return matches
    
    async def _collect_ipl_season_matches(self, year: int) -> List[Dict[str, Any]]:
        """Collect matches from IPL official website"""
        matches = []
        
        try:
            url = f"{self.sources['iplt20']}/matches/results/{year}"
            headers = {'User-Agent': self.ua.random}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Parse match data
                        match_elements = soup.find_all('div', class_='match-result')
                        for element in match_elements:
                            match_data = self._parse_ipl_match(element)
                            if match_data:
                                matches.append(match_data)
        
        except Exception as e:
            self.logger.error(f"Error collecting IPL matches: {str(e)}")
        
        return matches
    
    def _parse_cricbuzz_match(self, element) -> Optional[Dict[str, Any]]:
        """Parse match data from Cricbuzz HTML"""
        try:
            match_data = {
                'id': element.get('data-match-id', ''),
                'date': element.find('span', class_='date').text.strip(),
                'teams': [team.text.strip() for team in element.find_all('span', class_='team-name')],
                'venue': element.find('span', class_='venue').text.strip(),
                'result': element.find('span', class_='result').text.strip(),
                'score': element.find('span', class_='score').text.strip(),
                'source': 'cricbuzz'
            }
            return match_data
        except Exception as e:
            self.logger.error(f"Error parsing Cricbuzz match: {str(e)}")
            return None
    
    def _parse_espn_match(self, element) -> Optional[Dict[str, Any]]:
        """Parse match data from ESPNCricinfo HTML"""
        try:
            match_data = {
                'id': element.get('data-match-id', ''),
                'date': element.find('span', class_='date').text.strip(),
                'teams': [team.text.strip() for team in element.find_all('span', class_='team-name')],
                'venue': element.find('span', class_='venue').text.strip(),
                'result': element.find('span', class_='result').text.strip(),
                'score': element.find('span', class_='score').text.strip(),
                'source': 'espn'
            }
            return match_data
        except Exception as e:
            self.logger.error(f"Error parsing ESPNCricinfo match: {str(e)}")
            return None
    
    def _parse_ipl_match(self, element) -> Optional[Dict[str, Any]]:
        """Parse match data from IPL website HTML"""
        try:
            match_data = {
                'id': element.get('data-match-id', ''),
                'date': element.find('span', class_='date').text.strip(),
                'teams': [team.text.strip() for team in element.find_all('span', class_='team-name')],
                'venue': element.find('span', class_='venue').text.strip(),
                'result': element.find('span', class_='result').text.strip(),
                'score': element.find('span', class_='score').text.strip(),
                'source': 'ipl'
            }
            return match_data
        except Exception as e:
            self.logger.error(f"Error parsing IPL match: {str(e)}")
            return None
    
    def _deduplicate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate matches based on match ID"""
        seen_ids = set()
        unique_matches = []
        
        for match in matches:
            if match['id'] not in seen_ids:
                seen_ids.add(match['id'])
                unique_matches.append(match)
        
        return unique_matches
    
    def _save_season_data(self, year: int, matches: List[Dict[str, Any]]):
        """Save season data to file"""
        try:
            file_path = self.scraped_path / f'ipl_{year}_matches.json'
            with open(file_path, 'w') as f:
                json.dump(matches, f, indent=2)
            self.logger.info(f"Saved {len(matches)} matches for IPL {year}")
        except Exception as e:
            self.logger.error(f"Error saving season data: {str(e)}")
    
    def _save_historical_data(self, matches: List[Dict[str, Any]]):
        """Save complete historical data to file"""
        try:
            file_path = self.scraped_path / 'historical_matches.json'
            with open(file_path, 'w') as f:
                json.dump(matches, f, indent=2)
            self.logger.info(f"Saved {len(matches)} historical matches")
        except Exception as e:
            self.logger.error(f"Error saving historical data: {str(e)}")
    
    def _save_player_stats(self, player_id: str, stats: Dict[str, Any]):
        """Save player statistics to file"""
        try:
            file_path = self.scraped_path / f'player_{player_id}_stats.json'
            with open(file_path, 'w') as f:
                json.dump(stats, f, indent=2)
            self.logger.info(f"Saved stats for player {player_id}")
        except Exception as e:
            self.logger.error(f"Error saving player stats: {str(e)}")
    
    def _save_team_stats(self, team_id: str, stats: Dict[str, Any]):
        """Save team statistics to file"""
        try:
            file_path = self.scraped_path / f'team_{team_id}_stats.json'
            with open(file_path, 'w') as f:
                json.dump(stats, f, indent=2)
            self.logger.info(f"Saved stats for team {team_id}")
        except Exception as e:
            self.logger.error(f"Error saving team stats: {str(e)}")
    
    def _save_venue_stats(self, venue_id: str, stats: Dict[str, Any]):
        """Save venue statistics to file"""
        try:
            file_path = self.scraped_path / f'venue_{venue_id}_stats.json'
            with open(file_path, 'w') as f:
                json.dump(stats, f, indent=2)
            self.logger.info(f"Saved stats for venue {venue_id}")
        except Exception as e:
            self.logger.error(f"Error saving venue stats: {str(e)}") 