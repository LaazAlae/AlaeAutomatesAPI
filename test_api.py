#!/usr/bin/env python3
"""
Quick API test script for local development
"""

import requests
import time
import os
from pathlib import Path

def test_health_endpoint():
    """Test health check endpoint"""
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_process_endpoint():
    """Test process endpoint with sample files"""
    # This is just a placeholder - would need actual test files
    print("Process endpoint test would require sample PDF and Excel files")
    print("API endpoints available:")
    print("  POST /process - Process statements and return JSON")
    print("  POST /process-and-split - Process and return ZIP with split PDFs")
    print("  POST /questions - Get list of companies requiring manual review")
    print("  GET /health - Health check")

if __name__ == "__main__":
    print("API Test Suite")
    print("=" * 40)
    
    if test_health_endpoint():
        print("✓ API is running correctly")
        test_process_endpoint()
    else:
        print("✗ API is not responding")
        print("Start the API with: python app.py")