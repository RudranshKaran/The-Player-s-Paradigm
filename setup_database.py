import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

# Load environment variables
load_dotenv()

def setup_database():
    """Set up the MongoDB database and create necessary indexes"""
    
    mongo_uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("DATABASE_NAME")
    
    try:
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        
        # Test connection
        client.admin.command('ping')
        print("Connected successfully to MongoDB")
        
        # Access or create the database
        db = client[db_name]
        
        # Access or create collections
        players = db["players"]
        games = db["games"]
        sessions = db["sessions"]
        
        # Drop existing collections to start fresh (this fixes index issues)
        players.drop()
        games.drop()
        sessions.drop()
        print("Dropped existing collections to start fresh")
        
        # Create indexes for better query performance
        players.create_index([("name.first", ASCENDING), ("name.last", ASCENDING)])
        players.create_index([("baseline_mental_health", ASCENDING)])
        
        # Create unique index with partial filter to exclude null values
        games.create_index([("name", ASCENDING)], 
                          unique=True, 
                          partialFilterExpression={"name": {"$type": "string"}})
        games.create_index([("genre", ASCENDING)])
        
        sessions.create_index([("player_id", ASCENDING)])
        sessions.create_index([("game_id", ASCENDING)])
        sessions.create_index([("session_date", DESCENDING)])
        sessions.create_index([("mental_health_after", ASCENDING)])
        
        print(f"Database '{db_name}' is ready with all necessary collections and indexes")
        
    except ConnectionFailure as e:
        print(f"MongoDB Connection Failed: {e}")
        print("Please check that MongoDB is running and your connection string is correct")
        exit(1)
    except Exception as e:
        print(f"Error setting up database: {e}")
        exit(1)

if __name__ == "__main__":
    setup_database()
