import pandas as pd
from datetime import datetime

teams = [
    {
        'name': 'Mumbai Indians',
        'players': [
            {'id': 'RO01', 'name': 'Rohit Sharma'},
            {'id': 'SKY01', 'name': 'Suryakumar Yadav'}
        ]
    },
    {
        'name': 'Chennai Super Kings',
        'players': [
            {'id': 'MS01', 'name': 'MS Dhoni'},
            {'id': 'RJ01', 'name': 'Ravindra Jadeja'}
        ]
    },
    {
        'name': 'Gujarat Titans',
        'players': [
            {'id': 'HH01', 'name': 'Hardik Pandya'}
        ]
    }
]

matches = [
    {
        'match_id': '2025_01',
        'season': 2025,
        'date': '2024-03-20',
        'venue': 'Wankhede Stadium',
        'team1': 'Mumbai Indians',
        'team2': 'Chennai Super Kings',
        'toss_winner': 'Mumbai Indians',
        'toss_decision': 'bat',
        'winner': None,
        'player_id': 'RO01',
        'player_name': 'Rohit Sharma',
        'runs': None,
        'wickets': None,
        'strike_rate': None,
        'economy_rate': None,
        'opponent': 'Chennai Super Kings',
        'match_importance': 0.8,  # Opening match
        'pressure_index': 0.7     # High stakes game
    },
    {
        'match_id': '2025_02',
        'season': 2025,
        'date': '2024-03-22',
        'venue': 'MA Chidambaram Stadium',
        'team1': 'Chennai Super Kings',
        'team2': 'Gujarat Titans',
        'toss_winner': None,
        'toss_decision': None,
        'winner': None,
        'player_id': 'MS01',
        'player_name': 'MS Dhoni',
        'runs': None,
        'wickets': None,
        'strike_rate': None,
        'economy_rate': None,
        'opponent': 'Gujarat Titans',
        'match_importance': 0.6,
        'pressure_index': 0.5
    }
]

# Convert matches to DataFrame to ensure column consistency
matches_df = pd.DataFrame(matches)
matches = matches_df.to_dict('records') 