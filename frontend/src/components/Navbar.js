import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-bold text-primary-600">
              IPL Predictor
            </Link>
          </div>
          
          <div className="hidden md:flex space-x-8">
            <Link
              to="/player-stats"
              className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Player Stats
            </Link>
            <Link
              to="/team-stats"
              className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Team Stats
            </Link>
            <Link
              to="/predictions"
              className="text-gray-700 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium"
            >
              Predictions
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar; 