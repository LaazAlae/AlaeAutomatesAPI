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
from processors.statement_processor import StatementProcessor
from processors.invoice_processor import invoice_processor_bp
from processors.credit_card_batch_processor import credit_card_batch_bp
from company_memory import memory_manager

app = Flask(__name__)

# Register blueprints
app.register_blueprint(invoice_processor_bp, url_prefix='/api/invoice-processor')
app.register_blueprint(credit_card_batch_bp, url_prefix='/api/credit-card-batch')

# Also register credit card batch with alternative URL pattern for compatibility
app.register_blueprint(credit_card_batch_bp, url_prefix='/cc_batch', name='cc_batch_alt')

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
    logger.info(f"️  Session IDs: {list(sessions.keys())}")
    if session_id:
        logger.info(f"[SEARCH] Looking for: {session_id}")
        logger.info(f"[RESULT] Found: {session_id in sessions}")

# Load existing sessions on startup
load_sessions()

# Log startup
logger.info("[STARTUP] AlaeAutomates API v3.0 starting up")
logger.info("[CONFIG] Logging configured for internal debugging")

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
@app.route('/api/statement-processor', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/upload', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/process', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/questions', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/answers', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/download', methods=['OPTIONS'])
@app.route('/api/statement-processor/<session_id>/status', methods=['OPTIONS'])
def handle_options(session_id=None):
    return '', 200

@app.route('/health', methods=['GET'])
def health():
    logger.info("[HEALTH] Health check requested")
    return jsonify({
        'status': 'healthy',
        'service': 'AlaeAutomates API',
        'version': '3.0',
        'port': os.environ.get('PORT', 8000),
        'sessions': len(sessions),
        'timestamp': datetime.now().isoformat(),
        'active_sessions': list(sessions.keys())[:5] if sessions else [],
        'services': ['statement_processing', 'invoice_processing', 'credit_card_batch']
    })

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'AlaeAutomates API',
        'status': 'running',
        'version': '3.0',
        'services': {
            'statement_processing': 'PDF statement analysis with DNM matching',
            'invoice_processing': 'Invoice number extraction and splitting',
            'credit_card_batch': 'Credit card batch automation code generation'
        },
        'endpoints': {
            'health': '/health',
            'statement_api': '/api/statement-processor',
            'invoice_api': '/api/invoice-processor',
            'credit_card_batch_api': '/api/credit-card-batch'
        },
        'documentation': 'See API_DOCUMENTATION.md for complete integration guide'
    })


@app.route('/api/statement-processor', methods=['POST'])
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

@app.route('/api/statement-processor/<session_id>/upload', methods=['POST'])
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

@app.route('/api/statement-processor/<session_id>/process', methods=['POST'])
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
        
        # Build individual questions for similar company matches - MEMORY ENHANCED
        # The StatementProcessor already applied memory decisions during processing!
        # Only companies with unknown similarities will have ask_question=True
        companies_requiring_review = []
        memory_applied_count = 0
        
        for stmt in statements:
            if stmt.get('ask_question', False):
                similar_matches = stmt.get('similar_matches', [])
                if similar_matches:
                    # Create individual questions for each similar company
                    # These are already filtered by the memory system in StatementProcessor
                    individual_questions = []
                    for match in similar_matches:
                        individual_questions.append({
                            'question_id': str(uuid.uuid4()),
                            'dnm_company': match.get('company_name', ''),
                            'similarity_percentage': match.get('percentage', '')
                        })
                    
                    companies_requiring_review.append({
                        'statement_id': str(uuid.uuid4()),
                        'extracted_company': stmt.get('company_name', ''),
                        'current_destination': stmt.get('destination', ''),
                        'page_info': stmt.get('paging', 'page 1 of 1'),
                        'questions': individual_questions
                    })
            elif stmt.get('memory_decision_applied', False):
                # This statement was automatically resolved by memory system
                memory_applied_count += 1
        
        # Calculate total individual questions count
        total_questions = sum(len(company['questions']) for company in companies_requiring_review)
        
        logger.info(f"[MEMORY] Memory system automatically resolved {memory_applied_count} company decisions")
        logger.info(f"[QUESTIONS] {total_questions} questions remaining after memory filtering")
        
        # Store real results
        sessions[session_id]['statements'] = statements
        sessions[session_id]['companies_requiring_review'] = companies_requiring_review
        sessions[session_id]['status'] = 'processed'
        
        # Save updated sessions
        save_sessions()
        
        print(f"[RESULTS] REAL RESULTS: {len(statements)} statements, {len(companies_requiring_review)} companies, {total_questions} individual questions")
        
        return jsonify({
            'status': 'success',
            'message': 'Processing completed',
            'total_statements': len(statements),
            'companies_to_review': len(companies_requiring_review),
            'total_questions': total_questions
        })
        
    except Exception as e:
        print(f"[ERROR] Processing error: {e}")
        sessions[session_id]['status'] = 'error'
        save_sessions()  # Save error state
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/api/statement-processor/<session_id>/questions', methods=['GET'])
def get_questions(session_id):
    load_sessions()  # Load fresh session state
    
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    session_data = sessions[session_id]
    companies_requiring_review = session_data.get('companies_requiring_review', [])
    total_questions = sum(len(company['questions']) for company in companies_requiring_review)
    
    return jsonify({
        'status': 'success',
        'companies_requiring_review': companies_requiring_review,
        'total_questions': total_questions,
        'total_companies_to_review': len(companies_requiring_review),
        'processing_type': 'INDIVIDUAL COMPANY QUESTIONS FROM YOUR PDF'
    })

@app.route('/api/statement-processor/<session_id>/answers', methods=['POST'])
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
    
    # Apply answers to real statements AND store in memory system
    session_data = sessions[session_id]
    statements = session_data.get('statements', [])
    companies_requiring_review = session_data.get('companies_requiring_review', [])
    
    # Store answers in memory system for future use
    stored_count = 0
    try:
        for company in companies_requiring_review:
            extracted_company = company.get('extracted_company', '')
            for question in company.get('questions', []):
                question_id = question.get('question_id', '')
                if question_id in answers:
                    answer = answers[question_id]
                    if answer in ['yes', 'no']:  # Skip 'skip' answers
                        dnm_company = question.get('dnm_company', '')
                        similarity_percentage = float(question.get('similarity_percentage', '0').replace('%', ''))
                        user_decision = (answer == 'yes')
                        
                        # Store in memory system
                        success = memory_manager.store_answer(
                            extracted_company=extracted_company,
                            dnm_company=dnm_company,
                            similarity_percentage=similarity_percentage,
                            user_decision=user_decision,
                            session_id=session_id
                        )
                        if success:
                            stored_count += 1
                            logger.info(f"[MEMORY] Stored: {extracted_company} vs {dnm_company} = {answer}")
        
        logger.info(f"[MEMORY] Successfully stored {stored_count} answers in memory system")
        
    except Exception as e:
        logger.error(f"[MEMORY] Error storing answers in memory: {e}")
    
    # Apply answers to statements (existing logic)
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
        'message': 'Answers applied and stored in memory system!',
        'answers_count': len(answers),
        'stored_in_memory': stored_count
    })

@app.route('/api/statement-processor/<session_id>/download', methods=['GET'])
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
            results_content += f"First Page: {stmt.get('first_page_number', 'Unknown')}\n"
            results_content += f"Page Range: {stmt.get('page_number_in_uploaded_pdf', 'Unknown')}\n"
            # Handle new similar_matches format
            similar_matches = stmt.get('similar_matches', [])
            if similar_matches:
                results_content += f"Similar Matches ({len(similar_matches)} found):\n"
                for i, match in enumerate(similar_matches[:3], 1):  # Show top 3 matches
                    results_content += f"  {i}. {match.get('company_name', 'Unknown')} ({match.get('percentage', 'N/A')})\n"
            if stmt.get('user_answered'):
                results_content += f"User Answer: {stmt.get('user_answered')}\n"
        
        # Create ZIP file in memory
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Create logs folder in ZIP
            zip_file.writestr('logs/', '')  # Create logs directory
            
            # Add results file to logs folder
            zip_file.writestr('logs/processing_results.txt', results_content)
            
            # Add statements data as JSON to logs folder
            # Clean up internal logging data
            for statement in statements:
                if '_extraction_log' in statement:
                    del statement['_extraction_log']
            
            # Create clean JSON structure for API consumers
            data = {
                "dnm_companies": processor.dnm_companies,
                "extracted_statements": statements,
                "total_statements_found": len(statements),
                "processing_timestamp": datetime.now().isoformat()
            }
            
            zip_file.writestr('logs/processing_results.json', json.dumps(data, indent=2, ensure_ascii=False))
            
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
        
        # Create filename in monthlysttmnt(mm)(yyyy) format
        current_date = datetime.now()
        month = current_date.strftime("%m")
        year = current_date.strftime("%Y")
        filename = f'monthlysttmnt{month}{year}.zip'
        
        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating download ZIP: {e}")
        return jsonify({'error': f'Failed to create download package: {str(e)}'}), 500

@app.route('/api/statement-processor/<session_id>/status', methods=['GET'])
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

# ===== COMPANY MEMORY MANAGEMENT API =====

@app.route('/api/company-memory/stats', methods=['GET'])
def get_memory_stats():
    """Get system-wide company memory statistics."""
    try:
        stats = memory_manager.get_system_stats()
        logger.info("[MEMORY] Memory stats requested")
        return jsonify({'status': 'success', **stats})
    except Exception as e:
        logger.error(f"[MEMORY] Error getting stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/companies', methods=['GET'])
def get_all_companies():
    """Get all companies with their equivalence data."""
    try:
        companies = memory_manager.get_all_companies()
        logger.info(f"[MEMORY] Retrieved {len(companies)} companies from memory")
        return jsonify({'status': 'success', 'companies': companies})
    except Exception as e:
        logger.error(f"[MEMORY] Error getting companies: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/update', methods=['POST'])
def update_company_equivalences():
    """Update equivalences for a specific company."""
    try:
        data = request.json
        extracted_company = data.get('extracted_company')
        equivalences = data.get('equivalences', [])
        
        if not extracted_company or not equivalences:
            return jsonify({'status': 'error', 'message': 'Missing extracted_company or equivalences'}), 400
        
        success = memory_manager.update_company_equivalences(extracted_company, equivalences)
        if success:
            logger.info(f"[MEMORY] Updated equivalences for {extracted_company}")
            return jsonify({'status': 'success', 'message': 'Equivalences updated successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to update equivalences'}), 500
            
    except Exception as e:
        logger.error(f"[MEMORY] Error updating equivalences: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/delete/<path:company_name>', methods=['DELETE'])
def delete_company_memory(company_name):
    """Delete all memory data for a specific company."""
    try:
        success = memory_manager.delete_company(company_name)
        if success:
            logger.info(f"[MEMORY] Deleted company: {company_name}")
            return jsonify({'status': 'success', 'message': 'Company deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to delete company'}), 500
            
    except Exception as e:
        logger.error(f"[MEMORY] Error deleting company: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/check', methods=['POST'])
def check_previous_answer():
    """Check if a company pair has been answered before."""
    try:
        data = request.json
        extracted_company = data.get('extracted_company')
        dnm_company = data.get('dnm_company')
        
        if not extracted_company or not dnm_company:
            return jsonify({'status': 'error', 'message': 'Missing company names'}), 400
        
        result = memory_manager.check_previous_answer(extracted_company, dnm_company)
        return jsonify({'status': 'success', **result})
        
    except Exception as e:
        logger.error(f"[MEMORY] Error checking previous answer: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/store', methods=['POST'])
def store_company_answer():
    """Store a user's answer about company equivalence."""
    try:
        data = request.json
        extracted_company = data.get('extracted_company')
        dnm_company = data.get('dnm_company')
        similarity_percentage = data.get('similarity_percentage')
        user_decision = data.get('user_decision')
        
        # Optional fields
        session_id = data.get('session_id')
        statement_id = data.get('statement_id')
        page_info = data.get('page_info')
        destination = data.get('destination')
        
        if not all([extracted_company, dnm_company, similarity_percentage is not None, user_decision is not None]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        success = memory_manager.store_answer(
            extracted_company, dnm_company, similarity_percentage, user_decision,
            session_id, statement_id, page_info, destination
        )
        
        if success:
            logger.info(f"[MEMORY] Stored answer: {extracted_company} vs {dnm_company} = {user_decision}")
            return jsonify({'status': 'success', 'message': 'Answer stored successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to store answer'}), 500
            
    except Exception as e:
        logger.error(f"[MEMORY] Error storing answer: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/export', methods=['GET'])
def export_memory_data():
    """Export all memory data for backup."""
    try:
        data = memory_manager.export_data()
        logger.info(f"[MEMORY] Exported {data['total_records']} records")
        
        return Response(
            json.dumps(data, indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=company_memory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
    except Exception as e:
        logger.error(f"[MEMORY] Error exporting data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/company-memory/import', methods=['POST'])
def import_memory_data():
    """Import memory data from backup."""
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        data = json.loads(file.read().decode('utf-8'))
        success = memory_manager.import_data(data)
        
        if success:
            logger.info(f"[MEMORY] Imported {len(data.get('equivalences', []))} records")
            return jsonify({'status': 'success', 'message': 'Data imported successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to import data'}), 500
            
    except Exception as e:
        logger.error(f"[MEMORY] Error importing data: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Add OPTIONS handlers for memory endpoints
@app.route('/api/company-memory/<path:endpoint>', methods=['OPTIONS'])
def handle_memory_options(endpoint):
    return '', 200

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
    print("AlaeAutomates API v3.0 - Endpoints:")
    print("  / - API info and service overview")
    print("  /health - Health status")
    print("  /api/statement-processor/* - Statement processing API")
    print("  /api/invoice-processor/* - Invoice processing API") 
    print("  /api/credit-card-batch/* - Credit card batch automation API")
    print("=" * 60)
    print("This is the BACKEND API ONLY")
    print("For frontend demo, run: python frontend_demo.py")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False  # Turn off debug in production
    )