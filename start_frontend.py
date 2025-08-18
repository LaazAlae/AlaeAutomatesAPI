#!/usr/bin/env python3
"""
Quick Start Script for Frontend Demo
"""

import os
import subprocess
import sys

def main():
    # Check if Railway URL is provided
    railway_url = input("Enter your Railway API URL (or press Enter for localhost:8000): ").strip()
    
    if not railway_url:
        railway_url = "http://localhost:8000"
    
    # Remove trailing slash
    if railway_url.endswith('/'):
        railway_url = railway_url[:-1]
    
    # Set environment variable
    os.environ['API_URL'] = railway_url
    
    print(f"\nStarting frontend demo with API: {railway_url}")
    print("Press Ctrl+C to stop the frontend server")
    
    # Run the frontend demo
    try:
        subprocess.run([sys.executable, 'frontend_demo.py'], check=True)
    except KeyboardInterrupt:
        print("\nFrontend demo stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running frontend demo: {e}")

if __name__ == '__main__':
    main()