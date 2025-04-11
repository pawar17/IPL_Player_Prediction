"""
IPL 2025 Team Rosters
This module contains the complete team rosters for IPL 2025.
"""

# Team Rosters for IPL 2025
TEAM_ROSTERS = {
    "Chennai Super Kings": {
        "batsmen": [
            "Ruturaj Gaikwad",
            "Devon Conway",
            "Ajinkya Rahane",
            "Shivam Dube",
            "Moeen Ali",
            "MS Dhoni"
        ],
        "bowlers": [
            "Deepak Chahar",
            "Tushar Deshpande",
            "Maheesh Theekshana",
            "Matheesha Pathirana",
            "Mukesh Choudhary",
            "Simarjeet Singh"
        ],
        "all_rounders": [
            "Ravindra Jadeja",
            "Mitchell Santner",
            "Dwaine Pretorius",
            "Ben Stokes",
            "Rachin Ravindra"
        ]
    },
    "Royal Challengers Bangalore": {
        "batsmen": [
            "Faf du Plessis",
            "Virat Kohli",
            "Glenn Maxwell",
            "Rajat Patidar",
            "Dinesh Karthik",
            "Anuj Rawat"
        ],
        "bowlers": [
            "Mohammed Siraj",
            "Josh Hazlewood",
            "Harshal Patel",
            "Wanindu Hasaranga",
            "Karn Sharma",
            "Akash Deep"
        ],
        "all_rounders": [
            "Cameron Green",
            "Shahbaz Ahmed",
            "Mahipal Lomror",
            "Will Jacks",
            "Suyash Prabhudessai"
        ]
    },
    "Mumbai Indians": {
        "batsmen": [
            "Rohit Sharma",
            "Ishan Kishan",
            "Suryakumar Yadav",
            "Tilak Varma",
            "Tristan Stubbs",
            "Nehal Wadhera"
        ],
        "bowlers": [
            "Jasprit Bumrah",
            "Jason Behrendorff",
            "Piyush Chawla",
            "Akash Madhwal",
            "Kumar Kartikeya",
            "Arjun Tendulkar"
        ],
        "all_rounders": [
            "Hardik Pandya",
            "Tim David",
            "Romario Shepherd",
            "Vishnu Vinod",
            "Shams Mulani"
        ]
    },
    "Kolkata Knight Riders": {
        "batsmen": [
            "Shreyas Iyer",
            "Venkatesh Iyer",
            "Nitish Rana",
            "Rahmanullah Gurbaz",
            "Rinku Singh",
            "Angkrish Raghuvanshi"
        ],
        "bowlers": [
            "Mitchell Starc",
            "Varun Chakaravarthy",
            "Harshit Rana",
            "Vaibhav Arora",
            "Suyash Sharma",
            "Andre Russell"
        ],
        "all_rounders": [
            "Sunil Narine",
            "Andre Russell",
            "Rinku Singh",
            "Anukul Roy",
            "Ramandeep Singh"
        ]
    },
    "Rajasthan Royals": {
        "batsmen": [
            "Sanju Samson",
            "Yashasvi Jaiswal",
            "Jos Buttler",
            "Shimron Hetmyer",
            "Dhruv Jurel",
            "Riyan Parag"
        ],
        "bowlers": [
            "Trent Boult",
            "Yuzvendra Chahal",
            "Avesh Khan",
            "Sandeep Sharma",
            "Kuldeep Sen",
            "Navdeep Saini"
        ],
        "all_rounders": [
            "Ravichandran Ashwin",
            "Rovman Powell",
            "Donovan Ferreira",
            "Keshav Maharaj",
            "Adam Zampa"
        ]
    },
    "Delhi Capitals": {
        "batsmen": [
            "Rishabh Pant",
            "David Warner",
            "Prithvi Shaw",
            "Yash Dhull",
            "Abishek Porel",
            "Lalit Yadav"
        ],
        "bowlers": [
            "Anrich Nortje",
            "Kuldeep Yadav",
            "Mukesh Kumar",
            "Ishant Sharma",
            "Khaleel Ahmed",
            "Pravin Dubey"
        ],
        "all_rounders": [
            "Axar Patel",
            "Mitchell Marsh",
            "Jake Fraser-McGurk",
            "Sumit Kumar",
            "Kumar Kushagra"
        ]
    },
    "Punjab Kings": {
        "batsmen": [
            "Shikhar Dhawan",
            "Jonny Bairstow",
            "Prabhsimran Singh",
            "Jitesh Sharma",
            "Atharva Taide",
            "Harpreet Singh"
        ],
        "bowlers": [
            "Kagiso Rabada",
            "Arshdeep Singh",
            "Rahul Chahar",
            "Nathan Ellis",
            "Harshal Patel",
            "Harpreet Brar"
        ],
        "all_rounders": [
            "Sam Curran",
            "Liam Livingstone",
            "Rishi Dhawan",
            "Shashank Singh",
            "Vidhwath Kaverappa"
        ]
    },
    "Sunrisers Hyderabad": {
        "batsmen": [
            "Aiden Markram",
            "Heinrich Klaasen",
            "Abdul Samad",
            "Rahul Tripathi",
            "Mayank Agarwal",
            "Travis Head"
        ],
        "bowlers": [
            "Pat Cummins",
            "Bhuvneshwar Kumar",
            "T Natarajan",
            "Mayank Markande",
            "Jaydev Unadkat",
            "Umran Malik"
        ],
        "all_rounders": [
            "Marco Jansen",
            "Wanindu Hasaranga",
            "Washington Sundar",
            "Glenn Phillips",
            "Nitish Kumar Reddy"
        ]
    },
    "Gujarat Titans": {
        "batsmen": [
            "Shubman Gill",
            "Wriddhiman Saha",
            "David Miller",
            "Sai Sudharsan",
            "Kane Williamson",
            "Abhinav Manohar"
        ],
        "bowlers": [
            "Mohammed Shami",
            "Rashid Khan",
            "Josh Little",
            "Noor Ahmad",
            "Umesh Yadav",
            "Darshan Nalkande"
        ],
        "all_rounders": [
            "Hardik Pandya",
            "Vijay Shankar",
            "Azmatullah Omarzai",
            "Rahul Tewatia",
            "Jayant Yadav"
        ]
    }
}

def get_team_roster(team_name: str) -> dict:
    """Get the complete roster for a specific team"""
    return TEAM_ROSTERS.get(team_name, {})

def get_team_batsmen(team_name: str) -> list:
    """Get all batsmen for a specific team"""
    return TEAM_ROSTERS.get(team_name, {}).get("batsmen", [])

def get_team_bowlers(team_name: str) -> list:
    """Get all bowlers for a specific team"""
    return TEAM_ROSTERS.get(team_name, {}).get("bowlers", [])

def get_team_all_rounders(team_name: str) -> list:
    """Get all all-rounders for a specific team"""
    return TEAM_ROSTERS.get(team_name, {}).get("all_rounders", [])

def get_player_role(player_name: str) -> str:
    """Get the primary role of a player"""
    for team, roster in TEAM_ROSTERS.items():
        if player_name in roster["batsmen"]:
            return "batsman"
        elif player_name in roster["bowlers"]:
            return "bowler"
        elif player_name in roster["all_rounders"]:
            return "all_rounder"
    return "unknown" 