# Document Processing API

A professional Flask-based backend API for processing PDF documents with two main services. The backend runs on Railway, and the frontend demo runs locally for development and testing.

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
- Outputs organized PDF splits and processing logs

### Invoice Processing  
- Extracts invoice numbers from PDF files using pattern recognition
- Splits multi-invoice PDFs into separate files by invoice number
- Packages results in downloadable ZIP files

## Quick Start

### Backend Setup (Deploy to Railway)
1. Deploy `app.py` to Railway
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
python app.py

# Frontend demo (in another terminal)
API_URL=https://your-railway-app.railway.app python frontend_demo.py
```

## File Structure

```
app/
├── statement_processor.py    # Statement processing logic
└── invoice_processor.py      # Invoice processing logic
templates/
├── index.html               # Homepage
├── monthly_statements.html  # Statement processing interface  
└── invoice_processor.html   # Invoice processing interface
static/
└── css/
    └── styles.css           # Application styles
```

## API Endpoints

### Statement Processing
- `POST /api/v1/session` - Create processing session
- `POST /api/v1/session/{id}/upload` - Upload PDF and Excel files
- `POST /api/v1/session/{id}/process` - Process uploaded files
- `GET /api/v1/session/{id}/questions` - Get manual review questions
- `POST /api/v1/session/{id}/answers` - Submit manual review answers
- `GET /api/v1/session/{id}/download` - Download processing results

### Invoice Processing
- `POST /invoice-processor/` - Upload and process invoice PDF
- `GET /invoice-processor/downloads/{filename}` - Download separated invoices
- `POST /invoice-processor/clear_results` - Clear processing results

## Requirements

- Python 3.8+
- Flask 2.3.3
- PyMuPDF 1.23.5
- pandas 2.1.1
- openpyxl 3.1.2
- thefuzz 0.19.0

## Deployment

Ready for deployment on Railway, Render, or any WSGI-compatible platform.

See `API_DOCUMENTATION.md` for complete API reference and integration examples.