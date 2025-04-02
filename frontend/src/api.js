const API_BASE_URL = 'http://localhost:5000/api';

export const api = {
    // Get all matches
    getMatches: async () => {
        const response = await fetch(`${API_BASE_URL}/matches`);
        return response.json();
    },

    // Get predictions for a specific match
    getMatchPredictions: async (matchId) => {
        const response = await fetch(`${API_BASE_URL}/matches/${matchId}/predictions`);
        return response.json();
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