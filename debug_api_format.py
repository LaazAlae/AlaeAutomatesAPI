#!/usr/bin/env python3
"""
Debug script to show the API response format
Run this to see what your API is returning vs what frontend expects
"""

import requests
import json

API_BASE = "http://localhost:8000"

# Test what the API actually returns
try:
    # Create session
    response = requests.post(f"{API_BASE}/api/statement-processor")
    session_data = response.json()
    session_id = session_data['session_id']
    print("✅ Session created:", session_id)
    
    # Get questions (this will be empty since no files uploaded, but shows format)
    response = requests.get(f"{API_BASE}/api/statement-processor/{session_id}/questions")
    questions_data = response.json()
    
    print("\n📊 CURRENT API RESPONSE FORMAT:")
    print("=" * 50)
    print(json.dumps(questions_data, indent=2))
    
    print("\n🔍 EXPECTED STRUCTURE:")
    print("=" * 50)
    print("""
{
  "status": "success",
  "companies_requiring_review": [
    {
      "statement_id": "stmt-001",
      "extracted_company": "Abar Abstract", 
      "current_destination": "Foreign",
      "page_info": "page 1 of 1",
      "questions": [
        {
          "question_id": "q001",
          "dnm_company": "Joe Abstract",
          "similarity_percentage": "78.5%"
        }
      ]
    }
  ]
}
    """)
    
    print("\n⚠️  FRONTEND ERROR CAUSE:")
    print("=" * 50)
    print("Frontend is trying to access: company.questions[0]")
    print("But 'questions' field is undefined in the API response")
    print("This means frontend code needs to be updated to handle new format")
    
except Exception as e:
    print(f"❌ Error testing API: {e}")