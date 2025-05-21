# Gaming and Mental Health Analysis Platform

This project studies the effects of gaming on mental health using MongoDB for data storage, FastAPI for the backend, and Streamlit for the frontend visualization. The analysis is powered by Google's Gemini AI.

## Project Structure

- `generate_data.py` - Creates synthetic data for players, games, and gaming sessions
- `analyze_data.py` - FastAPI backend for game mental health analysis
- `streamlit_app.py` - Streamlit frontend for visualizing game analysis
- `requirements.txt` - Lists all required Python packages
- `.env` - Contains API keys and MongoDB connection information

## Data Schema

### Players Collection
```json
{
  "_id": ObjectId,
  "name": {
    "first": "John",
    "last": "Doe"
  },
  "age": 25,
  "gender": "Male",
  "baseline_mental_health": "Stressed",  // Can be: Stressed, Neutral, Relaxed, Excited, Anxious
  "created_at": ISODate("2025-05-20T14:00:00Z")
}
```

### Games Collection
```json
{
  "_id": ObjectId,
  "name": "CalmQuest",
  "genre": "Puzzle",  // Examples: Action, Puzzle, Strategy, Simulation, RPG, etc.
  "type": "Singleplayer",  // Singleplayer or Multiplayer
  "avg_session_duration_minutes": 45,
  "difficulty": "Medium",  // Easy, Medium, Hard
  "created_at": ISODate("2025-05-20T14:00:00Z")
}
```

### Sessions Collection
```json
{
  "_id": ObjectId,
  "player_id": ObjectId("..."),  // Reference to players._id
  "game_id": ObjectId("..."),    // Reference to games._id
  "session_date": ISODate("2025-05-19T20:00:00Z"),
  "duration_minutes": 60,
  "mental_health_after": "Relaxed",  // Same set as baseline_mental_health
  "notes": "Player felt less anxious after solving puzzles."
}
```

## Setup Instructions

1. Install MongoDB locally or use MongoDB Atlas
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your `.env` file with:
   - `GOOGLE_API_KEY` - Your Gemini API key
   - `MONGODB_URI` - Your MongoDB connection string
   - `DATABASE_NAME` - Name for your database (default: "gaming_mental_health")

4. Generate synthetic data:
   ```bash
   python generate_data.py
   ```

5. Start the FastAPI backend:
   ```bash
   python analyze_data.py api
   ```

6. In a separate terminal, launch the Streamlit frontend:
   ```bash
   streamlit run streamlit_app.py
   ```

## Features

- **FastAPI Backend**: RESTful API for game analysis
- **Streamlit Frontend**: Interactive visualization of game mental health impacts
- **Bokeh Visualizations**: Engaging charts and graphs for data presentation
- **AI-Powered Recommendations**: Gemini AI generates personalized recommendations

## API Endpoints

- `GET /games` - List all available games
- `GET /analyze/{game_name}` - Get detailed analysis for a specific game

## Technical Details

- **Data Generation**: Creates realistic, Indian-named players and popular games
- **Mental Health Modeling**: Uses Gemini AI to model psychological effects of gaming
- **Fallback Mechanisms**: Includes heuristic-based generation when API fails
- **Comprehensive Analysis**: Aggregates statistics and generates insights
- **Interactive Visualizations**: Bokeh-powered charts for data exploration

## Note

This project uses synthetic data and is intended for educational and research purposes. The mental health effects are modeled based on common psychological principles but should not be considered medical advice.
