"""
IPL 2025 Match and Team Data
"""

# IPL 2025 Teams and Squads
TEAMS = {
    "Chennai Super Kings": {
        "captain": "MS Dhoni",
        "coach": "Stephen Fleming",
        "home_ground": "M. A. Chidambaram Stadium",
        "players": [
            {"id": "CSK1", "name": "MS Dhoni", "role": "Wicket Keeper", "price": 16},
            {"id": "CSK2", "name": "Ruturaj Gaikwad", "role": "Batsman", "price": 6},
            {"id": "CSK3", "name": "Ravindra Jadeja", "role": "All-rounder", "price": 14},
            {"id": "CSK4", "name": "Moeen Ali", "role": "All-rounder", "price": 8},
            {"id": "CSK5", "name": "Deepak Chahar", "role": "Bowler", "price": 14},
            {"id": "CSK6", "name": "Shivam Dube", "role": "All-rounder", "price": 4},
            {"id": "CSK7", "name": "Tushar Deshpande", "role": "Bowler", "price": 20},
            {"id": "CSK8", "name": "Mitchell Santner", "role": "All-rounder", "price": 1.9},
            {"id": "CSK9", "name": "Devon Conway", "role": "Batsman", "price": 1},
            {"id": "CSK10", "name": "Ajinkya Rahane", "role": "Batsman", "price": 0.5},
            {"id": "CSK11", "name": "Matheesha Pathirana", "role": "Bowler", "price": 20},
            {"id": "CSK12", "name": "Maheesh Theekshana", "role": "Bowler", "price": 70},
            {"id": "CSK13", "name": "Rachin Ravindra", "role": "All-rounder", "price": 1.8},
            {"id": "CSK14", "name": "Shardul Thakur", "role": "All-rounder", "price": 4},
            {"id": "CSK15", "name": "Daryl Mitchell", "role": "All-rounder", "price": 14},
            {"id": "CSK16", "name": "Sameer Rizvi", "role": "Batsman", "price": 8.4},
            {"id": "CSK17", "name": "Mustafizur Rahman", "role": "Bowler", "price": 2},
            {"id": "CSK18", "name": "Avanish Rao Aravelly", "role": "Wicket Keeper", "price": 0.2},
            {"id": "CSK19", "name": "Mukesh Choudhary", "role": "Bowler", "price": 20},
            {"id": "CSK20", "name": "Prashant Solanki", "role": "Bowler", "price": 1.2},
            {"id": "CSK21", "name": "Simarjeet Singh", "role": "Bowler", "price": 20},
            {"id": "CSK22", "name": "RS Hangargekar", "role": "All-rounder", "price": 1.5},
            {"id": "CSK23", "name": "Shaik Rasheed", "role": "Batsman", "price": 20},
            {"id": "CSK24", "name": "Nishant Sindhu", "role": "All-rounder", "price": 0.6},
            {"id": "CSK25", "name": "Ajay Jadav Mandal", "role": "All-rounder", "price": 0.2}
        ]
    },
    "Mumbai Indians": {
        "captain": "Hardik Pandya",
        "coach": "Mark Boucher",
        "home_ground": "Wankhede Stadium",
        "players": [
            {"id": "MI1", "name": "Rohit Sharma", "role": "Batsman", "price": 16},
            {"id": "MI2", "name": "Hardik Pandya", "role": "All-rounder", "price": 15},
            {"id": "MI3", "name": "Jasprit Bumrah", "role": "Bowler", "price": 12},
            {"id": "MI4", "name": "Suryakumar Yadav", "role": "Batsman", "price": 8},
            {"id": "MI5", "name": "Ishan Kishan", "role": "Wicket Keeper", "price": 15.25},
            {"id": "MI6", "name": "Tilak Varma", "role": "All-rounder", "price": 1.7},
            {"id": "MI7", "name": "Tim David", "role": "All-rounder", "price": 8.25},
            {"id": "MI8", "name": "Piyush Chawla", "role": "Bowler", "price": 0.5},
            {"id": "MI9", "name": "Gerald Coetzee", "role": "Bowler", "price": 5},
            {"id": "MI10", "name": "Dewald Brevis", "role": "Batsman", "price": 3},
            {"id": "MI11", "name": "Romario Shepherd", "role": "All-rounder", "price": 8},
            {"id": "MI12", "name": "Mohammed Nabi", "role": "All-rounder", "price": 1.5},
            {"id": "MI13", "name": "Shams Mulani", "role": "All-rounder", "price": 20},
            {"id": "MI14", "name": "Naman Dhir", "role": "All-rounder", "price": 20},
            {"id": "MI15", "name": "Anshul Kamboj", "role": "Bowler", "price": 20},
            {"id": "MI16", "name": "Nehal Wadhera", "role": "Batsman", "price": 20},
            {"id": "MI17", "name": "Shreyas Gopal", "role": "Bowler", "price": 20},
            {"id": "MI18", "name": "Akash Madhwal", "role": "Bowler", "price": 20},
            {"id": "MI19", "name": "Kumar Kartikeya", "role": "Bowler", "price": 20},
            {"id": "MI20", "name": "Arjun Tendulkar", "role": "All-rounder", "price": 30},
            {"id": "MI21", "name": "Hrithik Shokeen", "role": "All-rounder", "price": 20},
            {"id": "MI22", "name": "Raghav Goyal", "role": "Bowler", "price": 20},
            {"id": "MI23", "name": "Suryansh Shedge", "role": "All-rounder", "price": 20},
            {"id": "MI24", "name": "Kwena Maphaka", "role": "Bowler", "price": 0.5},
            {"id": "MI25", "name": "Nuwan Thushara", "role": "Bowler", "price": 4.8}
        ]
    }
    # Add other teams similarly
}

# IPL 2025 Matches
MATCHES = [
    {
        "match_id": 1,
        "match_no": 1,
        "date": "2025-03-22",
        "time": "19:30",
        "venue": "M. A. Chidambaram Stadium, Chennai",
        "team1": "Chennai Super Kings",
        "team2": "Royal Challengers Bangalore",
        "stage": "Group Stage"
    },
    {
        "match_id": 2,
        "match_no": 2,
        "date": "2025-03-23",
        "time": "15:30",
        "venue": "Eden Gardens, Kolkata",
        "team1": "Kolkata Knight Riders",
        "team2": "Sunrisers Hyderabad",
        "stage": "Group Stage"
    }
    # Add all 72 matches
]

def get_match(match_no: int) -> dict:
    """Get match details by match number"""
    for match in MATCHES:
        if match["match_no"] == match_no:
            return match
    return None

def get_team(team_name: str) -> dict:
    """Get team details by team name"""
    return TEAMS.get(team_name)

def get_all_matches() -> list:
    """Get all matches"""
    return MATCHES

def get_all_teams() -> list:
    """Get all teams"""
    return list(TEAMS.keys()) 