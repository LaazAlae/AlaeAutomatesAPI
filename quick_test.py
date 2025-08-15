#!/usr/bin/env python3
"""
Quick test to verify the API structure without running the server
"""

def test_api_imports():
    """Test that the enterprise API imports correctly"""
    print("🧪 Testing API Structure")
    print("=" * 30)
    
    try:
        print("📦 Testing imports...")
        
        # Test core imports
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        # Test our app import
        from app_enterprise import app, socketio, session_manager
        print("✅ Enterprise app imports")
        
        # Test routes
        routes = []
        for rule in app.url_map.iter_rules():
            if not rule.rule.startswith('/static'):
                routes.append(rule.rule)
        
        expected_routes = [
            '/health',
            '/api/v1/session',
            '/api/v1/session/<session_id>/upload',
            '/api/v1/session/<session_id>/process',
            '/api/v1/session/<session_id>/questions',
            '/api/v1/session/<session_id>/answers', 
            '/api/v1/session/<session_id>/download',
            '/api/v1/session/<session_id>/status'
        ]
        
        print(f"\n📋 Found {len(routes)} API routes:")
        for route in sorted(routes):
            print(f"  ✅ {route}")
        
        missing = []
        for expected in expected_routes:
            if expected not in routes:
                missing.append(expected)
        
        if missing:
            print(f"\n❌ Missing routes: {missing}")
            return False
        else:
            print(f"\n🎉 All expected routes found!")
        
        # Test session manager
        session_id = session_manager.create_session()
        session_data = session_manager.get_session(session_id)
        
        if session_data and session_data['status'] == 'created':
            print("✅ Session manager works")
            session_manager.delete_session(session_id)
        else:
            print("❌ Session manager failed")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("\n💡 Install dependencies: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_deployment_status():
    """Show the current deployment status"""
    print(f"\n" + "=" * 50)
    print("🚀 DEPLOYMENT STATUS")
    print("=" * 50)
    
    import os
    from pathlib import Path
    
    files_to_check = [
        ('app_enterprise.py', 'Main enterprise API'),
        ('Procfile', 'Railway process configuration'),
        ('requirements.txt', 'Python dependencies'),
        ('railway.json', 'Railway deployment settings'),
        ('test_frontend_simulation.html', 'Frontend testing tool')
    ]
    
    print("📁 Required files:")
    for filename, description in files_to_check:
        if Path(filename).exists():
            print(f"  ✅ {filename} - {description}")
        else:
            print(f"  ❌ {filename} - {description}")
    
    # Check Procfile content
    procfile_path = Path('Procfile')
    if procfile_path.exists():
        content = procfile_path.read_text().strip()
        if 'app_enterprise' in content:
            print("✅ Procfile correctly points to app_enterprise")
        else:
            print("❌ Procfile needs to point to app_enterprise")
            print(f"   Current: {content}")
            print(f"   Should be: web: python app_enterprise.py")

def main():
    success = test_api_imports()
    show_deployment_status()
    
    if success:
        print(f"\n🎯 NEXT STEPS:")
        print("1. 🔥 Run standalone server:")
        print("   python run_standalone.py")
        print()
        print("2. 🌐 Test with frontend:")
        print("   Open test_frontend_simulation.html")
        print("   Use URL: http://localhost:5555")
        print()
        print("3. 🚀 Deploy to Railway:")
        print("   git add . && git commit -m 'Enterprise API ready' && git push")
        print()
        print("✨ Your enterprise API is ready to go!")
    else:
        print(f"\n❌ Fix the issues above before deployment")

if __name__ == "__main__":
    main()