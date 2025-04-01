import React from 'react';
import { Link } from 'react-router-dom';

function Home() {
  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          IPL Player Performance Prediction
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Get accurate predictions for IPL player performance based on historical data,
          recent form, and match context.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Player Statistics</h2>
          <p className="text-gray-600 mb-4">
            Access detailed player statistics including batting, bowling, and fielding records.
          </p>
          <Link
            to="/player-stats"
            className="inline-block bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
          >
            View Stats
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Team Analysis</h2>
          <p className="text-gray-600 mb-4">
            Analyze team performance, head-to-head records, and team dynamics.
          </p>
          <Link
            to="/team-stats"
            className="inline-block bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
          >
            View Analysis
          </Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Performance Predictions</h2>
          <p className="text-gray-600 mb-4">
            Get predictions for upcoming matches based on comprehensive analysis.
          </p>
          <Link
            to="/predictions"
            className="inline-block bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
          >
            Get Predictions
          </Link>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Data Collection</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>Historical match data</li>
              <li>Recent player performance</li>
              <li>Team statistics</li>
              <li>Match context and conditions</li>
            </ul>
          </div>
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Prediction Model</h3>
            <ul className="list-disc list-inside text-gray-600 space-y-2">
              <li>Statistical analysis</li>
              <li>Form factor calculation</li>
              <li>Context-based adjustments</li>
              <li>Performance trends</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home; 