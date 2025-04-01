from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import json
from datetime import datetime
import asyncio
from ..feature_engineering.feature_processor import FeatureProcessor
from ..real_time.updates_manager import UpdatesManager
from ..models.prediction_model import PredictionModel

app = FastAPI(
    title="IPL Player Performance Prediction API",
    description="API for predicting IPL player performance in real-time",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
logger = logging.getLogger(__name__)
feature_processor = FeatureProcessor()
updates_manager = UpdatesManager()
prediction_model = PredictionModel()

# Pydantic models for request/response
class PlayerRequest(BaseModel):
    player_id: str
    match_id: str
    team: str
    opposition: str
    venue: str
    is_home_game: bool
    player_role: str

class MatchContext(BaseModel):
    match_id: str
    team: str
    opposition: str
    venue: str
    is_home_game: bool
    weather: Optional[Dict[str, Any]] = None

class PredictionResponse(BaseModel):
    player_id: str
    match_id: str
    predicted_runs: float
    predicted_wickets: float
    predicted_strike_rate: float
    predicted_economy_rate: float
    confidence_score: float
    timestamp: str
    features: Dict[str, Any]

class PlayerStatsResponse(BaseModel):
    player_id: str
    recent_performance: List[Dict[str, Any]]
    current_form: float
    last_updated: str

class TeamStatsResponse(BaseModel):
    team_id: str
    recent_performance: List[Dict[str, Any]]
    current_form: float
    last_updated: str

class VenueStatsResponse(BaseModel):
    venue_id: str
    recent_matches: List[Dict[str, Any]]
    last_updated: str

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    try:
        # Start the updates manager
        asyncio.create_task(updates_manager.start_update_loop())
        logger.info("Updates manager started successfully")
    except Exception as e:
        logger.error(f"Error starting updates manager: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "IPL Player Performance Prediction API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_performance(request: PlayerRequest):
    """Predict player performance for a match"""
    try:
        # Get real-time data
        match_data = updates_manager.current_match_data.get(request.match_id)
        if not match_data:
            raise HTTPException(status_code=404, detail="Match data not found")
        
        # Get player stats
        player_stats = updates_manager.player_stats_cache.get(request.player_id)
        if not player_stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        # Get team stats
        team_stats = updates_manager.team_stats_cache.get(request.team)
        opposition_stats = updates_manager.team_stats_cache.get(request.opposition)
        
        # Get venue stats
        venue_stats = updates_manager.venue_stats_cache.get(request.venue)
        
        # Create match context
        match_context = {
            'match_id': request.match_id,
            'team': request.team,
            'opposition': request.opposition,
            'venue': request.venue,
            'is_home_game': request.is_home_game,
            'weather': match_data.get('weather', {})
        }
        
        # Process features
        features = feature_processor.process_features(player_stats, match_context)
        
        # Make prediction
        prediction = prediction_model.predict(features)
        
        return PredictionResponse(
            player_id=request.player_id,
            match_id=request.match_id,
            predicted_runs=prediction['runs'],
            predicted_wickets=prediction['wickets'],
            predicted_strike_rate=prediction['strike_rate'],
            predicted_economy_rate=prediction['economy_rate'],
            confidence_score=prediction['confidence'],
            timestamp=datetime.now().isoformat(),
            features=features
        )
        
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/player/{player_id}/stats", response_model=PlayerStatsResponse)
async def get_player_stats(player_id: str):
    """Get player statistics"""
    try:
        player_stats = updates_manager.player_stats_cache.get(player_id)
        if not player_stats:
            raise HTTPException(status_code=404, detail="Player stats not found")
        
        return PlayerStatsResponse(**player_stats)
        
    except Exception as e:
        logger.error(f"Error getting player stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/team/{team_id}/stats", response_model=TeamStatsResponse)
async def get_team_stats(team_id: str):
    """Get team statistics"""
    try:
        team_stats = updates_manager.team_stats_cache.get(team_id)
        if not team_stats:
            raise HTTPException(status_code=404, detail="Team stats not found")
        
        return TeamStatsResponse(**team_stats)
        
    except Exception as e:
        logger.error(f"Error getting team stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/venue/{venue_id}/stats", response_model=VenueStatsResponse)
async def get_venue_stats(venue_id: str):
    """Get venue statistics"""
    try:
        venue_stats = updates_manager.venue_stats_cache.get(venue_id)
        if not venue_stats:
            raise HTTPException(status_code=404, detail="Venue stats not found")
        
        return VenueStatsResponse(**venue_stats)
        
    except Exception as e:
        logger.error(f"Error getting venue stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/match/{match_id}")
async def get_match_data(match_id: str):
    """Get current match data"""
    try:
        match_data = updates_manager.current_match_data.get(match_id)
        if not match_data:
            raise HTTPException(status_code=404, detail="Match data not found")
        
        return match_data
        
    except Exception as e:
        logger.error(f"Error getting match data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "last_update": updates_manager.last_update.isoformat(),
        "is_updating": updates_manager.is_updating
    } 