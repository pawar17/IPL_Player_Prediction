import pandas as pd
import json
import requests
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import zipfile
import io
import os

logger = logging.getLogger(__name__)

class IPLDatasetCollector:
    def __init__(self, dataset_path: str):
        """Initialize the IPL dataset collector."""
        self.dataset_path = Path(dataset_path)
        if not self.dataset_path.exists():
            raise ValueError(f"Dataset path {dataset_path} does not exist")
            
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.ipl_dataset_path = self.data_path / 'ipl_dataset'
        self.base_url = "https://raw.githubusercontent.com/your-username/IPL-DATASET/main/csv/"
        self.csv_dir = self.dataset_path / 'csv'
        self.json_dir = self.dataset_path / 'json'
        
        # Create necessary directories
        self.ipl_dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache
        self._cache = {}
        self._cache_duration = 3600  # 1 hour
        
    def download_dataset(self):
        """Download and extract the IPL dataset"""
        try:
            self.logger.info("Downloading IPL dataset...")
            response = requests.get(self.base_url)
            if response.status_code != 200:
                raise Exception(f"Failed to download dataset: {response.status_code}")
                
            # Extract zip file
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                zip_ref.extractall(self.data_dir)
                
            self.logger.info("Successfully downloaded and extracted IPL dataset")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading dataset: {str(e)}")
            return False
            
    def get_player_stats(self, player_name: str) -> Dict[str, Any]:
        """Get player statistics from IPL dataset."""
        try:
            # Load ball-by-ball data
            ball_data = pd.read_csv(self.dataset_path / 'Ball_By_Ball_Match_Data.csv')
            
            # Name mapping for players with their variations
            name_mapping = {
                'Virat Kohli': ['V Kohli', 'Virat Kohli'],
                'Rohit Sharma': ['R Sharma', 'RG Sharma', 'Rohit'],
                'MS Dhoni': ['MS Dhoni', 'Dhoni'],
                'Shubman Gill': ['S Gill', 'Shubman Gill'],
                'VK Ostwal': ['V Ostwal', 'VK Ostwal'],
                'JB Little': ['J Little', 'JB Little'],
                'SS Mishra': ['S Mishra', 'SS Mishra'],
                'AM Ghazanfar': ['A Ghazanfar', 'AM Ghazanfar'],
                'Sakib Hussain': ['S Hussain', 'Sakib Hussain'],
                'AAP Atkinson': ['A Atkinson', 'AAP Atkinson']
            }
            
            # Get the mapped names or create variations of the original name
            mapped_names = name_mapping.get(player_name, [player_name])
            if not isinstance(mapped_names, list):
                mapped_names = [mapped_names]
            
            # Also try variations of the name if not in mapping
            if player_name not in name_mapping:
                # Split name and try with initials
                parts = player_name.split()
                if len(parts) > 1:
                    initials = ''.join(p[0] for p in parts[:-1])
                    last_name = parts[-1]
                    mapped_names.append(f"{initials} {last_name}")
            
            # Find matches for any of the name variations
            player_matches = ball_data[
                (ball_data['Batter'].isin(mapped_names)) | 
                (ball_data['Bowler'].isin(mapped_names))
            ]
            
            if player_matches.empty:
                logger.warning(f"No matches found for player {player_name} (tried variations: {mapped_names})")
                return {
                    'batting_average': 0.0,
                    'strike_rate': 0.0,
                    'bowling_economy': 0.0,
                    'recent_matches': 0
                }
            
            # Calculate batting stats
            batting_stats = player_matches[player_matches['Batter'].isin(mapped_names)]
            total_runs = batting_stats['BatsmanRun'].sum()
            total_balls = len(batting_stats)
            total_wickets = len(batting_stats[batting_stats['IsWicketDelivery'] == 1])
            
            batting_average = total_runs / total_wickets if total_wickets > 0 else total_runs
            strike_rate = (total_runs / total_balls * 100) if total_balls > 0 else 0.0
            
            # Calculate bowling stats
            bowling_stats = player_matches[player_matches['Bowler'].isin(mapped_names)]
            total_runs_given = bowling_stats['TotalRun'].sum()
            total_overs = len(bowling_stats) / 6  # Assuming 6 balls per over
            
            bowling_economy = total_runs_given / total_overs if total_overs > 0 else 0.0
            
            # Get recent matches (last 5)
            recent_matches = len(player_matches['ID'].unique())
            
            return {
                'batting_average': batting_average,
                'strike_rate': strike_rate,
                'bowling_economy': bowling_economy,
                'recent_matches': recent_matches
            }
            
        except Exception as e:
            logger.error(f"Error getting player stats for {player_name}: {str(e)}")
            return {
                'batting_average': 0.0,
                'strike_rate': 0.0,
                'bowling_economy': 0.0,
                'recent_matches': 0
            }
            
    def _get_match_stats(self, player_name: str) -> List[Dict]:
        """Get player's match-wise performance"""
        try:
            # Load match data
            match_data = pd.read_csv(self.csv_dir / 'Match_Info.csv')
            ball_data = pd.read_csv(self.csv_dir / 'Ball_By_Ball_Match_Data.csv')
            
            # Get matches where player participated
            player_matches = ball_data[
                (ball_data['Batter'] == player_name) |
                (ball_data['Bowler'] == player_name)
            ]['ID'].unique()
            
            match_stats = []
            for match_id in player_matches:
                # Get match details
                match = match_data[match_data['ID'] == match_id].iloc[0]
                
                # Get player's performance in this match
                match_ball_data = ball_data[ball_data['ID'] == match_id]
                batting_data = match_ball_data[match_ball_data['Batter'] == player_name]
                bowling_data = match_ball_data[match_ball_data['Bowler'] == player_name]
                
                match_stats.append({
                    'match_id': match_id,
                    'date': match['Date'],
                    'batting': {
                        'runs': int(batting_data['BatsmanRun'].sum()),
                        'balls': len(batting_data),
                        'fours': len(batting_data[batting_data['BatsmanRun'] == 4]),
                        'sixes': len(batting_data[batting_data['BatsmanRun'] == 6])
                    },
                    'bowling': {
                        'wickets': len(bowling_data[bowling_data['IsWicketDelivery'] == 1]),
                        'runs_conceded': int(bowling_data['TotalRun'].sum()),
                        'overs': len(bowling_data) / 6
                    }
                })
            
            return match_stats
            
        except Exception as e:
            self.logger.error(f"Error getting match stats for {player_name}: {str(e)}")
            return []
            
    def _get_default_stats(self, player_name: str) -> Dict:
        """Get default stats when data is missing"""
        return {
            'batting': {
                'current_form': {'average': 0, 'strike_rate': 0, 'runs': 0},
                'career': {'average': 0, 'strike_rate': 0, 'runs': 0}
            },
            'bowling': {
                'current_form': {'wickets': 0, 'economy': 0, 'average': 0},
                'career': {'wickets': 0, 'economy': 0, 'average': 0}
            },
            'match_stats': []
        }
        
    def get_team_stats(self, team_name: str) -> Dict:
        """Get team's stats from the IPL dataset"""
        try:
            # Check cache first
            cache_key = f"ipl_team_stats_{team_name}"
            if cache_key in self._cache:
                cached_data = self._cache[cache_key]
                if (datetime.now() - cached_data['timestamp']).total_seconds() < self._cache_duration:
                    self.logger.info(f"Using cached IPL team stats for {team_name}")
                    return cached_data['data']
            
            # Load match data
            match_data = pd.read_csv(self.csv_dir / 'Match_Info.csv')
            
            # Filter data for the team
            team_matches = match_data[
                (match_data['Team1'] == team_name) |
                (match_data['Team2'] == team_name)
            ]
            
            # Calculate team stats
            total_matches = len(team_matches)
            wins = len(team_matches[team_matches['WinningTeam'] == team_name])
            
            # Get recent form (last 5 matches)
            recent_matches = team_matches.sort_values('Date', ascending=False).head(5)
            recent_wins = len(recent_matches[recent_matches['WinningTeam'] == team_name])
            
            stats = {
                'total_matches': total_matches,
                'wins': wins,
                'win_rate': float(wins / max(1, total_matches)),
                'recent_form': {
                    'matches': len(recent_matches),
                    'wins': recent_wins,
                    'win_rate': float(recent_wins / max(1, len(recent_matches)))
                }
            }
            
            # Cache the results
            self._cache[cache_key] = {
                'data': stats,
                'timestamp': datetime.now()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting IPL team stats for {team_name}: {str(e)}")
            return self._get_default_team_stats()
            
    def _get_default_team_stats(self) -> Dict:
        """Get default team stats when data is missing"""
        return {
            'total_matches': 0,
            'wins': 0,
            'win_rate': 0.0,
            'recent_form': {
                'matches': 0,
                'wins': 0,
                'win_rate': 0.0
            }
        }
        
    def get_match_stats(self, match_id: str) -> Dict:
        """Get match statistics from the IPL dataset"""
        try:
            # Load match data
            match_data = pd.read_csv(self.csv_dir / 'Match_Info.csv')
            
            # Convert match_id to string for comparison
            match_id = str(match_id)
            
            # Filter for the specific match
            match = match_data[match_data['match_number'].astype(str) == match_id]
            if match.empty:
                self.logger.error(f"No match found with ID {match_id}")
                return None
                
            match = match.iloc[0]
            
            # Extract match info
            match_info = {
                'match_id': match_id,
                'team1': match['team1'],
                'team2': match['team2'],
                'date': match['match_date'],
                'venue': match['venue'],
                'city': match['city'],
                'toss_winner': match['toss_winner'],
                'toss_decision': match['toss_decision'],
                'winner': match['winner'],
                'player_of_match': match['player_of_match'],
                'team1_players': eval(match['team1_players']),
                'team2_players': eval(match['team2_players'])
            }
            
            return match_info
            
        except Exception as e:
            self.logger.error(f"Error getting match stats: {str(e)}")
            return None

    def get_team_roster(self, team_name: str) -> Dict[str, List[str]]:
        """Get team roster from the IPL dataset"""
        try:
            # Load teams info
            teams_data = pd.read_csv(self.csv_dir / 'teams_info.csv')
            
            # Filter for the specific team
            team_data = teams_data[teams_data['team_name'] == team_name]
            if team_data.empty:
                self.logger.error(f"No team found with name {team_name}")
                return {
                    'batsmen': [],
                    'bowlers': [],
                    'all_rounders': [],
                    'wicket_keepers': []
                }
            
            # Get team ID
            team_id = team_data.iloc[0]['espn_id']
            
            # Load player details
            players_data = pd.read_csv(self.csv_dir / '2024_players_details.csv')
            
            # Categorize players based on playing roles
            roster = {
                'batsmen': players_data[players_data['playingRoles'].str.contains('Batsman', na=False)]['Name'].tolist(),
                'bowlers': players_data[players_data['playingRoles'].str.contains('Bowler', na=False)]['Name'].tolist(),
                'all_rounders': players_data[players_data['playingRoles'].str.contains('Allrounder', na=False)]['Name'].tolist(),
                'wicket_keepers': players_data[players_data['playingRoles'].str.contains('Wicketkeeper', na=False)]['Name'].tolist()
            }
            
            return roster
            
        except Exception as e:
            self.logger.error(f"Error getting team roster for {team_name}: {str(e)}")
            return {
                'batsmen': [],
                'bowlers': [],
                'all_rounders': [],
                'wicket_keepers': []
            } 