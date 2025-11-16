# IPL Player Performance Prediction 2025

An AI-powered web application that predicts player performance for IPL 2025 matches. Get detailed predictions for batting and bowling performance including runs, wickets, strike rates, and economy rates for all players.

![IPL 2025](https://img.shields.io/badge/IPL-2025-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18.2-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-black)

## Features

- 🏏 **Match Predictions**: AI-powered predictions for all 72 IPL 2025 matches
- 📊 **Player Analytics**: Detailed batting and bowling predictions for 120+ players
- 🎨 **Modern UI**: Beautiful, responsive dashboard with real-time updates
- ⚡ **Fast Performance**: Instant predictions with optimized backend
- 📱 **Mobile Friendly**: Works seamlessly on all devices
- 🔄 **Real-time Data**: Up-to-date team rosters and match schedules

## Tech Stack

### Backend
- **Flask 3.0** - Python web framework
- **Python 3.11+** - Core backend language
- **Flask-CORS** - Cross-origin resource sharing
- **Pandas & NumPy** - Data processing

### Frontend
- **React 18.2** - Frontend framework
- **React Router** - Navigation
- **React Bootstrap** - UI components
- **Axios** - API communication

## Project Structure

```
IPL_Player_Prediction/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── api.js           # API integration
│   │   └── App.js           # Main app component
│   └── package.json         # Frontend dependencies
│
├── src/                     # Backend source code
│   ├── data/                # Data files
│   │   ├── ipl_2025_data.py        # Match schedules
│   │   └── team_rosters.py         # Team rosters
│   ├── data_collection/     # Data collection modules
│   └── prediction/          # Prediction models
│
├── static/                  # Static files for production
├── logs/                    # Application logs
├── app.py                   # Flask application entry point
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 16 or higher
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/IPL_Player_Prediction.git
cd IPL_Player_Prediction
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
cd ..
```

### Running the Application

#### Option 1: Using Batch Files (Windows)

Simply double-click `start_all.bat` or run:
```bash
start_all.bat
```

This will:
- Start the Flask backend on http://localhost:5000
- Start the React frontend on http://localhost:3000
- Open both in separate command windows

#### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:5000

## Usage Guide

### Dashboard
- View upcoming matches
- See tournament statistics
- Quick access to predictions

### Match Predictions
1. Navigate to "Match Predictions"
2. Select a match from the dropdown
3. View predictions for:
   - All players (combined)
   - Team 1 players
   - Team 2 players

### Prediction Details
Each prediction includes:
- **Batsmen**: Predicted runs and strike rate
- **Bowlers**: Predicted wickets and economy rate
- **All-rounders**: Both batting and bowling predictions

## API Endpoints

### Matches
- `GET /api/matches` - Get all IPL 2025 matches

### Predictions
- `GET /api/matches/<match_no>/predictions` - Get predictions for a specific match

### Teams
- `GET /api/teams` - Get all team rosters

## Configuration

The application uses the following default ports:
- Backend: `5000`
- Frontend: `3000`

To change these, modify:
- Backend: `app.py` (PORT variable)
- Frontend: `frontend/package.json` (start script)

## Features in Detail

### Prediction Algorithm
The system generates predictions based on:
- Player role (Batsman, Bowler, All-rounder)
- Historical performance patterns
- Match conditions
- Team composition

### Data Sources
- **Team Rosters**: `src/data/team_rosters.py`
- **Match Schedule**: `src/data/ipl_2025_data.py`

## Development

### Backend Development
```bash
# Run with debug mode
FLASK_ENV=development python app.py
```

### Frontend Development
```bash
cd frontend
npm start
```

### Building for Production
```bash
cd frontend
npm run build
```

## Troubleshooting

### Port Already in Use
If you see "port already in use" errors:

**Windows:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000
# Kill process (replace PID)
taskkill //F //PID <PID>
```

**Mac/Linux:**
```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9
```

### Module Not Found
```bash
# Reinstall Python dependencies
pip install -r requirements.txt

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Issues
Ensure Flask-CORS is properly installed:
```bash
pip install Flask-CORS==6.0.1
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Enhancements

- [ ] Integration with live match data APIs
- [ ] Historical prediction accuracy tracking
- [ ] Player comparison tools
- [ ] Advanced analytics dashboard
- [ ] Export predictions to PDF/CSV
- [ ] Mobile app version

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- IPL 2025 team roster data
- React Bootstrap for UI components
- Flask framework

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

## Project Status

🟢 **Active Development** - Regular updates and improvements

---

**Made with ❤️ for cricket fans and data enthusiasts**
