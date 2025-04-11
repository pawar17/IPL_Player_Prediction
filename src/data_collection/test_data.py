"""Test data for model evaluation"""

SAMPLE_MATCHES = [
    {
        'match_id': 'rcb_vs_gt_20240402',
        'team1': 'Royal Challengers Bangalore',
        'team2': 'Gujarat Titans',
        'date': '2024-04-02'
    },
    {
        'match_id': 'csk_vs_mi_20240401',
        'team1': 'Chennai Super Kings',
        'team2': 'Mumbai Indians',
        'date': '2024-04-01'
    }
]

SAMPLE_RESULTS = {
    'rcb_vs_gt_20240402': {
        'match_id': 'rcb_vs_gt_20240402',
        'team_totals': {
            'Royal Challengers Bangalore': {
                'runs': 182,
                'wickets': 6
            },
            'Gujarat Titans': {
                'runs': 168,
                'wickets': 8
            }
        },
        'Royal Challengers Bangalore': [
            {'name': 'Virat Kohli', 'runs': 72, 'wickets': 0, 'catches': 1},
            {'name': 'Faf du Plessis', 'runs': 45, 'wickets': 0, 'catches': 0},
            {'name': 'Glenn Maxwell', 'runs': 25, 'wickets': 1, 'catches': 1},
            {'name': 'Cameron Green', 'runs': 15, 'wickets': 1, 'catches': 0},
            {'name': 'Rajat Patidar', 'runs': 12, 'wickets': 0, 'catches': 1},
            {'name': 'Dinesh Karthik', 'runs': 8, 'wickets': 0, 'catches': 2},
            {'name': 'Anuj Rawat', 'runs': 5, 'wickets': 0, 'catches': 1},
            {'name': 'Mayank Dagar', 'runs': 0, 'wickets': 0, 'catches': 0},
            {'name': 'Alzarri Joseph', 'runs': 0, 'wickets': 2, 'catches': 0},
            {'name': 'Mohammed Siraj', 'runs': 0, 'wickets': 3, 'catches': 0},
            {'name': 'Yash Dayal', 'runs': 0, 'wickets': 1, 'catches': 0}
        ],
        'Gujarat Titans': [
            {'name': 'Shubman Gill', 'runs': 58, 'wickets': 0, 'catches': 1},
            {'name': 'Wriddhiman Saha', 'runs': 25, 'wickets': 0, 'catches': 2},
            {'name': 'Sai Sudharsan', 'runs': 30, 'wickets': 0, 'catches': 0},
            {'name': 'David Miller', 'runs': 35, 'wickets': 0, 'catches': 0},
            {'name': 'Vijay Shankar', 'runs': 8, 'wickets': 0, 'catches': 1},
            {'name': 'Rahul Tewatia', 'runs': 12, 'wickets': 0, 'catches': 0},
            {'name': 'Rashid Khan', 'runs': 0, 'wickets': 2, 'catches': 1},
            {'name': 'Noor Ahmad', 'runs': 0, 'wickets': 1, 'catches': 0},
            {'name': 'Umesh Yadav', 'runs': 0, 'wickets': 1, 'catches': 0},
            {'name': 'Spencer Johnson', 'runs': 0, 'wickets': 1, 'catches': 0},
            {'name': 'Mohit Sharma', 'runs': 0, 'wickets': 1, 'catches': 0}
        ]
    },
    'csk_vs_mi_20240401': {
        'match_id': 'csk_vs_mi_20240401',
        'team_totals': {
            'Chennai Super Kings': {
                'runs': 192,
                'wickets': 4
            },
            'Mumbai Indians': {
                'runs': 186,
                'wickets': 7
            }
        },
        'Chennai Super Kings': [
            {'name': 'Ruturaj Gaikwad', 'runs': 85, 'wickets': 0, 'catches': 1},
            {'name': 'Rachin Ravindra', 'runs': 42, 'wickets': 0, 'catches': 0},
            {'name': 'Ajinkya Rahane', 'runs': 25, 'wickets': 0, 'catches': 1},
            {'name': 'Shivam Dube', 'runs': 45, 'wickets': 0, 'catches': 0},
            {'name': 'Ravindra Jadeja', 'runs': 32, 'wickets': 2, 'catches': 2},
            {'name': 'MS Dhoni', 'runs': 20, 'wickets': 0, 'catches': 1},
            {'name': 'Deepak Chahar', 'runs': 12, 'wickets': 3, 'catches': 0},
            {'name': 'Tushar Deshpande', 'runs': 0, 'wickets': 2, 'catches': 0},
            {'name': 'Matheesha Pathirana', 'runs': 0, 'wickets': 2, 'catches': 0},
            {'name': 'Maheesh Theekshana', 'runs': 0, 'wickets': 1, 'catches': 0},
            {'name': 'Mustafizur Rahman', 'runs': 0, 'wickets': 0, 'catches': 1}
        ],
        'Mumbai Indians': [
            {'name': 'Rohit Sharma', 'runs': 65, 'wickets': 0, 'catches': 1},
            {'name': 'Ishan Kishan', 'runs': 48, 'wickets': 0, 'catches': 2},
            {'name': 'Tilak Varma', 'runs': 35, 'wickets': 0, 'catches': 0},
            {'name': 'Hardik Pandya', 'runs': 42, 'wickets': 1, 'catches': 1},
            {'name': 'Tim David', 'runs': 28, 'wickets': 0, 'catches': 0},
            {'name': 'Romario Shepherd', 'runs': 15, 'wickets': 1, 'catches': 0},
            {'name': 'Mohammad Nabi', 'runs': 8, 'wickets': 1, 'catches': 1},
            {'name': 'Piyush Chawla', 'runs': 0, 'wickets': 1, 'catches': 0},
            {'name': 'Gerald Coetzee', 'runs': 0, 'wickets': 2, 'catches': 0},
            {'name': 'Jasprit Bumrah', 'runs': 8, 'wickets': 2, 'catches': 1},
            {'name': 'Akash Madhwal', 'runs': 0, 'wickets': 1, 'catches': 0}
        ]
    }
}

SAMPLE_PLAYER_STATS = {
    'Virat Kohli': {
        'Batting_Average': 48.5,
        'Batting_Strike_Rate': 142.8,
        'Batting_Average_3yr_avg': 46.2,
        'Batting_Strike_Rate_3yr_avg': 140.5,
        'Career_Batting_Average': 45.8,
        'Career_Batting_Strike_Rate': 138.2,
        'Career_Runs_Scored': 7500,
        'Runs_Scored_3yr_avg': 650,
        'matches_played': 250,
        'Bowling_Average': 0,
        'Economy_Rate': 0,
        'Bowling_Average_3yr_avg': 0,
        'Economy_Rate_3yr_avg': 0,
        'Career_Wickets_Taken': 4,
        'Wickets_Taken_3yr_avg': 0.5,
        'Career_Catches_Taken': 120,
        'Career_Stumpings': 0
    },
    'Faf du Plessis': {
        'Batting_Average': 42.3,
        'Batting_Strike_Rate': 138.6,
        'Batting_Average_3yr_avg': 40.8,
        'Batting_Strike_Rate_3yr_avg': 136.2,
        'Career_Batting_Average': 38.5,
        'Career_Batting_Strike_Rate': 135.8,
        'Career_Runs_Scored': 4500,
        'Runs_Scored_3yr_avg': 550,
        'matches_played': 180,
        'Bowling_Average': 0,
        'Economy_Rate': 0,
        'Bowling_Average_3yr_avg': 0,
        'Economy_Rate_3yr_avg': 0,
        'Career_Wickets_Taken': 2,
        'Wickets_Taken_3yr_avg': 0.2,
        'Career_Catches_Taken': 85,
        'Career_Stumpings': 0
    },
    'Glenn Maxwell': {
        'Batting_Average': 35.8,
        'Batting_Strike_Rate': 158.2,
        'Batting_Average_3yr_avg': 34.2,
        'Batting_Strike_Rate_3yr_avg': 156.8,
        'Career_Batting_Average': 32.5,
        'Career_Batting_Strike_Rate': 155.2,
        'Career_Runs_Scored': 3500,
        'Runs_Scored_3yr_avg': 450,
        'matches_played': 150,
        'Bowling_Average': 28.5,
        'Economy_Rate': 8.2,
        'Bowling_Average_3yr_avg': 27.8,
        'Economy_Rate_3yr_avg': 8.0,
        'Career_Wickets_Taken': 85,
        'Wickets_Taken_3yr_avg': 12,
        'Career_Catches_Taken': 95,
        'Career_Stumpings': 0
    },
    'Mohammed Siraj': {
        'Batting_Average': 8.2,
        'Batting_Strike_Rate': 95.4,
        'Batting_Average_3yr_avg': 7.8,
        'Batting_Strike_Rate_3yr_avg': 94.2,
        'Career_Batting_Average': 7.5,
        'Career_Batting_Strike_Rate': 93.8,
        'Career_Runs_Scored': 250,
        'Runs_Scored_3yr_avg': 45,
        'matches_played': 100,
        'Bowling_Average': 24.6,
        'Economy_Rate': 7.8,
        'Bowling_Average_3yr_avg': 23.8,
        'Economy_Rate_3yr_avg': 7.6,
        'Career_Wickets_Taken': 120,
        'Wickets_Taken_3yr_avg': 25,
        'Career_Catches_Taken': 35,
        'Career_Stumpings': 0
    },
    'Rohit Sharma': {
        'Batting_Average': 45.2,
        'Batting_Strike_Rate': 140.5,
        'Batting_Average_3yr_avg': 43.8,
        'Batting_Strike_Rate_3yr_avg': 138.2,
        'Career_Batting_Average': 42.5,
        'Career_Batting_Strike_Rate': 136.8,
        'Career_Runs_Scored': 6500,
        'Runs_Scored_3yr_avg': 580,
        'matches_played': 240,
        'Bowling_Average': 35.2,
        'Economy_Rate': 8.5,
        'Bowling_Average_3yr_avg': 34.8,
        'Economy_Rate_3yr_avg': 8.2,
        'Career_Wickets_Taken': 15,
        'Wickets_Taken_3yr_avg': 2,
        'Career_Catches_Taken': 95,
        'Career_Stumpings': 0
    },
    'Hardik Pandya': {
        'Batting_Average': 32.5,
        'Batting_Strike_Rate': 145.8,
        'Batting_Average_3yr_avg': 31.2,
        'Batting_Strike_Rate_3yr_avg': 144.2,
        'Career_Batting_Average': 30.8,
        'Career_Batting_Strike_Rate': 142.5,
        'Career_Runs_Scored': 2800,
        'Runs_Scored_3yr_avg': 420,
        'matches_played': 120,
        'Bowling_Average': 28.2,
        'Economy_Rate': 8.4,
        'Bowling_Average_3yr_avg': 27.5,
        'Economy_Rate_3yr_avg': 8.2,
        'Career_Wickets_Taken': 65,
        'Wickets_Taken_3yr_avg': 15,
        'Career_Catches_Taken': 45,
        'Career_Stumpings': 0
    },
    'Jasprit Bumrah': {
        'Batting_Average': 6.2,
        'Batting_Strike_Rate': 85.4,
        'Batting_Average_3yr_avg': 5.8,
        'Batting_Strike_Rate_3yr_avg': 84.2,
        'Career_Batting_Average': 5.5,
        'Career_Batting_Strike_Rate': 82.8,
        'Career_Runs_Scored': 150,
        'Runs_Scored_3yr_avg': 35,
        'matches_played': 110,
        'Bowling_Average': 22.4,
        'Economy_Rate': 7.2,
        'Bowling_Average_3yr_avg': 21.8,
        'Economy_Rate_3yr_avg': 7.0,
        'Career_Wickets_Taken': 145,
        'Wickets_Taken_3yr_avg': 28,
        'Career_Catches_Taken': 25,
        'Career_Stumpings': 0
    },
    'MS Dhoni': {
        'Batting_Average': 38.2,
        'Batting_Strike_Rate': 148.5,
        'Batting_Average_3yr_avg': 36.8,
        'Batting_Strike_Rate_3yr_avg': 146.2,
        'Career_Batting_Average': 35.5,
        'Career_Batting_Strike_Rate': 144.8,
        'Career_Runs_Scored': 5200,
        'Runs_Scored_3yr_avg': 380,
        'matches_played': 250,
        'Bowling_Average': 0,
        'Economy_Rate': 0,
        'Bowling_Average_3yr_avg': 0,
        'Economy_Rate_3yr_avg': 0,
        'Career_Wickets_Taken': 0,
        'Wickets_Taken_3yr_avg': 0,
        'Career_Catches_Taken': 150,
        'Career_Stumpings': 45
    },
    'Ravindra Jadeja': {
        'Batting_Average': 32.8,
        'Batting_Strike_Rate': 142.5,
        'Batting_Average_3yr_avg': 31.5,
        'Batting_Strike_Rate_3yr_avg': 140.8,
        'Career_Batting_Average': 30.2,
        'Career_Batting_Strike_Rate': 138.5,
        'Career_Runs_Scored': 2800,
        'Runs_Scored_3yr_avg': 420,
        'matches_played': 220,
        'Bowling_Average': 25.4,
        'Economy_Rate': 7.6,
        'Bowling_Average_3yr_avg': 24.8,
        'Economy_Rate_3yr_avg': 7.4,
        'Career_Wickets_Taken': 135,
        'Wickets_Taken_3yr_avg': 25,
        'Career_Catches_Taken': 95,
        'Career_Stumpings': 0
    },
    'Shubman Gill': {
        'Batting_Average': 42.8,
        'Batting_Strike_Rate': 138.2,
        'Batting_Average_3yr_avg': 41.5,
        'Batting_Strike_Rate_3yr_avg': 136.8,
        'Career_Batting_Average': 40.2,
        'Career_Batting_Strike_Rate': 135.5,
        'Career_Runs_Scored': 2200,
        'Runs_Scored_3yr_avg': 580,
        'matches_played': 80,
        'Bowling_Average': 0,
        'Economy_Rate': 0,
        'Bowling_Average_3yr_avg': 0,
        'Economy_Rate_3yr_avg': 0,
        'Career_Wickets_Taken': 0,
        'Wickets_Taken_3yr_avg': 0,
        'Career_Catches_Taken': 35,
        'Career_Stumpings': 0
    },
    'Rashid Khan': {
        'Batting_Average': 18.5,
        'Batting_Strike_Rate': 152.8,
        'Batting_Average_3yr_avg': 17.2,
        'Batting_Strike_Rate_3yr_avg': 150.5,
        'Career_Batting_Average': 16.8,
        'Career_Batting_Strike_Rate': 148.2,
        'Career_Runs_Scored': 850,
        'Runs_Scored_3yr_avg': 220,
        'matches_played': 95,
        'Bowling_Average': 21.2,
        'Economy_Rate': 6.8,
        'Bowling_Average_3yr_avg': 20.5,
        'Economy_Rate_3yr_avg': 6.6,
        'Career_Wickets_Taken': 125,
        'Wickets_Taken_3yr_avg': 28,
        'Career_Catches_Taken': 45,
        'Career_Stumpings': 0
    }
} 