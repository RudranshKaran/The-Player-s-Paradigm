import os
import sys
import time

def run_script(script_name, description):
    """Run a Python script and handle any errors"""
    print(f"\n{'=' * 50}")
    print(f"RUNNING: {description}")
    print(f"{'=' * 50}\n")
    
    exit_code = os.system(f"python {script_name}")
    
    if exit_code != 0:
        print(f"\nERROR: {description} failed with exit code {exit_code}")
        sys.exit(exit_code)
    else:
        print(f"\nSUCCESS: {description} completed")

def main():
    # Start timing
    start_time = time.time()
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("ERROR: .env file not found. Please create it with your API keys and MongoDB connection string.")
        print("Example .env content:")
        print("GOOGLE_API_KEY=your_gemini_api_key_here")
        print("MONGODB_URI=mongodb://localhost:27017/")
        print("DATABASE_NAME=gaming_mental_health")
        sys.exit(1)
    
    # Step 1: Set up database
    run_script("setup_database.py", "Database setup")
    
    # Step 2: Generate data
    run_script("generate_data.py", "Data generation")
    
    # Step 3: Analyze data
    run_script("analyze_data.py", "Data analysis")
    
    # Calculate total runtime
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"\n{'=' * 50}")
    print(f"All processes completed successfully in {minutes} minutes and {seconds} seconds!")
    print(f"{'=' * 50}\n")
    print("You can find the analysis results in 'game_mental_health_analysis.md'")

if __name__ == "__main__":
    main()
