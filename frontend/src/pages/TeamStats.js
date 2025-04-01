import React, { useState, useEffect } from 'react';
import axios from 'axios';

function TeamStats() {
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/teams');
      setTeams(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch teams');
      setLoading(false);
    }
  };

  const fetchTeamStats = async (teamId) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/team/${teamId}/stats`);
      setSelectedTeam(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch team stats');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Team Statistics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Team List */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Teams</h2>
          <div className="space-y-2">
            {teams.map((team) => (
              <button
                key={team.id}
                onClick={() => fetchTeamStats(team.id)}
                className={`w-full text-left px-4 py-2 rounded-md ${
                  selectedTeam?.id === team.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'hover:bg-gray-100'
                }`}
              >
                {team.name}
              </button>
            ))}
          </div>
        </div>

        {/* Team Stats */}
        {selectedTeam && (
          <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {selectedTeam.name} - Statistics
            </h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Overall Performance</h3>
                <div className="space-y-2">
                  <p>Matches Played: {selectedTeam.overall.matches_played}</p>
                  <p>Wins: {selectedTeam.overall.wins}</p>
                  <p>Losses: {selectedTeam.overall.losses}</p>
                  <p>Win Rate: {selectedTeam.overall.win_rate}%</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Batting Stats</h3>
                <div className="space-y-2">
                  <p>Average Score: {selectedTeam.batting.avg_score}</p>
                  <p>Highest Score: {selectedTeam.batting.highest_score}</p>
                  <p>Total Runs: {selectedTeam.batting.total_runs}</p>
                  <p>Run Rate: {selectedTeam.batting.run_rate}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Bowling Stats</h3>
                <div className="space-y-2">
                  <p>Total Wickets: {selectedTeam.bowling.total_wickets}</p>
                  <p>Average Wickets: {selectedTeam.bowling.avg_wickets}</p>
                  <p>Economy Rate: {selectedTeam.bowling.economy_rate}</p>
                  <p>Best Bowling: {selectedTeam.bowling.best_bowling}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Recent Form</h3>
                <div className="space-y-2">
                  <p>Last 5 Matches: {selectedTeam.recent_form.last_5_matches}</p>
                  <p>Current Streak: {selectedTeam.recent_form.current_streak}</p>
                  <p>Home Record: {selectedTeam.recent_form.home_record}</p>
                  <p>Away Record: {selectedTeam.recent_form.away_record}</p>
                </div>
              </div>
            </div>

            {/* Team Squad */}
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Team Squad</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {selectedTeam.squad.map((player) => (
                  <div key={player.id} className="bg-gray-50 p-3 rounded-md">
                    <p className="font-medium">{player.name}</p>
                    <p className="text-sm text-gray-600">{player.role}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default TeamStats; 