import logging
from typing import Dict, List, Any
from pathlib import Path
import json
from datetime import datetime
from ..models.player_predictor import PlayerPredictor
from ..data_preparation.data_processor import DataProcessor
from ..data_collection.web_scraper import CricketWebScraper

class PredictionService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.predictor = PlayerPredictor()
        self.data_processor = DataProcessor()
        self.scraper = CricketWebScraper()
        
        # Load models if they exist
        self.predictor.load_models()
    
    def predict_match(self, team1: str, team2: str) -> Dict[str, Any]:
        """Predict player performances for an upcoming match"""
        try:
            self.logger.info(f"Predicting match between {team1} and {team2}")
            
            # Get current team rosters
            team1_roster = self.scraper.get_team_roster(team1)
            team2_roster = self.scraper.get_team_roster(team2)
            
            if not team1_roster or not team2_roster:
                raise Exception("Failed to get team rosters")
            
            # Get recent match data
            recent_matches = self.scraper.get_match_schedule()
            if not recent_matches:
                raise Exception("Failed to get recent matches")
            
            # Prepare features for each player
            predictions = {
                "match_info": {
                    "team1": team1,
                    "team2": team2,
                    "date": datetime.now().isoformat()
                },
                "top_performers": {
                    "batsman": {"name": "", "predicted_runs": 0, "strike_rate": 0},
                    "bowler": {"name": "", "predicted_wickets": 0, "economy_rate": 0},
                    "all_rounder": {"name": "", "predicted_runs": 0, "predicted_wickets": 0}
                },
                "player_predictions": []
            }
            
            # Predict for each player
            all_players = team1_roster["players"] + team2_roster["players"]
            for player in all_players:
                player_data = self._prepare_player_data(player, team1, team2, recent_matches)
                if player_data:
                    prediction = self.predictor.predict(player_data)
                    if prediction:
                        prediction["name"] = player["name"]
                        prediction["role"] = player["role"]
                        predictions["player_predictions"].append(prediction)
            
            # Sort players by predicted points
            predictions["player_predictions"].sort(
                key=lambda x: self._calculate_predicted_points(x)["total_points"],
                reverse=True
            )
            
            # Update top performers
            self._update_top_performers(predictions)
            
            # Save predictions
            self._save_predictions(predictions)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting match: {str(e)}")
            return {
                "error": str(e),
                "match_info": {
                    "team1": team1,
                    "team2": team2,
                    "date": datetime.now().isoformat()
                },
                "player_predictions": []
            }
    
    def _prepare_player_data(self, player: Dict, team1: str, team2: str,
                           recent_matches: Dict) -> Dict[str, Any]:
        """Prepare player data for prediction"""
        try:
            # Check player availability first
            availability = self._check_player_availability(player)
            if not availability["is_available"]:
                self.logger.warning(f"Player {player['name']} is not available: {availability['reason']}")
                return None
            
            # Get player's recent stats
            recent_stats = self._get_recent_stats(player["name"], recent_matches)
            
            # Get venue stats
            venue = self._get_match_venue(team1, team2, recent_matches)
            venue_stats = self._get_venue_stats(venue)
            
            # Get head-to-head stats
            opposition = team2 if player["name"] in [p["name"] for p in team1_roster["players"]] else team1
            h2h_stats = self._get_head_to_head_stats(player["name"], opposition)
            
            # Calculate features
            player_data = {
                # Availability information
                "availability_status": availability["status"],
                "availability_reason": availability["reason"],
                "recovery_progress": availability.get("recovery_progress", 100),
                "expected_return": availability.get("expected_return", None),
                
                # Recent performance
                "last_5_matches_runs_avg": recent_stats.get("runs_avg", 0),
                "last_5_matches_wickets_avg": recent_stats.get("wickets_avg", 0),
                "last_5_matches_sr_avg": recent_stats.get("strike_rate_avg", 0),
                "last_5_matches_er_avg": recent_stats.get("economy_rate_avg", 0),
                
                # Opposition and venue
                "opposition_rank": self._get_team_rank(opposition),
                "venue_runs_avg": venue_stats.get("runs_avg", 0),
                "venue_wickets_avg": venue_stats.get("wickets_avg", 0),
                
                # Head-to-head
                "head_to_head_runs_avg": h2h_stats.get("runs_avg", 0),
                "head_to_head_wickets_avg": h2h_stats.get("wickets_avg", 0),
                
                # Match context
                "days_since_last_match": recent_stats.get("days_since_last", 30),
                "is_home_game": player["name"] in [p["name"] for p in team1_roster["players"]],
                "is_powerplay_batsman": self._is_powerplay_player(player),
                "is_death_bowler": self._is_death_bowler(player),
                
                # Player status
                "is_injured": availability["status"] == "Injured",
                "is_recovering": availability["status"] == "Recovering",
                "is_rested": availability["status"] == "Rested",
                "is_available": availability["status"] == "Available"
            }
            
            return player_data
            
        except Exception as e:
            self.logger.error(f"Error preparing player data for {player['name']}: {str(e)}")
            return None
    
    def _check_player_availability(self, player: Dict) -> Dict[str, Any]:
        """Check player's availability status"""
        try:
            # Get player's current status from team roster
            status = player.get("status", "Available")
            reason = player.get("status_reason", "")
            
            # Check for injuries
            if "injured" in status.lower():
                return {
                    "is_available": False,
                    "status": "Injured",
                    "reason": reason or "Player is injured",
                    "recovery_progress": player.get("recovery_progress", 0),
                    "expected_return": player.get("expected_return_date")
                }
            
            # Check for rest/rotation
            if "rested" in status.lower():
                return {
                    "is_available": False,
                    "status": "Rested",
                    "reason": reason or "Player is being rested",
                    "expected_return": player.get("next_match_date")
                }
            
            # Check for recovery
            if "recovering" in status.lower():
                recovery_progress = player.get("recovery_progress", 0)
                return {
                    "is_available": recovery_progress >= 90,
                    "status": "Recovering",
                    "reason": reason or "Player is recovering from injury",
                    "recovery_progress": recovery_progress,
                    "expected_return": player.get("expected_return_date")
                }
            
            # Check for international duty
            if "international" in status.lower():
                return {
                    "is_available": False,
                    "status": "International Duty",
                    "reason": reason or "Player is on international duty",
                    "expected_return": player.get("next_match_date")
                }
            
            # Check for personal reasons
            if "personal" in status.lower():
                return {
                    "is_available": False,
                    "status": "Personal",
                    "reason": reason or "Player is unavailable for personal reasons",
                    "expected_return": player.get("next_match_date")
                }
            
            # Default case - player is available
            return {
                "is_available": True,
                "status": "Available",
                "reason": "Player is fully available"
            }
            
        except Exception as e:
            self.logger.error(f"Error checking availability for {player['name']}: {str(e)}")
            return {
                "is_available": False,
                "status": "Unknown",
                "reason": f"Error checking availability: {str(e)}"
            }
    
    def _adjust_prediction_for_availability(self, prediction: Dict[str, Any], player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust predictions based on player availability status"""
        if not player_data["is_available"]:
            # Set all predictions to 0 for unavailable players
            prediction.update({
                "runs": 0,
                "wickets": 0,
                "strike_rate": 0,
                "economy_rate": 0,
                "confidence": 0,
                "form": "Unavailable",
                "momentum": "N/A",
                "availability_status": player_data["availability_status"],
                "availability_reason": player_data["availability_reason"]
            })
        elif player_data["is_recovering"]:
            # Adjust predictions based on recovery progress
            recovery_factor = player_data["recovery_progress"] / 100
            prediction.update({
                "runs": round(prediction["runs"] * recovery_factor),
                "wickets": round(prediction["wickets"] * recovery_factor),
                "strike_rate": round(prediction["strike_rate"] * recovery_factor),
                "economy_rate": round(prediction["economy_rate"] * (2 - recovery_factor)),  # Higher ER when recovering
                "confidence": round(prediction["confidence"] * recovery_factor, 2),
                "form": "Recovering",
                "momentum": "Recovery",
                "availability_status": player_data["availability_status"],
                "availability_reason": player_data["availability_reason"]
            })
        
        return prediction
    
    def _calculate_predicted_points(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate predicted fantasy points with advanced scoring rules"""
        points = 0
        bonus_points = 0
        milestones = []
        
        # Batting points
        runs = prediction["runs"]
        points += runs  # 1 point per run
        
        # Batting milestones
        if runs >= 100:
            points += 16  # 16 points for century
            milestones.append("Century")
        elif runs >= 50:
            points += 8  # 8 points for half-century
            milestones.append("Half-century")
        
        # Strike rate bonuses
        sr = prediction["strike_rate"]
        if sr >= 200:
            bonus_points += 6
            milestones.append("200+ SR")
        elif sr >= 150:
            bonus_points += 4
            milestones.append("150+ SR")
        
        # Boundary bonuses
        fours = prediction.get("fours", 0)
        sixes = prediction.get("sixes", 0)
        points += fours  # 1 point per four
        points += 2 * sixes  # 2 points per six
        
        # Bowling points
        wickets = prediction["wickets"]
        points += wickets * 10  # 10 points per wicket
        
        # Bowling milestones
        if wickets >= 5:
            points += 16  # 16 points for 5-wicket haul
            milestones.append("5-wicket haul")
        elif wickets >= 3:
            points += 8  # 8 points for 3-wicket haul
            milestones.append("3-wicket haul")
        
        # Economy rate bonuses
        er = prediction["economy_rate"]
        if er < 5:
            bonus_points += 6
            milestones.append("ER < 5")
        elif er < 7:
            bonus_points += 4
            milestones.append("ER < 7")
        
        # Fielding points
        catches = prediction.get("catches", 0)
        stumpings = prediction.get("stumpings", 0)
        points += catches * 2  # 2 points per catch
        points += stumpings * 4  # 4 points per stumping
        
        # Match impact bonuses
        if prediction.get("is_mom", False):
            bonus_points += 8
            milestones.append("Man of the Match")
        
        # Form and momentum bonuses
        if prediction["form"] == "Excellent":
            bonus_points += 4
            milestones.append("Excellent Form")
        if prediction["momentum"] in ["Strong Upward", "Upward"]:
            bonus_points += 2
            milestones.append("Positive Momentum")
        
        # Confidence-based adjustment
        confidence = prediction["confidence"]
        if confidence > 0.8:
            bonus_points += 4
            milestones.append("High Confidence")
        
        # Calculate total points
        total_points = points + bonus_points
        
        return {
            "total_points": total_points,
            "base_points": points,
            "bonus_points": bonus_points,
            "milestones": milestones,
            "breakdown": {
                "batting": {
                    "runs": runs,
                    "fours": fours,
                    "sixes": sixes,
                    "strike_rate": sr
                },
                "bowling": {
                    "wickets": wickets,
                    "economy_rate": er
                },
                "fielding": {
                    "catches": catches,
                    "stumpings": stumpings
                }
            }
        }
    
    def _update_top_performers(self, predictions: Dict[str, Any]):
        """Update top performers in predictions"""
        batsmen = [p for p in predictions["player_predictions"] if p["role"] == "Batsman"]
        bowlers = [p for p in predictions["player_predictions"] if p["role"] == "Bowler"]
        all_rounders = [p for p in predictions["player_predictions"] if p["role"] == "All-rounder"]
        
        if batsmen:
            top_batsman = max(batsmen, key=lambda x: x["runs"])
            predictions["top_performers"]["batsman"] = {
                "name": top_batsman["name"],
                "predicted_runs": top_batsman["runs"],
                "strike_rate": top_batsman["strike_rate"]
            }
        
        if bowlers:
            top_bowler = max(bowlers, key=lambda x: x["wickets"])
            predictions["top_performers"]["bowler"] = {
                "name": top_bowler["name"],
                "predicted_wickets": top_bowler["wickets"],
                "economy_rate": top_bowler["economy_rate"]
            }
        
        if all_rounders:
            top_all_rounder = max(all_rounders, key=lambda x: x["runs"] + x["wickets"] * 10)
            predictions["top_performers"]["all_rounder"] = {
                "name": top_all_rounder["name"],
                "predicted_runs": top_all_rounder["runs"],
                "predicted_wickets": top_all_rounder["wickets"]
            }
    
    def _save_predictions(self, predictions: Dict[str, Any]):
        """Save predictions to file"""
        try:
            base_path = Path(__file__).parent.parent.parent
            predictions_path = base_path / "data" / "predictions"
            predictions_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prediction_{predictions['match_info']['team1']}_vs_{predictions['match_info']['team2']}_{timestamp}.json"
            
            with open(predictions_path / filename, "w") as f:
                json.dump(predictions, f, indent=4)
            
            self.logger.info(f"Predictions saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving predictions: {str(e)}")
    
    def _get_recent_stats(self, player_name: str, recent_matches: Dict) -> Dict[str, float]:
        """Get player's recent statistics"""
        stats = {
            "runs_avg": 0,
            "wickets_avg": 0,
            "strike_rate_avg": 0,
            "economy_rate_avg": 0,
            "days_since_last": 30
        }
        
        player_matches = []
        for match in recent_matches.get("matches", []):
            for team in match.get("teams", []):
                for player in team.get("players", []):
                    if player["name"] == player_name:
                        player_matches.append(player)
        
        if player_matches:
            stats["runs_avg"] = sum(m.get("runs", 0) for m in player_matches) / len(player_matches)
            stats["wickets_avg"] = sum(m.get("wickets", 0) for m in player_matches) / len(player_matches)
            stats["strike_rate_avg"] = sum(m.get("strike_rate", 0) for m in player_matches) / len(player_matches)
            stats["economy_rate_avg"] = sum(m.get("economy_rate", 0) for m in player_matches) / len(player_matches)
            
            if player_matches:
                last_match = max(player_matches, key=lambda x: x.get("date", ""))
                last_date = datetime.fromisoformat(last_match.get("date", ""))
                stats["days_since_last"] = (datetime.now() - last_date).days
        
        return stats
    
    def _get_match_venue(self, team1: str, team2: str, recent_matches: Dict) -> str:
        """Get venue for the upcoming match"""
        for match in recent_matches.get("matches", []):
            if match["teams"] == f"{team1} vs {team2}":
                return match["venue"]
        return "Unknown"
    
    def _get_venue_stats(self, venue: str) -> Dict[str, float]:
        """Get statistics for a venue"""
        return self.data_processor._get_venue_stats(venue)
    
    def _get_head_to_head_stats(self, player_name: str, opposition: str) -> Dict[str, float]:
        """Get head-to-head statistics against an opposition"""
        return self.data_processor._get_head_to_head_stats(player_name, opposition)
    
    def _get_team_rank(self, team: str) -> int:
        """Get current team rank"""
        return self.data_processor._get_team_rank(team)
    
    def _is_powerplay_player(self, player: Dict) -> bool:
        """Check if player is a powerplay specialist"""
        return self.data_processor._is_powerplay_player(player["name"], player)
    
    def _is_death_bowler(self, player: Dict) -> bool:
        """Check if player is a death overs specialist"""
        return self.data_processor._is_death_bowler(player["name"], player)
    
    def _analyze_player(self, player: Dict, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis of player's predicted performance"""
        analysis = {
            "player_info": {
                "name": player["name"],
                "role": player["role"],
                "team": player["team"],
                "experience": player.get("experience", "Unknown"),
                "rank": player.get("rank", "Unknown")
            },
            "performance_analysis": {
                "batting": self._analyze_batting(prediction),
                "bowling": self._analyze_bowling(prediction),
                "fielding": self._analyze_fielding(prediction),
                "overall": self._analyze_overall(prediction)
            },
            "match_context": {
                "form": prediction["form"],
                "momentum": prediction["momentum"],
                "confidence": prediction["confidence"],
                "milestones": prediction.get("milestones", [])
            },
            "risk_assessment": self._assess_risks(prediction),
            "recommendations": self._generate_recommendations(prediction)
        }
        
        return analysis
    
    def _analyze_batting(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze batting performance predictions"""
        runs = prediction["runs"]
        sr = prediction["strike_rate"]
        
        return {
            "runs_prediction": {
                "value": runs,
                "confidence_interval": prediction["runs_ci"],
                "expected_contribution": f"{runs/20:.1f}% of team total"
            },
            "strike_rate_analysis": {
                "value": sr,
                "confidence_interval": prediction["strike_rate_ci"],
                "efficiency": "High" if sr > 150 else "Moderate" if sr > 120 else "Low"
            },
            "boundary_hitting": {
                "fours": prediction.get("fours", 0),
                "sixes": prediction.get("sixes", 0),
                "boundary_percentage": f"{(prediction.get("fours", 0) * 4 + prediction.get("sixes", 0) * 6) / runs * 100:.1f}%"
            }
        }
    
    def _analyze_bowling(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bowling performance predictions"""
        wickets = prediction["wickets"]
        er = prediction["economy_rate"]
        
        return {
            "wickets_prediction": {
                "value": wickets,
                "confidence_interval": prediction["wickets_ci"],
                "expected_contribution": f"{wickets/10:.1f}% of team wickets"
            },
            "economy_analysis": {
                "value": er,
                "confidence_interval": prediction["economy_rate_ci"],
                "efficiency": "Excellent" if er < 6 else "Good" if er < 7 else "Moderate" if er < 8 else "Poor"
            },
            "impact_analysis": {
                "wicket_impact": "High" if wickets >= 3 else "Moderate" if wickets >= 1 else "Low",
                "economy_impact": "High" if er < 7 else "Moderate" if er < 8 else "Low"
            }
        }
    
    def _analyze_fielding(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fielding performance predictions"""
        catches = prediction.get("catches", 0)
        stumpings = prediction.get("stumpings", 0)
        
        return {
            "catches": {
                "predicted": catches,
                "impact": "High" if catches >= 2 else "Moderate" if catches >= 1 else "Low"
            },
            "stumpings": {
                "predicted": stumpings,
                "impact": "High" if stumpings >= 1 else "Low"
            },
            "overall_fielding": {
                "total_contributions": catches + stumpings,
                "expected_impact": "High" if catches + stumpings >= 2 else "Moderate" if catches + stumpings >= 1 else "Low"
            }
        }
    
    def _analyze_overall(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall performance predictions"""
        points = self._calculate_predicted_points(prediction)
        
        return {
            "fantasy_points": {
                "total": points["total_points"],
                "base_points": points["base_points"],
                "bonus_points": points["bonus_points"]
            },
            "performance_rating": self._calculate_performance_rating(prediction),
            "value_for_money": self._calculate_value_for_money(prediction),
            "match_impact": self._calculate_match_impact(prediction)
        }
    
    def _assess_risks(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks associated with player's predicted performance"""
        return {
            "form_risk": "High" if prediction["form"] == "Poor" else "Moderate" if prediction["form"] == "Average" else "Low",
            "consistency_risk": "High" if prediction["confidence"] < 0.6 else "Moderate" if prediction["confidence"] < 0.8 else "Low",
            "role_risk": self._assess_role_risk(prediction),
            "opposition_risk": self._assess_opposition_risk(prediction),
            "overall_risk": self._calculate_overall_risk(prediction)
        }
    
    def _generate_recommendations(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on player analysis"""
        return {
            "captaincy": self._recommend_captaincy(prediction),
            "vice_captaincy": self._recommend_vice_captaincy(prediction),
            "team_composition": self._recommend_team_composition(prediction),
            "strategy": self._generate_strategy_recommendations(prediction)
        }
    
    def _calculate_performance_rating(self, prediction: Dict[str, Any]) -> str:
        """Calculate overall performance rating"""
        points = self._calculate_predicted_points(prediction)
        total_points = points["total_points"]
        
        if total_points >= 100:
            return "Outstanding"
        elif total_points >= 80:
            return "Excellent"
        elif total_points >= 60:
            return "Very Good"
        elif total_points >= 40:
            return "Good"
        elif total_points >= 20:
            return "Average"
        else:
            return "Poor"
    
    def _calculate_value_for_money(self, prediction: Dict[str, Any]) -> str:
        """Calculate value for money rating"""
        points = self._calculate_predicted_points(prediction)
        total_points = points["total_points"]
        price = prediction.get("price", 10)  # Default price if not available
        
        points_per_price = total_points / price
        
        if points_per_price >= 10:
            return "Excellent"
        elif points_per_price >= 8:
            return "Very Good"
        elif points_per_price >= 6:
            return "Good"
        elif points_per_price >= 4:
            return "Average"
        else:
            return "Poor"
    
    def _calculate_match_impact(self, prediction: Dict[str, Any]) -> str:
        """Calculate expected match impact"""
        runs = prediction["runs"]
        wickets = prediction["wickets"]
        catches = prediction.get("catches", 0)
        stumpings = prediction.get("stumpings", 0)
        
        impact_score = 0
        impact_score += runs / 20  # Contribution to team total
        impact_score += wickets / 5  # Contribution to team wickets
        impact_score += (catches + stumpings) / 2  # Fielding impact
        
        if impact_score >= 2:
            return "Very High"
        elif impact_score >= 1.5:
            return "High"
        elif impact_score >= 1:
            return "Moderate"
        else:
            return "Low"
    
    def _assess_role_risk(self, prediction: Dict[str, Any]) -> str:
        """Assess risk based on player's role"""
        role = prediction.get("role", "")
        
        if role == "Batsman":
            return "Low" if prediction["runs"] >= 30 else "Moderate" if prediction["runs"] >= 20 else "High"
        elif role == "Bowler":
            return "Low" if prediction["wickets"] >= 2 else "Moderate" if prediction["wickets"] >= 1 else "High"
        elif role == "All-rounder":
            return "Low" if prediction["runs"] >= 20 and prediction["wickets"] >= 1 else "Moderate" if prediction["runs"] >= 10 or prediction["wickets"] >= 1 else "High"
        else:
            return "Moderate"
    
    def _assess_opposition_risk(self, prediction: Dict[str, Any]) -> str:
        """Assess risk based on opposition strength"""
        opposition_rank = prediction.get("opposition_rank", 5)
        
        if opposition_rank <= 2:
            return "High"
        elif opposition_rank <= 4:
            return "Moderate"
        else:
            return "Low"
    
    def _calculate_overall_risk(self, prediction: Dict[str, Any]) -> str:
        """Calculate overall risk assessment"""
        risks = [
            self._assess_risks(prediction)["form_risk"],
            self._assess_risks(prediction)["consistency_risk"],
            self._assess_risks(prediction)["role_risk"],
            self._assess_risks(prediction)["opposition_risk"]
        ]
        
        high_risks = risks.count("High")
        moderate_risks = risks.count("Moderate")
        
        if high_risks >= 2:
            return "High"
        elif high_risks == 1 or moderate_risks >= 2:
            return "Moderate"
        else:
            return "Low"
    
    def _recommend_captaincy(self, prediction: Dict[str, Any]) -> str:
        """Generate captaincy recommendation"""
        points = self._calculate_predicted_points(prediction)
        total_points = points["total_points"]
        risk = self._calculate_overall_risk(prediction)
        
        if total_points >= 80 and risk == "Low":
            return "Strong Captaincy Option"
        elif total_points >= 60 and risk == "Low":
            return "Good Captaincy Option"
        elif total_points >= 80 and risk == "Moderate":
            return "Risky Captaincy Option"
        else:
            return "Not Recommended for Captaincy"
    
    def _recommend_vice_captaincy(self, prediction: Dict[str, Any]) -> str:
        """Generate vice-captaincy recommendation"""
        points = self._calculate_predicted_points(prediction)
        total_points = points["total_points"]
        risk = self._calculate_overall_risk(prediction)
        
        if total_points >= 60 and risk == "Low":
            return "Strong Vice-Captaincy Option"
        elif total_points >= 40 and risk == "Low":
            return "Good Vice-Captaincy Option"
        elif total_points >= 60 and risk == "Moderate":
            return "Risky Vice-Captaincy Option"
        else:
            return "Not Recommended for Vice-Captaincy"
    
    def _recommend_team_composition(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """Generate team composition recommendations"""
        return {
            "must_have": self._calculate_performance_rating(prediction) in ["Outstanding", "Excellent"],
            "good_pick": self._calculate_performance_rating(prediction) in ["Very Good", "Good"],
            "differential": self._calculate_overall_risk(prediction) == "Moderate" and self._calculate_performance_rating(prediction) in ["Very Good", "Good"],
            "avoid": self._calculate_overall_risk(prediction) == "High" or self._calculate_performance_rating(prediction) == "Poor"
        }
    
    def _generate_strategy_recommendations(self, prediction: Dict[str, Any]) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        if prediction["form"] == "Excellent":
            recommendations.append("Consider as a differential pick due to excellent form")
        
        if prediction["momentum"] in ["Strong Upward", "Upward"]:
            recommendations.append("Good momentum suggests potential for high returns")
        
        if prediction["confidence"] > 0.8:
            recommendations.append("High confidence in predictions suggests reliable pick")
        
        if self._calculate_overall_risk(prediction) == "High":
            recommendations.append("High risk player - consider as a differential pick only")
        
        return recommendations 