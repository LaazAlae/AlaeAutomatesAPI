# Statement Processing API Documentation

## Overview

Enterprise-grade statement processing API with real-time WebSocket communication. This follows the professional workflow pattern used by major companies for complex document processing tasks.

## Architecture Pattern

This API implements the **Session-Based Processing Pattern** commonly used in enterprise applications:

1. **Session Creation** - Client creates a processing session
2. **File Upload** - Client uploads files to the session
3. **Background Processing** - Server processes files with real-time updates
4. **Interactive Review** - If manual review needed, client receives questions
5. **Answer Submission** - Client submits answers for manual review
6. **Final Processing** - Server completes processing and prepares results
7. **Download Results** - Client downloads processed files

## Base URL

```
Production: https://your-app.railway.app
Development: http://localhost:5000
```

## WebSocket Connection

```javascript
// Connect to WebSocket
const socket = io('https://your-app.railway.app');

// Join a session for real-time updates
socket.emit('join_session', { session_id: 'your-session-id' });
```

## API Endpoints

### 1. Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "statement-processor-enterprise",
  "websocket": true,
  "sessions": 5
}
```

### 2. Create Session

```http
POST /api/v1/session
```

**Response:**
```json
{
  "status": "success",
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "expires_in": 7200
}
```

### 3. Upload Files

```http
POST /api/v1/session/{session_id}/upload
Content-Type: multipart/form-data
```

**Parameters:**
- `pdf` (file): PDF statement file
- `excel` (file): Excel DNM list file

**Response:**
```json
{
  "status": "success",
  "message": "Files uploaded successfully",
  "files": {
    "pdf": {"name": "statements.pdf", "size": 1048576},
    "excel": {"name": "dnm_list.xlsx", "size": 65536}
  }
}
```

### 4. Start Processing

```http
POST /api/v1/session/{session_id}/process
```

**Response:**
```json
{
  "status": "success",
  "message": "Processing started",
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**WebSocket Events Emitted:**
- `progress_update` - Processing progress updates
- `questions_ready` - Manual review questions available
- `processing_complete` - Processing finished (no manual review needed)
- `processing_error` - Processing failed

### 5. Get Questions (if manual review needed)

```http
GET /api/v1/session/{session_id}/questions
```

**Response:**
```json
{
  "status": "success",
  "questions": [
    {
      "id": "question-uuid",
      "company_name": "ABC Corp Inc",
      "similar_to": "ABC Corporation",
      "percentage": "85.5%",
      "current_destination": "Natio Single"
    }
  ],
  "total_statements": 25
}
```

### 6. Submit Answers

```http
POST /api/v1/session/{session_id}/answers
Content-Type: application/json
```

**Request Body:**
```json
{
  "answers": {
    "ABC Corp Inc": "yes",
    "XYZ Company": "no",
    "Another Corp": "skip"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Answers submitted, finalizing processing..."
}
```

### 7. Download Results

```http
GET /api/v1/session/{session_id}/download
```

**Response:**
- Content-Type: `application/zip`
- File: `statement_results_{session_id}.zip`

### 8. Get Session Status

```http
GET /api/v1/session/{session_id}/status
```

**Response:**
```json
{
  "status": "success",
  "session": {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "status": "questions_ready",
    "created_at": "2025-01-15T10:30:00Z",
    "has_questions": true,
    "total_statements": 25,
    "questions_count": 3
  }
}
```

### 9. Delete Session

```http
DELETE /api/v1/session/{session_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Session deleted successfully"
}
```

## Session States

| State | Description |
|-------|-------------|
| `created` | Session created, ready for file upload |
| `files_uploaded` | Files uploaded, ready for processing |
| `processing` | Processing statements in background |
| `questions_ready` | Manual review questions available |
| `finalizing` | Applying answers and creating final output |
| `completed` | Processing complete, results ready for download |
| `error` | Processing failed |

## WebSocket Events

### Client → Server Events

#### `join_session`
```javascript
socket.emit('join_session', { 
  session_id: 'your-session-id' 
});
```

#### `leave_session`
```javascript
socket.emit('leave_session', { 
  session_id: 'your-session-id' 
});
```

### Server → Client Events

#### `connected`
```javascript
socket.on('connected', (data) => {
  console.log('Connected:', data.sid);
});
```

#### `progress_update`
```javascript
socket.on('progress_update', (data) => {
  /*
  {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "message": "Extracting statements from PDF...",
    "progress": 30,
    "timestamp": "2025-01-15T10:35:00Z",
    "data": {}
  }
  */
});
```

#### `questions_ready`
```javascript
socket.on('questions_ready', (data) => {
  /*
  {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "questions": [...],
    "total_statements": 25
  }
  */
});
```

#### `processing_complete`
```javascript
socket.on('processing_complete', (data) => {
  /*
  {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "total_statements": 25,
    "requires_manual_review": false,
    "files_created": ["DNM.pdf", "Foreign.pdf", "results.json"],
    "download_ready": true
  }
  */
});
```

#### `processing_error`
```javascript
socket.on('processing_error', (data) => {
  /*
  {
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "error": "Error message"
  }
  */
});
```

## Complete Workflow Example

### Frontend JavaScript Implementation

```javascript
class StatementProcessor {
  constructor(apiBaseUrl) {
    this.apiUrl = apiBaseUrl;
    this.socket = io(apiBaseUrl);
    this.sessionId = null;
    
    this.setupSocketListeners();
  }
  
  setupSocketListeners() {
    this.socket.on('connected', (data) => {
      console.log('WebSocket connected');
    });
    
    this.socket.on('progress_update', (data) => {
      this.updateProgress(data.message, data.progress);
    });
    
    this.socket.on('questions_ready', (data) => {
      this.showManualReviewQuestions(data.questions);
    });
    
    this.socket.on('processing_complete', (data) => {
      if (data.download_ready) {
        this.enableDownload();
      }
    });
    
    this.socket.on('processing_error', (data) => {
      this.showError(data.error);
    });
  }
  
  async startProcessing(pdfFile, excelFile) {
    try {
      // 1. Create session
      const sessionResponse = await fetch(`${this.apiUrl}/api/v1/session`, {
        method: 'POST'
      });
      const sessionData = await sessionResponse.json();
      this.sessionId = sessionData.session_id;
      
      // 2. Join WebSocket room
      this.socket.emit('join_session', { session_id: this.sessionId });
      
      // 3. Upload files
      const formData = new FormData();
      formData.append('pdf', pdfFile);
      formData.append('excel', excelFile);
      
      const uploadResponse = await fetch(
        `${this.apiUrl}/api/v1/session/${this.sessionId}/upload`,
        {
          method: 'POST',
          body: formData
        }
      );
      
      if (!uploadResponse.ok) throw new Error('Upload failed');
      
      // 4. Start processing
      const processResponse = await fetch(
        `${this.apiUrl}/api/v1/session/${this.sessionId}/process`,
        {
          method: 'POST'
        }
      );
      
      if (!processResponse.ok) throw new Error('Processing start failed');
      
      console.log('Processing started...');
      
    } catch (error) {
      this.showError(error.message);
    }
  }
  
  async submitAnswers(answers) {
    try {
      const response = await fetch(
        `${this.apiUrl}/api/v1/session/${this.sessionId}/answers`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers })
        }
      );
      
      if (!response.ok) throw new Error('Answer submission failed');
      
    } catch (error) {
      this.showError(error.message);
    }
  }
  
  downloadResults() {
    window.open(`${this.apiUrl}/api/v1/session/${this.sessionId}/download`);
  }
  
  updateProgress(message, progress) {
    console.log(`Progress: ${progress}% - ${message}`);
    // Update your UI progress bar here
  }
  
  showManualReviewQuestions(questions) {
    // Show questions in your UI
    console.log('Manual review needed:', questions);
  }
  
  enableDownload() {
    // Enable download button in UI
    console.log('Results ready for download');
  }
  
  showError(message) {
    console.error('Error:', message);
    // Show error in UI
  }
}

// Usage
const processor = new StatementProcessor('https://your-app.railway.app');

// Start processing when user selects files
document.getElementById('process-button').onclick = () => {
  const pdfFile = document.getElementById('pdf-input').files[0];
  const excelFile = document.getElementById('excel-input').files[0];
  processor.startProcessing(pdfFile, excelFile);
};
```

### HTML Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Statement Processor</title>
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
</head>
<body>
    <div>
        <h1>Statement Processing</h1>
        
        <div>
            <label>PDF File:</label>
            <input type="file" id="pdf-input" accept=".pdf">
        </div>
        
        <div>
            <label>Excel File:</label>
            <input type="file" id="excel-input" accept=".xlsx,.xls">
        </div>
        
        <button id="process-button">Start Processing</button>
        
        <div id="progress">
            <div id="progress-bar" style="width: 0%; background: green; height: 20px;"></div>
            <p id="progress-text">Ready</p>
        </div>
        
        <div id="questions" style="display: none;">
            <h3>Manual Review Required</h3>
            <div id="questions-list"></div>
            <button id="submit-answers">Submit Answers</button>
        </div>
        
        <button id="download-button" style="display: none;">Download Results</button>
    </div>
    
    <script src="statement-processor.js"></script>
</body>
</html>
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Error message",
  "status": "error"
}
```

HTTP Status Codes:
- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found (invalid session)
- `413` - File Too Large
- `500` - Internal Server Error

## Security Features

- Session-based processing with automatic cleanup
- File type validation
- File size limits (50MB)
- Request timeout protection
- Secure filename handling
- CORS configuration
- WebSocket room isolation

## Performance Optimizations

- O(n) linear processing time
- Memory-efficient file handling
- Background processing threads
- Automatic garbage collection
- Session cleanup
- Connection pooling

## Deployment Configuration

### Railway Configuration

The API is configured for Railway deployment with:

- **Procfile**: Gunicorn with eventlet workers for WebSocket support
- **railway.json**: Health check and build configuration  
- **requirements.txt**: Optimized dependencies for Railway
- **Environment**: Automatic PORT detection

### Environment Variables

Set these in Railway dashboard:

```bash
SECRET_KEY=your-production-secret-key
# Optional: Redis URL for production session storage
REDIS_URL=redis://...
```

## Rate Limiting & Quotas

For production deployment, consider adding:
- Rate limiting per IP/session
- File upload quotas
- Session limits per user
- Processing timeout limits

This API follows enterprise patterns and is production-ready for Railway deployment!