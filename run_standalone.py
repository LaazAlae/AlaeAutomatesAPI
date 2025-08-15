#!/usr/bin/env python3
"""
Standalone runner for the Statement Processing API
This avoids conflicts with other services on your system
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a unique port to avoid conflicts
os.environ['PORT'] = '5555'

def main():
    print("🚀 Starting Statement Processing Enterprise API")
    print("=" * 50)
    print("Port: 5555 (avoiding conflicts with your existing services)")
    print("Health check: http://localhost:5555/health")
    print("Test frontend: Open test_frontend_simulation.html and use http://localhost:5555")
    print("=" * 50)
    
    try:
        # Import and run the enterprise app
        from app_enterprise import app, socketio
        
        # Show available routes
        print("\n📋 Available API endpoints:")
        for rule in app.url_map.iter_rules():
            methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
            print(f"  {rule.rule} [{', '.join(methods)}]")
        
        print(f"\n🌐 Starting server on port 5555...")
        print("Press Ctrl+C to stop")
        
        # Run with SocketIO
        socketio.run(
            app,
            host='127.0.0.1',  # Localhost only
            port=5555,
            debug=True,
            allow_unsafe_werkzeug=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure you have all dependencies installed:")
        print("pip install -r requirements.txt")
        return 1
    
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        return 0
    
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())