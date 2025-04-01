import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import json
from datetime import datetime, timedelta

class DataProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.scraped_path = self.data_path / 'scraped'
        self.processed_path = self.data_path / 'processed'
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.raw_path = self.data_path / 'raw'
    
    def prepare_historical_data(self) -> Optional[pd.DataFrame]:
        """Prepare historical data for model training"""
        try:
            # Load raw data
            matches_df = pd.read_csv(self.raw_path / 'matches.csv')
            deliveries_df = pd.read_csv(self.raw_path / 'deliveries.csv')
            
            # Process player performances
            player_stats = deliveries_df.groupby('player_name').agg({
                'runs': ['mean', 'std'],
                'wickets': ['mean', 'std'],
                'strike_rate': ['mean', 'std'],
                'economy_rate': ['mean', 'std'],
                'is_home_game': 'mean',
                'is_powerplay_batsman': 'mean',
                'is_death_bowler': 'mean',
                'form_factor': 'last',
                'consistency_score': 'last',
                'pressure_index': 'last',
                'last_5_matches_runs_avg': 'last',
                'last_5_matches_wickets_avg': 'last',
                'last_5_matches_sr_avg': 'last',
                'last_5_matches_er_avg': 'last',
                'days_since_last_match': 'last'
            }).reset_index()
            
            # Flatten column names
            player_stats.columns = [
                'player_name',
                'runs_mean', 'runs_std',
                'wickets_mean', 'wickets_std',
                'strike_rate_mean', 'strike_rate_std',
                'economy_rate_mean', 'economy_rate_std',
                'is_home_game',
                'is_powerplay_batsman',
                'is_death_bowler',
                'form_factor',
                'consistency_score',
                'pressure_index',
                'last_5_matches_runs_avg',
                'last_5_matches_wickets_avg',
                'last_5_matches_sr_avg',
                'last_5_matches_er_avg',
                'days_since_last_match'
            ]
            
            # Add target variables from most recent match
            recent_performances = deliveries_df.sort_values('match_id').groupby('player_name').last().reset_index()
            player_stats = pd.merge(
                player_stats,
                recent_performances[['player_name', 'runs', 'wickets', 'strike_rate', 'economy_rate']],
                on='player_name',
                how='left'
            )
            
            # Save processed data
            self.processed_path.mkdir(parents=True, exist_ok=True)
            player_stats.to_csv(self.processed_path / 'processed_data.csv', index=False)
            
            self.logger.info(f"Processed data for {len(player_stats)} players")
            return player_stats
            
        except Exception as e:
            self.logger.error(f"Error preparing historical data: {str(e)}")
            return None
    
    def _load_match_data(self) -> List[Dict]:
        """Load match data from scraped files"""
        match_data = []
        match_files = list(self.scraped_path.glob("match_stats_*.json"))
        
        for file in match_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    match_data.append(data)
            except Exception as e:
                self.logger.error(f"Error loading match data from {file}: {str(e)}")
                continue
        
        return match_data
    
    def _load_player_stats(self) -> Dict[str, Dict]:
        """Load player statistics from scraped files"""
        player_stats = {}
        stats_files = list(self.scraped_path.glob("player_stats_*.json"))
        
        for file in stats_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    player_stats.update(data)
            except Exception as e:
                self.logger.error(f"Error loading player stats from {file}: {str(e)}")
                continue
        
        return player_stats
    
    def _calculate_features(self, player_id: str, match_id: str, date: datetime,
                          historical_stats: Dict, match_data: Dict) -> Dict:
        """Calculate features for a player in a match"""
        try:
            # Get last 5 matches for the player
            last_5_matches = self._get_last_n_matches(player_id, match_id, 5)
            
            # Calculate basic averages
            runs_avg = np.mean([m.get('runs', 0) for m in last_5_matches])
            wickets_avg = np.mean([m.get('wickets', 0) for m in last_5_matches])
            sr_avg = np.mean([m.get('strike_rate', 0) for m in last_5_matches])
            er_avg = np.mean([m.get('economy_rate', 0) for m in last_5_matches])
            
            # Calculate derived features
            form_factor = self._calculate_form_factor(last_5_matches)
            consistency_score = self._calculate_consistency(last_5_matches)
            pressure_index = self._calculate_pressure_index(match_data)
            
            # Get basic venue stats
            venue = match_data['venue']
            venue_stats = self._get_venue_stats(venue)
            
            # Get head-to-head stats
            opposition = self._get_opposition(match_data, player_id)
            h2h_stats = self._get_head_to_head_stats(player_id, opposition)
            
            # Calculate days since last match
            last_match = self._get_last_match_date(player_id, match_id)
            days_since_last = (date - last_match).days if last_match else 30
            
            # Determine player role
            is_powerplay = self._is_powerplay_player(player_id, historical_stats)
            is_death = self._is_death_bowler(player_id, historical_stats)
            
            features = {
                'player_id': player_id,
                'match_id': match_id,
                'date': date.isoformat(),
                
                # Core Performance Features
                'last_5_matches_runs_avg': runs_avg,
                'last_5_matches_wickets_avg': wickets_avg,
                'last_5_matches_sr_avg': sr_avg,
                'last_5_matches_er_avg': er_avg,
                
                # Derived Features
                'form_factor': form_factor,
                'consistency_score': consistency_score,
                'pressure_index': pressure_index,
                
                # Match Context
                'days_since_last_match': days_since_last,
                'is_home_game': self._is_home_game(match_data, player_id),
                'is_powerplay_batsman': is_powerplay,
                'is_death_bowler': is_death,
                
                # Basic Stats
                'runs': historical_stats.get('runs', 0),
                'wickets': historical_stats.get('wickets', 0),
                'strike_rate': historical_stats.get('strike_rate', 0),
                'economy_rate': historical_stats.get('economy_rate', 0)
            }
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error calculating features for {player_id}: {str(e)}")
            return None
    
    def _get_last_n_matches(self, player_id: str, current_match_id: str, n: int) -> List[Dict]:
        """Get last n matches for a player"""
        matches = []
        match_files = sorted(self.scraped_path.glob("match_stats_*.json"))
        
        for file in match_files:
            with open(file, 'r') as f:
                match_data = json.load(f)
                if match_data['match_id'] == current_match_id:
                    continue
                    
                for team in match_data['teams']:
                    for player in team['players']:
                        if player['name'] == player_id:
                            matches.append(player)
                            if len(matches) >= n:
                                return matches
        
        return matches
    
    def _get_venue_stats(self, venue: str) -> Dict[str, float]:
        """Get average statistics for a venue"""
        venue_stats = {'runs_avg': 0, 'wickets_avg': 0}
        venue_matches = []
        
        match_files = list(self.scraped_path.glob("match_stats_*.json"))
        for file in match_files:
            with open(file, 'r') as f:
                match_data = json.load(f)
                if match_data['venue'] == venue:
                    venue_matches.append(match_data)
        
        if venue_matches:
            all_runs = []
            all_wickets = []
            for match in venue_matches:
                for team in match['teams']:
                    for player in team['players']:
                        all_runs.append(player.get('runs', 0))
                        all_wickets.append(player.get('wickets', 0))
            
            venue_stats['runs_avg'] = np.mean(all_runs)
            venue_stats['wickets_avg'] = np.mean(all_wickets)
        
        return venue_stats
    
    def _get_head_to_head_stats(self, player_id: str, opposition: str) -> Dict[str, float]:
        """Get head-to-head statistics against an opposition"""
        h2h_stats = {'runs_avg': 0, 'wickets_avg': 0}
        h2h_matches = []
        
        match_files = list(self.scraped_path.glob("match_stats_*.json"))
        for file in match_files:
            with open(file, 'r') as f:
                match_data = json.load(f)
                if opposition in match_data['teams']:
                    for team in match_data['teams']:
                        for player in team['players']:
                            if player['name'] == player_id:
                                h2h_matches.append(player)
        
        if h2h_matches:
            runs = [m.get('runs', 0) for m in h2h_matches]
            wickets = [m.get('wickets', 0) for m in h2h_matches]
            h2h_stats['runs_avg'] = np.mean(runs)
            h2h_stats['wickets_avg'] = np.mean(wickets)
        
        return h2h_stats
    
    def _get_last_match_date(self, player_id: str, current_match_id: str) -> datetime:
        """Get the date of player's last match"""
        match_files = sorted(self.scraped_path.glob("match_stats_*.json"), reverse=True)
        
        for file in match_files:
            with open(file, 'r') as f:
                match_data = json.load(f)
                if match_data['match_id'] == current_match_id:
                    continue
                    
                for team in match_data['teams']:
                    for player in team['players']:
                        if player['name'] == player_id:
                            return datetime.fromisoformat(match_data['date'])
        
        return None
    
    def _is_home_game(self, match_data: Dict, player_id: str) -> bool:
        """Check if it's a home game for the player"""
        for team in match_data['teams']:
            if player_id in [p['name'] for p in team['players']]:
                return team.get('is_home', False)
        return False
    
    def _is_powerplay_player(self, player_id: str, stats: Dict) -> bool:
        """Check if player is a powerplay specialist"""
        if 'batting_order' in stats:
            return stats['batting_order'] <= 3
        return False
    
    def _is_death_bowler(self, player_id: str, stats: Dict) -> bool:
        """Check if player is a death overs specialist"""
        if 'bowling_phase' in stats:
            return stats['bowling_phase'] == 'death'
        return False
    
    def _get_team_rank(self, team: str) -> int:
        """Get current team rank"""
        # This should be implemented based on your ranking system
        return 5  # Default rank
    
    def _get_opposition(self, match_data: Dict, player_id: str) -> str:
        """Get opposition team for a player"""
        for team in match_data['teams']:
            if player_id not in [p['name'] for p in team['players']]:
                return team['name']
        return None
    
    def _calculate_form_factor(self, recent_performances: List[float]) -> float:
        """Calculate form factor based on recent performances"""
        if not recent_performances:
            return 1.0
        
        # Apply exponential weights to recent performances
        weights = np.exp([-0.2 * i for i in range(len(recent_performances))])
        weighted_avg = np.average(recent_performances, weights=weights)
        overall_avg = np.mean(recent_performances)
        
        return weighted_avg / overall_avg if overall_avg > 0 else 1.0
    
    def _calculate_consistency(self, performances: List[float]) -> float:
        """Calculate consistency score based on performance variance"""
        if not performances:
            return 0.5
        
        # Calculate coefficient of variation (lower is more consistent)
        mean = np.mean(performances)
        std = np.std(performances)
        cv = std / mean if mean > 0 else float('inf')
        
        # Convert to 0-1 score (higher is more consistent)
        consistency = 1 / (1 + cv)
        return min(max(consistency, 0), 1)
    
    def _calculate_pressure_index(self, match_data: Dict) -> float:
        """Calculate pressure index based on match context"""
        pressure = 0.5
        
        # Check if it's a knockout match
        if match_data.get('is_knockout', False):
            pressure += 0.2
            
        # Check if it's against a strong opponent
        if match_data.get('opposition_rank', 5) <= 3:
            pressure += 0.2
            
        # Check if it's a home game
        if match_data.get('is_home_game', False):
            pressure -= 0.1
            
        return min(max(pressure, 0), 1) 