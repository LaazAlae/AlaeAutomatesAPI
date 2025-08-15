#!/usr/bin/env python3
"""
Enterprise Statement Processing API with WebSocket Support
Professional workflow implementation for real-time processing
"""

import os
import tempfile
import traceback
import uuid
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import zipfile
import io
import threading
from datetime import datetime, timedelta

from statement_processor import StatementProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with WebSocket support
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'production-secret-key-change-me')

# Configure CORS for frontend integration
CORS(app, origins=["*"])

# Initialize SocketIO with production settings
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25
)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_TIMEOUT'] = 300  # 5 minutes timeout

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

# In-memory session storage (use Redis in production)
class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.cleanup_interval = 3600  # 1 hour
        self._start_cleanup_thread()
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            'created_at': datetime.now(),
            'status': 'created',
            'files': {},
            'statements': [],
            'questions': [],
            'answers': {},
            'results': None
        }
        logger.info(f"Created session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict):
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]['updated_at'] = datetime.now()
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            # Cleanup temporary files
            session_data = self.sessions[session_id]
            for file_path in session_data.get('files', {}).values():
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup file {file_path}: {e}")
            
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def _cleanup_expired_sessions(self):
        """Remove sessions older than 2 hours"""
        while True:
            try:
                now = datetime.now()
                expired_sessions = []
                
                for session_id, session_data in self.sessions.items():
                    created_at = session_data.get('created_at', now)
                    if now - created_at > timedelta(hours=2):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    self.delete_session(session_id)
                
                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
                    
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
            
            time.sleep(self.cleanup_interval)
    
    def _start_cleanup_thread(self):
        cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()

session_manager = SessionManager()

class APIError(Exception):
    """Custom API exception class"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_files(pdf_file, excel_file) -> None:
    """Validate uploaded files"""
    if not pdf_file or pdf_file.filename == '':
        raise APIError("No PDF file provided", 400)
    
    if not excel_file or excel_file.filename == '':
        raise APIError("No Excel file provided", 400)
    
    if not allowed_file(pdf_file.filename):
        raise APIError("Invalid PDF file format", 400)
    
    if not allowed_file(excel_file.filename):
        raise APIError("Invalid Excel file format", 400)

def emit_progress(session_id: str, message: str, progress: int, data: Dict = None):
    """Emit progress update via WebSocket"""
    socketio.emit('progress_update', {
        'session_id': session_id,
        'message': message,
        'progress': progress,
        'timestamp': datetime.now().isoformat(),
        'data': data or {}
    }, room=session_id)

# Error handlers
@app.errorhandler(APIError)
def handle_api_error(error):
    response = jsonify({'error': error.message, 'status': 'error'})
    response.status_code = error.status_code
    return response

@app.errorhandler(413)
def handle_file_too_large(error):
    return jsonify({
        'error': 'File too large. Maximum size is 50MB.',
        'status': 'error'
    }), 413

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.error(f"Unexpected error: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'sid': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    session_id = data.get('session_id')
    if session_id and session_manager.get_session(session_id):
        join_room(session_id)
        emit('joined_session', {'session_id': session_id, 'status': 'joined'})
    else:
        emit('error', {'message': 'Invalid session ID'})

@socketio.on('leave_session')
def handle_leave_session(data):
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        emit('left_session', {'session_id': session_id, 'status': 'left'})

# REST API Endpoints

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy', 
        'service': 'statement-processor-enterprise',
        'websocket': True,
        'sessions': len(session_manager.sessions)
    })

@app.route('/api/v1/session', methods=['POST'])
def create_session():
    """Create a new processing session"""
    session_id = session_manager.create_session()
    return jsonify({
        'status': 'success',
        'session_id': session_id,
        'expires_in': 7200  # 2 hours
    })

@app.route('/api/v1/session/<session_id>/upload', methods=['POST'])
def upload_files(session_id: str):
    """Upload files to a session"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise APIError("Invalid session ID", 404)
        
        if 'pdf' not in request.files or 'excel' not in request.files:
            raise APIError("Both 'pdf' and 'excel' files are required")
        
        pdf_file = request.files['pdf']
        excel_file = request.files['excel']
        
        validate_files(pdf_file, excel_file)
        
        # Save files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='stmt_') as tmp_pdf:
            pdf_path = tmp_pdf.name
            pdf_file.save(pdf_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', prefix='dnm_') as tmp_excel:
            excel_path = tmp_excel.name
            excel_file.save(excel_path)
        
        # Update session
        session_manager.update_session(session_id, {
            'files': {'pdf': pdf_path, 'excel': excel_path},
            'status': 'files_uploaded'
        })
        
        logger.info(f"Files uploaded for session {session_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Files uploaded successfully',
            'files': {
                'pdf': {'name': pdf_file.filename, 'size': os.path.getsize(pdf_path)},
                'excel': {'name': excel_file.filename, 'size': os.path.getsize(excel_path)}
            }
        })
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {traceback.format_exc()}")
        raise APIError(f"Upload failed: {str(e)}", 500)

@app.route('/api/v1/session/<session_id>/process', methods=['POST'])
def start_processing(session_id: str):
    """Start processing uploaded files"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise APIError("Invalid session ID", 404)
        
        if session_data['status'] != 'files_uploaded':
            raise APIError("Files not uploaded or already processed", 400)
        
        # Start processing in background thread
        def process_statements():
            try:
                emit_progress(session_id, "Starting statement extraction...", 10)
                
                files = session_data['files']
                processor = StatementProcessor(files['pdf'], files['excel'])
                
                emit_progress(session_id, "Extracting statements from PDF...", 30)
                statements = processor.extract_statements()
                
                emit_progress(session_id, "Analyzing statements...", 60)
                
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
                
                # Update session with results
                session_manager.update_session(session_id, {
                    'statements': statements,
                    'questions': questions,
                    'status': 'questions_ready' if questions else 'ready_for_output'
                })
                
                if questions:
                    emit_progress(session_id, "Manual review required", 100, {
                        'questions_count': len(questions),
                        'requires_manual_review': True
                    })
                    
                    socketio.emit('questions_ready', {
                        'session_id': session_id,
                        'questions': questions,
                        'total_statements': len(statements)
                    }, room=session_id)
                else:
                    emit_progress(session_id, "Processing complete", 100, {
                        'requires_manual_review': False
                    })
                    
                    socketio.emit('processing_complete', {
                        'session_id': session_id,
                        'total_statements': len(statements),
                        'requires_manual_review': False
                    }, room=session_id)
                
            except Exception as e:
                logger.error(f"Processing failed for session {session_id}: {traceback.format_exc()}")
                session_manager.update_session(session_id, {'status': 'error'})
                socketio.emit('processing_error', {
                    'session_id': session_id,
                    'error': str(e)
                }, room=session_id)
        
        # Start processing thread
        processing_thread = threading.Thread(target=process_statements)
        processing_thread.start()
        
        session_manager.update_session(session_id, {'status': 'processing'})
        
        return jsonify({
            'status': 'success',
            'message': 'Processing started',
            'session_id': session_id
        })
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Process start failed: {traceback.format_exc()}")
        raise APIError(f"Failed to start processing: {str(e)}", 500)

@app.route('/api/v1/session/<session_id>/questions', methods=['GET'])
def get_questions(session_id: str):
    """Get questions for manual review"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise APIError("Invalid session ID", 404)
    
    if session_data['status'] != 'questions_ready':
        raise APIError("Questions not ready", 400)
    
    return jsonify({
        'status': 'success',
        'questions': session_data['questions'],
        'total_statements': len(session_data['statements'])
    })

@app.route('/api/v1/session/<session_id>/answers', methods=['POST'])
def submit_answers(session_id: str):
    """Submit answers for manual review questions"""
    try:
        session_data = session_manager.get_session(session_id)
        if not session_data:
            raise APIError("Invalid session ID", 404)
        
        if session_data['status'] != 'questions_ready':
            raise APIError("No questions waiting for answers", 400)
        
        answers = request.json.get('answers', {})
        
        # Start final processing in background
        def finalize_processing():
            try:
                emit_progress(session_id, "Applying manual review answers...", 10)
                
                statements = session_data['statements']
                questions = session_data['questions']
                
                # Apply answers to statements
                question_map = {q['company_name']: q for q in questions}
                
                for stmt in statements:
                    company_name = stmt.get('company_name', '')
                    if company_name in answers:
                        answer = answers[company_name]
                        if answer == 'yes':
                            stmt['destination'] = 'DNM'
                        stmt['user_answered'] = answer
                
                emit_progress(session_id, "Creating split PDFs...", 50)
                
                # Create final output
                files = session_data['files']
                processor = StatementProcessor(files['pdf'], files['excel'])
                
                # Create split PDFs
                split_results = processor.create_split_pdfs(statements)
                
                # Save results JSON
                json_filename = processor.save_results(statements)
                
                emit_progress(session_id, "Preparing download...", 90)
                
                # Create ZIP file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add PDF files
                    pdf_files = ["DNM.pdf", "Foreign.pdf", "natioSingle.pdf", "natioMulti.pdf"]
                    files_added = []
                    
                    for pdf_file in pdf_files:
                        if os.path.exists(pdf_file):
                            zip_file.write(pdf_file, pdf_file)
                            files_added.append(pdf_file)
                    
                    # Add JSON results
                    if os.path.exists(json_filename):
                        zip_file.write(json_filename, json_filename)
                        files_added.append(json_filename)
                
                zip_buffer.seek(0)
                
                # Store results in session
                session_manager.update_session(session_id, {
                    'status': 'completed',
                    'results': {
                        'zip_data': zip_buffer.getvalue(),
                        'files_created': files_added,
                        'split_results': split_results
                    }
                })
                
                emit_progress(session_id, "Processing complete!", 100)
                
                socketio.emit('processing_complete', {
                    'session_id': session_id,
                    'files_created': files_added,
                    'download_ready': True
                }, room=session_id)
                
                # Cleanup temporary files
                for pdf_file in pdf_files + [json_filename]:
                    try:
                        if os.path.exists(pdf_file):
                            os.remove(pdf_file)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup {pdf_file}: {e}")
                
            except Exception as e:
                logger.error(f"Final processing failed for session {session_id}: {traceback.format_exc()}")
                session_manager.update_session(session_id, {'status': 'error'})
                socketio.emit('processing_error', {
                    'session_id': session_id,
                    'error': str(e)
                }, room=session_id)
        
        # Start final processing
        processing_thread = threading.Thread(target=finalize_processing)
        processing_thread.start()
        
        session_manager.update_session(session_id, {
            'answers': answers,
            'status': 'finalizing'
        })
        
        return jsonify({
            'status': 'success',
            'message': 'Answers submitted, finalizing processing...'
        })
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Answer submission failed: {traceback.format_exc()}")
        raise APIError(f"Failed to submit answers: {str(e)}", 500)

@app.route('/api/v1/session/<session_id>/download', methods=['GET'])
def download_results(session_id: str):
    """Download processed results"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise APIError("Invalid session ID", 404)
    
    if session_data['status'] != 'completed':
        raise APIError("Processing not completed", 400)
    
    results = session_data.get('results')
    if not results or 'zip_data' not in results:
        raise APIError("Results not available", 404)
    
    return send_file(
        io.BytesIO(results['zip_data']),
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'statement_results_{session_id[:8]}.zip'
    )

@app.route('/api/v1/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id: str):
    """Get current session status"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise APIError("Invalid session ID", 404)
    
    # Remove sensitive data
    safe_data = {
        'session_id': session_id,
        'status': session_data['status'],
        'created_at': session_data['created_at'].isoformat(),
        'has_questions': len(session_data.get('questions', [])) > 0,
        'total_statements': len(session_data.get('statements', [])),
        'questions_count': len(session_data.get('questions', []))
    }
    
    return jsonify({
        'status': 'success',
        'session': safe_data
    })

@app.route('/api/v1/session/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete a session and cleanup resources"""
    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise APIError("Invalid session ID", 404)
    
    session_manager.delete_session(session_id)
    
    return jsonify({
        'status': 'success',
        'message': 'Session deleted successfully'
    })

if __name__ == '__main__':
    # Railway automatically sets PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    
    # Production settings for Railway with WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False
    )