import json
from pathlib import Path
from datetime import datetime
from data_collector import DataCollector

def test_data_collection():
    # Create test directory
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # Initialize collector
    collector = DataCollector(data_dir="test_data")
    
    print("Starting data collection test...")
    
    # Test recent matches
    print("\nTesting recent matches...")
    live_matches = collector.fetch_live_matches()
    save_data(live_matches, test_dir / "recent_matches.json")
    print(f"Found {len(live_matches)} recent matches")
    
    # Test trending players
    print("\nTesting trending players...")
    trending_players = collector.get_trending_players()
    save_data(trending_players, test_dir / "trending_players.json")
    print("Retrieved trending players data")
    
    # Test team rankings
    print("\nTesting team rankings...")
    team_rankings = collector.get_team_rankings()
    save_data(team_rankings, test_dir / "team_rankings.json")
    print("Retrieved team rankings")
    
    # Test batsmen rankings
    print("\nTesting batsmen rankings...")
    batsmen_rankings = collector.get_batsmen_rankings()
    save_data(batsmen_rankings, test_dir / "batsmen_rankings.json")
    print("Retrieved batsmen rankings")
    
    # Test top stats
    print("\nTesting top stats...")
    top_stats = collector.get_top_stats()
    save_data(top_stats, test_dir / "top_stats.json")
    print("Retrieved top stats")
    
    # If we have any matches, test match-specific endpoints
    if live_matches:
        match_id = live_matches[0].get('match_id')
        if match_id:
            print(f"\nTesting match-specific endpoints for match {match_id}...")
            
            # Test match details
            match_details = collector.get_match_details(match_id)
            save_data(match_details, test_dir / f"match_{match_id}_details.json")
            print("Retrieved match details")
            
            # Test match scorecard
            match_scorecard = collector.get_match_scorecard(match_id)
            save_data(match_scorecard, test_dir / f"match_{match_id}_scorecard.json")
            print("Retrieved match scorecard")
            
            # Test match comments
            match_comments = collector.get_match_comments(match_id)
            save_data(match_comments, test_dir / f"match_{match_id}_comments.json")
            print("Retrieved match comments")
    
    print("\nTest completed! Check the test_data directory for results.")

def save_data(data, filepath):
    """Save data to a JSON file with timestamp"""
    output = {
        'timestamp': datetime.now().isoformat(),
        'data': data
    }
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    test_data_collection() 