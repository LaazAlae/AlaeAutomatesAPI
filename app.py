#!/usr/bin/env python3
"""
Real Statement Processing API - Uses actual statement_processor.py
This processes your real PDF and Excel files!
"""

from flask import Flask, jsonify, request, Response
import uuid
import json
import tempfile
import os
from datetime import datetime
from statement_processor import StatementProcessor

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
        'service': 'REAL Statement Processing API',
        'processing': 'ACTUAL PDF PROCESSING',
        'port': 9000,
        'sessions': len(sessions),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'REAL Statement Processing API',
        'status': 'running',
        'processing': 'Uses actual statement_processor.py',
        'note': 'This processes your real PDF and Excel files!'
    })

@app.route('/api/v1/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'status': 'created',
        'created_at': datetime.now().isoformat(),
        'files': {},
        'statements': [],
        'questions': []
    }
    return jsonify({
        'status': 'success',
        'session_id': session_id
    })

@app.route('/api/v1/session/<session_id>/upload', methods=['POST'])
def upload_files(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    if 'pdf' not in request.files or 'excel' not in request.files:
        return jsonify({'error': 'Both PDF and Excel files required'}), 400
    
    pdf_file = request.files['pdf']
    excel_file = request.files['excel']
    
    # Save real files temporarily
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='stmt_') as tmp_pdf:
            pdf_path = tmp_pdf.name
            pdf_file.save(pdf_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', prefix='dnm_') as tmp_excel:
            excel_path = tmp_excel.name
            excel_file.save(excel_path)
        
        # Store file paths in session
        sessions[session_id]['files'] = {
            'pdf_path': pdf_path,
            'excel_path': excel_path,
            'pdf_name': pdf_file.filename,
            'excel_name': excel_file.filename
        }
        sessions[session_id]['status'] = 'files_uploaded'
        
        return jsonify({
            'status': 'success',
            'message': 'Real files uploaded and saved',
            'files': {
                'pdf': {'name': pdf_file.filename, 'size': os.path.getsize(pdf_path)},
                'excel': {'name': excel_file.filename, 'size': os.path.getsize(excel_path)}
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'File upload failed: {str(e)}'}), 500

@app.route('/api/v1/session/<session_id>/process', methods=['POST'])
def process_statements(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    if session_data['status'] != 'files_uploaded':
        return jsonify({'error': 'Files not uploaded'}), 400
    
    try:
        # Get file paths
        files = session_data['files']
        pdf_path = files['pdf_path']
        excel_path = files['excel_path']
        
        print(f"🔍 REAL PROCESSING: {files['pdf_name']} + {files['excel_name']}")
        
        # Create StatementProcessor with real files
        processor = StatementProcessor(pdf_path, excel_path)
        
        # Extract statements from real PDF using real Excel DNM list
        statements = processor.extract_statements()
        
        # Find questions that need manual review
        questions = []
        for stmt in statements:
            if stmt.get('ask_question', False):
                questions.append({
                    'id': str(uuid.uuid4()),
                    'company_name': stmt.get('company_name', ''),
                    'similar_to': stmt.get('similar_to', ''),
                    'percentage': stmt.get('percentage', ''),
                    'current_destination': stmt.get('destination', '')
                })
        
        # Store real results
        sessions[session_id]['statements'] = statements
        sessions[session_id]['questions'] = questions
        sessions[session_id]['status'] = 'processed'
        
        print(f"✅ REAL RESULTS: {len(statements)} statements, {len(questions)} questions")
        
        return jsonify({
            'status': 'success',
            'message': 'REAL processing completed!',
            'total_statements': len(statements),
            'questions_needed': len(questions),
            'processing_type': 'ACTUAL PDF PROCESSING'
        })
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        sessions[session_id]['status'] = 'error'
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/v1/session/<session_id>/questions', methods=['GET'])
def get_questions(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    
    return jsonify({
        'status': 'success',
        'questions': session_data.get('questions', []),
        'total_statements': len(session_data.get('statements', [])),
        'processing_type': 'REAL QUESTIONS FROM YOUR PDF'
    })

@app.route('/api/v1/session/<session_id>/answers', methods=['POST'])
def submit_answers(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    answers = request.json.get('answers', {}) if request.json else {}
    
    # Apply answers to real statements
    session_data = sessions[session_id]
    statements = session_data.get('statements', [])
    
    for stmt in statements:
        company_name = stmt.get('company_name', '')
        if company_name in answers:
            answer = answers[company_name]
            if answer == 'yes':
                stmt['destination'] = 'DNM'
            stmt['user_answered'] = answer
    
    sessions[session_id]['answers'] = answers
    sessions[session_id]['statements'] = statements
    sessions[session_id]['status'] = 'finalized'
    
    return jsonify({
        'status': 'success',
        'message': 'Real answers applied to real statements!',
        'answers_count': len(answers)
    })

@app.route('/api/v1/session/<session_id>/download', methods=['GET'])
def download_results(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    statements = session_data.get('statements', [])
    
    # Create detailed results file
    content = f"""REAL STATEMENT PROCESSING RESULTS
Session ID: {session_id}
Processed: {datetime.now().isoformat()}

=== PROCESSING SUMMARY ===
Total Statements Found: {len(statements)}
Questions Required: {len(session_data.get('questions', []))}
Status: {session_data['status']}

=== FILES PROCESSED ===
PDF: {session_data['files']['pdf_name']}
Excel: {session_data['files']['excel_name']}

=== DETAILED RESULTS ===
"""
    
    for i, stmt in enumerate(statements, 1):
        content += f"\n--- Statement {i} ---\n"
        content += f"Company: {stmt.get('company_name', 'Unknown')}\n"
        content += f"Destination: {stmt.get('destination', 'Unknown')}\n"
        content += f"Location: {stmt.get('location', 'Unknown')}\n"
        content += f"Pages: {stmt.get('number_of_pages', 'Unknown')}\n"
        content += f"Manual Required: {stmt.get('manual_required', False)}\n"
        if stmt.get('similar_to'):
            content += f"Similar To: {stmt.get('similar_to')} ({stmt.get('percentage', 'N/A')})\n"
        if stmt.get('user_answered'):
            content += f"User Answer: {stmt.get('user_answered')}\n"
        content += f"Raw Text Preview: {stmt.get('rest_of_lines', '')[:200]}...\n"
    
    return Response(
        content,
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=REAL_results_{session_id[:8]}.txt'
        }
    )

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
            'created_at': session_data['created_at'],
            'statements_count': len(session_data.get('statements', [])),
            'questions_count': len(session_data.get('questions', []))
        }
    })

if __name__ == '__main__':
    print("🚀 REAL Statement Processing API")
    print("Port: 9000")
    print("Processing: ACTUAL PDF + Excel files")
    print("Health: http://localhost:9000/health")
    print("Uses: statement_processor.py for real processing")
    print("CORS enabled for browser testing")
    
    app.run(
        host='0.0.0.0',
        port=9000,
        debug=True
    )