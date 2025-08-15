# Railway Deployment Guide

## Quick Deployment

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Enterprise statement processing API"
   git push origin main
   ```

2. **Deploy to Railway:**
   - Go to [railway.app](https://railway.app)
   - Connect your GitHub repository
   - Select this repository
   - Railway auto-deploys!

## File Structure Overview

```
├── app_enterprise.py      # 🚀 Main enterprise API (use this)
├── app.py                 # Simple API (backup)
├── statement_processor.py # Core O(n) processing engine
├── requirements.txt       # Dependencies for Railway
├── Procfile              # Railway deployment config
├── railway.json          # Railway settings
├── API_DOCUMENTATION.md  # Complete API documentation
└── test files...         # Testing utilities
```

## Two API Versions Available

### 🚀 **app_enterprise.py** (RECOMMENDED)
- **WebSocket support** for real-time updates
- **Session-based processing** (enterprise pattern)
- **Professional workflow** used by big companies
- **Real-time progress updates**
- **Interactive manual review**
- **Production-ready** with comprehensive error handling

### 📝 **app.py** (Simple version)
- Traditional REST API
- Simpler implementation
- Good for basic use cases

## Enterprise Workflow (Recommended)

```
1. Frontend creates session → GET session_id
2. Frontend uploads files → Real-time progress via WebSocket
3. API processes in background → Progress updates in real-time
4. If manual review needed → WebSocket sends questions
5. Frontend shows questions → User answers
6. API finalizes processing → WebSocket notifies completion
7. Frontend downloads results → ZIP with split PDFs
```

## Production Environment Variables

Set in Railway dashboard:

```bash
# Required
SECRET_KEY=your-super-secret-production-key-here

# Optional (Railway provides these automatically)
PORT=5000
```

## Performance Features

✅ **O(n) Linear Time Complexity** - Verified and optimized
✅ **Memory Efficient** - Railway 512MB compatible
✅ **WebSocket Real-time** - No polling needed
✅ **Session Management** - Automatic cleanup
✅ **Background Processing** - Non-blocking operations
✅ **Error Recovery** - Comprehensive error handling

## Railway Optimizations

- **Memory**: Garbage collection, efficient data structures
- **CPU**: Background threads, optimized algorithms
- **Network**: WebSocket for real-time, compressed responses
- **Storage**: Temporary file cleanup, session expiration

## API Endpoints Summary

### Core Session Flow
```
POST /api/v1/session                    # Create session
POST /api/v1/session/{id}/upload        # Upload files
POST /api/v1/session/{id}/process       # Start processing
GET  /api/v1/session/{id}/questions     # Get manual review questions
POST /api/v1/session/{id}/answers       # Submit answers
GET  /api/v1/session/{id}/download      # Download results
```

### Monitoring
```
GET  /health                            # Health check
GET  /api/v1/session/{id}/status        # Session status
```

## Frontend Integration

Use the complete JavaScript example in `API_DOCUMENTATION.md`:

```javascript
// Connect WebSocket
const socket = io('https://your-app.railway.app');

// Start processing
const processor = new StatementProcessor('https://your-app.railway.app');
processor.startProcessing(pdfFile, excelFile);

// Handle real-time updates
socket.on('progress_update', (data) => {
    updateProgressBar(data.progress);
});
```

## Testing Your Deployment

After deployment, test with:

```bash
# Health check
curl https://your-app.railway.app/health

# Create session
curl -X POST https://your-app.railway.app/api/v1/session
```

## Security Features

- ✅ File type validation
- ✅ File size limits (50MB)
- ✅ Session isolation
- ✅ Automatic cleanup
- ✅ CORS configuration
- ✅ Secure file handling
- ✅ Request timeouts

## Railway Free Tier Compatibility

This API is optimized for Railway's free tier:
- Memory usage under 512MB
- CPU-efficient algorithms
- Fast startup times
- Automatic scaling

## Troubleshooting

### Common Issues:

1. **"Module not found" errors**
   - Check `requirements.txt` includes all dependencies
   - Railway installs automatically

2. **Memory issues**
   - API is optimized for 512MB
   - Uses garbage collection and cleanup

3. **WebSocket connection fails**
   - Check CORS settings
   - Verify client is using correct URL

4. **File upload fails**
   - Check 50MB file size limit
   - Verify file types (PDF, Excel only)

### Debug Mode:

For development, run locally:
```bash
pip install -r requirements.txt
python app_enterprise.py
```

## Ready for Production! 🚀

Your statement processing API is now enterprise-ready with:
- Real-time WebSocket communication
- Professional session-based workflow
- O(n) performance optimization
- Railway deployment compatibility
- Comprehensive documentation

Deploy to Railway and start processing statements with your frontend!