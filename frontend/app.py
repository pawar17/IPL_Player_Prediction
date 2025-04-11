import streamlit as st
import pandas as pd
import json
import sys
import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import prediction system
from src.prediction.predict_player_performance import PlayerPredictionSystem

# Set page configuration
st.set_page_config(
    page_title="IPL 2025 Player Prediction",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize prediction system
@st.cache_resource
def get_prediction_system():
    return PlayerPredictionSystem()

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #0066cc;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #003366;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #0066cc;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    .confidence {
        font-size: 0.9rem;
        color: #888;
        font-style: italic;
    }
    .player-role {
        font-size: 1rem;
        color: #555;
        font-weight: bold;
    }
    .team-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #003366;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize prediction system
    system = get_prediction_system()
    
    # Header
    st.markdown('<h1 class="main-header">IPL 2025 Player Performance Prediction</h1>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.image("https://www.iplt20.com/assets/images/ipl-logo-new-old.png", width=200)
    st.sidebar.markdown("## Prediction Options")
    
    # Prediction type selection
    prediction_type = st.sidebar.radio(
        "Select Prediction Type",
        ["Player Prediction", "Team Prediction", "Match Prediction"]
    )
    
    # Get match information
    matches = system.get_match_info()
    match_options = [f"Match {m['match_no']}: {m['team1']} vs {m['team2']} ({m['date']})" for m in matches]
    
    # Match selection
    selected_match_idx = st.sidebar.selectbox("Select Match", range(len(match_options)), format_func=lambda x: match_options[x])
    selected_match = matches[selected_match_idx]
    match_no = selected_match['match_no']
    
    # Display match information
    st.markdown(f"""
    <div class="card">
        <h2 class="sub-header">Match Information</h2>
        <p><strong>Match:</strong> {selected_match['team1']} vs {selected_match['team2']}</p>
        <p><strong>Date:</strong> {selected_match['date']}</p>
        <p><strong>Venue:</strong> {selected_match['venue']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Player Prediction
    if prediction_type == "Player Prediction":
        st.markdown('<h2 class="sub-header">Player Performance Prediction</h2>', unsafe_allow_html=True)
        
        # Get team players
        team1_players = system.get_team_players(selected_match['team1'])
        team2_players = system.get_team_players(selected_match['team2'])
        
        # Combine players with team information
        all_players = [(p['name'], selected_match['team1'], p['role']) for p in team1_players] + \
                     [(p['name'], selected_match['team2'], p['role']) for p in team2_players]
        
        # Player selection
        selected_player_idx = st.selectbox(
            "Select Player",
            range(len(all_players)),
            format_func=lambda x: f"{all_players[x][0]} ({all_players[x][1]}) - {all_players[x][2]}"
        )
        
        selected_player_name, selected_player_team, selected_player_role = all_players[selected_player_idx]
        
        if st.button("Predict Player Performance"):
            with st.spinner(f"Predicting performance for {selected_player_name}..."):
                # Make prediction
                prediction = system.predict_player_performance(match_no, selected_player_name)
                
                if "error" in prediction:
                    st.error(f"Error: {prediction['error']}")
                else:
                    # Display prediction results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="card">
                            <h3>{selected_player_name}</h3>
                            <p class="player-role">{selected_player_role}</p>
                            <p class="team-name">{selected_player_team}</p>
                            
                            <div style="margin-top: 20px;">
                                <p class="metric-label">Predicted Runs</p>
                                <p class="metric-value">{prediction['runs']['value']}</p>
                                <p class="confidence">Range: {prediction['runs']['lower_bound']} - {prediction['runs']['upper_bound']}</p>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <p class="metric-label">Predicted Strike Rate</p>
                                <p class="metric-value">{prediction['strike_rate']['value']}</p>
                                <p class="confidence">Range: {prediction['strike_rate']['lower_bound']} - {prediction['strike_rate']['upper_bound']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="card">
                            <h3>Bowling Performance</h3>
                            
                            <div style="margin-top: 20px;">
                                <p class="metric-label">Predicted Wickets</p>
                                <p class="metric-value">{prediction['wickets']['value']}</p>
                                <p class="confidence">Range: {prediction['wickets']['lower_bound']} - {prediction['wickets']['upper_bound']}</p>
                            </div>
                            
                            <div style="margin-top: 20px;">
                                <p class="metric-label">Predicted Economy Rate</p>
                                <p class="metric-value">{prediction['economy_rate']['value']}</p>
                                <p class="confidence">Range: {prediction['economy_rate']['lower_bound']} - {prediction['economy_rate']['upper_bound']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Create visualizations
                    st.markdown('<h3 class="sub-header">Performance Visualization</h3>', unsafe_allow_html=True)
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                    
                    # Batting metrics
                    batting_metrics = ['runs', 'strike_rate']
                    batting_values = [prediction[m]['value'] for m in batting_metrics]
                    batting_lower = [prediction[m]['lower_bound'] for m in batting_metrics]
                    batting_upper = [prediction[m]['upper_bound'] for m in batting_metrics]
                    
                    # Bowling metrics
                    bowling_metrics = ['wickets', 'economy_rate']
                    bowling_values = [prediction[m]['value'] for m in bowling_metrics]
                    bowling_lower = [prediction[m]['lower_bound'] for m in bowling_metrics]
                    bowling_upper = [prediction[m]['upper_bound'] for m in bowling_metrics]
                    
                    # Batting plot
                    ax1.bar(batting_metrics, batting_values, color='#0066cc')
                    ax1.errorbar(batting_metrics, batting_values, 
                                yerr=[(v-l, u-v) for v, l, u in zip(batting_values, batting_lower, batting_upper)],
                                fmt='none', color='black', capsize=5)
                    ax1.set_title('Batting Metrics')
                    ax1.set_ylabel('Value')
                    
                    # Bowling plot
                    ax2.bar(bowling_metrics, bowling_values, color='#cc0000')
                    ax2.errorbar(bowling_metrics, bowling_values, 
                                yerr=[(v-l, u-v) for v, l, u in zip(bowling_values, bowling_lower, bowling_upper)],
                                fmt='none', color='black', capsize=5)
                    ax2.set_title('Bowling Metrics')
                    ax2.set_ylabel('Value')
                    
                    plt.tight_layout()
                    st.pyplot(fig)
    
    # Team Prediction
    elif prediction_type == "Team Prediction":
        st.markdown('<h2 class="sub-header">Team Performance Prediction</h2>', unsafe_allow_html=True)
        
        # Team selection
        selected_team = st.radio("Select Team", [selected_match['team1'], selected_match['team2']])
        
        if st.button("Predict Team Performance"):
            with st.spinner(f"Predicting performance for {selected_team}..."):
                # Make prediction
                predictions = system.predict_team_performance(match_no, selected_team)
                
                if not predictions:
                    st.error(f"Error: Could not predict performance for {selected_team}")
                else:
                    # Display team summary
                    st.markdown(f'<h3 class="sub-header">{selected_team} - Predicted Performance</h3>', unsafe_allow_html=True)
                    
                    # Create dataframe for team performance
                    team_data = []
                    for player_pred in predictions:
                        player_name = player_pred['player_name']
                        role = player_pred['role']
                        pred = player_pred['prediction']
                        
                        if "error" not in pred:
                            team_data.append({
                                'Player': player_name,
                                'Role': role,
                                'Runs': pred['runs']['value'],
                                'Strike Rate': pred['strike_rate']['value'],
                                'Wickets': pred['wickets']['value'],
                                'Economy Rate': pred['economy_rate']['value']
                            })
                    
                    team_df = pd.DataFrame(team_data)
                    
                    # Display team dataframe
                    st.dataframe(team_df, use_container_width=True)
                    
                    # Create visualizations
                    st.markdown('<h3 class="sub-header">Team Visualization</h3>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top run scorers
                        fig, ax = plt.subplots(figsize=(10, 6))
                        top_batsmen = team_df.sort_values('Runs', ascending=False).head(5)
                        sns.barplot(x='Runs', y='Player', data=top_batsmen, ax=ax, palette='Blues_d')
                        ax.set_title('Top 5 Predicted Run Scorers')
                        ax.set_xlabel('Predicted Runs')
                        st.pyplot(fig)
                    
                    with col2:
                        # Top wicket takers
                        fig, ax = plt.subplots(figsize=(10, 6))
                        top_bowlers = team_df.sort_values('Wickets', ascending=False).head(5)
                        sns.barplot(x='Wickets', y='Player', data=top_bowlers, ax=ax, palette='Reds_d')
                        ax.set_title('Top 5 Predicted Wicket Takers')
                        ax.set_xlabel('Predicted Wickets')
                        st.pyplot(fig)
                    
                    # Team totals
                    st.markdown('<h3 class="sub-header">Team Totals</h3>', unsafe_allow_html=True)
                    
                    total_runs = team_df['Runs'].sum()
                    total_wickets = team_df['Wickets'].sum()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="card" style="text-align: center;">
                            <p class="metric-label">Predicted Team Total</p>
                            <p class="metric-value">{total_runs}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="card" style="text-align: center;">
                            <p class="metric-label">Predicted Wickets Taken</p>
                            <p class="metric-value">{total_wickets}</p>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Match Prediction
    else:
        st.markdown('<h2 class="sub-header">Match Performance Prediction</h2>', unsafe_allow_html=True)
        
        if st.button("Predict Match Performance"):
            with st.spinner(f"Predicting performance for match {match_no}..."):
                # Make prediction
                predictions = system.predict_match_performance(match_no)
                
                if "error" in predictions:
                    st.error(f"Error: {predictions['error']}")
                else:
                    # Get team predictions
                    team1_name = predictions['team1']['name']
                    team2_name = predictions['team2']['name']
                    team1_preds = predictions['team1']['predictions']
                    team2_preds = predictions['team2']['predictions']
                    
                    # Create dataframes for both teams
                    team1_data = []
                    team2_data = []
                    
                    for player_pred in team1_preds:
                        player_name = player_pred['player_name']
                        role = player_pred['role']
                        pred = player_pred['prediction']
                        
                        if "error" not in pred:
                            team1_data.append({
                                'Player': player_name,
                                'Role': role,
                                'Runs': pred['runs']['value'],
                                'Strike Rate': pred['strike_rate']['value'],
                                'Wickets': pred['wickets']['value'],
                                'Economy Rate': pred['economy_rate']['value']
                            })
                    
                    for player_pred in team2_preds:
                        player_name = player_pred['player_name']
                        role = player_pred['role']
                        pred = player_pred['prediction']
                        
                        if "error" not in pred:
                            team2_data.append({
                                'Player': player_name,
                                'Role': role,
                                'Runs': pred['runs']['value'],
                                'Strike Rate': pred['strike_rate']['value'],
                                'Wickets': pred['wickets']['value'],
                                'Economy Rate': pred['economy_rate']['value']
                            })
                    
                    team1_df = pd.DataFrame(team1_data)
                    team2_df = pd.DataFrame(team2_data)
                    
                    # Calculate team totals
                    team1_runs = team1_df['Runs'].sum()
                    team2_runs = team2_df['Runs'].sum()
                    team1_wickets = team1_df['Wickets'].sum()
                    team2_wickets = team2_df['Wickets'].sum()
                    
                    # Display match summary
                    st.markdown('<h3 class="sub-header">Match Summary</h3>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"""
                        <div class="card">
                            <h3 class="team-name">{team1_name}</h3>
                            <p class="metric-label">Predicted Score</p>
                            <p class="metric-value">{team1_runs}/{min(10, team2_wickets)}</p>
                            <p class="metric-label">Wickets Taken</p>
                            <p class="metric-value">{team1_wickets}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                        <div class="card">
                            <h3 class="team-name">{team2_name}</h3>
                            <p class="metric-label">Predicted Score</p>
                            <p class="metric-value">{team2_runs}/{min(10, team1_wickets)}</p>
                            <p class="metric-label">Wickets Taken</p>
                            <p class="metric-value">{team2_wickets}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Determine match winner
                    winner = team1_name if team1_runs > team2_runs else team2_name
                    margin = abs(team1_runs - team2_runs)
                    
                    st.markdown(f"""
                    <div class="card" style="text-align: center; margin-top: 20px;">
                        <h3>Predicted Winner</h3>
                        <p class="metric-value">{winner}</p>
                        <p>by {margin} runs</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display team details in tabs
                    tab1, tab2 = st.tabs([team1_name, team2_name])
                    
                    with tab1:
                        st.dataframe(team1_df, use_container_width=True)
                        
                        # Visualizations for team 1
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Top run scorers
                            fig, ax = plt.subplots(figsize=(10, 6))
                            top_batsmen = team1_df.sort_values('Runs', ascending=False).head(5)
                            sns.barplot(x='Runs', y='Player', data=top_batsmen, ax=ax, palette='Blues_d')
                            ax.set_title(f'Top 5 Predicted Run Scorers - {team1_name}')
                            ax.set_xlabel('Predicted Runs')
                            st.pyplot(fig)
                        
                        with col2:
                            # Top wicket takers
                            fig, ax = plt.subplots(figsize=(10, 6))
                            top_bowlers = team1_df.sort_values('Wickets', ascending=False).head(5)
                            sns.barplot(x='Wickets', y='Player', data=top_bowlers, ax=ax, palette='Reds_d')
                            ax.set_title(f'Top 5 Predicted Wicket Takers - {team1_name}')
                            ax.set_xlabel('Predicted Wickets')
                            st.pyplot(fig)
                    
                    with tab2:
                        st.dataframe(team2_df, use_container_width=True)
                        
                        # Visualizations for team 2
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Top run scorers
                            fig, ax = plt.subplots(figsize=(10, 6))
                            top_batsmen = team2_df.sort_values('Runs', ascending=False).head(5)
                            sns.barplot(x='Runs', y='Player', data=top_batsmen, ax=ax, palette='Blues_d')
                            ax.set_title(f'Top 5 Predicted Run Scorers - {team2_name}')
                            ax.set_xlabel('Predicted Runs')
                            st.pyplot(fig)
                        
                        with col2:
                            # Top wicket takers
                            fig, ax = plt.subplots(figsize=(10, 6))
                            top_bowlers = team2_df.sort_values('Wickets', ascending=False).head(5)
                            sns.barplot(x='Wickets', y='Player', data=top_bowlers, ax=ax, palette='Reds_d')
                            ax.set_title(f'Top 5 Predicted Wicket Takers - {team2_name}')
                            ax.set_xlabel('Predicted Wickets')
                            st.pyplot(fig)
                    
                    # Comparison visualization
                    st.markdown('<h3 class="sub-header">Team Comparison</h3>', unsafe_allow_html=True)
                    
                    fig, ax = plt.subplots(figsize=(10, 6))
                    
                    x = np.arange(2)
                    width = 0.35
                    
                    ax.bar(x - width/2, [team1_runs, team1_wickets], width, label=team1_name)
                    ax.bar(x + width/2, [team2_runs, team2_wickets], width, label=team2_name)
                    
                    ax.set_xticks(x)
                    ax.set_xticklabels(['Runs', 'Wickets'])
                    ax.legend()
                    
                    plt.tight_layout()
                    st.pyplot(fig)

    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; color: #666;">
        <p>IPL 2025 Player Performance Prediction System</p>
        <p>Data last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
