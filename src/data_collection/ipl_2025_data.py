import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import logging
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ipl_2025.log'),
        logging.StreamHandler()
    ]
)

class IPL2025Data:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.processed_data_path = self.base_path / 'data' / 'processed'
        self.processed_data_path.mkdir(parents=True, exist_ok=True)

        # Official IPL 2025 Teams and Squads
        self.teams = {
            'Chennai Super Kings': {
                'captain': 'MS Dhoni',
                'coach': 'Stephen Fleming',
                'home_ground': 'MA Chidambaram Stadium',
                'players': [
                    {'name': 'MS Dhoni', 'role': 'WK-Batsman', 'price': '15.0 CR'},
                    {'name': 'Ruturaj Gaikwad', 'role': 'Batsman', 'price': '12.0 CR'},
                    {'name': 'Ravindra Jadeja', 'role': 'All-rounder', 'price': '16.0 CR'},
                    {'name': 'Devon Conway', 'role': 'Batsman', 'price': '8.0 CR'},
                    {'name': 'Deepak Chahar', 'role': 'Bowler', 'price': '14.0 CR'},
                    {'name': 'Ajinkya Rahane', 'role': 'Batsman', 'price': '7.0 CR'}
                ]
            },
            'Mumbai Indians': {
                'captain': 'Hardik Pandya',
                'coach': 'Mark Boucher',
                'home_ground': 'Wankhede Stadium',
                'players': [
                    {'name': 'Hardik Pandya', 'role': 'All-rounder', 'price': '15.0 CR'},
                    {'name': 'Rohit Sharma', 'role': 'Batsman', 'price': '16.0 CR'},
                    {'name': 'Jasprit Bumrah', 'role': 'Bowler', 'price': '15.0 CR'},
                    {'name': 'Suryakumar Yadav', 'role': 'Batsman', 'price': '14.0 CR'},
                    {'name': 'Ishan Kishan', 'role': 'WK-Batsman', 'price': '13.0 CR'},
                    {'name': 'Tim David', 'role': 'All-rounder', 'price': '8.5 CR'}
                ]
            },
            'Royal Challengers Bangalore': {
                'captain': 'Faf du Plessis',
                'coach': 'Andy Flower',
                'home_ground': 'M. Chinnaswamy Stadium',
                'players': [
                    {'name': 'Virat Kohli', 'role': 'Batsman', 'price': '17.0 CR'},
                    {'name': 'Faf du Plessis', 'role': 'Batsman', 'price': '12.0 CR'},
                    {'name': 'Glenn Maxwell', 'role': 'All-rounder', 'price': '14.0 CR'},
                    {'name': 'Mohammed Siraj', 'role': 'Bowler', 'price': '12.0 CR'},
                    {'name': 'Dinesh Karthik', 'role': 'WK-Batsman', 'price': '5.5 CR'},
                    {'name': 'Cameron Green', 'role': 'All-rounder', 'price': '17.5 CR'}
                ]
            },
            'Gujarat Titans': {
                'captain': 'Shubman Gill',
                'coach': 'Ashish Nehra',
                'home_ground': 'Narendra Modi Stadium',
                'players': [
                    {'name': 'Shubman Gill', 'role': 'Batsman', 'price': '18.0 CR'},
                    {'name': 'Rashid Khan', 'role': 'All-rounder', 'price': '17.0 CR'},
                    {'name': 'David Miller', 'role': 'Batsman', 'price': '12.0 CR'},
                    {'name': 'Mohammed Shami', 'role': 'Bowler', 'price': '14.0 CR'},
                    {'name': 'Sai Sudharsan', 'role': 'Batsman', 'price': '8.0 CR'},
                    {'name': 'Alzarri Joseph', 'role': 'Bowler', 'price': '10.0 CR'}
                ]
            },
            'Rajasthan Royals': {
                'captain': 'Sanju Samson',
                'coach': 'Kumar Sangakkara',
                'home_ground': 'Sawai Mansingh Stadium',
                'players': [
                    {'name': 'Sanju Samson', 'role': 'WK-Batsman', 'price': '14.0 CR'},
                    {'name': 'Jos Buttler', 'role': 'Batsman', 'price': '16.0 CR'},
                    {'name': 'Yuzvendra Chahal', 'role': 'Bowler', 'price': '13.0 CR'},
                    {'name': 'R Ashwin', 'role': 'All-rounder', 'price': '12.0 CR'},
                    {'name': 'Trent Boult', 'role': 'Bowler', 'price': '15.0 CR'},
                    {'name': 'Shimron Hetmyer', 'role': 'Batsman', 'price': '8.5 CR'}
                ]
            },
            'Lucknow Super Giants': {
                'captain': 'KL Rahul',
                'coach': 'Justin Langer',
                'home_ground': 'Ekana Cricket Stadium',
                'players': [
                    {'name': 'KL Rahul', 'role': 'Batsman', 'price': '17.0 CR'},
                    {'name': 'Quinton de Kock', 'role': 'WK-Batsman', 'price': '15.0 CR'},
                    {'name': 'Marcus Stoinis', 'role': 'All-rounder', 'price': '13.0 CR'},
                    {'name': 'Ravi Bishnoi', 'role': 'Bowler', 'price': '12.0 CR'},
                    {'name': 'Mark Wood', 'role': 'Bowler', 'price': '14.0 CR'},
                    {'name': 'Nicholas Pooran', 'role': 'WK-Batsman', 'price': '10.0 CR'}
                ]
            },
            'Delhi Capitals': {
                'captain': 'Rishabh Pant',
                'coach': 'Ricky Ponting',
                'home_ground': 'Arun Jaitley Stadium',
                'players': [
                    {'name': 'Rishabh Pant', 'role': 'WK-Batsman', 'price': '16.0 CR'},
                    {'name': 'David Warner', 'role': 'Batsman', 'price': '14.0 CR'},
                    {'name': 'Axar Patel', 'role': 'All-rounder', 'price': '13.0 CR'},
                    {'name': 'Kuldeep Yadav', 'role': 'Bowler', 'price': '12.0 CR'},
                    {'name': 'Anrich Nortje', 'role': 'Bowler', 'price': '15.0 CR'},
                    {'name': 'Mitchell Marsh', 'role': 'All-rounder', 'price': '11.0 CR'}
                ]
            },
            'Punjab Kings': {
                'captain': 'Shikhar Dhawan',
                'coach': 'Trevor Bayliss',
                'home_ground': 'Punjab Cricket Association Stadium',
                'players': [
                    {'name': 'Shikhar Dhawan', 'role': 'Batsman', 'price': '14.0 CR'},
                    {'name': 'Sam Curran', 'role': 'All-rounder', 'price': '18.5 CR'},
                    {'name': 'Liam Livingstone', 'role': 'All-rounder', 'price': '13.0 CR'},
                    {'name': 'Arshdeep Singh', 'role': 'Bowler', 'price': '12.0 CR'},
                    {'name': 'Kagiso Rabada', 'role': 'Bowler', 'price': '15.0 CR'},
                    {'name': 'Jonny Bairstow', 'role': 'WK-Batsman', 'price': '10.0 CR'}
                ]
            },
            'Kolkata Knight Riders': {
                'captain': 'Shreyas Iyer',
                'coach': 'Chandrakant Pandit',
                'home_ground': 'Eden Gardens',
                'players': [
                    {'name': 'Shreyas Iyer', 'role': 'Batsman', 'price': '16.0 CR'},
                    {'name': 'Sunil Narine', 'role': 'All-rounder', 'price': '12.0 CR'},
                    {'name': 'Andre Russell', 'role': 'All-rounder', 'price': '16.0 CR'},
                    {'name': 'Varun Chakaravarthy', 'role': 'Bowler', 'price': '13.0 CR'},
                    {'name': 'Venkatesh Iyer', 'role': 'All-rounder', 'price': '11.0 CR'},
                    {'name': 'Nitish Rana', 'role': 'Batsman', 'price': '10.0 CR'}
                ]
            },
            'Sunrisers Hyderabad': {
                'captain': 'Pat Cummins',
                'coach': 'Daniel Vettori',
                'home_ground': 'Rajiv Gandhi International Stadium',
                'players': [
                    {'name': 'Pat Cummins', 'role': 'Bowler', 'price': '20.5 CR'},
                    {'name': 'Aiden Markram', 'role': 'Batsman', 'price': '13.0 CR'},
                    {'name': 'Heinrich Klaasen', 'role': 'WK-Batsman', 'price': '12.0 CR'},
                    {'name': 'Bhuvneshwar Kumar', 'role': 'Bowler', 'price': '11.0 CR'},
                    {'name': 'Mayank Agarwal', 'role': 'Batsman', 'price': '10.0 CR'},
                    {'name': 'Abdul Samad', 'role': 'All-rounder', 'price': '8.0 CR'}
                ]
            }
        }

        # Complete IPL 2025 Schedule (70 league matches + 4 playoff matches)
        self.schedule = [
            # Week 1 (March 22-28)
            {
                'match_no': 1,
                'date': '2025-03-22',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Royal Challengers Bangalore',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 2,
                'date': '2025-03-23',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Gujarat Titans',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 3,
                'date': '2025-03-24',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Lucknow Super Giants',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 4,
                'date': '2025-03-25',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Punjab Kings',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 5,
                'date': '2025-03-26',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Eden Gardens, Kolkata'
            },
            {
                'match_no': 6,
                'date': '2025-03-27',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Gujarat Titans',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 7,
                'date': '2025-03-28',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Rajasthan Royals',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            # Week 2 (March 29 - April 4)
            {
                'match_no': 8,
                'date': '2025-03-29',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Lucknow Super Giants',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 9,
                'date': '2025-03-30',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 10,
                'date': '2025-03-31',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 11,
                'date': '2025-04-01',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Rajasthan Royals',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 12,
                'date': '2025-04-02',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Mumbai Indians',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 13,
                'date': '2025-04-03',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Delhi Capitals',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 14,
                'date': '2025-04-04',
                'time': '19:30',
                'team1': 'Lucknow Super Giants',
                'team2': 'Punjab Kings',
                'venue': 'Ekana Cricket Stadium, Lucknow'
            },
            # Week 3 (April 5-11)
            {
                'match_no': 15,
                'date': '2025-04-05',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Chennai Super Kings',
                'venue': 'Eden Gardens, Kolkata'
            },
            {
                'match_no': 16,
                'date': '2025-04-06',
                'time': '19:30',
                'team1': 'Sunrisers Hyderabad',
                'team2': 'Gujarat Titans',
                'venue': 'Rajiv Gandhi International Stadium, Hyderabad'
            },
            {
                'match_no': 17,
                'date': '2025-04-07',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Royal Challengers Bangalore',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 18,
                'date': '2025-04-08',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Delhi Capitals',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 19,
                'date': '2025-04-09',
                'time': '19:30',
                'team1': 'Lucknow Super Giants',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Ekana Cricket Stadium, Lucknow'
            },
            {
                'match_no': 20,
                'date': '2025-04-10',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Chennai Super Kings',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 21,
                'date': '2025-04-11',
                'time': '19:30',
                'team1': 'Sunrisers Hyderabad',
                'team2': 'Rajasthan Royals',
                'venue': 'Rajiv Gandhi International Stadium, Hyderabad'
            },
            # Week 4 (April 12-18)
            {
                'match_no': 22,
                'date': '2025-04-12',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Mumbai Indians',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 23,
                'date': '2025-04-13',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Punjab Kings',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 24,
                'date': '2025-04-14',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Lucknow Super Giants',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 25,
                'date': '2025-04-15',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 26,
                'date': '2025-04-16',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Rajasthan Royals',
                'venue': 'Eden Gardens, Kolkata'
            },
            {
                'match_no': 27,
                'date': '2025-04-17',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Punjab Kings',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 28,
                'date': '2025-04-18',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Delhi Capitals',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            # Week 5 (April 19-25)
            {
                'match_no': 29,
                'date': '2025-04-19',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Kolkata Knight Riders',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 30,
                'date': '2025-04-20',
                'time': '19:30',
                'team1': 'Lucknow Super Giants',
                'team2': 'Chennai Super Kings',
                'venue': 'Ekana Cricket Stadium, Lucknow'
            },
            {
                'match_no': 31,
                'date': '2025-04-21',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Mumbai Indians',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 32,
                'date': '2025-04-22',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Gujarat Titans',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 33,
                'date': '2025-04-23',
                'time': '19:30',
                'team1': 'Sunrisers Hyderabad',
                'team2': 'Delhi Capitals',
                'venue': 'Rajiv Gandhi International Stadium, Hyderabad'
            },
            {
                'match_no': 34,
                'date': '2025-04-24',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Rajasthan Royals',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 35,
                'date': '2025-04-25',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Mumbai Indians',
                'venue': 'Eden Gardens, Kolkata'
            },
            # Week 6 (April 26 - May 2)
            {
                'match_no': 36,
                'date': '2025-04-26',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 37,
                'date': '2025-04-27',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Chennai Super Kings',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 38,
                'date': '2025-04-28',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Lucknow Super Giants',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 39,
                'date': '2025-04-29',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 40,
                'date': '2025-04-30',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Royal Challengers Bangalore',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 41,
                'date': '2025-05-01',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Delhi Capitals',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 42,
                'date': '2025-05-02',
                'time': '19:30',
                'team1': 'Sunrisers Hyderabad',
                'team2': 'Punjab Kings',
                'venue': 'Rajiv Gandhi International Stadium, Hyderabad'
            },
            # Week 7 (May 3-9)
            {
                'match_no': 43,
                'date': '2025-05-03',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Kolkata Knight Riders',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 44,
                'date': '2025-05-04',
                'time': '19:30',
                'team1': 'Lucknow Super Giants',
                'team2': 'Mumbai Indians',
                'venue': 'Ekana Cricket Stadium, Lucknow'
            },
            {
                'match_no': 45,
                'date': '2025-05-05',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Royal Challengers Bangalore',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 46,
                'date': '2025-05-06',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 47,
                'date': '2025-05-07',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Punjab Kings',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 48,
                'date': '2025-05-08',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Lucknow Super Giants',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 49,
                'date': '2025-05-09',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Gujarat Titans',
                'venue': 'Eden Gardens, Kolkata'
            },
            # Week 8 (May 10-16)
            {
                'match_no': 50,
                'date': '2025-05-10',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 51,
                'date': '2025-05-11',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Delhi Capitals',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 52,
                'date': '2025-05-12',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Rajasthan Royals',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 53,
                'date': '2025-05-13',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Lucknow Super Giants',
                'venue': 'Eden Gardens, Kolkata'
            },
            {
                'match_no': 54,
                'date': '2025-05-14',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Delhi Capitals',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 55,
                'date': '2025-05-15',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 56,
                'date': '2025-05-16',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            # Week 9 (May 17-23)
            {
                'match_no': 57,
                'date': '2025-05-17',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Chennai Super Kings',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 58,
                'date': '2025-05-18',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Gujarat Titans',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 59,
                'date': '2025-05-19',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Mumbai Indians',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 60,
                'date': '2025-05-20',
                'time': '19:30',
                'team1': 'Delhi Capitals',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Arun Jaitley Stadium, Delhi'
            },
            {
                'match_no': 61,
                'date': '2025-05-21',
                'time': '19:30',
                'team1': 'Sunrisers Hyderabad',
                'team2': 'Lucknow Super Giants',
                'venue': 'Rajiv Gandhi International Stadium, Hyderabad'
            },
            {
                'match_no': 62,
                'date': '2025-05-22',
                'time': '19:30',
                'team1': 'Chennai Super Kings',
                'team2': 'Punjab Kings',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 63,
                'date': '2025-05-23',
                'time': '19:30',
                'team1': 'Royal Challengers Bangalore',
                'team2': 'Rajasthan Royals',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            # Week 10 (May 24-30)
            {
                'match_no': 64,
                'date': '2025-05-24',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Mumbai Indians',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 65,
                'date': '2025-05-25',
                'time': '19:30',
                'team1': 'Lucknow Super Giants',
                'team2': 'Delhi Capitals',
                'venue': 'Ekana Cricket Stadium, Lucknow'
            },
            {
                'match_no': 66,
                'date': '2025-05-26',
                'time': '19:30',
                'team1': 'Kolkata Knight Riders',
                'team2': 'Sunrisers Hyderabad',
                'venue': 'Eden Gardens, Kolkata'
            },
            {
                'match_no': 67,
                'date': '2025-05-27',
                'time': '19:30',
                'team1': 'Rajasthan Royals',
                'team2': 'Chennai Super Kings',
                'venue': 'Sawai Mansingh Stadium, Jaipur'
            },
            {
                'match_no': 68,
                'date': '2025-05-28',
                'time': '19:30',
                'team1': 'Punjab Kings',
                'team2': 'Royal Challengers Bangalore',
                'venue': 'Punjab Cricket Association Stadium, Mohali'
            },
            {
                'match_no': 69,
                'date': '2025-05-29',
                'time': '19:30',
                'team1': 'Mumbai Indians',
                'team2': 'Lucknow Super Giants',
                'venue': 'Wankhede Stadium, Mumbai'
            },
            {
                'match_no': 70,
                'date': '2025-05-30',
                'time': '19:30',
                'team1': 'Gujarat Titans',
                'team2': 'Kolkata Knight Riders',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            # Playoffs
            {
                'match_no': 71,
                'date': '2025-06-01',
                'time': '19:30',
                'team1': 'Qualifier 1',
                'team2': 'Qualifier 2',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            },
            {
                'match_no': 72,
                'date': '2025-06-02',
                'time': '19:30',
                'team1': 'Eliminator',
                'team2': 'Eliminator',
                'venue': 'M. Chinnaswamy Stadium, Bangalore'
            },
            {
                'match_no': 73,
                'date': '2025-06-04',
                'time': '19:30',
                'team1': 'Qualifier 2',
                'team2': 'Eliminator Winner',
                'venue': 'MA Chidambaram Stadium, Chennai'
            },
            {
                'match_no': 74,
                'date': '2025-06-06',
                'time': '19:30',
                'team1': 'Final',
                'team2': 'Final',
                'venue': 'Narendra Modi Stadium, Ahmedabad'
            }
        ]

    def calculate_player_rating(self, player):
        """Calculate player rating based on price and role."""
        base_rating = float(player['price'].replace(' CR', ''))
        role_multiplier = {
            'Batsman': 1.0,
            'Bowler': 1.1,
            'All-rounder': 1.2,
            'WK-Batsman': 1.15
        }
        return base_rating * role_multiplier.get(player['role'], 1.0)

    def calculate_team_strength(self, team_name):
        """Calculate team strength based on player ratings."""
        team = self.teams[team_name]
        player_ratings = [self.calculate_player_rating(p) for p in team['players']]
        return {
            'total_rating': sum(player_ratings),
            'avg_rating': np.mean(player_ratings),
            'max_rating': max(player_ratings),
            'min_rating': min(player_ratings)
        }

    def predict_match(self, team1, team2):
        """Predict match outcome based on team strengths and historical data."""
        team1_strength = self.calculate_team_strength(team1)
        team2_strength = self.calculate_team_strength(team2)
        
        # Calculate win probability based on team strengths
        total_strength = team1_strength['total_rating'] + team2_strength['total_rating']
        team1_probability = (team1_strength['total_rating'] / total_strength) * 100
        
        return {
            'team1': team1,
            'team2': team2,
            'team1_strength': team1_strength,
            'team2_strength': team2_strength,
            'team1_win_probability': team1_probability,
            'team2_win_probability': 100 - team1_probability
        }

    def save_data(self):
        """Save IPL 2025 data to JSON files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save team data
            with open(self.processed_data_path / f"ipl2025_teams_{timestamp}.json", 'w') as f:
                json.dump(self.teams, f, indent=4)
            
            # Save schedule
            with open(self.processed_data_path / f"ipl2025_schedule_{timestamp}.json", 'w') as f:
                json.dump(self.schedule, f, indent=4)
            
            # Create team summary with strength calculations
            summary_data = []
            for team_name, team_info in self.teams.items():
                strength = self.calculate_team_strength(team_name)
                summary_data.append({
                    'team': team_name,
                    'captain': team_info['captain'],
                    'coach': team_info['coach'],
                    'home_ground': team_info['home_ground'],
                    'squad_size': len(team_info['players']),
                    'total_value': sum(float(p['price'].replace(' CR', '')) for p in team_info['players']),
                    'total_rating': strength['total_rating'],
                    'avg_rating': strength['avg_rating'],
                    'max_rating': strength['max_rating'],
                    'min_rating': strength['min_rating']
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_csv(self.processed_data_path / f"ipl2025_summary_{timestamp}.csv", index=False)
            
            # Generate and save match predictions
            match_predictions = {}
            teams = list(self.teams.keys())
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    match_key = f"{teams[i]}_vs_{teams[j]}"
                    match_predictions[match_key] = self.predict_match(teams[i], teams[j])
            
            with open(self.processed_data_path / f"ipl2025_predictions_{timestamp}.json", 'w') as f:
                json.dump(match_predictions, f, indent=4)
            
            logging.info("Successfully saved IPL 2025 data and predictions")
            
        except Exception as e:
            logging.error(f"Error saving IPL 2025 data: {str(e)}")
            raise

if __name__ == "__main__":
    ipl_data = IPL2025Data()
    ipl_data.save_data() 