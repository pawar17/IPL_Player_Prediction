import asyncio
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
from typing import Dict, List, Optional
import aiohttp
from dotenv import load_dotenv
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LatestDataUpdater:
    def __init__(self):
        load_dotenv()
        self.base_url = "https://api.cricbuzz.com/api/v1"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }
        self.data_dir = Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.historical_dir = self.data_dir / "historical"
        self.historical_dir.mkdir(exist_ok=True)

    async def get_latest_matches(self) -> List[Dict]:
        """Get the latest IPL matches."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/matches"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return [match for match in data.get("matches", []) 
                                if match.get("series", {}).get("name", "").lower() == "indian premier league"]
                    else:
                        logger.error("Failed to fetch latest matches")
                        return []
        except Exception as e:
            logger.error(f"Error fetching latest matches: {str(e)}")
            return []

    async def get_match_details(self, match_id: str) -> Dict:
        """Get detailed information about a specific match."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/match/{match_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch match {match_id} details")
                        return None
        except Exception as e:
            logger.error(f"Error fetching match {match_id} details: {str(e)}")
            return None

    async def get_player_stats(self, player_id: str) -> Dict:
        """Get player statistics."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                url = f"{self.base_url}/player/{player_id}/stats"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch player {player_id} stats")
                        return None
        except Exception as e:
            logger.error(f"Error fetching player {player_id} stats: {str(e)}")
            return None

    def process_match_data(self, match_data: Dict) -> Dict:
        """Process match data into a structured format."""
        try:
            return {
                "match_id": match_data.get("id"),
                "date": match_data.get("date"),
                "team1": match_data.get("team1"),
                "team2": match_data.get("team2"),
                "toss_winner": match_data.get("toss_winner"),
                "toss_decision": match_data.get("toss_decision"),
                "winner": match_data.get("winner"),
                "margin": match_data.get("margin"),
                "player_of_match": match_data.get("player_of_match"),
                "score": match_data.get("score"),
                "extras": match_data.get("extras"),
                "innings": match_data.get("innings", [])
            }
        except Exception as e:
            logger.error(f"Error processing match data: {str(e)}")
            return None

    def process_player_stats(self, player_stats: Dict) -> Dict:
        """Process player statistics into a structured format."""
        try:
            return {
                "player_id": player_stats.get("id"),
                "name": player_stats.get("name"),
                "batting_stats": {
                    "matches": player_stats.get("batting", {}).get("matches"),
                    "runs": player_stats.get("batting", {}).get("runs"),
                    "highest_score": player_stats.get("batting", {}).get("highest_score"),
                    "average": player_stats.get("batting", {}).get("average"),
                    "strike_rate": player_stats.get("batting", {}).get("strike_rate")
                },
                "bowling_stats": {
                    "matches": player_stats.get("bowling", {}).get("matches"),
                    "wickets": player_stats.get("bowling", {}).get("wickets"),
                    "best_figures": player_stats.get("bowling", {}).get("best_figures"),
                    "average": player_stats.get("bowling", {}).get("average"),
                    "economy_rate": player_stats.get("bowling", {}).get("economy_rate")
                }
            }
        except Exception as e:
            logger.error(f"Error processing player stats: {str(e)}")
            return None

    def save_match_data(self, match_data: Dict):
        """Save match data to JSON file."""
        try:
            filepath = self.data_dir / f"latest_match_{match_data['match_id']}.json"
            pd.DataFrame([match_data]).to_json(filepath, orient='records')
            logger.info(f"Saved latest match data to {filepath}")
        except Exception as e:
            logger.error(f"Error saving match data: {str(e)}")

    def save_player_stats(self, player_stats: Dict):
        """Save player statistics to JSON file."""
        try:
            filepath = self.historical_dir / f"player_{player_stats['player_id']}.json"
            pd.DataFrame([player_stats]).to_json(filepath, orient='records')
            logger.info(f"Saved player stats to {filepath}")
        except Exception as e:
            logger.error(f"Error saving player stats: {str(e)}")

    async def update_player_stats(self, player_id: str):
        """Update player statistics."""
        try:
            player_stats = await self.get_player_stats(player_id)
            if player_stats:
                processed_stats = self.process_player_stats(player_stats)
                if processed_stats:
                    self.save_player_stats(processed_stats)
                    logger.info(f"Updated stats for player {player_id}")
        except Exception as e:
            logger.error(f"Error updating player stats: {str(e)}")

    async def update_latest_data(self):
        """Update latest match data and player statistics."""
        try:
            # Get latest matches
            latest_matches = await self.get_latest_matches()
            
            for match in latest_matches:
                match_id = match.get("id")
                match_details = await self.get_match_details(match_id)
                
                if match_details:
                    processed_match = self.process_match_data(match_details)
                    if processed_match:
                        self.save_match_data(processed_match)
                        
                        # Update player statistics
                        for player in match_details.get("players", []):
                            await self.update_player_stats(player.get("id"))
            
            logger.info("Latest data update completed")
        except Exception as e:
            logger.error(f"Error updating latest data: {str(e)}")

async def main():
    updater = LatestDataUpdater()
    await updater.update_latest_data()

if __name__ == "__main__":
    asyncio.run(main()) 