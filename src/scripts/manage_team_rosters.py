import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeamRosterManager:
    def __init__(self):
        load_dotenv()
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rosters_file = self.data_dir / "team_rosters.json"

    def load_rosters(self) -> Dict:
        """Load current team rosters from file."""
        try:
            if self.rosters_file.exists():
                with open(self.rosters_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading rosters: {str(e)}")
            return {}

    def save_rosters(self, rosters: Dict):
        """Save team rosters to file."""
        try:
            with open(self.rosters_file, 'w') as f:
                json.dump(rosters, f, indent=2)
            logger.info("Saved team rosters")
        except Exception as e:
            logger.error(f"Error saving rosters: {str(e)}")

    def update_player_availability(self, player_id: str, team: str, status: str, reason: str = None):
        """Update player availability status."""
        try:
            rosters = self.load_rosters()
            
            if team not in rosters:
                rosters[team] = {
                    "players": {},
                    "last_updated": datetime.now().isoformat()
                }
            
            if player_id not in rosters[team]["players"]:
                rosters[team]["players"][player_id] = {
                    "status": status,
                    "reason": reason,
                    "last_updated": datetime.now().isoformat()
                }
            else:
                rosters[team]["players"][player_id].update({
                    "status": status,
                    "reason": reason,
                    "last_updated": datetime.now().isoformat()
                })
            
            self.save_rosters(rosters)
            logger.info(f"Updated availability for player {player_id} in team {team}")
        except Exception as e:
            logger.error(f"Error updating player availability: {str(e)}")

    def get_available_players(self, team: str) -> List[str]:
        """Get list of available players for a team."""
        try:
            rosters = self.load_rosters()
            if team in rosters:
                return [
                    player_id for player_id, info in rosters[team]["players"].items()
                    if info["status"] == "available"
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting available players: {str(e)}")
            return []

    def get_player_status(self, player_id: str, team: str) -> Dict:
        """Get current status of a player."""
        try:
            rosters = self.load_rosters()
            if team in rosters and player_id in rosters[team]["players"]:
                return rosters[team]["players"][player_id]
            return None
        except Exception as e:
            logger.error(f"Error getting player status: {str(e)}")
            return None

    def generate_roster_report(self):
        """Generate a summary report of team rosters."""
        try:
            rosters = this.load_rosters()
            report = []
            report.append("Team Rosters Report")
            report.append("=" * 50)
            report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            for team, data in rosters.items():
                report.append(f"\nTeam: {team}")
                report.append("-" * 30)
                
                available = []
                unavailable = []
                injured = []
                
                for player_id, info in data["players"].items():
                    if info["status"] == "available":
                        available.append(player_id)
                    elif info["status"] == "injured":
                        injured.append(player_id)
                    else:
                        unavailable.append(player_id)
                
                report.append(f"Total Players: {len(data['players'])}")
                report.append(f"Available: {len(available)}")
                report.append(f"Unavailable: {len(unavailable)}")
                report.append(f"Injured: {len(injured)}")
                
                if injured:
                    report.append("\nInjured Players:")
                    for player_id in injured:
                        info = data["players"][player_id]
                        report.append(f"- {player_id}: {info.get('reason', 'No reason specified')}")
            
            # Save report
            report_file = self.data_dir / "roster_report.txt"
            with open(report_file, 'w') as f:
                f.write("\n".join(report))
            logger.info(f"Saved roster report to {report_file}")
        except Exception as e:
            logger.error(f"Error generating roster report: {str(e)}")

def main():
    manager = TeamRosterManager()
    manager.generate_roster_report()

if __name__ == "__main__":
    main() 