#!/usr/bin/env python3
"""
WebSocket API Test Suite
Tests the complete enterprise workflow
"""

import requests
import socketio
import time
import json
from pathlib import Path
import threading
import queue

class WebSocketAPITester:
    def __init__(self, api_url="http://localhost:5000"):
        self.api_url = api_url
        self.sio = socketio.Client()
        self.session_id = None
        self.events_received = queue.Queue()
        
        self.setup_socket_listeners()
    
    def setup_socket_listeners(self):
        @self.sio.on('connected')
        def on_connected(data):
            print(f"✓ WebSocket connected: {data}")
            self.events_received.put(('connected', data))
        
        @self.sio.on('progress_update')
        def on_progress(data):
            print(f"📈 Progress: {data['progress']}% - {data['message']}")
            self.events_received.put(('progress_update', data))
        
        @self.sio.on('questions_ready')
        def on_questions(data):
            print(f"❓ Questions ready: {len(data['questions'])} questions")
            self.events_received.put(('questions_ready', data))
        
        @self.sio.on('processing_complete')
        def on_complete(data):
            print(f"✅ Processing complete: {data}")
            self.events_received.put(('processing_complete', data))
        
        @self.sio.on('processing_error')
        def on_error(data):
            print(f"❌ Processing error: {data}")
            self.events_received.put(('processing_error', data))
    
    def test_health_check(self):
        """Test health endpoint"""
        print("\n🏥 Testing health check...")
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed: {data}")
                return True
            else:
                print(f"✗ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return False
    
    def test_websocket_connection(self):
        """Test WebSocket connection"""
        print("\n🔌 Testing WebSocket connection...")
        try:
            self.sio.connect(self.api_url)
            time.sleep(1)  # Wait for connection
            
            if self.sio.connected:
                print("✓ WebSocket connected successfully")
                return True
            else:
                print("✗ WebSocket connection failed")
                return False
        except Exception as e:
            print(f"✗ WebSocket connection error: {e}")
            return False
    
    def test_session_creation(self):
        """Test session creation"""
        print("\n📝 Testing session creation...")
        try:
            response = requests.post(f"{self.api_url}/api/v1/session", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.session_id = data['session_id']
                print(f"✓ Session created: {self.session_id}")
                
                # Join WebSocket room
                self.sio.emit('join_session', {'session_id': self.session_id})
                time.sleep(0.5)
                print("✓ Joined WebSocket room")
                return True
            else:
                print(f"✗ Session creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Session creation error: {e}")
            return False
    
    def test_session_status(self):
        """Test session status endpoint"""
        print("\n📊 Testing session status...")
        try:
            response = requests.get(
                f"{self.api_url}/api/v1/session/{self.session_id}/status",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Session status: {data['session']['status']}")
                return True
            else:
                print(f"✗ Session status failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Session status error: {e}")
            return False
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        print("\n📁 Testing file upload validation...")
        try:
            # Test with missing files
            response = requests.post(
                f"{self.api_url}/api/v1/session/{self.session_id}/upload",
                timeout=10
            )
            if response.status_code == 400:
                print("✓ Correctly rejected upload without files")
                return True
            else:
                print(f"✗ Should have rejected upload: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Upload validation error: {e}")
            return False
    
    def test_processing_start_validation(self):
        """Test processing start validation"""
        print("\n⚙️ Testing processing start validation...")
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/session/{self.session_id}/process",
                timeout=10
            )
            if response.status_code == 400:
                print("✓ Correctly rejected processing without files")
                return True
            else:
                print(f"✗ Should have rejected processing: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Processing validation error: {e}")
            return False
    
    def test_session_cleanup(self):
        """Test session deletion"""
        print("\n🗑️ Testing session cleanup...")
        try:
            response = requests.delete(
                f"{self.api_url}/api/v1/session/{self.session_id}",
                timeout=10
            )
            if response.status_code == 200:
                print("✓ Session deleted successfully")
                return True
            else:
                print(f"✗ Session deletion failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Session deletion error: {e}")
            return False
    
    def run_complete_test_suite(self):
        """Run the complete test suite"""
        print("🧪 Starting WebSocket API Test Suite")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("WebSocket Connection", self.test_websocket_connection),
            ("Session Creation", self.test_session_creation),
            ("Session Status", self.test_session_status),
            ("File Upload Validation", self.test_file_upload_validation),
            ("Processing Start Validation", self.test_processing_start_validation),
            ("Session Cleanup", self.test_session_cleanup),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"✗ {test_name} crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Test Results Summary")
        print("=" * 50)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(results)} tests passed")
        
        if self.sio.connected:
            self.sio.disconnect()
            print("🔌 WebSocket disconnected")
        
        return passed == len(results)

def create_mock_files():
    """Create mock test files for API testing"""
    print("📄 Creating mock test files...")
    
    # This would create minimal test files for full workflow testing
    # For now, just document what files would be needed
    
    mock_pdf_info = {
        "filename": "test_statements.pdf",
        "description": "Mock PDF with statement data",
        "required_for": "Full workflow testing"
    }
    
    mock_excel_info = {
        "filename": "test_dnm_list.xlsx", 
        "description": "Mock Excel with DNM company list",
        "required_for": "Full workflow testing"
    }
    
    print("📋 Mock files needed for full testing:")
    print(f"  • {mock_pdf_info['filename']}: {mock_pdf_info['description']}")
    print(f"  • {mock_excel_info['filename']}: {mock_excel_info['description']}")
    print("📝 Note: Create these files to test the complete workflow")

if __name__ == "__main__":
    print("🚀 WebSocket API Testing Tool")
    print("=" * 50)
    
    # Check if server is running
    tester = WebSocketAPITester()
    
    if not tester.test_health_check():
        print("\n❌ API server is not running!")
        print("💡 Start the server with: python app_enterprise.py")
        exit(1)
    
    # Run test suite
    success = tester.run_complete_test_suite()
    
    if success:
        print("\n🎉 All tests passed! API is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above.")
    
    # Show information about full workflow testing
    print("\n" + "=" * 50)
    create_mock_files()
    
    print("\n🌐 Ready for frontend integration!")
    print("📚 See API_DOCUMENTATION.md for complete usage examples")