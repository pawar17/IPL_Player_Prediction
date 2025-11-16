// Use relative path for API calls
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

// Get all matches
export const getMatches = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/matches`);
        if (!response.ok) {
            throw new Error('Failed to fetch matches');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching matches:', error);
        throw error;
    }
};

// Get predictions for a specific match
export const getMatchPredictions = async (matchNo) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/matches/${matchNo}/predictions`);
        if (!response.ok) {
            throw new Error('Failed to fetch match predictions');
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching match predictions:', error);
        throw error;
    }
};

// Get predictions for a specific player
export const getPlayerPredictions = async (playerId) => {
    const response = await fetch(`${API_BASE_URL}/players/${playerId}/predictions`);
    return response.json();
};

// Get all teams
export const getTeams = async () => {
    const response = await fetch(`${API_BASE_URL}/teams`);
    return response.json();
};

// Get all players
export const getPlayers = async () => {
    const response = await fetch(`${API_BASE_URL}/players`);
    return response.json();
};

// Get all predictions
export const getPredictions = async () => {
    const response = await fetch(`${API_BASE_URL}/predictions`);
    return response.json();
};

// Get all venues
export const getVenues = async () => {
    const response = await fetch(`${API_BASE_URL}/venues`);
    return response.json();
};

// Check API health
export const checkHealth = async () => {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
};

// Also export as an object for backward compatibility
export const api = {
    getMatches,
    getMatchPredictions,
    getPlayerPredictions,
    getTeams,
    getPlayers,
    getPredictions,
    getVenues,
    checkHealth
}; 