#!/usr/bin/env python3
"""
Production Flask API for Statement Processing System
Optimized for Railway hosting with memory efficiency and security
"""

import os
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import zipfile
import io

from statement_processor import StatementProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for frontend integration
CORS(app, origins=["*"])

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_TIMEOUT'] = 300  # 5 minutes timeout

ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

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

def cleanup_temp_files(*file_paths):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")

@app.errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = jsonify({'error': error.message, 'status': 'error'})
    response.status_code = error.status_code
    return response

@app.errorhandler(413)
def handle_file_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'error': 'File too large. Maximum size is 50MB.',
        'status': 'error'
    }), 413

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error',
        'status': 'error'
    }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({'status': 'healthy', 'service': 'statement-processor'})

@app.route('/process', methods=['POST'])
def process_statements():
    """Main endpoint for processing statements"""
    pdf_path = None
    excel_path = None
    
    try:
        # Validate request
        if 'pdf' not in request.files or 'excel' not in request.files:
            raise APIError("Both 'pdf' and 'excel' files are required")
        
        pdf_file = request.files['pdf']
        excel_file = request.files['excel']
        
        validate_files(pdf_file, excel_file)
        
        # Create temporary files with secure names
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.pdf',
            prefix='stmt_'
        ) as tmp_pdf:
            pdf_path = tmp_pdf.name
            pdf_file.save(pdf_path)
        
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.xlsx', 
            prefix='dnm_'
        ) as tmp_excel:
            excel_path = tmp_excel.name
            excel_file.save(excel_path)
        
        logger.info(f"Processing files: PDF({os.path.getsize(pdf_path)} bytes), Excel({os.path.getsize(excel_path)} bytes)")
        
        # Process statements
        processor = StatementProcessor(pdf_path, excel_path)
        statements = processor.extract_statements()
        
        # Calculate statistics
        total_statements = len(statements)
        destinations = {}
        manual_required = 0
        
        for stmt in statements:
            dest = stmt.get('destination', 'Unknown')
            destinations[dest] = destinations.get(dest, 0) + 1
            if stmt.get('manual_required', False):
                manual_required += 1
        
        response_data = {
            'status': 'success',
            'total_statements': total_statements,
            'manual_review_required': manual_required,
            'destinations': destinations,
            'statements': statements,
            'processing_info': {
                'dnm_companies_loaded': len(processor.dnm_companies),
                'pdf_pages_processed': len(statements)  # Approximate
            }
        }
        
        logger.info(f"Successfully processed {total_statements} statements")
        return jsonify(response_data)
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Processing failed: {traceback.format_exc()}")
        raise APIError(f"Processing failed: {str(e)}", 500)
    
    finally:
        cleanup_temp_files(pdf_path, excel_path)

@app.route('/process-and-split', methods=['POST'])
def process_and_split():
    """Process statements and return split PDFs as ZIP"""
    pdf_path = None
    excel_path = None
    output_files = []
    
    try:
        # Validate request
        if 'pdf' not in request.files or 'excel' not in request.files:
            raise APIError("Both 'pdf' and 'excel' files are required")
        
        pdf_file = request.files['pdf']
        excel_file = request.files['excel']
        answers = request.form.get('answers', '{}')  # JSON string of manual answers
        
        validate_files(pdf_file, excel_file)
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            pdf_path = tmp_pdf.name
            pdf_file.save(pdf_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_excel:
            excel_path = tmp_excel.name
            excel_file.save(excel_path)
        
        # Process statements
        processor = StatementProcessor(pdf_path, excel_path)
        statements = processor.extract_statements()
        
        # Apply manual answers if provided
        try:
            import json
            manual_answers = json.loads(answers) if answers != '{}' else {}
            
            for stmt in statements:
                company_name = stmt.get('company_name', '')
                if company_name in manual_answers:
                    answer = manual_answers[company_name]
                    if answer == 'yes':
                        stmt['destination'] = 'DNM'
                    stmt['user_answered'] = answer
        except json.JSONDecodeError:
            logger.warning("Invalid manual answers JSON, proceeding without manual answers")
        
        # Create split PDFs
        split_results = processor.create_split_pdfs(statements)
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add split PDF files
            pdf_files = ["DNM.pdf", "Foreign.pdf", "natioSingle.pdf", "natioMulti.pdf"]
            files_added = 0
            
            for pdf_file_name in pdf_files:
                if os.path.exists(pdf_file_name):
                    zip_file.write(pdf_file_name, pdf_file_name)
                    output_files.append(pdf_file_name)
                    files_added += 1
            
            # Add results JSON
            json_filename = processor.save_results(statements)
            if os.path.exists(json_filename):
                zip_file.write(json_filename, json_filename)
                output_files.append(json_filename)
        
        zip_buffer.seek(0)
        
        logger.info(f"Created ZIP with {files_added} PDF files and 1 JSON file")
        
        return send_file(
            io.BytesIO(zip_buffer.read()),
            mimetype='application/zip',
            as_attachment=True,
            download_name='statement_results.zip'
        )
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Processing and split failed: {traceback.format_exc()}")
        raise APIError(f"Processing failed: {str(e)}", 500)
    
    finally:
        cleanup_temp_files(pdf_path, excel_path, *output_files)

@app.route('/questions', methods=['POST'])
def get_questions():
    """Get list of companies requiring manual review"""
    pdf_path = None
    excel_path = None
    
    try:
        if 'pdf' not in request.files or 'excel' not in request.files:
            raise APIError("Both 'pdf' and 'excel' files are required")
        
        pdf_file = request.files['pdf']
        excel_file = request.files['excel']
        
        validate_files(pdf_file, excel_file)
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            pdf_path = tmp_pdf.name
            pdf_file.save(pdf_path)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_excel:
            excel_path = tmp_excel.name
            excel_file.save(excel_path)
        
        # Process statements
        processor = StatementProcessor(pdf_path, excel_path)
        statements = processor.extract_statements()
        
        # Extract questions that need manual review
        questions = []
        for stmt in statements:
            if stmt.get('ask_question', False):
                questions.append({
                    'company_name': stmt.get('company_name', ''),
                    'similar_to': stmt.get('similar_to', ''),
                    'percentage': stmt.get('percentage', ''),
                    'destination': stmt.get('destination', '')
                })
        
        return jsonify({
            'status': 'success',
            'total_questions': len(questions),
            'questions': questions
        })
        
    except APIError:
        raise
    except Exception as e:
        logger.error(f"Questions extraction failed: {traceback.format_exc()}")
        raise APIError(f"Failed to extract questions: {str(e)}", 500)
    
    finally:
        cleanup_temp_files(pdf_path, excel_path)

if __name__ == '__main__':
    # Railway automatically sets PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    
    # Production settings for Railway
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        threaded=True
    )