import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from .cricbuzz_collector import CricbuzzCollector

class DataPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / 'data'
        self.raw_path = self.data_path / 'raw'
        self.processed_path = self.data_path / 'processed'
        self.cache_path = self.data_path / 'cache'
        
        # Create necessary directories
        for path in [self.raw_path, self.processed_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Initialize Cricbuzz collector
        self.collector = CricbuzzCollector()
        
        # Cache for storing processed data
        self._cache = {}
    
    def process_historical_data(self) -> pd.DataFrame:
        """Process historical IPL data from 2008-2024"""
        try:
            # Load match data
            matches_df = pd.read_csv(self.base_path / 'data' / 'historical' / 'matches.csv')
            
            # Load deliveries data
            deliveries_df = pd.read_csv(self.base_path / 'data' / 'historical' / 'deliveries.csv')
            
            # Process match data
            matches_df['date'] = pd.to_datetime(matches_df['date'])
            matches_df['season'] = matches_df['date'].dt.year
            
            # Process deliveries data
            deliveries_df = deliveries_df.merge(matches_df[['match_id', 'season', 'venue']], on='match_id')
            
            # Calculate player statistics
            batting_stats = deliveries_df.groupby(['batsman', 'season', 'venue']).agg({
                'batsman_runs': ['sum', 'count', 'mean'],
                'match_id': 'nunique'
            }).reset_index()
            
            bowling_stats = deliveries_df.groupby(['bowler', 'season', 'venue']).agg({
                'is_wicket': 'sum',
                'total_runs': ['sum', 'mean'],
                'match_id': 'nunique'
            }).reset_index()
            
            # Rename columns
            batting_stats.columns = ['player_name', 'season', 'venue', 'runs_scored', 'balls_faced', 
                                   'batting_average', 'matches_played']
            bowling_stats.columns = ['player_name', 'season', 'venue', 'wickets_taken', 'runs_conceded',
                                   'bowling_average', 'matches_played']
            
            # Calculate strike rates and economy rates
            batting_stats['batting_strike_rate'] = (batting_stats['runs_scored'] / batting_stats['balls_faced']) * 100
            bowling_stats['economy_rate'] = (bowling_stats['runs_conceded'] / bowling_stats['balls_faced']) * 6
            
            # Calculate rolling averages for recent form
            batting_stats['recent_runs'] = batting_stats.groupby('player_name')['runs_scored'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
            batting_stats['recent_strike_rate'] = batting_stats.groupby('player_name')['batting_strike_rate'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
            
            bowling_stats['recent_wickets'] = bowling_stats.groupby('player_name')['wickets_taken'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
            bowling_stats['recent_economy'] = bowling_stats.groupby('player_name')['economy_rate'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean()
            )
            
            # Merge batting and bowling stats
            historical_data = pd.merge(batting_stats, bowling_stats, 
                                     on=['player_name', 'season', 'venue', 'matches_played'],
                                     how='outer')
            
            # Fill NaN values
            historical_data = historical_data.fillna(0)
            
            # Calculate form indicators
            historical_data['batting_form'] = historical_data.apply(
                lambda x: self._calculate_form_score(x, 'batting'),
                axis=1
            )
            
            historical_data['bowling_form'] = historical_data.apply(
                lambda x: self._calculate_form_score(x, 'bowling'),
                axis=1
            )
            
            # Save processed historical data
            historical_data.to_csv(self.processed_path / 'historical_data.csv', index=False)
            self.logger.info("Historical data processed successfully")
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error processing historical data: {str(e)}")
            raise
    
    def update_recent_data(self) -> pd.DataFrame:
        """Update data with recent matches and player stats"""
        try:
            # Load latest processed data
            latest_data = pd.read_csv(self.processed_path / 'historical_data.csv')
            
            # Get current season data from Cricbuzz
            current_season = datetime.now().year
            current_data = []
            
            # Define all IPL teams
            ipl_teams = [
                'Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bangalore',
                'Kolkata Knight Riders', 'Rajasthan Royals', 'Delhi Capitals',
                'Punjab Kings', 'Sunrisers Hyderabad', 'Gujarat Titans',
                'Lucknow Super Giants'
            ]
            
            # Get data for each team
            for team_name in ipl_teams:
                team_stats = self.collector.get_team_stats(team_name)
                if team_stats:
                    for player_stats in team_stats:
                        # Extract relevant features
                        player_data = {
                            'year': current_season,
                            'player_name': player_stats['name'],
                            'team': team_name,
                            'matches_batted': player_stats['batting']['career']['matches'],
                            'runs_scored': player_stats['batting']['career']['runs'],
                            'batting_average': player_stats['batting']['career']['average'],
                            'batting_strike_rate': player_stats['batting']['career']['strike_rate'],
                            'matches_bowled': player_stats['bowling']['career']['matches'],
                            'wickets_taken': player_stats['bowling']['career']['wickets'],
                            'bowling_average': player_stats['bowling']['career']['average'],
                            'economy_rate': player_stats['bowling']['career']['economy'],
                            'batting_form': self._calculate_form_score(player_stats['batting']['current_form'], 'batting'),
                            'bowling_form': self._calculate_form_score(player_stats['bowling']['current_form'], 'bowling')
                        }
                        current_data.append(player_data)
            
            # Convert to DataFrame
            current_df = pd.DataFrame(current_data)
            
            # Merge with historical data
            updated_data = pd.concat([latest_data, current_df], ignore_index=True)
            
            # Save updated data
            updated_data.to_csv(self.processed_path / 'updated_data.csv', index=False)
            self.logger.info("Recent data updated successfully")
            
            return updated_data
            
        except Exception as e:
            self.logger.error(f"Error updating recent data: {str(e)}")
            raise
    
    def prepare_prediction_data(self, player_name: str) -> Dict:
        """Prepare data for player prediction"""
        try:
            # Load latest data
            data = pd.read_csv(self.processed_path / 'updated_data.csv')
            
            # Get player's historical data
            player_data = data[data['player_name'] == player_name].copy()
            
            if player_data.empty:
                self.logger.warning(f"No data found for player: {player_name}")
                return {}
            
            # Get recent form from Cricbuzz
            recent_stats = self.collector.get_player_stats(player_name)
            
            # Combine historical and recent data
            prediction_data = {
                'historical': {
                    'batting': {
                        'average': player_data['batting_average'].mean(),
                        'strike_rate': player_data['batting_strike_rate'].mean(),
                        'form': player_data['batting_form'].iloc[-1]
                    },
                    'bowling': {
                        'average': player_data['bowling_average'].mean(),
                        'economy': player_data['economy_rate'].mean(),
                        'form': player_data['bowling_form'].iloc[-1]
                    }
                },
                'recent': recent_stats
            }
            
            return prediction_data
            
        except Exception as e:
            self.logger.error(f"Error preparing prediction data: {str(e)}")
            raise
    
    def _calculate_form_score(self, stats: Dict, category: str) -> float:
        """Calculate form score based on recent performance"""
        try:
            if category == 'batting':
                runs = stats.get('runs', 0)
                strike_rate = stats.get('strike_rate', 0)
                if runs == 0 or strike_rate == 0:
                    return 0.5
                runs_score = min(runs / 100, 1.0)
                sr_score = min(strike_rate / 200, 1.0)
                return (runs_score + sr_score) / 2
            else:
                wickets = stats.get('wickets', 0)
                economy = stats.get('economy', 0)
                if wickets == 0 or economy == 0:
                    return 0.5
                wickets_score = min(wickets / 5, 1.0)
                economy_score = max(1 - (economy / 12), 0)
                return (wickets_score + economy_score) / 2
        except:
            return 0.5
    
    def run_pipeline(self):
        """Run the complete data pipeline"""
        try:
            # Process historical data
            historical_data = self.process_historical_data()
            
            # For now, we'll use historical data as our updated data
            historical_data.to_csv(self.processed_path / 'updated_data.csv', index=False)
            
            self.logger.info("Data pipeline completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running data pipeline: {str(e)}")
            return False 