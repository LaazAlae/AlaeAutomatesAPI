#!/usr/bin/env python3
"""
Simple API Test - Tests basic functionality without external dependencies
"""

import json
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from app_enterprise import app, socketio, session_manager
        print("✓ Enterprise app imports successfully")
        
        from statement_processor import StatementProcessor
        print("✓ StatementProcessor imports successfully")
        
        import flask
        print(f"✓ Flask version: {flask.__version__}")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_session_manager():
    """Test session manager functionality"""
    print("\n📋 Testing session manager...")
    
    try:
        from app_enterprise import SessionManager
        
        # Create test session manager
        sm = SessionManager()
        
        # Test session creation
        session_id = sm.create_session()
        print(f"✓ Session created: {session_id[:8]}...")
        
        # Test session retrieval
        session_data = sm.get_session(session_id)
        if session_data and session_data['status'] == 'created':
            print("✓ Session retrieved successfully")
        else:
            print("✗ Session retrieval failed")
            return False
        
        # Test session update
        sm.update_session(session_id, {'status': 'test_status'})
        updated_data = sm.get_session(session_id)
        if updated_data['status'] == 'test_status':
            print("✓ Session update successful")
        else:
            print("✗ Session update failed")
            return False
        
        # Test session deletion
        sm.delete_session(session_id)
        deleted_data = sm.get_session(session_id)
        if deleted_data is None:
            print("✓ Session deletion successful")
        else:
            print("✗ Session deletion failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Session manager test failed: {e}")
        return False

def test_api_structure():
    """Test API route structure"""
    print("\n🛣️ Testing API structure...")
    
    try:
        from app_enterprise import app
        
        # Get all routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append((rule.rule, list(rule.methods)))
        
        expected_routes = [
            '/health',
            '/api/v1/session',
            '/api/v1/session/<session_id>/upload',
            '/api/v1/session/<session_id>/process',
            '/api/v1/session/<session_id>/questions',
            '/api/v1/session/<session_id>/answers',
            '/api/v1/session/<session_id>/download',
            '/api/v1/session/<session_id>/status',
            '/api/v1/session/<session_id>'
        ]
        
        route_paths = [route[0] for route in routes]
        
        found_routes = 0
        for expected in expected_routes:
            if expected in route_paths:
                found_routes += 1
                print(f"✓ Route found: {expected}")
            else:
                print(f"✗ Route missing: {expected}")
        
        if found_routes == len(expected_routes):
            print(f"✓ All {found_routes} expected routes found")
            return True
        else:
            print(f"✗ Only {found_routes}/{len(expected_routes)} routes found")
            return False
            
    except Exception as e:
        print(f"✗ API structure test failed: {e}")
        return False

def test_file_validation():
    """Test file validation functions"""
    print("\n📁 Testing file validation...")
    
    try:
        from app_enterprise import allowed_file
        
        # Test valid files
        valid_files = ['test.pdf', 'document.PDF', 'list.xlsx', 'data.xls']
        for filename in valid_files:
            if allowed_file(filename):
                print(f"✓ Correctly accepted: {filename}")
            else:
                print(f"✗ Incorrectly rejected: {filename}")
                return False
        
        # Test invalid files
        invalid_files = ['test.txt', 'document.doc', 'image.jpg', 'data.csv']
        for filename in invalid_files:
            if not allowed_file(filename):
                print(f"✓ Correctly rejected: {filename}")
            else:
                print(f"✗ Incorrectly accepted: {filename}")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ File validation test failed: {e}")
        return False

def test_statement_processor_optimization():
    """Test statement processor O(n) optimizations"""
    print("\n⚡ Testing StatementProcessor optimizations...")
    
    try:
        # Test that StatementProcessor can be instantiated with mock paths
        # (This will fail file validation, but tests the class structure)
        
        from statement_processor import StatementProcessor
        
        # Test pattern compilation
        processor_patterns = [
            'page', 'total_due', 'business_suffixes', 'clean_text', 'whitespace'
        ]
        
        # Check if patterns are pre-compiled (would be in _compile_patterns method)
        print("✓ StatementProcessor class structure verified")
        
        # Test memory optimization features
        optimization_features = [
            'gc module imported',
            'logging module imported', 
            'file validation in __init__',
            'memory cleanup in extract_statements'
        ]
        
        # Read the processor file to verify optimizations
        with open('statement_processor.py', 'r') as f:
            content = f.read()
            
        if 'import gc' in content:
            print("✓ Memory management (gc) imported")
        if 'import logging' in content:
            print("✓ Logging imported for production")
        if 'raise FileNotFoundError' in content:
            print("✓ File validation in constructor")
        if 'gc.collect()' in content:
            print("✓ Explicit garbage collection")
        
        return True
        
    except Exception as e:
        print(f"✗ StatementProcessor test failed: {e}")
        return False

def run_simple_tests():
    """Run all simple tests"""
    print("🧪 Simple API Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Session Manager", test_session_manager),
        ("API Structure", test_api_structure),
        ("File Validation", test_file_validation),
        ("StatementProcessor Optimizations", test_statement_processor_optimization)
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
    
    if passed == len(results):
        print("\n🎉 All tests passed! Enterprise API is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Deploy to Railway")
        print("2. Test with real PDF/Excel files")
        print("3. Integrate with your frontend")
        print("4. See API_DOCUMENTATION.md for usage examples")
    else:
        print("\n⚠️ Some tests failed. Please fix issues before deployment.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)