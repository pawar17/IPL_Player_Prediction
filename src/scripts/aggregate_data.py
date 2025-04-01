import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataAggregator:
    def __init__(self):
        self.data_dir = Path("data")
        self.historical_dir = self.data_dir / "historical"
        self.output_dir = self.data_dir / "aggregated"
        self.output_dir.mkdir(exist_ok=True)

    def load_historical_data(self) -> pd.DataFrame:
        """Load historical match data."""
        try:
            # Load historical match data
            matches_df = pd.read_csv(self.historical_dir / "ipl_matches_2008_2023.csv")
            logger.info(f"Loaded {len(matches_df)} historical matches")
            return matches_df
        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")
            return pd.DataFrame()

    def load_current_season_data(self) -> pd.DataFrame:
        """Load current season data from ipl_2025_data.py."""
        try:
            from ipl_2025_data import matches, teams
            matches_df = pd.DataFrame(matches)
            teams_df = pd.DataFrame(teams)
            logger.info(f"Loaded {len(matches_df)} current season matches")
            return matches_df, teams_df
        except Exception as e:
            logger.error(f"Error loading current season data: {str(e)}")
            return pd.DataFrame(), pd.DataFrame()

    def load_latest_updates(self) -> pd.DataFrame:
        """Load latest match updates from Cricbuzz."""
        try:
            latest_matches = []
            for file in self.data_dir.glob("latest_match_*.json"):
                with open(file, 'r') as f:
                    match_data = json.load(f)
                    latest_matches.extend(match_data)
            latest_df = pd.DataFrame(latest_matches)
            logger.info(f"Loaded {len(latest_df)} latest match updates from Cricbuzz")
            return latest_df
        except Exception as e:
            logger.error(f"Error loading latest updates: {str(e)}")
            return pd.DataFrame()

    def load_ipl_website_data(self) -> pd.DataFrame:
        """Load data scraped from IPL website."""
        try:
            ipl_data = []
            for file in self.data_dir.glob("ipl_website_*.json"):
                with open(file, 'r') as f:
                    data = json.load(f)
                    ipl_data.extend(data)
            ipl_df = pd.DataFrame(ipl_data)
            logger.info(f"Loaded {len(ipl_df)} records from IPL website")
            return ipl_df
        except Exception as e:
            logger.error(f"Error loading IPL website data: {str(e)}")
            return pd.DataFrame()

    def load_player_stats(self) -> pd.DataFrame:
        """Load player statistics."""
        try:
            player_stats = []
            for file in self.historical_dir.glob("player_*.json"):
                with open(file, 'r') as f:
                    stats = json.load(f)
                    player_stats.extend(stats)
            stats_df = pd.DataFrame(player_stats)
            logger.info(f"Loaded {len(stats_df)} player statistics")
            return stats_df
        except Exception as e:
            logger.error(f"Error loading player stats: {str(e)}")
            return pd.DataFrame()

    def aggregate_match_data(self) -> pd.DataFrame:
        """Aggregate all match data sources."""
        try:
            # Load all data sources
            historical_df = self.load_historical_data()
            current_matches_df, teams_df = self.load_current_season_data()
            latest_df = self.load_latest_updates()
            ipl_df = self.load_ipl_website_data()

            # Combine all match data
            all_matches = pd.concat([
                historical_df,
                current_matches_df,
                latest_df,
                ipl_df
            ], ignore_index=True)

            # Remove duplicates based on match_id
            all_matches = all_matches.drop_duplicates(subset=['match_id'])

            # Sort by date
            all_matches['date'] = pd.to_datetime(all_matches['date'])
            all_matches = all_matches.sort_values('date')

            logger.info(f"Aggregated {len(all_matches)} total matches")
            return all_matches
        except Exception as e:
            logger.error(f"Error aggregating match data: {str(e)}")
            return pd.DataFrame()

    def aggregate_player_data(self) -> pd.DataFrame:
        """Aggregate player statistics and current status."""
        try:
            # Load player stats
            stats_df = self.load_player_stats()
            
            # Load current season data for player availability
            _, teams_df = self.load_current_season_data()
            
            # Load IPL website data for additional player info
            ipl_df = self.load_ipl_website_data()
            
            # Extract player availability from teams data
            player_availability = []
            for _, team in teams_df.iterrows():
                for player in team['players']:
                    player_availability.append({
                        'player_id': player['id'],
                        'name': player['name'],
                        'team': team['name'],
                        'status': player['status'],
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
            
            availability_df = pd.DataFrame(player_availability)
            
            # Merge stats with availability and IPL website data
            player_data = pd.merge(
                stats_df,
                availability_df,
                on=['player_id', 'name'],
                how='outer'
            )

            # Add any additional player info from IPL website
            if not ipl_df.empty:
                player_data = pd.merge(
                    player_data,
                    ipl_df[['player_id', 'name', 'role', 'price', 'country']],
                    on=['player_id', 'name'],
                    how='left'
                )

            logger.info(f"Aggregated {len(player_data)} player records")
            return player_data
        except Exception as e:
            logger.error(f"Error aggregating player data: {str(e)}")
            return pd.DataFrame()

    def save_aggregated_data(self):
        """Save aggregated data for model input."""
        try:
            # Aggregate data
            matches_df = self.aggregate_match_data()
            players_df = self.aggregate_player_data()

            # Save to CSV
            matches_df.to_csv(self.output_dir / "aggregated_matches.csv", index=False)
            players_df.to_csv(self.output_dir / "aggregated_players.csv", index=False)

            # Generate summary report
            report = [
                "Data Aggregation Report",
                "=" * 50,
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"\nTotal Matches: {len(matches_df)}",
                f"Total Players: {len(players_df)}",
                f"\nData Sources:",
                "- Historical matches (2008-2023)",
                "- Current season matches (2025)",
                "- Latest match updates (Cricbuzz)",
                "- IPL website data",
                "- Player statistics",
                "- Team rosters and availability"
            ]

            with open(self.output_dir / "aggregation_report.txt", 'w') as f:
                f.write("\n".join(report))

            logger.info("Saved aggregated data and report")
        except Exception as e:
            logger.error(f"Error saving aggregated data: {str(e)}")

def main():
    aggregator = DataAggregator()
    aggregator.save_aggregated_data()

if __name__ == "__main__":
    main() 