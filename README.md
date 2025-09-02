# AlaeAutomates API

A professional Flask-based backend API for processing PDF documents and Excel automation with three main services. The backend runs on Railway, and the frontend demo runs locally for development and testing.

## Architecture

### Backend (Railway Hosted)
- Pure API endpoints, no frontend templates
- Handles PDF processing and file operations
- CORS enabled for frontend integration

### Frontend (Local Development)
- Separate Flask app for demonstrating API usage
- HTML templates and JavaScript clients
- Connects to Railway-hosted backend API

## Services

### Statement Processing
- Processes PDF bank statements and matches company names against Do Not Mail (DNM) Excel lists
- Features industry-standard fuzzy matching with comprehensive similarity analysis
- Provides manual review system for uncertain matches with all potential matches displayed
- Outputs organized PDF splits and processing results

#### Advanced Company Name Matching System
The statement processor includes one of the most sophisticated company name matching systems available, designed to provide maximum accuracy while maintaining high performance:

**Multi-Algorithm Fuzzy Matching**
- Uses Python's `difflib.SequenceMatcher` with Ratcliff-Obershelp algorithm for industry-standard text similarity
- Compares against ALL companies in the DNM list, not just the first match found
- Returns all matches above 60% threshold, sorted by similarity score
- Provides exact percentage scores for each potential match

**Intelligent Text Preprocessing**
- Removes business suffixes (Inc, LLC, Corp, Ltd, etc.) for normalized comparison
- Handles punctuation, spacing, and capitalization variations
- Strips common business artifacts like "ATTN:", "C/O", suite numbers, and addresses
- Normalizes ampersands, "and", and other connector words

**Enhanced Multi-Line Company Name Extraction**
- Detects company name boundaries using address pattern recognition
- Combines multiple lines until address patterns are encountered
- Handles company names split across 2-4 lines in PDF text
- Uses industry-standard address detection patterns (street addresses, PO boxes, ZIP codes)

**Comprehensive Match Analysis**
- Exact match detection (100% accuracy)
- Fuzzy matching with configurable thresholds (default 60%+)
- Multiple similarity candidates ranked by confidence
- Automatic high-confidence matching (90%+ similarity)

**Why This Approach is Superior**
1. **Complete Coverage**: Compares against ALL companies, ensuring no potential matches are missed
2. **Industry Standards**: Uses proven algorithms employed by major document processing systems
3. **Configurable Accuracy**: 60% threshold provides optimal balance of precision and recall
4. **Transparent Results**: Shows all potential matches with exact percentages for informed decision-making
5. **Performance Optimized**: O(n) complexity with pre-normalized company mappings for fast lookups
6. **Real-World Tested**: Handles variations in company name formatting commonly found in financial documents

This matching system provides enterprise-grade accuracy for financial document processing, ensuring regulatory compliance and operational efficiency.

### Invoice Processing  
- Extracts invoice numbers from PDF files using pattern recognition
- Splits multi-invoice PDFs into separate files by invoice number
- Packages results in downloadable ZIP files

### Credit Card Batch Automation
- Processes Excel files with credit card data 
- Generates enhanced JavaScript automation code for Legacy Edge browsers
- Includes safety checks, element visibility verification, and error handling

## Quick Start

### Backend Setup (Deploy to Railway)
1. Deploy `main.py` to Railway
2. Set environment variables if needed
3. Your API will be available at `https://your-app.railway.app`

### Frontend Demo (Local Development)
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start frontend demo:
```bash
python start_frontend.py
```

3. Enter your Railway API URL when prompted

4. Access the demo at `http://localhost:3000`

### Manual Setup
```bash
# Backend only (API endpoints)
python main.py

# Frontend demo (in another terminal)
API_URL=https://your-railway-app.railway.app python frontend_demo.py
```

## File Structure

```
main.py                      # Backend API (Railway deployment)
frontend_demo.py             # Frontend demo server (local only)
start_frontend.py            # Quick start script
processors/
├── statement_processor.py       # Statement processing logic
├── invoice_processor.py         # Invoice processing logic
└── credit_card_batch_processor.py # Credit card batch automation
templates/
├── index.html                   # Homepage
├── monthly_statements.html      # Statement processing interface  
├── invoice_separator.html       # Invoice processing interface
└── credit_card_batch.html       # Credit card batch automation
static/
├── css/
│   └── styles.css          # Application styles
└── js/
    └── api-client.js       # JavaScript API client
```

## API Endpoints

### Statement Processing
- `POST /api/statement-processor` - Create processing session
- `POST /api/statement-processor/{id}/upload` - Upload PDF and Excel files
- `POST /api/statement-processor/{id}/process` - Process uploaded files
- `GET /api/statement-processor/{id}/questions` - Get manual review questions
- `POST /api/statement-processor/{id}/answers` - Submit manual review answers
- `GET /api/statement-processor/{id}/download` - Download processing results

### Invoice Processing
- `POST /api/invoice-processor` - Upload and process invoice PDF
- `GET /api/invoice-processor/downloads/{filename}` - Download separated invoices
- `POST /api/invoice-processor/clear_results` - Clear processing results

### Credit Card Batch Processing
- `POST /api/credit-card-batch` - Process Excel file and generate automation code

## Requirements

- Python 3.8+
- Flask 2.3.3
- PyMuPDF 1.23.5 (for PDF text extraction)
- openpyxl 3.1.2 (for Excel processing)
- PyPDF2 (for PDF splitting operations)
- difflib (built-in, for fuzzy string matching)

## Deployment

Ready for deployment on Railway, Render, or any WSGI-compatible platform.

See `API_DOCUMENTATION.md` for complete API reference and integration examples.