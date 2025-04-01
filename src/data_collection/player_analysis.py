import os
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('player_analysis.log'),
        logging.StreamHandler()
    ]
)

class PlayerAnalyzer:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.processed_data_path = self.base_path / 'data' / 'processed'
        self.processed_data_path.mkdir(parents=True, exist_ok=True)
        
        # Load historical data
        self.matches_df = pd.read_csv(self.processed_data_path / 'processed_matches.csv')
        self.deliveries_df = pd.read_csv(self.processed_data_path / 'processed_deliveries.csv')
        self.player_stats_df = pd.read_csv(self.processed_data_path / 'player_stats.csv')
        
        # IPL 2024 Teams and their key players (based on 2024 auction)
        self.teams = {
            'Chennai Super Kings': {
                'captain': 'MS Dhoni',
                'key_players': ['MS Dhoni', 'Ruturaj Gaikwad', 'Ravindra Jadeja', 'Moeen Ali', 'Deepak Chahar']
            },
            'Delhi Capitals': {
                'captain': 'Rishabh Pant',
                'key_players': ['Rishabh Pant', 'David Warner', 'Axar Patel', 'Kuldeep Yadav', 'Anrich Nortje']
            },
            'Gujarat Titans': {
                'captain': 'Shubman Gill',
                'key_players': ['Shubman Gill', 'Rashid Khan', 'David Miller', 'Mohammed Shami', 'Sai Sudharsan']
            },
            'Kolkata Knight Riders': {
                'captain': 'Shreyas Iyer',
                'key_players': ['Shreyas Iyer', 'Sunil Narine', 'Andre Russell', 'Varun Chakaravarthy', 'Venkatesh Iyer']
            },
            'Lucknow Super Giants': {
                'captain': 'KL Rahul',
                'key_players': ['KL Rahul', 'Quinton de Kock', 'Marcus Stoinis', 'Ravi Bishnoi', 'Mark Wood']
            },
            'Mumbai Indians': {
                'captain': 'Hardik Pandya',
                'key_players': ['Hardik Pandya', 'Rohit Sharma', 'Jasprit Bumrah', 'Suryakumar Yadav', 'Tilak Varma']
            },
            'Punjab Kings': {
                'captain': 'Shikhar Dhawan',
                'key_players': ['Shikhar Dhawan', 'Sam Curran', 'Liam Livingstone', 'Arshdeep Singh', 'Kagiso Rabada']
            },
            'Rajasthan Royals': {
                'captain': 'Sanju Samson',
                'key_players': ['Sanju Samson', 'Jos Buttler', 'Yuzvendra Chahal', 'R Ashwin', 'Trent Boult']
            },
            'Royal Challengers Bangalore': {
                'captain': 'Faf du Plessis',
                'key_players': ['Faf du Plessis', 'Virat Kohli', 'Glenn Maxwell', 'Mohammed Siraj', 'Cameron Green']
            },
            'Sunrisers Hyderabad': {
                'captain': 'Pat Cummins',
                'key_players': ['Pat Cummins', 'Aiden Markram', 'Heinrich Klaasen', 'Bhuvneshwar Kumar', 'Mayank Agarwal']
            }
        }

    def analyze_player_performance(self, player_name: str) -> Dict:
        """Analyze historical performance of a player."""
        try:
            # Get player's batting stats
            batting_stats = self.player_stats_df[self.player_stats_df['player'] == player_name]
            
            if batting_stats.empty:
                return {
                    'player': player_name,
                    'total_runs': 0,
                    'matches_played': 0,
                    'average': 0,
                    'strike_rate': 0,
                    'fours': 0,
                    'sixes': 0
                }
            
            stats = batting_stats.iloc[0]
            return {
                'player': player_name,
                'total_runs': int(stats['total_runs']),
                'matches_played': int(stats['balls_faced'] / 20),  # Approximate matches
                'average': float(stats['average']),
                'strike_rate': float(stats['strike_rate']),
                'fours': int(stats['fours']),
                'sixes': int(stats['sixes'])
            }
        except Exception as e:
            logging.error(f"Error analyzing player {player_name}: {str(e)}")
            return {}

    def analyze_team_composition(self, team_name: str) -> Dict:
        """Analyze team composition and strength."""
        try:
            team_info = self.teams[team_name]
            team_analysis = {
                'team': team_name,
                'captain': team_info['captain'],
                'key_players': team_info['key_players'],
                'player_stats': {}
            }
            
            # Analyze each key player
            for player in team_info['key_players']:
                team_analysis['player_stats'][player] = self.analyze_player_performance(player)
            
            return team_analysis
        except Exception as e:
            logging.error(f"Error analyzing team {team_name}: {str(e)}")
            return {}

    def generate_match_predictions(self, team1: str, team2: str) -> Dict:
        """Generate predictions for a match between two teams."""
        try:
            team1_analysis = self.analyze_team_composition(team1)
            team2_analysis = self.analyze_team_composition(team2)
            
            # Calculate team strength based on player stats
            team1_strength = sum(
                stats['total_runs'] * 0.7 + stats['strike_rate'] * 0.3
                for stats in team1_analysis['player_stats'].values()
            )
            
            team2_strength = sum(
                stats['total_runs'] * 0.7 + stats['strike_rate'] * 0.3
                for stats in team2_analysis['player_stats'].values()
            )
            
            # Calculate win probability
            total_strength = team1_strength + team2_strength
            team1_probability = (team1_strength / total_strength) * 100 if total_strength > 0 else 50
            
            return {
                'team1': team1,
                'team2': team2,
                'team1_strength': team1_strength,
                'team2_strength': team2_strength,
                'team1_win_probability': team1_probability,
                'team2_win_probability': 100 - team1_probability,
                'team1_analysis': team1_analysis,
                'team2_analysis': team2_analysis
            }
        except Exception as e:
            logging.error(f"Error generating predictions for {team1} vs {team2}: {str(e)}")
            return {}

    def save_data(self, data: Dict, filename: str):
        """Save data to JSON file."""
        try:
            filepath = self.processed_data_path / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"Successfully saved data to {filename}")
        except Exception as e:
            logging.error(f"Error saving data: {str(e)}")
            raise

    def run(self):
        """Run the complete analysis pipeline."""
        try:
            logging.info("Starting player and team analysis...")
            
            # Analyze each team
            team_analyses = {}
            for team in self.teams:
                logging.info(f"Analyzing {team}...")
                team_analyses[team] = self.analyze_team_composition(team)
            
            # Generate predictions for all possible matchups
            match_predictions = {}
            teams = list(self.teams.keys())
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    team1, team2 = teams[i], teams[j]
                    match_key = f"{team1}_vs_{team2}"
                    logging.info(f"Generating predictions for {match_key}...")
                    match_predictions[match_key] = self.generate_match_predictions(team1, team2)
            
            # Save all data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_data(team_analyses, f"team_analyses_{timestamp}.json")
            self.save_data(match_predictions, f"match_predictions_{timestamp}.json")
            
            # Create a summary DataFrame
            summary_data = []
            for team, analysis in team_analyses.items():
                team_stats = analysis['player_stats']
                total_runs = sum(stats['total_runs'] for stats in team_stats.values())
                avg_strike_rate = np.mean([stats['strike_rate'] for stats in team_stats.values()])
                
                summary_data.append({
                    'team': team,
                    'total_runs': total_runs,
                    'avg_strike_rate': avg_strike_rate,
                    'key_players': len(team_stats)
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(self.processed_data_path / f"team_summary_{timestamp}.csv", index=False)
            
            logging.info("Successfully completed player and team analysis")
            
        except Exception as e:
            logging.error(f"Error in analysis pipeline: {str(e)}")
            raise

if __name__ == "__main__":
    analyzer = PlayerAnalyzer()
    analyzer.run() 