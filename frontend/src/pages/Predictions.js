import React, { useState, useEffect } from 'react';
import axios from 'axios';

function Predictions() {
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMatches();
  }, []);

  useEffect(() => {
    if (selectedMatch) {
      fetchMatchTeams(selectedMatch.id);
    }
  }, [selectedMatch]);

  const fetchMatches = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/matches');
      setMatches(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch matches');
      setLoading(false);
    }
  };

  const fetchMatchTeams = async (matchId) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/match/${matchId}/teams`);
      setTeams(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to fetch match teams');
      setLoading(false);
    }
  };

  const getPredictions = async () => {
    if (!selectedMatch || !selectedTeam) return;

    try {
      setLoading(true);
      const response = await axios.post('http://localhost:8000/api/predict/team', {
        match_id: selectedMatch.id,
        team_id: selectedTeam.id
      });
      setPredictions(response.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to get predictions');
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
      <h1 className="text-3xl font-bold text-gray-900">Performance Predictions</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Match Selection */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Match</h2>
          <div className="space-y-2">
            {matches.map((match) => (
              <button
                key={match.id}
                onClick={() => setSelectedMatch(match)}
                className={`w-full text-left px-4 py-2 rounded-md ${
                  selectedMatch?.id === match.id
                    ? 'bg-primary-100 text-primary-700'
                    : 'hover:bg-gray-100'
                }`}
              >
                <div className="font-medium">{match.team1} vs {match.team2}</div>
                <div className="text-sm text-gray-600">
                  {new Date(match.date).toLocaleDateString()} at {match.venue}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Team Selection */}
        {selectedMatch && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Team</h2>
            <div className="space-y-2">
              {teams.map((team) => (
                <button
                  key={team.id}
                  onClick={() => setSelectedTeam(team)}
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
        )}

        {/* Predictions */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Predictions</h2>
          {selectedTeam && (
            <div className="space-y-4">
              <button
                onClick={getPredictions}
                className="w-full bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
              >
                Generate Predictions
              </button>

              {predictions.length > 0 && (
                <div className="space-y-4">
                  {predictions.map((prediction) => (
                    <div key={prediction.player_id} className="bg-gray-50 p-4 rounded-md">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        {prediction.player_name}
                      </h3>
                      <div className="space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <p className="text-sm text-gray-600">Expected Runs</p>
                            <p className="font-medium">{prediction.expected_runs}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Expected Wickets</p>
                            <p className="font-medium">{prediction.expected_wickets}</p>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <p className="text-sm text-gray-600">Strike Rate</p>
                            <p className="font-medium">{prediction.expected_strike_rate}</p>
                          </div>
                          <div>
                            <p className="text-sm text-gray-600">Economy Rate</p>
                            <p className="font-medium">{prediction.expected_economy_rate}</p>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Confidence</p>
                          <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div
                              className="bg-primary-600 h-2.5 rounded-full"
                              style={{ width: `${prediction.confidence.overall}%` }}
                            ></div>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {prediction.confidence.overall}% confidence
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Predictions; 