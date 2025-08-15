# Statement Processing API

Production-ready Flask API for processing financial statements from PDFs. Optimized for Railway deployment with O(n) performance.

## Features

- **O(n) Performance**: Linear time complexity for optimal processing speed
- **Memory Efficient**: Optimized for Railway's free tier (512MB RAM)
- **Production Ready**: Comprehensive error handling, logging, and security
- **Railway Optimized**: Configured for seamless Railway deployment

## API Endpoints

### `GET /health`
Health check endpoint for Railway monitoring.

### `POST /process`
Process statements and return analysis in JSON format.
- **Files**: `pdf` (PDF file), `excel` (Excel DNM list)
- **Response**: JSON with statements, statistics, and processing info

### `POST /process-and-split`
Process statements and return split PDFs as ZIP file.
- **Files**: `pdf` (PDF file), `excel` (Excel DNM list)
- **Form Data**: `answers` (JSON string of manual review answers)
- **Response**: ZIP file containing split PDFs and JSON results

### `POST /questions`
Get list of companies requiring manual review.
- **Files**: `pdf` (PDF file), `excel` (Excel DNM list)
- **Response**: JSON with questions for manual review

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Test the API
python test_api.py
```

## Railway Deployment

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Python app
3. Set environment variables if needed
4. Deploy automatically on push to main branch

### Railway Configuration
- **Build**: Uses Nixpacks with requirements.txt
- **Start Command**: `gunicorn` with optimized settings
- **Health Check**: `/health` endpoint
- **Memory**: Optimized for 512MB limit

## File Structure

```
├── app.py              # Main Flask application
├── statement_processor.py  # Core processing logic
├── requirements.txt    # Python dependencies
├── Procfile           # Railway/Heroku process file
├── railway.json       # Railway configuration
├── test_api.py        # API testing script
└── README.md          # This file
```

## Performance Optimizations

- **O(n) Algorithm**: Linear time complexity
- **Memory Management**: Garbage collection and efficient data structures
- **Streaming**: Process large files without loading everything into memory
- **Caching**: Avoid reprocessing pages
- **Production Server**: Gunicorn with optimized worker settings

## Security Features

- File type validation
- Secure filename handling
- Request size limits (50MB)
- Timeout protection (5 minutes)
- Error sanitization
- CORS configuration

## Railway Free Tier Compatibility

- Memory usage under 512MB
- CPU optimization for shared resources
- Efficient dependency management
- Health checks for reliability