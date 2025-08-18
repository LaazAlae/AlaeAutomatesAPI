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
import logging
import sys
from datetime import datetime
from app.statement_processor import StatementProcessor
from app.invoice_processor import invoice_processor_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(invoice_processor_bp, url_prefix='/invoice-processor')

# Configure enterprise-grade logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Simple persistent storage for Railway multi-worker support
import pickle
import fcntl

sessions = {}
SESSION_FILE = '/tmp/sessions.pkl'

def load_sessions():
    """Load sessions from persistent storage"""
    global sessions
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, 'rb') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                sessions = pickle.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            logger.info(f"[STORAGE] Loaded {len(sessions)} sessions from persistent storage")
        else:
            sessions = {}
            logger.info("[STORAGE] No persistent sessions found, starting fresh")
    except Exception as e:
        logger.error(f"[ERROR] Failed to load sessions: {e}")
        sessions = {}

def save_sessions():
    """Save sessions to persistent storage"""
    try:
        with open(SESSION_FILE, 'wb') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            pickle.dump(sessions, f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        logger.debug(f"[STORAGE] Saved {len(sessions)} sessions to persistent storage")
    except Exception as e:
        logger.error(f"[ERROR] Failed to save sessions: {e}")

def debug_sessions(action, session_id=None):
    """Debug helper to track session state"""
    logger.info(f"[DEBUG] SESSION DEBUG - {action}")
    logger.info(f"[INFO] Total sessions: {len(sessions)}")
    logger.info(f"🗂️  Session IDs: {list(sessions.keys())}")
    if session_id:
        logger.info(f"[SEARCH] Looking for: {session_id}")
        logger.info(f"[RESULT] Found: {session_id in sessions}")

# Load existing sessions on startup
load_sessions()

# Log startup
logger.info("[STARTUP] Statement Processing API starting up")
logger.info("[CONFIG] Logging configured - Check api.log for detailed logs")

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.before_request
def log_request():
    logger.info(f"[REQUEST] {request.method} {request.path} from {request.remote_addr}")
    logger.info(f"[REQUEST] Content-Type: {request.content_type}")
    if request.is_json and request.json:
        logger.info(f"[REQUEST] Request body: {json.dumps(request.json, indent=2)}")
    elif request.method == 'POST' and request.content_type and 'multipart' in request.content_type:
        logger.info(f"[REQUEST] Multipart form data with files: {list(request.files.keys())}")

# Add OPTIONS handler for CORS preflight
@app.route('/api/v1/session', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/upload', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/process', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/questions', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/answers', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/download', methods=['OPTIONS'])
@app.route('/api/v1/session/<session_id>/status', methods=['OPTIONS'])
def handle_options(session_id=None):
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    logger.info("[HEALTH] Health check requested")
    return jsonify({
        'status': 'healthy',
        'service': 'REAL Statement Processing API',
        'processing': 'ACTUAL PDF PROCESSING',
        'port': os.environ.get('PORT', 8000),
        'sessions': len(sessions),
        'timestamp': datetime.now().isoformat(),
        'active_sessions': list(sessions.keys())[:5] if sessions else []
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Document Processing API',
        'status': 'running',
        'version': '2.0',
        'services': {
            'statement_processing': 'PDF statement analysis with DNM matching',
            'invoice_processing': 'Invoice number extraction and splitting'
        },
        'endpoints': {
            'health': '/health',
            'logs': '/logs',
            'statement_api': '/api/v1/session',
            'invoice_api': '/invoice-processor'
        },
        'documentation': 'See API_DOCUMENTATION.md for complete integration guide'
    })

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get recent API logs for debugging"""
    try:
        # Read last 100 lines of log file
        with open('api.log', 'r') as f:
            lines = f.readlines()
            recent_logs = lines[-100:] if len(lines) > 100 else lines
        
        return jsonify({
            'status': 'success',
            'logs': recent_logs,
            'total_lines': len(lines),
            'showing': len(recent_logs)
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'success',
            'logs': ['Log file not found yet - API just started'],
            'total_lines': 0,
            'showing': 0
        })
    except Exception as e:
        logger.error(f"[ERROR] Failed to read logs: {str(e)}")
        return jsonify({'error': f'Failed to read logs: {str(e)}'}), 500

@app.route('/api/v1/session', methods=['POST'])
def create_session():
    # Load fresh sessions to get latest state
    load_sessions()
    
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        'status': 'created',
        'created_at': datetime.now().isoformat(),
        'files': {},
        'statements': [],
        'questions': []
    }
    
    # Save sessions persistently
    save_sessions()
    
    logger.info(f"[SESSION] Session created: {session_id}")
    logger.info(f"[INFO] Total active sessions: {len(sessions)}")
    debug_sessions("AFTER_CREATE", session_id)
    
    return jsonify({
        'status': 'success',
        'session_id': session_id
    })

@app.route('/api/v1/session/<session_id>/upload', methods=['POST'])
def upload_files(session_id):
    # Load fresh sessions to get latest state from other workers
    load_sessions()
    
    logger.info(f"[UPLOAD] Upload request for session: {session_id}")
    debug_sessions("BEFORE_UPLOAD_CHECK", session_id)
    
    if session_id not in sessions:
        logger.error(f"[ERROR] Session not found: {session_id}")
        debug_sessions("SESSION_NOT_FOUND", session_id)
        return jsonify({'error': 'Session not found', 'session_id': session_id, 'available_sessions': list(sessions.keys())}), 404
    
    if 'pdf' not in request.files or 'excel' not in request.files:
        logger.error(f"[ERROR] Missing files. Available: {list(request.files.keys())}")
        return jsonify({'error': 'Both PDF and Excel files required', 'received_files': list(request.files.keys())}), 400
    
    pdf_file = request.files['pdf']
    excel_file = request.files['excel']
    
    logger.info(f"[FILES] Received files: PDF={pdf_file.filename}, Excel={excel_file.filename}")
    
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
        
        # Save updated sessions
        save_sessions()
        
        logger.info(f"[SUCCESS] Files uploaded successfully for session {session_id}")
        logger.info(f"[INFO] PDF size: {os.path.getsize(pdf_path)} bytes, Excel size: {os.path.getsize(excel_path)} bytes")
        
        return jsonify({
            'status': 'success',
            'message': 'Real files uploaded and saved',
            'session_id': session_id,
            'files': {
                'pdf': {'name': pdf_file.filename, 'size': os.path.getsize(pdf_path)},
                'excel': {'name': excel_file.filename, 'size': os.path.getsize(excel_path)}
            }
        })
        
    except Exception as e:
        logger.error(f"[ERROR] File upload failed for session {session_id}: {str(e)}")
        return jsonify({'error': f'File upload failed: {str(e)}', 'session_id': session_id}), 500

@app.route('/api/v1/session/<session_id>/process', methods=['POST'])
def process_statements(session_id):
    load_sessions()  # Load fresh session state
    
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
        
        print(f"[PROCESS] REAL PROCESSING: {files['pdf_name']} + {files['excel_name']}")
        
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
        
        # Save updated sessions
        save_sessions()
        
        print(f"[RESULTS] REAL RESULTS: {len(statements)} statements, {len(questions)} questions")
        
        return jsonify({
            'status': 'success',
            'message': 'REAL processing completed!',
            'total_statements': len(statements),
            'questions_needed': len(questions),
            'processing_type': 'ACTUAL PDF PROCESSING'
        })
        
    except Exception as e:
        print(f"[ERROR] Processing error: {e}")
        sessions[session_id]['status'] = 'error'
        save_sessions()  # Save error state
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/v1/session/<session_id>/questions', methods=['GET'])
def get_questions(session_id):
    load_sessions()  # Load fresh session state
    
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
    load_sessions()  # Load fresh session state
    logger.info(f"[ANSWERS] Answers submission for session: {session_id}")
    
    if session_id not in sessions:
        logger.error(f"[ERROR] Session not found for answers: {session_id}")
        return jsonify({'error': 'Session not found'}), 404
    
    # Handle JSON payload safely
    answers = {}
    if request.is_json and request.json:
        answers = request.json.get('answers', {})
    elif request.form:
        # Fallback to form data if not JSON
        answers = dict(request.form)
    
    logger.info(f"[INFO] Received {len(answers)} answers for session {session_id}")
    
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
    
    # Save updated sessions
    save_sessions()
    
    return jsonify({
        'status': 'success',
        'message': 'Real answers applied to real statements!',
        'answers_count': len(answers)
    })

@app.route('/api/v1/session/<session_id>/download', methods=['GET'])
def download_results(session_id):
    load_sessions()  # Load fresh session state
    
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    statements = session_data.get('statements', [])
    
    if not statements:
        return jsonify({'error': 'No processed statements found'}), 400
    
    try:
        import zipfile
        from io import BytesIO
        
        # Get file paths from session
        pdf_path = session_data['files']['pdf_path']
        excel_path = session_data['files']['excel_path']
        
        # Initialize processor and create split PDFs
        processor = StatementProcessor(pdf_path, excel_path)
        
        # Create split PDFs
        split_results = processor.create_split_pdfs(statements)
        
        # Create detailed results file content
        results_content = f"""STATEMENT PROCESSING RESULTS
Session ID: {session_id}
Processed: {datetime.now().isoformat()}

=== PROCESSING SUMMARY ===
Total Statements Found: {len(statements)}
Questions Required: {len(session_data.get('questions', []))}
Status: {session_data['status']}

=== FILES PROCESSED ===
PDF: {session_data['files']['pdf_name']}
Excel: {session_data['files']['excel_name']}

=== SPLIT RESULTS ===
"""
        
        for dest, count in split_results.items():
            results_content += f"{dest}: {count} pages\n"
        
        results_content += "\n=== DETAILED STATEMENT LIST ===\n"
        
        for i, stmt in enumerate(statements, 1):
            results_content += f"\n--- Statement {i} ---\n"
            results_content += f"Company: {stmt.get('company_name', 'Unknown')}\n"
            results_content += f"Destination: {stmt.get('destination', 'Unknown')}\n"
            results_content += f"Location: {stmt.get('location', 'Unknown')}\n"
            results_content += f"Pages: {stmt.get('number_of_pages', 'Unknown')}\n"
            if stmt.get('similar_to'):
                results_content += f"Similar To: {stmt.get('similar_to')} ({stmt.get('percentage', 'N/A')})\n"
            if stmt.get('user_answered'):
                results_content += f"User Answer: {stmt.get('user_answered')}\n"
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create logs folder in ZIP
            zip_file.writestr('logs/', '')  # Create logs directory
            
            # Add results file to logs folder
            zip_file.writestr('logs/results.txt', results_content)
            
            # Add statements data as JSON to logs folder
            zip_file.writestr('logs/statements.json', json.dumps(statements, indent=2))
            
            # Add split PDF files in root directory
            pdf_files = {
                "DNM": "DNM.pdf",
                "Foreign": "Foreign.pdf", 
                "Natio Single": "natioSingle.pdf",
                "Natio Multi": "natioMulti.pdf"
            }
            
            for dest, filename in pdf_files.items():
                if os.path.exists(filename) and dest in split_results:
                    zip_file.write(filename, filename)
                    # Clean up temporary files
                    try:
                        os.remove(filename)
                    except:
                        pass
        
        zip_buffer.seek(0)
        
        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename=statements_results_{session_id[:8]}.zip'
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating download ZIP: {e}")
        return jsonify({'error': f'Failed to create download package: {str(e)}'}), 500

@app.route('/api/v1/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    load_sessions()  # Load fresh session state
    
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

# For Gunicorn deployment
def create_app():
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print("=" * 60)
    print("DOCUMENT PROCESSING API - BACKEND ONLY")
    print("=" * 60)
    print(f"API URL: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/health")
    print("=" * 60)
    print("API Endpoints:")
    print("  / - API info and service overview")
    print("  /health - Health status")
    print("  /logs - System logs")
    print("  /api/v1/session/* - Statement processing API")
    print("  /invoice-processor/* - Invoice processing API")
    print("=" * 60)
    print("This is the BACKEND API ONLY")
    print("For frontend demo, run: python frontend_demo.py")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Turn off debug in production
    )