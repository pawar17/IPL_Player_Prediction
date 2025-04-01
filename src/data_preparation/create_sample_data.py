import pandas as pd
import numpy as np
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_data(num_matches=100, num_players=50):
    """Create sample IPL data for testing"""
    try:
        # Create data directory if it doesn't exist
        data_path = Path(__file__).parent.parent.parent / 'data' / 'raw'
        data_path.mkdir(parents=True, exist_ok=True)
        
        # Create sample players
        players = [f"Player_{i}" for i in range(num_players)]
        teams = ['MI', 'CSK', 'RCB', 'KKR', 'PBKS', 'RR', 'SRH', 'DC']
        
        # Create matches data
        matches_data = []
        for i in range(num_matches):
            team1, team2 = np.random.choice(teams, size=2, replace=False)
            matches_data.append({
                'id': i + 1,
                'season': np.random.randint(2020, 2024),
                'team1': team1,
                'team2': team2,
                'toss_winner': np.random.choice([team1, team2]),
                'winner': np.random.choice([team1, team2]),
                'venue': f"Venue_{np.random.randint(1, 10)}"
            })
        
        matches_df = pd.DataFrame(matches_data)
        
        # Create player performance data
        performance_data = []
        for match_id in range(1, num_matches + 1):
            # Select random players for both teams
            match = matches_df[matches_df['id'] == match_id].iloc[0]
            team1_players = np.random.choice(players, size=11, replace=False)
            team2_players = np.random.choice(list(set(players) - set(team1_players)), size=11, replace=False)
            
            for player in team1_players:
                # Batting performance
                runs = np.random.randint(0, 100)
                balls = max(1, np.random.randint(1, runs + 20))
                fours = np.random.randint(0, max(1, runs // 10))
                sixes = np.random.randint(0, max(1, runs // 15))
                
                # Bowling performance
                overs = np.random.randint(0, 4)
                if overs > 0:
                    wickets = np.random.randint(0, 5)
                    runs_conceded = np.random.randint(overs * 4, max(overs * 4 + 1, overs * 12))
                else:
                    wickets = 0
                    runs_conceded = 0
                
                # Calculate form factor and other metrics
                form_factor = np.random.uniform(0.5, 2.0)
                consistency_score = np.random.uniform(0, 1)
                pressure_index = np.random.uniform(0, 1)
                
                performance_data.append({
                    'match_id': match_id,
                    'player_name': player,
                    'team': match['team1'],
                    'runs': runs,
                    'balls_faced': balls,
                    'fours': fours,
                    'sixes': sixes,
                    'strike_rate': (runs / balls * 100) if balls > 0 else 0,
                    'overs_bowled': overs,
                    'wickets': wickets,
                    'runs_conceded': runs_conceded,
                    'economy_rate': (runs_conceded / overs) if overs > 0 else 0,
                    'catches': np.random.randint(0, 3),
                    'is_home_game': np.random.choice([0, 1]),
                    'is_powerplay_batsman': np.random.choice([0, 1]),
                    'is_death_bowler': np.random.choice([0, 1]),
                    'form_factor': form_factor,
                    'consistency_score': consistency_score,
                    'pressure_index': pressure_index,
                    'last_5_matches_runs_avg': np.random.uniform(20, 50),
                    'last_5_matches_wickets_avg': np.random.uniform(0, 3),
                    'last_5_matches_sr_avg': np.random.uniform(100, 150),
                    'last_5_matches_er_avg': np.random.uniform(6, 10),
                    'days_since_last_match': np.random.randint(3, 10)
                })
        
        performance_df = pd.DataFrame(performance_data)
        
        # Save data
        matches_df.to_csv(data_path / 'matches.csv', index=False)
        performance_df.to_csv(data_path / 'deliveries.csv', index=False)
        
        logger.info(f"Created sample data with {len(matches_df)} matches and {len(performance_df)} player performances")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating sample data: {str(e)}")
        return False

if __name__ == "__main__":
    create_sample_data() 