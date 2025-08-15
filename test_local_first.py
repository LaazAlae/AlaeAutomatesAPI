#!/usr/bin/env python3
"""
Test the enterprise API locally first before Railway deployment
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path

def test_enterprise_api_locally():
    """Test the enterprise API on a different port to avoid conflicts"""
    
    print("🧪 Testing Enterprise API Locally")
    print("=" * 50)
    
    # Use a different port to avoid conflict with your existing service
    test_port = 5001
    os.environ['PORT'] = str(test_port)
    
    print(f"📍 Starting API on port {test_port} (avoiding conflict with your existing service)")
    
    # Start the enterprise API in background
    try:
        # Start the API process
        api_process = subprocess.Popen(
            [sys.executable, 'app_enterprise.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, 'PORT': str(test_port)}
        )
        
        print("⏳ Waiting for API to start...")
        time.sleep(5)  # Give it time to start
        
        # Test the health endpoint
        try:
            response = requests.get(f"http://localhost:{test_port}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Enterprise API is working!")
                print(f"   Response: {data}")
                
                # Test session creation
                session_response = requests.post(f"http://localhost:{test_port}/api/v1/session", timeout=10)
                if session_response.status_code == 200:
                    session_data = session_response.json()
                    print(f"✅ Session creation works!")
                    print(f"   Session ID: {session_data['session_id'][:8]}...")
                    
                    # Test session status
                    session_id = session_data['session_id']
                    status_response = requests.get(f"http://localhost:{test_port}/api/v1/session/{session_id}/status", timeout=10)
                    if status_response.status_code == 200:
                        print("✅ Session status endpoint works!")
                        print("\n🎉 All tests passed! Enterprise API is ready for Railway deployment.")
                        
                        print(f"\n🌐 Test the full frontend at:")
                        print(f"   1. Open test_frontend_simulation.html in your browser")
                        print(f"   2. Set API URL to: http://localhost:{test_port}")
                        print(f"   3. Test the complete workflow")
                        
                        # Keep the server running for manual testing
                        print(f"\n🚀 API is running at http://localhost:{test_port}")
                        print("   Press Ctrl+C to stop the server")
                        
                        try:
                            api_process.wait()  # Wait for user to stop
                        except KeyboardInterrupt:
                            print("\n🛑 Stopping API server...")
                            api_process.terminate()
                            api_process.wait()
                        
                        return True
                    else:
                        print(f"❌ Session status failed: {status_response.status_code}")
                else:
                    print(f"❌ Session creation failed: {session_response.status_code}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to API - check if it started properly")
            
            # Show the API output for debugging
            try:
                stdout, stderr = api_process.communicate(timeout=5)
                if stdout:
                    print(f"\n📋 API stdout:\n{stdout.decode()}")
                if stderr:
                    print(f"\n🔥 API stderr:\n{stderr.decode()}")
            except subprocess.TimeoutExpired:
                print("⏳ API is still starting...")
        
        finally:
            # Clean up
            if api_process.poll() is None:
                api_process.terminate()
                api_process.wait()
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return False

def show_railway_deployment_info():
    """Show information about Railway deployment"""
    print("\n" + "=" * 50)
    print("🚀 Railway Deployment Information")
    print("=" * 50)
    
    print("Your Railway app is still using the old app.py file.")
    print("Here's how to fix it:")
    print()
    print("1. 📝 Make sure your git repository has these files:")
    print("   ✅ app_enterprise.py (main application)")
    print("   ✅ Procfile (fixed to use app_enterprise.py)")
    print("   ✅ requirements.txt (with all dependencies)")
    print("   ✅ railway.json (proper configuration)")
    print()
    print("2. 🔄 Redeploy to Railway:")
    print("   git add .")
    print("   git commit -m 'Fix: Use enterprise API'")
    print("   git push origin main")
    print()
    print("3. 🔍 Check Railway logs after deployment:")
    print("   Should show: 'Starting Statement Processing Enterprise API'")
    print()
    print("4. ✅ Test health endpoint:")
    print("   https://web-production-7ca0.up.railway.app/health")
    print("   Should return enterprise API status")

if __name__ == "__main__":
    print("🔍 Your localhost:5000 is running a different service:")
    print("   AlaeAutomates 2.0 Backend API")
    print("   This is NOT the statement processor API")
    print()
    
    success = test_enterprise_api_locally()
    
    if not success:
        show_railway_deployment_info()
    
    print("\n📋 Summary:")
    print("- Your localhost:5000 = Different API service")
    print("- Enterprise API = app_enterprise.py (what you need)")
    print("- Railway deployment = Needs to use app_enterprise.py")
    print()
    print("✨ After local testing succeeds, redeploy to Railway!")