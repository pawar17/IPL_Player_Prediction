import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import numpy as np

class UpdatesManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.realtime_path = self.data_path / 'realtime'
        self.realtime_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize update tracking
        self.last_update = datetime.now()
        self.update_interval = timedelta(minutes=5)  # Default update interval
        self.is_updating = False
        
        # Initialize data storage
        self.current_match_data = {}
        self.player_stats_cache = {}
        self.team_stats_cache = {}
        self.venue_stats_cache = {}
        
        # Initialize thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def start_update_loop(self):
        """Start the continuous update loop"""
        while True:
            try:
                await self.check_and_update()
                await asyncio.sleep(self.update_interval.total_seconds())
            except Exception as e:
                self.logger.error(f"Error in update loop: {str(e)}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def check_and_update(self):
        """Check if updates are needed and perform them"""
        if self.is_updating:
            return
            
        current_time = datetime.now()
        if current_time - self.last_update >= self.update_interval:
            await self.perform_updates()
    
    async def perform_updates(self):
        """Perform all necessary updates"""
        self.is_updating = True
        try:
            # Update match data
            await self.update_match_data()
            
            # Update player statistics
            await self.update_player_stats()
            
            # Update team statistics
            await self.update_team_stats()
            
            # Update venue statistics
            await self.update_venue_stats()
            
            # Update weather data
            await self.update_weather_data()
            
            # Save updated data
            await self.save_updated_data()
            
            self.last_update = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error performing updates: {str(e)}")
        finally:
            self.is_updating = False
    
    async def update_match_data(self):
        """Update current match data"""
        try:
            # In a real implementation, this would fetch from live API
            # For now, we'll simulate with sample data
            current_matches = await self._fetch_current_matches()
            
            for match in current_matches:
                match_id = match['id']
                self.current_match_data[match_id] = {
                    'status': match['status'],
                    'score': match['score'],
                    'overs': match['overs'],
                    'current_batsmen': match['current_batsmen'],
                    'current_bowlers': match['current_bowlers'],
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error updating match data: {str(e)}")
    
    async def update_player_stats(self):
        """Update player statistics"""
        try:
            # In a real implementation, this would fetch from live API
            # For now, we'll simulate with sample data
            for match_id, match_data in self.current_match_data.items():
                for player in match_data['current_batsmen'] + match_data['current_bowlers']:
                    player_id = player['id']
                    if player_id not in self.player_stats_cache:
                        self.player_stats_cache[player_id] = {
                            'recent_performance': [],
                            'current_form': 0.0,
                            'last_updated': datetime.now().isoformat()
                        }
                    
                    # Update recent performance
                    self.player_stats_cache[player_id]['recent_performance'].append({
                        'match_id': match_id,
                        'runs': player.get('runs', 0),
                        'wickets': player.get('wickets', 0),
                        'strike_rate': player.get('strike_rate', 0),
                        'economy_rate': player.get('economy_rate', 0),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Keep only last 5 matches
                    self.player_stats_cache[player_id]['recent_performance'] = \
                        self.player_stats_cache[player_id]['recent_performance'][-5:]
                    
                    # Update current form
                    self.player_stats_cache[player_id]['current_form'] = \
                        self._calculate_current_form(self.player_stats_cache[player_id]['recent_performance'])
                    
        except Exception as e:
            self.logger.error(f"Error updating player stats: {str(e)}")
    
    async def update_team_stats(self):
        """Update team statistics"""
        try:
            # In a real implementation, this would fetch from live API
            # For now, we'll simulate with sample data
            for match_id, match_data in self.current_match_data.items():
                for team in [match_data['team1'], match_data['team2']]:
                    team_id = team['id']
                    if team_id not in self.team_stats_cache:
                        self.team_stats_cache[team_id] = {
                            'recent_performance': [],
                            'current_form': 0.0,
                            'last_updated': datetime.now().isoformat()
                        }
                    
                    # Update recent performance
                    self.team_stats_cache[team_id]['recent_performance'].append({
                        'match_id': match_id,
                        'runs': team.get('runs', 0),
                        'wickets': team.get('wickets', 0),
                        'run_rate': team.get('run_rate', 0),
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Keep only last 5 matches
                    self.team_stats_cache[team_id]['recent_performance'] = \
                        self.team_stats_cache[team_id]['recent_performance'][-5:]
                    
                    # Update current form
                    self.team_stats_cache[team_id]['current_form'] = \
                        self._calculate_team_form(self.team_stats_cache[team_id]['recent_performance'])
                    
        except Exception as e:
            self.logger.error(f"Error updating team stats: {str(e)}")
    
    async def update_venue_stats(self):
        """Update venue statistics"""
        try:
            # In a real implementation, this would fetch from live API
            # For now, we'll simulate with sample data
            for match_id, match_data in self.current_match_data.items():
                venue_id = match_data['venue']['id']
                if venue_id not in self.venue_stats_cache:
                    self.venue_stats_cache[venue_id] = {
                        'recent_matches': [],
                        'last_updated': datetime.now().isoformat()
                    }
                
                # Update recent matches
                self.venue_stats_cache[venue_id]['recent_matches'].append({
                    'match_id': match_id,
                    'total_runs': match_data['score']['total'],
                    'total_wickets': match_data['score']['wickets'],
                    'run_rate': match_data['score']['run_rate'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Keep only last 10 matches
                self.venue_stats_cache[venue_id]['recent_matches'] = \
                    self.venue_stats_cache[venue_id]['recent_matches'][-10:]
                
        except Exception as e:
            self.logger.error(f"Error updating venue stats: {str(e)}")
    
    async def update_weather_data(self):
        """Update weather data for current matches"""
        try:
            # In a real implementation, this would fetch from weather API
            # For now, we'll simulate with sample data
            for match_id, match_data in self.current_match_data.items():
                venue_id = match_data['venue']['id']
                weather_data = await self._fetch_weather_data(venue_id)
                
                match_data['weather'] = {
                    'temperature': weather_data['temperature'],
                    'humidity': weather_data['humidity'],
                    'wind_speed': weather_data['wind_speed'],
                    'rain_probability': weather_data['rain_probability'],
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error updating weather data: {str(e)}")
    
    async def save_updated_data(self):
        """Save all updated data to files"""
        try:
            # Save current match data
            with open(self.realtime_path / 'current_matches.json', 'w') as f:
                json.dump(self.current_match_data, f, indent=2)
            
            # Save player stats
            with open(self.realtime_path / 'player_stats.json', 'w') as f:
                json.dump(self.player_stats_cache, f, indent=2)
            
            # Save team stats
            with open(self.realtime_path / 'team_stats.json', 'w') as f:
                json.dump(self.team_stats_cache, f, indent=2)
            
            # Save venue stats
            with open(self.realtime_path / 'venue_stats.json', 'w') as f:
                json.dump(self.venue_stats_cache, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving updated data: {str(e)}")
    
    def _calculate_current_form(self, recent_performance: List[Dict[str, Any]]) -> float:
        """Calculate current form based on recent performance"""
        if not recent_performance:
            return 0.0
            
        # Calculate weighted average of performance metrics
        weights = [0.4, 0.3, 0.2, 0.1]  # Weights for runs, wickets, SR, ER
        form_scores = []
        
        for perf in recent_performance:
            score = (
                weights[0] * (perf['runs'] / 30) +  # Normalize runs to 30
                weights[1] * (perf['wickets'] / 3) +  # Normalize wickets to 3
                weights[2] * (perf['strike_rate'] / 150) +  # Normalize SR to 150
                weights[3] * (1 - perf['economy_rate'] / 12)  # Normalize ER to 12
            )
            form_scores.append(score)
        
        return np.mean(form_scores)
    
    def _calculate_team_form(self, recent_performance: List[Dict[str, Any]]) -> float:
        """Calculate team form based on recent performance"""
        if not recent_performance:
            return 0.0
            
        # Calculate weighted average of team performance metrics
        weights = [0.5, 0.3, 0.2]  # Weights for runs, wickets, run rate
        form_scores = []
        
        for perf in recent_performance:
            score = (
                weights[0] * (perf['runs'] / 160) +  # Normalize runs to 160
                weights[1] * (perf['wickets'] / 7) +  # Normalize wickets to 7
                weights[2] * (perf['run_rate'] / 8)  # Normalize run rate to 8
            )
            form_scores.append(score)
        
        return np.mean(form_scores)
    
    async def _fetch_current_matches(self) -> List[Dict[str, Any]]:
        """Fetch current matches from API"""
        # In a real implementation, this would make an API call
        # For now, return sample data
        return [
            {
                'id': 'match1',
                'status': 'in_progress',
                'score': {'total': 120, 'wickets': 3, 'run_rate': 7.5},
                'overs': 16,
                'current_batsmen': [
                    {'id': 'batsman1', 'runs': 45, 'strike_rate': 150},
                    {'id': 'batsman2', 'runs': 30, 'strike_rate': 120}
                ],
                'current_bowlers': [
                    {'id': 'bowler1', 'wickets': 2, 'economy_rate': 7.0},
                    {'id': 'bowler2', 'wickets': 1, 'economy_rate': 8.0}
                ],
                'team1': {'id': 'team1', 'runs': 120, 'wickets': 3, 'run_rate': 7.5},
                'team2': {'id': 'team2', 'runs': 0, 'wickets': 0, 'run_rate': 0},
                'venue': {'id': 'venue1', 'name': 'Sample Venue'}
            }
        ]
    
    async def _fetch_weather_data(self, venue_id: str) -> Dict[str, Any]:
        """Fetch weather data for a venue"""
        # In a real implementation, this would make an API call to a weather service
        # For now, return sample data
        return {
            'temperature': 28,
            'humidity': 65,
            'wind_speed': 12,
            'rain_probability': 0.2
        } 