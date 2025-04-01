import logging
from pathlib import Path
import json
from datetime import datetime
from web_scraper import CricketWebScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prediction_updates.log'),
        logging.StreamHandler()
    ]
)

def load_schedule():
    """Load the IPL 2024 schedule"""
    base_path = Path(__file__).parent.parent.parent
    schedule_path = base_path / 'data' / 'processed' / 'ipl2024_schedule_20240401_145632.json'
    
    with open(schedule_path, 'r') as f:
        return json.load(f)

def update_predictions():
    """Update predictions for all upcoming matches"""
    scraper = CricketWebScraper()
    schedule = load_schedule()
    
    # Get current date
    current_date = datetime.now().date()
    
    # Filter upcoming matches
    upcoming_matches = [
        match for match in schedule
        if datetime.strptime(match['date'], '%Y-%m-%d').date() >= current_date
    ]
    
    logging.info(f"Found {len(upcoming_matches)} upcoming matches")
    
    # Update predictions for each match
    for match in upcoming_matches:
        try:
            logging.info(f"Updating predictions for match {match['match_no']}: {match['team1']} vs {match['team2']}")
            
            # Generate match ID (you'll need to implement this based on your match ID format)
            match_id = f"ipl2024_{match['match_no']}"
            
            # Get updated predictions
            predictions = scraper.update_match_predictions(match_id)
            
            # Save predictions
            scraper.save_data(predictions, f"match_{match_id}_predictions")
            
            logging.info(f"Successfully updated predictions for match {match['match_no']}")
            
        except Exception as e:
            logging.error(f"Error updating predictions for match {match['match_no']}: {str(e)}")
            continue

def generate_team_rankings():
    """Generate updated team rankings based on latest data"""
    scraper = CricketWebScraper()
    
    # Load all match predictions
    predictions_path = scraper.data_path / "match_predictions"
    if not predictions_path.exists():
        logging.error("No match predictions found")
        return
    
    # Calculate team ratings based on predictions
    team_ratings = {}
    
    for prediction_file in predictions_path.glob("match_*.json"):
        with open(prediction_file, 'r') as f:
            prediction = json.load(f)
            
            # Update team ratings based on predictions
            for team in ['team1', 'team2']:
                team_name = prediction[team]['name']
                if team_name not in team_ratings:
                    team_ratings[team_name] = {
                        'total_rating': 0,
                        'matches': 0,
                        'wins': 0,
                        'losses': 0,
                        'win_probability': 0
                    }
                
                team_ratings[team_name]['matches'] += 1
                team_ratings[team_name]['win_probability'] += prediction['win_probability'][f'{team}_probability']
                
                if prediction['win_probability'][f'{team}_probability'] > 0.5:
                    team_ratings[team_name]['wins'] += 1
                else:
                    team_ratings[team_name]['losses'] += 1
    
    # Calculate final ratings
    for team in team_ratings:
        team_ratings[team]['total_rating'] = (
            team_ratings[team]['win_probability'] / team_ratings[team]['matches'] * 100
        )
    
    # Save team rankings
    scraper.save_data(team_ratings, "team_rankings")
    
    # Log rankings
    logging.info("Updated Team Rankings:")
    for team, rating in sorted(team_ratings.items(), key=lambda x: x[1]['total_rating'], reverse=True):
        logging.info(f"{team}: {rating['total_rating']:.2f} (W: {rating['wins']}, L: {rating['losses']})")

def main():
    """Main function to update predictions and rankings"""
    logging.info("Starting prediction updates")
    
    try:
        # Update match predictions
        update_predictions()
        
        # Generate team rankings
        generate_team_rankings()
        
        logging.info("Successfully completed all updates")
        
    except Exception as e:
        logging.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main() 