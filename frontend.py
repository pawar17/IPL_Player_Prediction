import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# API configuration
API_URL = "http://localhost:8000"

def fetch_data(endpoint):
    """Fetch data from API endpoint"""
    try:
        response = requests.get(f"{API_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="IPL Player Prediction", layout="wide")
    
    st.title("IPL Player Performance Prediction")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Dashboard", "Matches", "Players", "Predictions", "Live Data"]
    )
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Matches":
        show_matches()
    elif page == "Players":
        show_players()
    elif page == "Predictions":
        show_predictions()
    elif page == "Live Data":
        show_live_data()

def show_dashboard():
    st.header("Dashboard")
    
    # Fetch data
    matches = fetch_data("matches")
    teams = fetch_data("teams")
    players = fetch_data("players")
    
    if matches and teams and players:
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Matches", len(matches))
        with col2:
            st.metric("Total Teams", len(teams))
        with col3:
            st.metric("Total Players", len(players))
        
        # Recent matches chart
        st.subheader("Recent Matches")
        matches_df = pd.DataFrame(matches)
        fig = px.bar(matches_df.head(5), x="date", y="match_importance",
                    title="Match Importance of Recent Matches")
        st.plotly_chart(fig)
        
        # Team performance
        st.subheader("Team Performance")
        teams_df = pd.DataFrame(teams)
        fig = px.scatter(teams_df, x="stats", y="stats",
                        title="Team Statistics")
        st.plotly_chart(fig)

def show_matches():
    st.header("Matches")
    
    matches = fetch_data("matches")
    if matches:
        matches_df = pd.DataFrame(matches)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_team = st.selectbox("Select Team", ["All"] + list(matches_df["team1"].unique()))
        with col2:
            selected_status = st.selectbox("Select Status", ["All"] + list(matches_df["status"].unique()))
        
        # Filter data
        if selected_team != "All":
            matches_df = matches_df[
                (matches_df["team1"] == selected_team) |
                (matches_df["team2"] == selected_team)
            ]
        if selected_status != "All":
            matches_df = matches_df[matches_df["status"] == selected_status]
        
        # Display matches
        st.dataframe(matches_df)

def show_players():
    st.header("Players")
    
    players = fetch_data("players")
    teams = fetch_data("teams")
    
    if players and teams:
        players_df = pd.DataFrame(players)
        teams_df = pd.DataFrame(teams)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            selected_team = st.selectbox("Select Team", ["All"] + list(teams_df["name"].unique()))
        with col2:
            selected_role = st.selectbox("Select Role", ["All"] + list(players_df["role"].unique()))
        
        # Filter data
        if selected_team != "All":
            players_df = players_df[players_df["team_id"] == selected_team]
        if selected_role != "All":
            players_df = players_df[players_df["role"] == selected_role]
        
        # Display players
        st.dataframe(players_df)
        
        # Player statistics
        if len(players_df) > 0:
            st.subheader("Player Statistics")
            selected_player = st.selectbox("Select Player", players_df["name"].tolist())
            player_data = players_df[players_df["name"] == selected_player].iloc[0]
            
            # Create metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Consistency Score", f"{player_data['consistency_score']:.2f}")
            with col2:
                st.metric("Role", player_data["role"])
            with col3:
                st.metric("Team", player_data["team_id"])

def show_predictions():
    st.header("Predictions")
    
    matches = fetch_data("matches")
    players = fetch_data("players")
    predictions = fetch_data("predictions")
    
    if matches and players and predictions:
        # Create prediction form
        st.subheader("Make a Prediction")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_match = st.selectbox("Select Match", matches)
        with col2:
            selected_player = st.selectbox("Select Player", players)
        
        if st.button("Predict"):
            # Make prediction request
            try:
                response = requests.post(
                    f"{API_URL}/predict",
                    json={
                        "match_id": selected_match["match_id"],
                        "player_id": selected_player["player_id"]
                    }
                )
                prediction = response.json()
                
                # Display prediction
                st.success("Prediction Generated!")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Predicted Score", f"{prediction['predicted_score']:.2f}")
                with col2:
                    st.metric("Confidence", f"{prediction['confidence']:.2%}")
            except Exception as e:
                st.error(f"Error making prediction: {str(e)}")
        
        # Display historical predictions
        st.subheader("Historical Predictions")
        predictions_df = pd.DataFrame(predictions)
        st.dataframe(predictions_df)

def show_live_data():
    st.header("Live Data")
    
    live_data = fetch_data("live-data")
    if live_data:
        # Live matches
        st.subheader("Live Matches")
        live_matches = pd.DataFrame(live_data["live_matches"])
        st.dataframe(live_matches)
        
        # Trending players
        st.subheader("Trending Players")
        trending_players = pd.DataFrame(live_data["trending_players"])
        st.dataframe(trending_players)
        
        # Team rankings
        st.subheader("Team Rankings")
        team_rankings = pd.DataFrame(live_data["team_rankings"])
        fig = px.bar(team_rankings, x="team", y="points",
                    title="Team Rankings")
        st.plotly_chart(fig)
        
        # Batsmen rankings
        st.subheader("Batsmen Rankings")
        batsmen_rankings = pd.DataFrame(live_data["batsmen_rankings"])
        fig = px.bar(batsmen_rankings, x="player", y="runs",
                    title="Batsmen Rankings")
        st.plotly_chart(fig)

if __name__ == "__main__":
    main() 