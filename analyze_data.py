import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import uvicorn

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Connect to MongoDB
mongo_uri = os.getenv("MONGODB_URI")
db_name = os.getenv("DATABASE_NAME")
client = MongoClient(mongo_uri)
db = client[db_name]

# Collections
players_collection = db["players"]
games_collection = db["games"]
sessions_collection = db["sessions"]

# Create FastAPI app
app = FastAPI(
    title="Game Mental Health Analysis API",
    description="API for analyzing the effect of games on mental health",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class GameAnalysisRequest(BaseModel):
    game_name: str

class ChartData(BaseModel):
    title: str
    chart_type: str  # "bar", "pie", "line", etc.
    data: Dict[str, Any]
    
class GameAnalysisResponse(BaseModel):
    game_name: str
    summary: str
    mental_health_impact: Dict[str, Any]
    recommendations: List[str]
    charts: List[ChartData]

def extract_game_statistics(game_name: str):
    """Extract statistics for a specific game from the database"""
    
    # Find game by name
    game = games_collection.find_one({"name": game_name})
    if not game:
        return None
    
    # Get sessions for this game
    sessions = list(sessions_collection.find({"game_id": game["_id"]}))
    
    if not sessions:
        return {
            "game_info": game,
            "sessions": [],
            "mental_health_impact": {},
            "no_data": True
        }
    
    # Get player IDs from sessions
    player_ids = [session["player_id"] for session in sessions]
    
    # Get player information
    players = list(players_collection.find({"_id": {"$in": player_ids}}))
    player_dict = {str(player["_id"]): player for player in players}
    
    # Analyze mental health transitions
    mental_health_transitions = {}
    session_durations = []
    
    for session in sessions:
        player_id = str(session["player_id"])
        if player_id in player_dict:
            player = player_dict[player_id]
            baseline = player["baseline_mental_health"]
            after = session["mental_health_after"]
            
            key = f"{baseline} -> {after}"
            if key not in mental_health_transitions:
                mental_health_transitions[key] = 0
            mental_health_transitions[key] += 1
            
            session_durations.append(session["duration_minutes"])
    
    # Calculate impact percentages
    total_sessions = len(sessions)
    positive_impact = 0
    negative_impact = 0
    neutral_impact = 0
    for key, count in mental_health_transitions.items():
        baseline, after = key.split(" -> ")
        
        # Enhanced impact classification
        # Define positive transitions (improving mental health or maintaining good state)
        if (baseline in ["Stressed", "Anxious"] and after in ["Relaxed", "Neutral", "Excited"]) or \
           (baseline == "Neutral" and after in ["Relaxed", "Excited"]) or \
           (baseline in ["Relaxed", "Excited"] and after in ["Relaxed", "Excited"]):
            positive_impact += count
        # Define negative transitions (worsening mental health)
        elif (baseline in ["Relaxed", "Excited", "Neutral"] and after in ["Stressed", "Anxious"]) or \
             (baseline in ["Stressed", "Anxious"] and after in ["Stressed", "Anxious"]):
            negative_impact += count
        # Everything else is neutral impact (mainly maintaining neutral state)
        else:
            neutral_impact += count# Calculate percentages
    min_percentage = 0.1  # Set minimum percentage to avoid zeros
    min_negative_percentage = 5.0  # Set minimum percentage for negative impact
    
    # Calculate raw percentages
    positive_percentage = (positive_impact / total_sessions) * 100 if total_sessions > 0 else 0
    negative_percentage = (negative_impact / total_sessions) * 100 if total_sessions > 0 else 0
    neutral_percentage = (neutral_impact / total_sessions) * 100 if total_sessions > 0 else 0
    
    # Apply minimum threshold to any zero values
    if positive_percentage == 0:
        positive_percentage = min_percentage
    if negative_percentage < min_negative_percentage:
        negative_percentage = min_negative_percentage
    if neutral_percentage == 0:
        neutral_percentage = min_percentage
        
    # Normalize to ensure total is 100% if values were adjusted
    total = positive_percentage + negative_percentage + neutral_percentage
    if total != 100 and total > 0:
        scaling_factor = 100 / total
        positive_percentage *= scaling_factor
        negative_percentage *= scaling_factor
        neutral_percentage *= scaling_factor
    
    impact_stats = {
        "positive_impact": positive_impact,
        "negative_impact": negative_impact,
        "neutral_impact": neutral_impact,
        "positive_percentage": positive_percentage,
        "negative_percentage": negative_percentage,
        "neutral_percentage": neutral_percentage,
    }
    
    # Calculate average session duration
    avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0
    
    # Compile statistics
    statistics = {
        "game_info": game,
        "sessions": {
            "total": total_sessions,
            "avg_duration": avg_duration
        },
        "mental_health_transitions": mental_health_transitions,
        "mental_health_impact": impact_stats,
        "no_data": False
    }
    
    return statistics

def analyze_game_with_gemini(game_statistics):
    """Use Gemini to analyze the game statistics"""
    
    if game_statistics.get("no_data", False):
        return {
            "summary": f"Insufficient data available for {game_statistics['game_info']['name']}. No sessions have been recorded yet.",
            "recommendations": ["Try playing this game and recording sessions to get an analysis."],
            "charts": []
        }
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    game_info = game_statistics["game_info"]
    
    # Prepare a detailed prompt with the statistics
    prompt = f"""
    You are a data scientist specializing in human-computer interaction and mental health. 
    Analyze the following gaming and mental health statistics to provide insights on how this specific game affects mental wellbeing.
    
    GAME INFORMATION:
    - Name: {game_info['name']}
    - Genre: {game_info['genre']}
    - Type: {game_info['type']}
    - Difficulty: {game_info['difficulty']}
    - Average Session Duration (design): {game_info['avg_session_duration_minutes']} minutes
    
    SESSION DATA:
    - Total Sessions: {game_statistics['sessions']['total']}
    - Actual Average Duration: {round(game_statistics['sessions']['avg_duration'], 2)} minutes
    
    MENTAL HEALTH IMPACT:
    - Positive Impact: {round(game_statistics['mental_health_impact']['positive_percentage'], 2)}%
    - Negative Impact: {round(game_statistics['mental_health_impact']['negative_percentage'], 2)}%
    - Neutral Impact: {round(game_statistics['mental_health_impact']['neutral_percentage'], 2)}%
    
    MENTAL HEALTH TRANSITIONS:
    {json.dumps(game_statistics['mental_health_transitions'], indent=2)}
    
    Please provide:
    
    1. SUMMARY: A concise analysis of how this game affects mental health based on the data.
    
    2. KEY FINDINGS: 
       - What mental health states benefit most from playing this game?
       - What mental health states might be negatively affected by this game?
       - How does session duration appear to affect outcomes?
    
    3. RECOMMENDATIONS: Provide 3-5 specific recommendations for players on:
       - How to maximize positive mental health benefits from this game
       - How to avoid potential negative effects
       - Optimal session duration
       - Best time of day to play (if relevant based on game type)
       - Any specific practices to follow while playing
      Provide your answer in JSON format with the following structure:
    {{
      "summary": "Your comprehensive analysis summary here",
      "recommendations": ["recommendation1", "recommendation2", "recommendation3", "recommendation4", "recommendation5"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        analysis_text = response.text
        
        # Extract and parse JSON from the response
        if "```json" in analysis_text:
            json_text = analysis_text.split("```json")[1].split("```")[0].strip()
        elif "```" in analysis_text:
            json_text = analysis_text.split("```")[1].split("```")[0].strip()
        else:
            # Try to find JSON block
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_text = analysis_text[start_idx:end_idx]
            else:
                raise ValueError("Couldn't find valid JSON in response")
        
        # Parse the extracted JSON
        analysis_json = json.loads(json_text)
        
        # Add chart data for visualization
        analysis_json["charts"] = create_chart_data(game_statistics)
        
        return analysis_json
    
    except Exception as e:
        print(f"Error analyzing game with Gemini: {e}")
        # Fallback to simple analysis
        return {
            "summary": f"Analysis of {game_info['name']} shows that it has a {round(game_statistics['mental_health_impact']['positive_percentage'])}% positive impact on mental health based on {game_statistics['sessions']['total']} recorded sessions.",
            "recommendations": [
                f"Keep sessions under {int(game_statistics['sessions']['avg_duration'] * 1.2)} minutes to avoid fatigue",
                "Take regular breaks to stretch and rest your eyes",
                "Play in a well-lit room to reduce eye strain",
                "Set clear time limits before starting play sessions",
                "Consider playing with friends for a more enjoyable experience"
            ],
            "charts": create_chart_data(game_statistics)
        }

def create_chart_data(game_statistics):
    """Create chart data for visualizations"""
    charts = []
    
    # Chart 1: Mental Health Impact Pie Chart
    impact_data = {
        "labels": ["Positive", "Negative", "Neutral"],
        "values": [
            game_statistics["mental_health_impact"]["positive_percentage"],
            game_statistics["mental_health_impact"]["negative_percentage"],
            game_statistics["mental_health_impact"]["neutral_percentage"]
        ]
    }
    charts.append({
        "title": "Mental Health Impact",
        "chart_type": "pie",
        "data": impact_data
    })
    
    # Chart 2: Mental Health Transitions Bar Chart
    transitions = game_statistics["mental_health_transitions"]
    if transitions:
        sorted_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)
        transition_data = {
            "labels": [t[0] for t in sorted_transitions[:8]],  # Top 8 transitions
            "values": [t[1] for t in sorted_transitions[:8]]
        }
        charts.append({
            "title": "Common Mental Health Transitions",
            "chart_type": "bar",
            "data": transition_data
        })
    
    # Add more charts as needed
    
    return charts

# FastAPI Endpoints
@app.get("/")
async def root():
    return {"message": "Game Mental Health Analysis API is running. Use /games to list available games or /analyze/{game_name} to analyze a specific game."}

@app.get("/games", response_model=List[str])
async def list_games():
    """Get a list of all available games in the database"""
    games = games_collection.find({}, {"name": 1})
    return [game["name"] for game in games]

@app.get("/analyze/{game_name}", response_model=GameAnalysisResponse)
async def analyze_game(game_name: str):
    """Analyze the mental health impact of a specific game"""
    # Extract game statistics
    game_statistics = extract_game_statistics(game_name)
    
    if not game_statistics:
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found")
      # Analyze with Gemini
    analysis = analyze_game_with_gemini(game_statistics)
    
    # Create response
    return {
        "game_name": game_name,
        "summary": analysis["summary"],
        "mental_health_impact": {
            "positive": game_statistics["mental_health_impact"]["positive_percentage"],
            "negative": game_statistics["mental_health_impact"]["negative_percentage"],
            "neutral": game_statistics["mental_health_impact"]["neutral_percentage"]
        },
        "recommendations": analysis["recommendations"],
        "charts": analysis["charts"]
    }

def run_api():
    """Run the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        print("Starting FastAPI server...")
        run_api()
    else:
        print("Please use 'python analyze_data.py api' to run the API server")
        print("For the Streamlit frontend, use 'streamlit run streamlit_app.py'")
