import React, { useState, useEffect } from 'react';
import axios from 'axios';

function PlayerStats() {
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPlayers();
  }, []);

  const fetchPlayers = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/players');
      setPlayers(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch players');
      setLoading(false);
    }
  };

  const fetchPlayerStats = async (playerId) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/player/${playerId}/stats`);
      setSelectedPlayer(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch player stats');
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
      <h1 className="text-3xl font-bold text-gray-900">Player Statistics</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Player List */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Players</h2>
          <div className="space-y-2">
            {players.map((player) => (
              <button
                key={player.id}
                onClick={() => fetchPlayerStats(player.id)}
                className={`w-full text-left px-4 py-2 rounded-md ${
                  selectedPlayer?.id === player.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'hover:bg-gray-100'
                }`}
              >
                {player.name}
              </button>
            ))}
          </div>
        </div>

        {/* Player Stats */}
        {selectedPlayer && (
          <div className="md:col-span-2 bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              {selectedPlayer.name} - Statistics
            </h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Batting</h3>
                <div className="space-y-2">
                  <p>Matches: {selectedPlayer.batting.matches}</p>
                  <p>Runs: {selectedPlayer.batting.runs}</p>
                  <p>Average: {selectedPlayer.batting.average}</p>
                  <p>Strike Rate: {selectedPlayer.batting.strike_rate}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Bowling</h3>
                <div className="space-y-2">
                  <p>Matches: {selectedPlayer.bowling.matches}</p>
                  <p>Wickets: {selectedPlayer.bowling.wickets}</p>
                  <p>Average: {selectedPlayer.bowling.average}</p>
                  <p>Economy: {selectedPlayer.bowling.economy}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Recent Form</h3>
                <div className="space-y-2">
                  <p>Last 5 Matches: {selectedPlayer.recent_form.last_5_matches}</p>
                  <p>Average Runs: {selectedPlayer.recent_form.avg_runs}</p>
                  <p>Average Wickets: {selectedPlayer.recent_form.avg_wickets}</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Career Highlights</h3>
                <div className="space-y-2">
                  <p>Best Batting: {selectedPlayer.highlights.best_batting}</p>
                  <p>Best Bowling: {selectedPlayer.highlights.best_bowling}</p>
                  <p>Player of the Match: {selectedPlayer.highlights.player_of_match}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default PlayerStats; 