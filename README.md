# Document Processing API

A professional Flask-based API for processing PDF documents with two main services:

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

### Installation
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
python app.py
```

### Access the Application
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/health`
- Statement Processing: `http://localhost:8000/monthly-statements`
- Invoice Processing: `http://localhost:8000/invoice-processor`

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