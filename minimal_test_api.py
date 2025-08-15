#!/usr/bin/env python3
"""
Minimal working API for testing
"""

from flask import Flask, jsonify, request
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# Simple storage
sessions = {}

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Statement Processing API',
        'port': 8000,
        'sessions': len(sessions),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Statement Processing API',
        'status': 'running',
        'endpoints': [
            'GET /health',
            'POST /api/v1/session',
            'POST /api/v1/session/{id}/upload',
            'POST /api/v1/session/{id}/process'
        ]
    })

@app.route('/api/v1/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'status': 'created',
        'created_at': datetime.now().isoformat()
    }
    return jsonify({
        'status': 'success',
        'session_id': session_id
    })

@app.route('/api/v1/session/<session_id>/upload', methods=['POST'])
def upload_files(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    # Check for files (will be empty in browser test)
    sessions[session_id]['status'] = 'files_uploaded'
    
    return jsonify({
        'status': 'success',
        'message': 'Files uploaded (simulated)'
    })

@app.route('/api/v1/session/<session_id>/process', methods=['POST'])
def process_statements(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    sessions[session_id]['status'] = 'completed'
    sessions[session_id]['results'] = {
        'total_statements': 5,
        'questions_needed': 2
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Processing completed (simulated)',
        'total_statements': 5,
        'questions_needed': 2
    })

@app.route('/api/v1/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    return jsonify({
        'status': 'success',
        'session': {
            'session_id': session_id,
            'status': session_data['status'],
            'created_at': session_data['created_at']
        }
    })

@app.route('/api/v1/session/<session_id>/questions', methods=['GET'])
def get_questions(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    # Simulate some questions for manual review
    questions = [
        {
            'id': str(uuid.uuid4()),
            'company_name': 'ABC Corp Inc',
            'similar_to': 'ABC Corporation', 
            'percentage': '85.5%',
            'current_destination': 'Natio Single'
        },
        {
            'id': str(uuid.uuid4()),
            'company_name': 'XYZ Company LLC',
            'similar_to': 'XYZ Company',
            'percentage': '92.1%',
            'current_destination': 'Foreign'
        }
    ]
    
    return jsonify({
        'status': 'success',
        'questions': questions,
        'total_statements': 5
    })

@app.route('/api/v1/session/<session_id>/answers', methods=['POST'])
def submit_answers(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    answers = request.json.get('answers', {}) if request.json else {}
    sessions[session_id]['answers'] = answers
    sessions[session_id]['status'] = 'finalized'
    
    return jsonify({
        'status': 'success',
        'message': 'Answers submitted successfully (simulated)'
    })

@app.route('/api/v1/session/<session_id>/download', methods=['GET'])
def download_results(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    # Create a simple text file as a placeholder
    content = f"""Statement Processing Results
Session ID: {session_id}
Status: {sessions[session_id]['status']}
Processed at: {datetime.now().isoformat()}

This is a simulated result file.
In the real implementation, this would be a ZIP file containing:
- Split PDF files (DNM.pdf, Foreign.pdf, etc.)
- JSON results file
- Processing summary
"""
    
    from flask import Response
    return Response(
        content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=results_{session_id[:8]}.txt'
        }
    )

@app.route('/api/v1/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    del sessions[session_id]
    return jsonify({
        'status': 'success',
        'message': 'Session deleted successfully'
    })

if __name__ == '__main__':
    print("🚀 Minimal Statement Processing API")
    print("Port: 8000")
    print("Health: http://localhost:8000/health")
    print("CORS enabled for browser testing")
    
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=8000,
        debug=True
    )