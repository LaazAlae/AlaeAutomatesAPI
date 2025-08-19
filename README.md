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
- Provides manual review system for uncertain matches
- Outputs organized PDF splits and processing results

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
- PyMuPDF 1.23.5
- openpyxl 3.1.2
- thefuzz 0.19.0

## Deployment

Ready for deployment on Railway, Render, or any WSGI-compatible platform.

See `API_DOCUMENTATION.md` for complete API reference and integration examples.