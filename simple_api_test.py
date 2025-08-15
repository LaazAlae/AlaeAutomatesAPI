#!/usr/bin/env python3
"""
Simple API test version without WebSocket dependencies
This will run locally to test the basic functionality
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
import uuid
import os
import json
from datetime import datetime
from pathlib import Path

# Simple Flask app for testing
app = Flask(__name__)
CORS(app, origins=["*"])

# Simple in-memory session storage
sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'statement-processor-enterprise',
        'websocket': False,  # Disabled for simple testing
        'sessions': len(sessions),
        'message': 'Simple test version - WebSocket disabled'
    })

@app.route('/api/v1/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'created_at': datetime.now().isoformat(),
        'status': 'created',
        'files': {},
        'statements': [],
        'questions': []
    }
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'expires_in': 7200
    })

@app.route('/api/v1/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    session_data = sessions[session_id]
    return jsonify({
        'status': 'success',
        'session': {
            'session_id': session_id,
            'status': session_data['status'],
            'created_at': session_data['created_at'],
            'has_questions': len(session_data.get('questions', [])) > 0,
            'total_statements': len(session_data.get('statements', [])),
            'questions_count': len(session_data.get('questions', []))
        }
    })

@app.route('/api/v1/session/<session_id>/upload', methods=['POST'])
def upload_files(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    if 'pdf' not in request.files or 'excel' not in request.files:
        return jsonify({'error': 'Both PDF and Excel files required'}), 400
    
    pdf_file = request.files['pdf']
    excel_file = request.files['excel']
    
    # Simple validation
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid PDF file'}), 400
    
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        return jsonify({'error': 'Invalid Excel file'}), 400
    
    sessions[session_id]['status'] = 'files_uploaded'
    sessions[session_id]['files'] = {
        'pdf': pdf_file.filename,
        'excel': excel_file.filename
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Files uploaded successfully',
        'files': {
            'pdf': {'name': pdf_file.filename, 'size': len(pdf_file.read())},
            'excel': {'name': excel_file.filename, 'size': len(excel_file.read())}
        }
    })

@app.route('/api/v1/session/<session_id>/process', methods=['POST'])
def start_processing(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    if sessions[session_id]['status'] != 'files_uploaded':
        return jsonify({'error': 'Files not uploaded'}), 400
    
    # Simulate processing - in real app this would be background
    sessions[session_id]['status'] = 'completed'
    sessions[session_id]['statements'] = [
        {
            'company_name': 'Sample Company Inc',
            'destination': 'DNM',
            'manual_required': False
        },
        {
            'company_name': 'Test Corp',
            'destination': 'Natio Single', 
            'manual_required': True,
            'ask_question': True,
            'similar_to': 'Test Corporation',
            'percentage': '85.5%'
        }
    ]
    
    # Add sample questions
    sessions[session_id]['questions'] = [
        {
            'id': str(uuid.uuid4()),
            'company_name': 'Test Corp',
            'similar_to': 'Test Corporation',
            'percentage': '85.5%',
            'current_destination': 'Natio Single'
        }
    ]
    
    return jsonify({
        'status': 'success',
        'message': 'Processing completed (simulated)',
        'session_id': session_id,
        'total_statements': 2,
        'questions_needed': 1
    })

@app.route('/api/v1/session/<session_id>/questions', methods=['GET'])
def get_questions(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    return jsonify({
        'status': 'success',
        'questions': sessions[session_id].get('questions', []),
        'total_statements': len(sessions[session_id].get('statements', []))
    })

@app.route('/api/v1/session/<session_id>/answers', methods=['POST'])
def submit_answers(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    answers = request.json.get('answers', {})
    sessions[session_id]['answers'] = answers
    sessions[session_id]['status'] = 'completed'
    
    return jsonify({
        'status': 'success',
        'message': 'Answers submitted successfully'
    })

@app.route('/api/v1/session/<session_id>/download', methods=['GET'])
def download_results(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    # Create a simple text file as a placeholder
    content = f"Statement Processing Results\n"
    content += f"Session ID: {session_id}\n"
    content += f"Statements: {len(sessions[session_id].get('statements', []))}\n"
    content += f"Processing completed at: {datetime.now().isoformat()}\n"
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        temp_path = f.name
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f'results_{session_id[:8]}.txt'
    )

@app.route('/api/v1/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session ID'}), 404
    
    del sessions[session_id]
    return jsonify({
        'status': 'success',
        'message': 'Session deleted successfully'
    })

# Add a simple root endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Statement Processing API - Test Version',
        'status': 'running',
        'endpoints': [
            'GET /health',
            'POST /api/v1/session',
            'GET /api/v1/session/{id}/status',
            'POST /api/v1/session/{id}/upload',
            'POST /api/v1/session/{id}/process',
            'GET /api/v1/session/{id}/questions',
            'POST /api/v1/session/{id}/answers',
            'GET /api/v1/session/{id}/download',
            'DELETE /api/v1/session/{id}'
        ],
        'note': 'This is a simplified test version without WebSocket support'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 6000))  # Use port 6000 to avoid all conflicts
    
    print("🚀 Statement Processing API - Simple Test Version")
    print("=" * 55)
    print(f"Port: {port}")
    print(f"Health: http://localhost:{port}/health")
    print(f"API Root: http://localhost:{port}/")
    print("=" * 55)
    print("📋 Available endpoints:")
    
    with app.app_context():
        for rule in app.url_map.iter_rules():
            methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
            print(f"  {rule.rule} [{', '.join(methods)}]")
    
    print("\n🌐 Test with frontend:")
    print("  1. Open test_frontend_simulation.html")
    print(f"  2. Set API URL to: http://localhost:{port}")
    print("  3. Test the workflow (files will be simulated)")
    print("\nPress Ctrl+C to stop")
    print("=" * 55)
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=True
    )