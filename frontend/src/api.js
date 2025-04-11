// Use relative path for API calls
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

export const api = {
    // Get all matches
    getMatches: async () => {
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
    },

    // Get predictions for a specific match
    getMatchPredictions: async (matchNo) => {
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
    },

    // Get predictions for a specific player
    getPlayerPredictions: async (playerId) => {
        const response = await fetch(`${API_BASE_URL}/players/${playerId}/predictions`);
        return response.json();
    },

    // Get all teams
    getTeams: async () => {
        const response = await fetch(`${API_BASE_URL}/teams`);
        return response.json();
    },

    // Get all players
    getPlayers: async () => {
        const response = await fetch(`${API_BASE_URL}/players`);
        return response.json();
    },

    // Get all predictions
    getPredictions: async () => {
        const response = await fetch(`${API_BASE_URL}/predictions`);
        return response.json();
    },

    // Get all venues
    getVenues: async () => {
        const response = await fetch(`${API_BASE_URL}/venues`);
        return response.json();
    },

    // Check API health
    checkHealth: async () => {
        const response = await fetch(`${API_BASE_URL}/health`);
        return response.json();
    }
}; 