import os
import json
import random
import re  # Add regex module for cleaning JSON
from datetime import datetime, timedelta, UTC  # Add UTC for timezone-aware datetime
from dotenv import load_dotenv
import google.generativeai as genai
from pymongo import MongoClient
from tqdm import tqdm
from faker import Faker

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

# Initialize Faker
fake = Faker(['en_IN'])

# Collections
players_collection = db["players"]
games_collection = db["games"]
sessions_collection = db["sessions"]

# Mental health states
MENTAL_HEALTH_STATES = ["Stressed", "Neutral", "Relaxed", "Excited", "Anxious"]
GAME_GENRES = ["Action", "Puzzle", "Strategy", "Simulation", "RPG", "Adventure", "Sports", "Racing", "Fighting", "Educational"]
GAME_DIFFICULTIES = ["Easy", "Medium", "Hard"]

def generate_player_data(count=50):
    """Generate player data using Gemini API for Indian names"""
    print("Generating player data...")
    
    # Prompt for Gemini to generate Indian names
    prompt = """
    Generate {count} unique Indian names with the following format for each:
    {{
        "first": "Indian first name",
        "last": "Indian last name",
        "age": between 18-65,
        "gender": "Male" or "Female"
    }}
    
    Output should be valid JSON array.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt.format(count=count))
    
    # Parse the response to get the JSON array
    try:
        # Extract JSON from the response
        json_text = response.text
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        
        players_data = json.loads(json_text)
        
        # Add additional fields and insert into the collection
        for player in tqdm(players_data):
            player_doc = {
                "name": {
                    "first": player["first"],
                    "last": player["last"]
                },                "age": player["age"],
                "gender": player["gender"],
                "baseline_mental_health": random.choice(MENTAL_HEALTH_STATES),
                "created_at": datetime.now(UTC)
            }
            players_collection.insert_one(player_doc)
        
        print(f"Successfully inserted {len(players_data)} player documents")
        return players_collection.find()
    
    except Exception as e:
        print(f"Error generating player data: {e}")
        # Fallback to Faker if Gemini API fails
        return generate_player_data_fallback(count)

def generate_player_data_fallback(count=50):
    """Fallback method using Faker to generate Indian names"""
    print("Using fallback method to generate player data...")
    
    players = []
    for _ in tqdm(range(count)):
        gender = random.choice(["Male", "Female"])
        first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
        player_doc = {
            "name": {
                "first": first_name,
                "last": fake.last_name()
            },            "age": random.randint(18, 65),
            "gender": gender,
            "baseline_mental_health": random.choice(MENTAL_HEALTH_STATES),
            "created_at": datetime.now(UTC)
        }
        result = players_collection.insert_one(player_doc)
        players.append({"_id": result.inserted_id, **player_doc})
    
    print(f"Successfully inserted {count} player documents (fallback)")
    return players

def generate_game_data():
    """Generate common game data"""
    print("Generating game data...")
    
    # Common games that most people would recognize
    games = [
        {"name": "Candy Crush", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 15, "difficulty": "Easy"},
        {"name": "PUBG Mobile", "genre": "Action", "type": "Multiplayer", "avg_session_duration_minutes": 25, "difficulty": "Medium"},
        {"name": "Minecraft", "genre": "Simulation", "type": "Both", "avg_session_duration_minutes": 60, "difficulty": "Medium"},
        {"name": "Subway Surfers", "genre": "Action", "type": "Singleplayer", "avg_session_duration_minutes": 10, "difficulty": "Easy"},
        {"name": "Ludo King", "genre": "Board", "type": "Multiplayer", "avg_session_duration_minutes": 20, "difficulty": "Easy"},
        {"name": "Chess", "genre": "Strategy", "type": "Multiplayer", "avg_session_duration_minutes": 30, "difficulty": "Hard"},
        {"name": "FIFA Mobile", "genre": "Sports", "type": "Both", "avg_session_duration_minutes": 20, "difficulty": "Medium"},
        {"name": "Call of Duty Mobile", "genre": "Action", "type": "Multiplayer", "avg_session_duration_minutes": 25, "difficulty": "Medium"},
        {"name": "Temple Run", "genre": "Action", "type": "Singleplayer", "avg_session_duration_minutes": 8, "difficulty": "Easy"},
        {"name": "Among Us", "genre": "Strategy", "type": "Multiplayer", "avg_session_duration_minutes": 15, "difficulty": "Medium"},
        {"name": "Angry Birds", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 12, "difficulty": "Easy"},
        {"name": "Wordle", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 5, "difficulty": "Medium"},
        {"name": "Clash of Clans", "genre": "Strategy", "type": "Multiplayer", "avg_session_duration_minutes": 15, "difficulty": "Medium"},
        {"name": "Roblox", "genre": "Simulation", "type": "Multiplayer", "avg_session_duration_minutes": 40, "difficulty": "Easy"},
        {"name": "Free Fire", "genre": "Action", "type": "Multiplayer", "avg_session_duration_minutes": 20, "difficulty": "Medium"},
        {"name": "Tetris", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 10, "difficulty": "Medium"},
        {"name": "Sudoku", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 15, "difficulty": "Medium"},
        {"name": "8 Ball Pool", "genre": "Sports", "type": "Multiplayer", "avg_session_duration_minutes": 10, "difficulty": "Easy"},
        {"name": "Fruit Ninja", "genre": "Action", "type": "Singleplayer", "avg_session_duration_minutes": 5, "difficulty": "Easy"},
        {"name": "Asphalt 9", "genre": "Racing", "type": "Both", "avg_session_duration_minutes": 15, "difficulty": "Medium"},
        {"name": "CalmQuest", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 45, "difficulty": "Medium"},
        {"name": "MindfulMaze", "genre": "Puzzle", "type": "Singleplayer", "avg_session_duration_minutes": 30, "difficulty": "Easy"},
        {"name": "ZenGarden", "genre": "Simulation", "type": "Singleplayer", "avg_session_duration_minutes": 25, "difficulty": "Easy"},
        {"name": "RelaxRiver", "genre": "Adventure", "type": "Singleplayer", "avg_session_duration_minutes": 20, "difficulty": "Easy"},
        {"name": "ThoughtfulThicket", "genre": "RPG", "type": "Singleplayer", "avg_session_duration_minutes": 45, "difficulty": "Medium"}
    ]
      # Add created_at and insert into collection
    game_ids = []
    for game in tqdm(games):
        game_doc = {
            **game,
            "created_at": datetime.now(UTC)
        }
        result = games_collection.insert_one(game_doc)
        game_ids.append({"_id": result.inserted_id, **game_doc})
    
    print(f"Successfully inserted {len(games)} game documents")
    return game_ids

def generate_session_data(players, games, count_per_player=5):
    """Generate session data with mental health effects"""
    print("Generating session data...")
      # Generate session data for mental health study
    prompt = """
    I need to analyze the effects of different game genres on mental health. Based on research and psychological principles:
    
    1. For a person with baseline mental health: "{baseline_mental_health}"
    2. Who played a {game_genre} game called "{game_name}" (difficulty: {difficulty}) for {duration} minutes
    
    What would be their likely mental health state after the session? Choose EXACTLY ONE from: Stressed, Neutral, Relaxed, Excited, Anxious
    
    Also provide a short note about why this change might have occurred (or why their state remained the same).
    
    IMPORTANT: Give your answer ONLY as a valid JSON object with this exact structure, with no markdown formatting, backticks, or additional text:
    {{
        "mental_health_after": "STATE",
        "notes": "BRIEF EXPLANATION"
    }}
    
    Make sure to use double quotes, not single quotes, and avoid using special characters or line breaks in the values.
    """
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    sessions = []
    # Current date for reference
    current_date = datetime.now(UTC)
    
    # For each player, generate multiple gaming sessions
    for player in tqdm(players):
        # Randomly select games for this player
        player_games = random.sample(games, min(count_per_player, len(games)))
        
        for game in player_games:
            # Randomize the session date (within the last 30 days)
            days_ago = random.randint(0, 30)
            session_date = current_date - timedelta(days=days_ago)
            
            # Randomize the session duration (based on game's average but with some variation)
            base_duration = game["avg_session_duration_minutes"]
            duration_variance = base_duration * 0.4  # 40% variance
            duration = max(5, int(base_duration + random.uniform(-duration_variance, duration_variance)))
            
            try:
                # Get mental health effect from Gemini
                response = model.generate_content(
                    prompt.format(
                        baseline_mental_health=player["baseline_mental_health"],
                        game_genre=game["genre"],
                        game_name=game["name"],
                        difficulty=game["difficulty"],
                        duration=duration
                    )
                )                # Extract JSON from the response
                json_text = response.text
                
                # Try to find and clean JSON data
                try:
                    # Try to extract from code blocks
                    if "```json" in json_text:
                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_text:
                        json_text = json_text.split("```")[1].split("```")[0].strip()
                    
                    # Manual JSON extraction as a last resort
                    if "{" in json_text and "}" in json_text:
                        # Extract text between the first { and last }
                        start_idx = json_text.find('{')
                        end_idx = json_text.rfind('}') + 1
                        json_text = json_text[start_idx:end_idx]
                    
                    # Fix common issues with JSON
                    json_text = re.sub(r'//.*?(\n|$)', '', json_text)  # Remove comments
                    json_text = json_text.replace("'", '"')  # Replace single quotes with double quotes
                    json_text = json_text.replace('\n', ' ')  # Remove newlines
                    
                    # Remove trailing commas before closing brackets
                    json_text = re.sub(r',\s*}', '}', json_text)
                    json_text = re.sub(r',\s*]', ']', json_text)
                    
                    # Fix missing quotes around keys
                    json_text = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', json_text)
                    
                    # Try to parse the JSON
                    effect_data = json.loads(json_text)
                    
                    # Validate expected structure
                    if not isinstance(effect_data, dict):
                        raise ValueError("Invalid JSON structure")
                    
                    # Make sure required fields exist
                    mental_health_after = effect_data.get("mental_health_after")
                    notes = effect_data.get("notes")
                    
                    if not mental_health_after or not notes:
                        raise ValueError("Missing required fields in JSON")
                      # Ensure mental_health_after is valid
                    if mental_health_after not in MENTAL_HEALTH_STATES:
                        mental_health_after = random.choice(MENTAL_HEALTH_STATES)
                        effect_data["mental_health_after"] = mental_health_after
                    
                except Exception as json_error:
                    print(f"JSON parsing error: {json_error}, falling back to simple structure")
                    # Create a simple fallback response if JSON parsing fails
                    effect_data = {
                        "mental_health_after": random.choice(MENTAL_HEALTH_STATES),
                        "notes": f"Effect of {game['name']} on player with {player['baseline_mental_health']} baseline."
                    }
                
                session_doc = {
                    "player_id": player["_id"],
                    "game_id": game["_id"],
                    "session_date": session_date,
                    "duration_minutes": duration,
                    "mental_health_after": effect_data["mental_health_after"],
                    "notes": effect_data["notes"]
                }
                
                sessions_collection.insert_one(session_doc)
                sessions.append(session_doc)
                
            except Exception as e:
                print(f"Error generating session data: {e}")
                # Fallback to a simple heuristic model
                session_doc = generate_session_fallback(player, game, session_date, duration)
                sessions_collection.insert_one(session_doc)
                sessions.append(session_doc)
    
    print(f"Successfully inserted {len(sessions)} session documents")
    return sessions

def generate_session_fallback(player, game, session_date, duration):
    """Fallback method for generating session data using simple heuristics"""
    baseline = player["baseline_mental_health"]
    
    # Simple heuristics for mental health transitions based on game characteristics
    transitions = {
        # If player is stressed
        "Stressed": {
            "Puzzle": ["Neutral", "Relaxed"],  # Puzzles tend to calm stressed people
            "Simulation": ["Relaxed", "Neutral"],  # Simulation games can be calming
            "Strategy": ["Neutral", "Excited"],  # Strategy can be engaging but may maintain stress
            "Action": ["Excited", "Stressed"],  # Action can be exciting but may maintain stress
            "RPG": ["Relaxed", "Neutral"],  # RPGs can be immersive and distracting from stress
            "Adventure": ["Excited", "Neutral"],
            "Sports": ["Excited", "Neutral"],
            "Racing": ["Excited", "Stressed"],
            "Fighting": ["Stressed", "Excited"],
            "Educational": ["Neutral", "Relaxed"],
            "Board": ["Neutral", "Relaxed"]
        },
        # If player is neutral
        "Neutral": {
            "Puzzle": ["Relaxed", "Neutral"],
            "Simulation": ["Relaxed", "Neutral"],
            "Strategy": ["Excited", "Neutral"],
            "Action": ["Excited", "Stressed"],
            "RPG": ["Excited", "Relaxed"],
            "Adventure": ["Excited", "Relaxed"],
            "Sports": ["Excited", "Neutral"],
            "Racing": ["Excited", "Stressed"],
            "Fighting": ["Excited", "Stressed"],
            "Educational": ["Neutral", "Relaxed"],
            "Board": ["Neutral", "Relaxed"]
        },
        # If player is relaxed
        "Relaxed": {
            "Puzzle": ["Relaxed", "Neutral"],
            "Simulation": ["Relaxed", "Neutral"],
            "Strategy": ["Neutral", "Excited"],
            "Action": ["Excited", "Stressed"],
            "RPG": ["Relaxed", "Excited"],
            "Adventure": ["Excited", "Relaxed"],
            "Sports": ["Excited", "Neutral"],
            "Racing": ["Excited", "Neutral"],
            "Fighting": ["Excited", "Stressed"],
            "Educational": ["Relaxed", "Neutral"],
            "Board": ["Relaxed", "Neutral"]
        },
        # If player is excited
        "Excited": {
            "Puzzle": ["Neutral", "Relaxed"],
            "Simulation": ["Neutral", "Relaxed"],
            "Strategy": ["Excited", "Neutral"],
            "Action": ["Excited", "Stressed"],
            "RPG": ["Excited", "Relaxed"],
            "Adventure": ["Excited", "Relaxed"],
            "Sports": ["Excited", "Neutral"],
            "Racing": ["Excited", "Stressed"],
            "Fighting": ["Excited", "Stressed"],
            "Educational": ["Neutral", "Relaxed"],
            "Board": ["Neutral", "Excited"]
        },
        # If player is anxious
        "Anxious": {
            "Puzzle": ["Neutral", "Anxious"],
            "Simulation": ["Relaxed", "Neutral"],
            "Strategy": ["Anxious", "Neutral"],
            "Action": ["Anxious", "Stressed"],
            "RPG": ["Neutral", "Relaxed"],
            "Adventure": ["Excited", "Anxious"],
            "Sports": ["Excited", "Anxious"],
            "Racing": ["Anxious", "Excited"],
            "Fighting": ["Anxious", "Stressed"],
            "Educational": ["Neutral", "Anxious"],
            "Board": ["Neutral", "Relaxed"]
        }
    }
    
    # Determine effect based on genre, with more weight toward the first option
    # for longer durations and more weight toward maintaining state for shorter durations
    genre = game["genre"]
    if genre not in transitions[baseline]:
        genre = "Puzzle"  # Default to puzzle if genre not in our heuristics
    
    potential_states = transitions[baseline][genre]
    
    # Duration effect: longer sessions have stronger effects
    if duration > game["avg_session_duration_minutes"] * 1.5:
        # Long session - stronger effect, more likely to change state
        after_state = potential_states[0]
    elif duration < game["avg_session_duration_minutes"] * 0.5:
        # Short session - weaker effect, more likely to maintain state
        after_state = baseline
    else:
        # Normal session - random selection with weights
        after_state = random.choices(
            [potential_states[0], potential_states[1], baseline],
            weights=[0.5, 0.3, 0.2],
            k=1
        )[0]
    
    # Generate notes based on the transition
    notes = generate_note_for_transition(baseline, after_state, game, duration)
    
    return {
        "player_id": player["_id"],
        "game_id": game["_id"],
        "session_date": session_date,
        "duration_minutes": duration,
        "mental_health_after": after_state,
        "notes": notes
    }

def generate_note_for_transition(before, after, game, duration):
    """Generate a realistic note explaining the mental health transition"""
    if before == after:
        notes = [
            f"Player maintained {before.lower()} state throughout the {game['name']} session.",
            f"No significant change in mental state after playing {game['name']} for {duration} minutes.",
            f"The {game['genre'].lower()} game didn't appear to shift their {before.lower()} baseline.",
            f"{game['name']} experience aligned with their existing {before.lower()} mental state."
        ]
    elif (before == "Stressed" or before == "Anxious") and (after == "Relaxed" or after == "Neutral"):
        notes = [
            f"The {game['genre'].lower()} gameplay helped reduce {before.lower()} feelings.",
            f"Player reported feeling calmer after {duration} minutes of {game['name']}.",
            f"{game['name']} provided a positive distraction from {before.lower()} thoughts.",
            f"The immersive experience of {game['genre'].lower()} gameplay shifted mood positively."
        ]
    elif (before == "Relaxed" or before == "Neutral") and (after == "Stressed" or after == "Anxious"):
        notes = [
            f"The {game['difficulty'].lower()} difficulty level of {game['name']} introduced some tension.",
            f"Competitive elements in this {game['genre'].lower()} game increased stress levels.",
            f"After {duration} minutes, player exhibited signs of mental fatigue and {after.lower()} behavior.",
            f"The fast-paced nature of {game['name']} shifted their calm state to more {after.lower()}."
        ]
    elif after == "Excited":
        notes = [
            f"Player became more animated and engaged during the {game['name']} session.",
            f"The {game['genre'].lower()} gameplay stimulated increased enthusiasm and energy.",
            f"After {duration} minutes, {game['name']} elevated mood to a more excited state.",
            f"The achievements in {game['name']} triggered dopamine release and excitement."
        ]
    else:
        notes = [
            f"Playing {game['name']} for {duration} minutes shifted mental state from {before.lower()} to {after.lower()}.",
            f"The {game['genre'].lower()} genre appeared to have a measurable effect on mental state.",
            f"{game['name']} gameplay resulted in a noteworthy transition in emotional baseline.",
            f"Mental health monitoring showed clear shift after the {game['difficulty'].lower()}-difficulty gaming session."
        ]
    
    return random.choice(notes)

def run_data_generation():
    """Run the full data generation process"""
    print("Starting data generation process...")
    
    # Clear existing collections if they exist
    players_collection.delete_many({})
    games_collection.delete_many({})
    sessions_collection.delete_many({})
    
    # Generate and load data
    players = list(generate_player_data())
    games = generate_game_data()
    sessions = generate_session_data(players, games)
    
    # Summary
    print("\nData Generation Complete!")
    print(f"Generated {len(players)} players")
    print(f"Generated {len(games)} games")
    print(f"Generated {len(sessions)} gaming sessions")
    
    # Example queries
    print("\nExample Summary Queries:")
    
    # Count of sessions by game genre
    pipeline = [
        {"$lookup": {"from": "games", "localField": "game_id", "foreignField": "_id", "as": "game_info"}},
        {"$unwind": "$game_info"},
        {"$group": {"_id": "$game_info.genre", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    genre_counts = list(sessions_collection.aggregate(pipeline))
    print("\nSessions by Game Genre:")
    for genre in genre_counts:
        print(f"{genre['_id']}: {genre['count']} sessions")
    
    # Mental health transitions
    pipeline = [
        {"$lookup": {"from": "players", "localField": "player_id", "foreignField": "_id", "as": "player_info"}},
        {"$unwind": "$player_info"},
        {"$group": {
            "_id": {
                "before": "$player_info.baseline_mental_health",
                "after": "$mental_health_after"
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    transition_counts = list(sessions_collection.aggregate(pipeline))
    print("\nMental Health Transitions (Before -> After):")
    for transition in transition_counts:
        print(f"{transition['_id']['before']} -> {transition['_id']['after']}: {transition['count']} instances")

if __name__ == "__main__":
    run_data_generation()
