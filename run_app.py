"""
Run script for the Gaming and Mental Health Analysis Platform
This script provides a simple way to start both backend and frontend services
"""

import os
import subprocess
import time
import threading
import webbrowser
import sys

def start_backend():
    """Start the FastAPI backend server"""
    print("Starting FastAPI backend...")
    backend_process = subprocess.Popen(
        [sys.executable, "analyze_data.py", "api"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for backend to start
    time.sleep(2)
    if backend_process.poll() is not None:
        print("Error starting backend:")
        print(backend_process.stderr.read())
        sys.exit(1)
    
    print("Backend started successfully!")
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("Starting Streamlit frontend...")
    frontend_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for frontend to start
    time.sleep(5)
    if frontend_process.poll() is not None:
        print("Error starting frontend:")
        print(frontend_process.stderr.read())
        sys.exit(1)
        
    print("Frontend started successfully!")
    return frontend_process

def open_browser():
    """Open the browser to the Streamlit app"""
    print("Opening application in browser...")
    webbrowser.open("http://localhost:8501")

def main():
    """Main function to run the application"""
    print("="*50)
    print("Gaming and Mental Health Analysis Platform")
    print("="*50)
    
    # Ensure database setup
    if not os.path.exists(".database_initialized"):
        print("\nSetting up database...")
        subprocess.run([sys.executable, "setup_database.py"], check=True)
        
        print("\nGenerating sample data...")
        subprocess.run([sys.executable, "generate_data.py"], check=True)
        
        # Create a marker file to avoid re-initializing
        with open(".database_initialized", "w") as f:
            f.write("Database initialized")
    
    # Start services
    backend = start_backend()
    frontend = start_frontend()
    
    # Open browser after a short delay
    threading.Timer(2, open_browser).start()
    
    print("\nApplication is now running!")
    print("- Backend API: http://localhost:8000")
    print("- Frontend UI: http://localhost:8501")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping application...")
        backend.terminate()
        frontend.terminate()
        print("Application stopped.")

if __name__ == "__main__":
    main()
