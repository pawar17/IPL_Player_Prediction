import React, { useState, useEffect } from 'react';
import { api } from '../api';

const MatchPredictions = () => {
    const [matches, setMatches] = useState([]);
    const [selectedMatch, setSelectedMatch] = useState(null);
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadMatches();
    }, []);

    useEffect(() => {
        if (selectedMatch) {
            loadPredictions(selectedMatch);
        }
    }, [selectedMatch]);

    const loadMatches = async () => {
        try {
            const data = await api.getMatches();
            setMatches(data);
        } catch (err) {
            setError('Failed to load matches');
            console.error(err);
        }
    };

    const loadPredictions = async (matchId) => {
        setLoading(true);
        setError(null);
        try {
            const data = await api.getMatchPredictions(matchId);
            setPredictions(data);
        } catch (err) {
            setError('Failed to load predictions');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">IPL Player Predictions</h1>
            
            {/* Match Selection */}
            <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Match
                </label>
                <select
                    className="w-full p-2 border rounded"
                    value={selectedMatch || ''}
                    onChange={(e) => setSelectedMatch(e.target.value)}
                >
                    <option value="">Select a match...</option>
                    {matches.map((match) => (
                        <option key={match.match_id} value={match.match_id}>
                            {match.team1} vs {match.team2} - {match.date}
                        </option>
                    ))}
                </select>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="text-center py-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {/* Predictions Display */}
            {predictions.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {predictions.map((pred) => (
                        <div key={pred.player.id} className="border rounded p-4">
                            <h3 className="font-bold text-lg mb-2">{pred.player.name}</h3>
                            <p className="text-sm text-gray-600 mb-2">{pred.player.team}</p>
                            <div className="grid grid-cols-2 gap-2">
                                <div>
                                    <p className="text-sm font-medium">Runs</p>
                                    <p className="text-lg">{pred.prediction.runs}</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Wickets</p>
                                    <p className="text-lg">{pred.prediction.wickets}</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Strike Rate</p>
                                    <p className="text-lg">{pred.prediction.strike_rate}</p>
                                </div>
                                <div>
                                    <p className="text-sm font-medium">Economy Rate</p>
                                    <p className="text-lg">{pred.prediction.economy_rate}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default MatchPredictions; 