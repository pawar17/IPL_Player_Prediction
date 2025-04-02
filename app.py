from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from database import get_db
from models import Match, Team, Player, MatchPlayer, Venue, Prediction
from data_collector import DataCollector
from data_processor import DataProcessor

app = FastAPI(title="IPL Player Prediction API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data collector and processor
data_collector = DataCollector()
data_processor = DataProcessor()

@app.get("/")
async def root():
    return {"message": "Welcome to IPL Player Prediction API"}

@app.get("/matches")
async def get_matches(
    db: Session = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    matches = db.query(Match).offset(offset).limit(limit).all()
    return matches

@app.get("/matches/{match_id}")
async def get_match(match_id: str, db: Session = Depends(get_db)):
    match = db.query(Match).filter(Match.match_id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match

@app.get("/teams")
async def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()
    return teams

@app.get("/teams/{team_id}")
async def get_team(team_id: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.team_id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@app.get("/players")
async def get_players(
    db: Session = Depends(get_db),
    team_id: Optional[str] = None
):
    query = db.query(Player)
    if team_id:
        query = query.filter(Player.team_id == team_id)
    players = query.all()
    return players

@app.get("/players/{player_id}")
async def get_player(player_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@app.get("/predictions")
async def get_predictions(
    db: Session = Depends(get_db),
    match_id: Optional[str] = None,
    player_id: Optional[str] = None
):
    query = db.query(Prediction)
    if match_id:
        query = query.filter(Prediction.match_id == match_id)
    if player_id:
        query = query.filter(Prediction.player_id == player_id)
    predictions = query.all()
    return predictions

@app.get("/venues")
async def get_venues(db: Session = Depends(get_db)):
    venues = db.query(Venue).all()
    return venues

@app.get("/venues/{venue_id}")
async def get_venue(venue_id: str, db: Session = Depends(get_db)):
    venue = db.query(Venue).filter(Venue.venue_id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue

@app.post("/predict")
async def predict_player_performance(
    match_id: str,
    player_id: str,
    db: Session = Depends(get_db)
):
    # Get match and player data
    match = db.query(Match).filter(Match.match_id == match_id).first()
    player = db.query(Player).filter(Player.player_id == player_id).first()
    
    if not match or not player:
        raise HTTPException(status_code=404, detail="Match or player not found")
    
    # Process data and make prediction
    prediction_data = data_processor.process_match_data(match)
    player_data = data_processor.process_player_data(player)
    
    # Make prediction (implement your prediction logic here)
    predicted_score = 0.0  # Replace with actual prediction
    confidence = 0.0  # Replace with actual confidence score
    
    # Save prediction
    prediction = Prediction(
        match_id=match.id,
        player_id=player.id,
        predicted_score=predicted_score,
        confidence=confidence,
        features=json.dumps({
            "match_data": prediction_data,
            "player_data": player_data
        })
    )
    
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    return prediction

@app.get("/live-data")
async def get_live_data():
    """Get live match data and updates"""
    try:
        live_matches = data_collector.fetch_live_matches()
        trending_players = data_collector.fetch_trending_players()
        team_rankings = data_collector.fetch_team_rankings()
        batsmen_rankings = data_collector.fetch_batsmen_rankings()
        top_stats = data_collector.fetch_top_stats()
        
        return {
            "live_matches": live_matches,
            "trending_players": trending_players,
            "team_rankings": team_rankings,
            "batsmen_rankings": batsmen_rankings,
            "top_stats": top_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 