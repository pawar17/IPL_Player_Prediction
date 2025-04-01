import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
from dotenv import load_dotenv
import os

# Import updaters
from update_latest_data import LatestDataUpdater
from manage_team_rosters import TeamRosterManager
from update_ipl_website_data import IPLWebsiteScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UpdateOrchestrator:
    def __init__(self):
        load_dotenv()
        self.data_updater = LatestDataUpdater()
        self.roster_manager = TeamRosterManager()
        self.ipl_scraper = IPLWebsiteScraper()
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def run_updates(self):
        """Run all updates in sequence."""
        try:
            logger.info("Starting data updates...")
            
            # Update latest match data and player stats from Cricbuzz
            await self.data_updater.update_latest_data()
            
            # Update data from IPL website
            self.ipl_scraper.update_all_data()
            
            # Update team rosters
            self.roster_manager.generate_roster_report()
            
            logger.info("All updates completed successfully")
        except Exception as e:
            logger.error(f"Error running updates: {str(e)}")

    def generate_update_report(self):
        """Generate a summary report of the update process."""
        try:
            report = []
            report.append("Data Update Report")
            report.append("=" * 50)
            report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Count latest match files from Cricbuzz
            latest_matches = list(self.data_dir.glob("latest_match_*.json"))
            report.append(f"\nLatest Matches (Cricbuzz): {len(latest_matches)}")
            
            # Count IPL website data files
            ipl_files = list(self.data_dir.glob("ipl_website_*.json"))
            report.append(f"IPL Website Data Files: {len(ipl_files)}")
            
            # Get roster status
            rosters = self.roster_manager.load_rosters()
            total_teams = len(rosters)
            total_players = sum(len(team["players"]) for team in rosters.values())
            report.append(f"\nTeam Rosters:")
            report.append(f"Total Teams: {total_teams}")
            report.append(f"Total Players: {total_players}")
            
            # Save report
            report_file = self.data_dir / "update_report.txt"
            with open(report_file, 'w') as f:
                f.write("\n".join(report))
            logger.info(f"Saved update report to {report_file}")
        except Exception as e:
            logger.error(f"Error generating update report: {str(e)}")

async def main():
    orchestrator = UpdateOrchestrator()
    await orchestrator.run_updates()
    orchestrator.generate_update_report()

if __name__ == "__main__":
    asyncio.run(main()) 