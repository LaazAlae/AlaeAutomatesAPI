#!/usr/bin/env python3
"""
Quick Start Script for Frontend Demo
Automatically opens browser to http://localhost:3000
"""

import os
import subprocess
import sys
import webbrowser
import time
from threading import Timer

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)  # Wait for server to start
    webbrowser.open('http://localhost:3000')

def main():
    # Always use the fixed Railway URL
    railway_url = "https://alaeautomatesapi.up.railway.app"
    
    # Set environment variable
    os.environ['API_URL'] = railway_url
    
    print(f"\nStarting frontend demo with API: {railway_url}")
    print("Opening browser to: http://localhost:3000")
    print("Press Ctrl+C to stop the frontend server")
    
    # Schedule browser opening
    Timer(2.0, open_browser).start()
    
    # Run the frontend demo
    try:
        subprocess.run([sys.executable, 'frontend_demo.py'], check=True)
    except KeyboardInterrupt:
        print("\nFrontend demo stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running frontend demo: {e}")

if __name__ == '__main__':
    main()