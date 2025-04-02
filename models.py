from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String, unique=True)
    date = Column(DateTime)
    venue = Column(String)
    team1_id = Column(Integer, ForeignKey('teams.id'))
    team2_id = Column(Integer, ForeignKey('teams.id'))
    status = Column(String)
    score = Column(String)
    match_importance = Column(Float)
    pressure_index = Column(Float)
    venue_factors = Column(JSON)
    team_form = Column(JSON)
    head_to_head = Column(JSON)
    
    # Relationships
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    players = relationship("MatchPlayer", back_populates="match")

class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(String, unique=True)
    name = Column(String)
    home_ground = Column(String)
    coach = Column(String)
    stats = Column(JSON)
    
    # Relationships
    home_matches = relationship("Match", foreign_keys="Match.team1_id", backref="home_team")
    away_matches = relationship("Match", foreign_keys="Match.team2_id", backref="away_team")
    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(String, unique=True)
    name = Column(String)
    role = Column(String)
    team_id = Column(Integer, ForeignKey('teams.id'))
    stats = Column(JSON)
    form = Column(JSON)
    role_metrics = Column(JSON)
    batting_metrics = Column(JSON)
    bowling_metrics = Column(JSON)
    consistency_score = Column(Float)
    pressure_metrics = Column(JSON)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    match_performances = relationship("MatchPlayer", back_populates="player")

class MatchPlayer(Base):
    __tablename__ = 'match_players'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    runs = Column(Integer)
    wickets = Column(Integer)
    overs = Column(Float)
    maidens = Column(Integer)
    economy_rate = Column(Float)
    strike_rate = Column(Float)
    catches = Column(Integer)
    stumpings = Column(Integer)
    performance_score = Column(Float)
    
    # Relationships
    match = relationship("Match", back_populates="players")
    player = relationship("Player", back_populates="match_performances")

class Venue(Base):
    __tablename__ = 'venues'
    
    id = Column(Integer, primary_key=True)
    venue_id = Column(String, unique=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    capacity = Column(Integer)
    pitch_type = Column(String)
    boundary_size = Column(String)
    stats = Column(JSON)

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    predicted_score = Column(Float)
    confidence = Column(Float)
    features = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    match = relationship("Match")
    player = relationship("Player")

def init_db(db_url: str):
    """Initialize database connection and create tables"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine 