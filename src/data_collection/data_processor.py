import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path
import json
from config import (
    DATA_DIR, HISTORICAL_DATA_FILE, PLAYER_STATS_FILE,
    VALIDATION_RULES, TEAMS, PLAYER_ROLES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.historical_data = None
        self.player_stats = {}
        self.load_data()

    def load_data(self):
        """Load historical data and player statistics"""
        try:
            # Load historical matches
            historical_file = self.data_dir / "historical_matches.csv"
            if historical_file.exists():
                self.historical_data = pd.read_csv(historical_file)
                logger.info(f"Loaded historical data with {len(self.historical_data)} matches")
            else:
                logger.warning("Historical data file not found")

            # Load player statistics
            player_stats_file = self.data_dir / "player_stats.json"
            if player_stats_file.exists():
                with open(player_stats_file, 'r') as f:
                    self.player_stats = json.load(f)
                logger.info(f"Loaded player statistics for {len(self.player_stats)} players")
            else:
                logger.warning("Player statistics file not found")
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    def process_match_data(self, match_data: Dict) -> Dict:
        """Process and enrich match data with additional metrics"""
        try:
            processed_data = {
                'match_id': match_data.get('match_id'),
                'date': match_data.get('date'),
                'venue': match_data.get('venue'),
                'team1': match_data.get('team1'),
                'team2': match_data.get('team2'),
                'status': match_data.get('status'),
                'score': match_data.get('score'),
                'match_importance': self._calculate_match_importance(match_data),
                'pressure_index': self._calculate_pressure_index(match_data),
                'venue_factors': self._get_venue_factors(match_data.get('venue')),
                'team_form': self._calculate_team_form(match_data),
                'head_to_head': self._get_head_to_head_stats(match_data),
                'players': self._process_players(match_data.get('players', []))
            }
            return processed_data
        except Exception as e:
            logger.error(f"Error processing match data: {e}")
            return {}

    def _calculate_match_importance(self, match_data: Dict) -> float:
        """Calculate match importance based on tournament stage and context"""
        try:
            importance = 1.0
            status = match_data.get('status', '').lower()
            
            if 'final' in status:
                importance = 4.0
            elif 'semi' in status:
                importance = 3.0
            elif 'playoff' in status:
                importance = 2.0
            
            return importance
        except Exception as e:
            logger.error(f"Error calculating match importance: {e}")
            return 1.0

    def _calculate_pressure_index(self, match_data: Dict) -> float:
        """Calculate pressure index based on match context"""
        try:
            pressure = 1.0
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            # Check if it's a rivalry match
            if team1 in TEAMS and team2 in TEAMS:
                pressure *= 1.3
            
            # Check if it's a must-win situation
            if 'must win' in match_data.get('status', '').lower():
                pressure *= 1.4
            
            return pressure
        except Exception as e:
            logger.error(f"Error calculating pressure index: {e}")
            return 1.0

    def _get_venue_factors(self, venue: str) -> Dict:
        """Get venue-specific factors"""
        try:
            factors = {
                'home_advantage': 1.0,
                'pitch_type': 'unknown',
                'boundary_size': 'medium'
            }
            
            # Check if venue is home ground for any team
            for team, info in TEAMS.items():
                if info['home_ground'] == venue:
                    factors['home_advantage'] = 1.2
                    break
            
            return factors
        except Exception as e:
            logger.error(f"Error getting venue factors: {e}")
            return {'home_advantage': 1.0, 'pitch_type': 'unknown', 'boundary_size': 'medium'}

    def _calculate_team_form(self, match_data: Dict) -> Dict:
        """Calculate team form based on recent matches"""
        try:
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            form = {
                team1: {'wins': 0, 'losses': 0, 'form_score': 0.5},
                team2: {'wins': 0, 'losses': 0, 'form_score': 0.5}
            }
            
            if self.historical_data is not None:
                for team in [team1, team2]:
                    recent_matches = self.historical_data[
                        (self.historical_data['team1'] == team) | 
                        (self.historical_data['team2'] == team)
                    ].tail(5)
                    
                    for _, match in recent_matches.iterrows():
                        if match['winner'] == team:
                            form[team]['wins'] += 1
                        else:
                            form[team]['losses'] += 1
                    
                    total = form[team]['wins'] + form[team]['losses']
                    if total > 0:
                        form[team]['form_score'] = form[team]['wins'] / total
            
            return form
        except Exception as e:
            logger.error(f"Error calculating team form: {e}")
            return {}

    def _get_head_to_head_stats(self, match_data: Dict) -> Dict:
        """Get head-to-head statistics between teams"""
        try:
            team1 = match_data.get('team1')
            team2 = match_data.get('team2')
            
            h2h = {
                'total_matches': 0,
                'team1_wins': 0,
                'team2_wins': 0,
                'win_ratio': 0.5
            }
            
            if self.historical_data is not None:
                h2h_matches = self.historical_data[
                    ((self.historical_data['team1'] == team1) & (self.historical_data['team2'] == team2)) |
                    ((self.historical_data['team1'] == team2) & (self.historical_data['team2'] == team1))
                ]
                
                h2h['total_matches'] = len(h2h_matches)
                h2h['team1_wins'] = len(h2h_matches[h2h_matches['winner'] == team1])
                h2h['team2_wins'] = len(h2h_matches[h2h_matches['winner'] == team2])
                
                if h2h['total_matches'] > 0:
                    h2h['win_ratio'] = h2h['team1_wins'] / h2h['total_matches']
            
            return h2h
        except Exception as e:
            logger.error(f"Error getting head-to-head stats: {e}")
            return {}

    def _process_players(self, players: List[Dict]) -> List[Dict]:
        """Process and enrich player data"""
        try:
            processed_players = []
            for player in players:
                player_id = player.get('id')
                if player_id in self.player_stats:
                    stats = self.player_stats[player_id]
                    processed_player = {
                        'id': player_id,
                        'name': player.get('name'),
                        'role': player.get('role'),
                        'form': self._calculate_player_form(stats),
                        'role_metrics': self._calculate_role_metrics(stats, player.get('role')),
                        'batting_metrics': self._calculate_batting_metrics(stats),
                        'bowling_metrics': self._calculate_bowling_metrics(stats),
                        'consistency_score': self._calculate_consistency_score(stats),
                        'pressure_metrics': self._calculate_pressure_metrics(stats)
                    }
                    processed_players.append(processed_player)
            return processed_players
        except Exception as e:
            logger.error(f"Error processing players: {e}")
            return []

    def _calculate_player_form(self, stats: Dict) -> Dict:
        """Calculate player form based on recent performances"""
        try:
            form = {
                'runs': 0,
                'wickets': 0,
                'strike_rate': 0,
                'economy_rate': 0,
                'form_score': 0.5
            }
            
            if 'recent_matches' in stats:
                recent = stats['recent_matches'][:5]  # Last 5 matches
                total_runs = sum(match.get('runs', 0) for match in recent)
                total_wickets = sum(match.get('wickets', 0) for match in recent)
                
                form['runs'] = total_runs / len(recent) if recent else 0
                form['wickets'] = total_wickets / len(recent) if recent else 0
                form['strike_rate'] = stats.get('batting', {}).get('strike_rate', 0)
                form['economy_rate'] = stats.get('bowling', {}).get('economy_rate', 0)
                
                # Calculate form score based on performance consistency
                form['form_score'] = self._calculate_form_score(recent)
            
            return form
        except Exception as e:
            logger.error(f"Error calculating player form: {e}")
            return {}

    def _calculate_role_metrics(self, stats: Dict, role: str) -> Dict:
        """Calculate role-specific metrics"""
        try:
            metrics = {
                'role_importance': 1.0,
                'role_performance': 0.5
            }
            
            if role == 'Batsman':
                metrics['role_importance'] = 1.2
                metrics['role_performance'] = stats.get('batting', {}).get('average', 0) / 50
            elif role == 'Bowler':
                metrics['role_importance'] = 1.1
                metrics['role_performance'] = stats.get('bowling', {}).get('average', 0) / 30
            elif role == 'All-Rounder':
                metrics['role_importance'] = 1.3
                batting_perf = stats.get('batting', {}).get('average', 0) / 50
                bowling_perf = stats.get('bowling', {}).get('average', 0) / 30
                metrics['role_performance'] = (batting_perf + bowling_perf) / 2
            
            return metrics
        except Exception as e:
            logger.error(f"Error calculating role metrics: {e}")
            return {}

    def _calculate_batting_metrics(self, stats: Dict) -> Dict:
        """Calculate batting-specific metrics"""
        try:
            batting = stats.get('batting', {})
            return {
                'average': batting.get('average', 0),
                'strike_rate': batting.get('strike_rate', 0),
                'boundary_rate': batting.get('boundary_rate', 0),
                'consistency': batting.get('consistency', 0.5)
            }
        except Exception as e:
            logger.error(f"Error calculating batting metrics: {e}")
            return {}

    def _calculate_bowling_metrics(self, stats: Dict) -> Dict:
        """Calculate bowling-specific metrics"""
        try:
            bowling = stats.get('bowling', {})
            return {
                'average': bowling.get('average', 0),
                'economy_rate': bowling.get('economy_rate', 0),
                'wicket_rate': bowling.get('wicket_rate', 0),
                'consistency': bowling.get('consistency', 0.5)
            }
        except Exception as e:
            logger.error(f"Error calculating bowling metrics: {e}")
            return {}

    def _calculate_consistency_score(self, stats: Dict) -> float:
        """Calculate overall consistency score"""
        try:
            batting_consistency = stats.get('batting', {}).get('consistency', 0.5)
            bowling_consistency = stats.get('bowling', {}).get('consistency', 0.5)
            return (batting_consistency + bowling_consistency) / 2
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.5

    def _calculate_pressure_metrics(self, stats: Dict) -> Dict:
        """Calculate performance under pressure"""
        try:
            return {
                'high_stakes_performance': stats.get('pressure', {}).get('high_stakes', 0.5),
                'chase_performance': stats.get('pressure', {}).get('chase', 0.5),
                'death_overs_performance': stats.get('pressure', {}).get('death_overs', 0.5)
            }
        except Exception as e:
            logger.error(f"Error calculating pressure metrics: {e}")
            return {}

    def _calculate_form_score(self, recent_matches: List[Dict]) -> float:
        """Calculate form score based on recent performance consistency"""
        try:
            if not recent_matches:
                return 0.5
            
            scores = []
            for match in recent_matches:
                score = 0.5
                
                # Batting performance
                if 'runs' in match:
                    if match['runs'] >= 50:
                        score += 0.2
                    elif match['runs'] >= 30:
                        score += 0.1
                
                # Bowling performance
                if 'wickets' in match:
                    if match['wickets'] >= 3:
                        score += 0.2
                    elif match['wickets'] >= 2:
                        score += 0.1
                
                scores.append(score)
            
            return sum(scores) / len(scores)
        except Exception as e:
            logger.error(f"Error calculating form score: {e}")
            return 0.5

    def validate_data(self, data: Dict) -> bool:
        """Validate data against defined rules"""
        try:
            # Validate player statistics
            for player in data.get('players', []):
                stats = player.get('recent_stats', {})
                
                # Check runs
                runs = stats.get('batting', {}).get('runs', 0)
                if not (VALIDATION_RULES['min_runs'] <= runs <= VALIDATION_RULES['max_runs']):
                    logger.warning(f"Invalid runs value: {runs}")
                    return False
                
                # Check wickets
                wickets = stats.get('bowling', {}).get('wickets', 0)
                if not (VALIDATION_RULES['min_wickets'] <= wickets <= VALIDATION_RULES['max_wickets']):
                    logger.warning(f"Invalid wickets value: {wickets}")
                    return False
                
                # Check strike rate
                strike_rate = stats.get('batting', {}).get('strike_rate', 0)
                if not (VALIDATION_RULES['min_strike_rate'] <= strike_rate <= VALIDATION_RULES['max_strike_rate']):
                    logger.warning(f"Invalid strike rate: {strike_rate}")
                    return False
                
                # Check economy rate
                economy_rate = stats.get('bowling', {}).get('economy_rate', 0)
                if not (VALIDATION_RULES['min_economy_rate'] <= economy_rate <= VALIDATION_RULES['max_economy_rate']):
                    logger.warning(f"Invalid economy rate: {economy_rate}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating data: {e}")
            return False

    def save_processed_data(self, data: Dict, match_id: str):
        """Save processed data to file"""
        try:
            output_file = self.data_dir / f"processed_match_{match_id}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved processed data for match {match_id}")
        except Exception as e:
            logger.error(f"Error saving processed data: {e}")

if __name__ == "__main__":
    processor = DataProcessor()
    # Example usage
    test_match = {
        'match_id': 'test123',
        'date': '2024-04-02',
        'venue': 'Wankhede Stadium',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'status': 'Final',
        'score': '180/5',
        'players': []
    }
    processed_data = processor.process_match_data(test_match)
    processor.save_processed_data(processed_data, 'test123') 