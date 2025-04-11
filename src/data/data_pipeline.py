import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
    def load_data(self):
        """Load all data sources"""
        logger.info("Loading data sources...")
        
        # Load matches data
        matches_df = pd.read_csv(self.historical_dir / "matches.csv")
        logger.info(f"Loaded {len(matches_df)} matches")
        
        # Load player statistics
        player_stats_df = pd.read_csv(self.raw_dir / "cricket_data.csv")
        logger.info(f"Loaded {len(player_stats_df)} player records")
        
        # Load deliveries data
        deliveries_df = pd.read_csv(self.historical_dir / "deliveries.csv")
        logger.info(f"Loaded {len(deliveries_df)} deliveries")
        
        return matches_df, player_stats_df, deliveries_df
    
    def process_matches(self, matches_df):
        """Process matches data to extract relevant features"""
        logger.info("Processing matches data...")
        
        # Convert date to datetime
        matches_df['date'] = pd.to_datetime(matches_df['date'])
        
        # Extract year and month
        matches_df['year'] = matches_df['date'].dt.year
        matches_df['month'] = matches_df['date'].dt.month
        
        # Fill missing cities with venue city
        matches_df['city'] = matches_df['city'].fillna(matches_df['venue'].str.split(',').str[0])
        
        # Fill missing player_of_match with most valuable player from deliveries
        # This will be handled in combine_data method
        
        # Create venue features
        venue_stats = matches_df.groupby('venue').agg({
            'id': 'count',
            'result_margin': ['mean', 'std']
        }).reset_index()
        
        venue_stats.columns = ['venue', 'matches_played', 'avg_margin', 'margin_std']
        
        # Merge venue stats back
        matches_df = matches_df.merge(venue_stats, on='venue', how='left')
        
        return matches_df
    
    def process_player_stats(self, player_stats_df, deliveries_df):
        """Process player statistics to create standardized features"""
        logger.info("Processing player statistics...")
        
        # Clean Year column - remove 'No stats' and convert to integer
        player_stats_df = player_stats_df[player_stats_df['Year'] != 'No stats'].copy()
        player_stats_df['Year'] = pd.to_numeric(player_stats_df['Year'], errors='coerce').astype('Int32')
        
        # Drop rows with missing years
        player_stats_df = player_stats_df.dropna(subset=['Year'])
        
        # Convert numeric columns
        numeric_cols = ['Runs_Scored', 'Batting_Average', 'Batting_Strike_Rate',
                       'Wickets_Taken', 'Bowling_Average', 'Economy_Rate',
                       'Matches_Batted', 'Not_Outs', 'Highest_Score', 'Balls_Faced',
                       'Centuries', 'Half_Centuries', 'Fours', 'Sixes',
                       'Catches_Taken', 'Stumpings', 'Matches_Bowled', 'Balls_Bowled',
                       'Runs_Conceded', 'Four_Wicket_Hauls', 'Five_Wicket_Hauls']
        
        for col in numeric_cols:
            player_stats_df[col] = pd.to_numeric(player_stats_df[col], errors='coerce')
        
        # Calculate career statistics
        career_stats = player_stats_df.groupby('Player_Name').agg({
            'Matches_Batted': 'sum',
            'Runs_Scored': 'sum',
            'Batting_Average': 'mean',
            'Batting_Strike_Rate': 'mean',
            'Wickets_Taken': 'sum',
            'Bowling_Average': 'mean',
            'Economy_Rate': 'mean',
            'Catches_Taken': 'sum',
            'Stumpings': 'sum'
        }).reset_index()
        
        # Add career stats columns
        career_stats.columns = [f'Career_{col}' for col in career_stats.columns]
        career_stats = career_stats.rename(columns={'Career_Player_Name': 'Player_Name'})
        
        # Merge career stats back
        player_stats_df = player_stats_df.merge(career_stats, on='Player_Name', how='left')
        
        # Calculate rolling averages (last 3 seasons)
        player_stats_df = player_stats_df.sort_values(['Player_Name', 'Year'])
        
        for col in numeric_cols:
            player_stats_df[f'{col}_3yr_avg'] = player_stats_df.groupby('Player_Name')[col].transform(
                lambda x: x.rolling(window=3, min_periods=1).mean()
            )
        
        # Add ball-by-ball statistics from deliveries
        ball_stats = deliveries_df.groupby(['batter', 'bowler']).agg({
            'batsman_runs': ['sum', 'count'],
            'is_wicket': 'sum'
        }).reset_index()
        
        ball_stats.columns = ['batter', 'bowler', 'ball_runs', 'balls_faced', 'wickets_taken']
        
        # Log statistics about processed data
        logger.info(f"Processed {len(player_stats_df)} player records across {player_stats_df['Year'].nunique()} years")
        logger.info(f"Number of unique players: {player_stats_df['Player_Name'].nunique()}")
        
        return player_stats_df, ball_stats
    
    def combine_data(self, matches_df, player_stats_df, ball_stats):
        """Combine matches and player statistics into a single dataset"""
        logger.info("Combining data sources...")
        
        # Create a base dataset with all matches
        combined_df = matches_df.copy()
        
        # Add player statistics
        player_stats_pivot = player_stats_df.pivot_table(
            index=['Player_Name', 'Year'],
            values=['Runs_Scored', 'Batting_Average', 'Batting_Strike_Rate',
                   'Wickets_Taken', 'Bowling_Average', 'Economy_Rate',
                   'Runs_Scored_3yr_avg', 'Batting_Average_3yr_avg', 'Batting_Strike_Rate_3yr_avg',
                   'Wickets_Taken_3yr_avg', 'Bowling_Average_3yr_avg', 'Economy_Rate_3yr_avg',
                   'Career_Matches_Batted', 'Career_Runs_Scored', 'Career_Batting_Average',
                   'Career_Batting_Strike_Rate', 'Career_Wickets_Taken', 'Career_Bowling_Average',
                   'Career_Economy_Rate', 'Career_Catches_Taken', 'Career_Stumpings'],
            aggfunc='mean'
        ).reset_index()
        
        # Log some statistics before merging
        logger.info(f"Number of matches before merge: {len(combined_df)}")
        logger.info(f"Unique players in matches: {combined_df['player_of_match'].nunique()}")
        logger.info(f"Unique players in stats: {player_stats_pivot['Player_Name'].nunique()}")
        
        # Merge with matches data based on player of match and year
        combined_df = combined_df.merge(
            player_stats_pivot,
            left_on=['player_of_match', 'year'],
            right_on=['Player_Name', 'Year'],
            how='left'
        )
        
        # Add ball-by-ball statistics for the match
        match_ball_stats = ball_stats.merge(
            combined_df[['id', 'player_of_match']],
            left_on='batter',
            right_on='player_of_match',
            how='inner'
        )
        
        match_ball_stats = match_ball_stats.groupby('id').agg({
            'ball_runs': 'sum',
            'balls_faced': 'sum',
            'wickets_taken': 'sum'
        }).reset_index()
        
        # Merge ball stats
        combined_df = combined_df.merge(
            match_ball_stats,
            on='id',
            how='left'
        )
        
        # Fill missing values
        numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
        combined_df[numeric_cols] = combined_df[numeric_cols].fillna(0)
        
        # Log merge results
        matches_with_stats = combined_df.dropna(subset=['Batting_Average', 'Bowling_Average']).shape[0]
        logger.info(f"Matches with player statistics: {matches_with_stats} ({matches_with_stats/len(combined_df)*100:.1f}%)")
        
        return combined_df
    
    def save_processed_data(self, df, filename="combined_data.csv"):
        """Save processed data to CSV"""
        output_path = self.processed_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
        
    def run_pipeline(self):
        """Run the complete data pipeline"""
        try:
            # Load data
            matches_df, player_stats_df, deliveries_df = self.load_data()
            
            # Process data
            matches_df = self.process_matches(matches_df)
            player_stats_df, ball_stats = self.process_player_stats(player_stats_df, deliveries_df)
            
            # Combine data
            combined_df = self.combine_data(matches_df, player_stats_df, ball_stats)
            
            # Save processed data
            self.save_processed_data(combined_df)
            
            logger.info("Data pipeline completed successfully")
            return combined_df
            
        except Exception as e:
            logger.error(f"Error in data pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run_pipeline() 