# AlaeAutomates API Integration Guide

## Adding a New Feature to the API

This guide provides step-by-step instructions for integrating a new feature into the AlaeAutomates API system, following the established patterns and architecture.

## Project Architecture Overview

```
AlaeAutomatesAPI/
├── main.py                 # Main Flask app with blueprint registration
├── app.py                  # Frontend demo server
├── processors/             # API logic modules
│   ├── __init__.py
│   ├── statement_processor.py
│   ├── invoice_processor.py
│   ├── credit_card_batch_processor.py
│   └── excel_formatter_processor.py
├── templates/              # Frontend HTML templates
│   ├── index.html
│   ├── monthly_statements.html
│   ├── invoice_separator.html
│   ├── credit_card_batch.html
│   └── excel_formatter.html
├── static/
│   └── css/
│       └── styles.css      # Shared CSS styles
├── requirements.txt        # Python dependencies
└── start_frontend.py       # Frontend launcher
```

## Step-by-Step Integration Process

### Step 1: Create the Processor Module

Create a new file in `processors/[feature_name]_processor.py`:

```python
from flask import Blueprint, request, jsonify, send_file
import os
import tempfile
from werkzeug.utils import secure_filename

# Create Blueprint with consistent naming
[feature_name]_bp = Blueprint('[feature_name]', __name__)

# Global storage for processed files (session-based)
processed_files = {}

@[feature_name]_bp.route('/', methods=['GET'])
def get_service_info():
    """Service information endpoint"""
    return jsonify({
        "service": "[Feature Name] API",
        "description": "Brief description of what this feature does",
        "supported_formats": ["format1", "format2"],  # e.g., ["xlsx", "pdf"]
        "endpoints": {
            "GET /": "Get service information",
            "POST /process": "Process uploaded file",
            "GET /download/<file_id>": "Download processed file"
        }
    })

@[feature_name]_bp.route('/process', methods=['POST'])
def process_file():
    """Main processing endpoint"""
    try:
        # File validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file extension
        allowed_extensions = ['.xlsx', '.xls', '.pdf']  # Adjust as needed
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Unsupported file type. Allowed: {", ".join(allowed_extensions)}'}), 400

        # Process the file
        # [Your processing logic here]

        # Generate unique file ID and store result
        import uuid
        file_id = str(uuid.uuid4())

        # Store processed file path for download
        processed_files[file_id] = {
            'file_path': output_file_path,
            'original_name': file.filename,
            'processed_at': time.time()
        }

        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'file_id': file_id,
            # Add other relevant response data
            'processing_stats': {
                'items_processed': 0,  # Replace with actual count
                'processing_time': 0   # Replace with actual time
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@[feature_name]_bp.route('/download/<file_id>', methods=['GET'])
def download_processed_file(file_id):
    """Download processed file by ID"""
    if file_id not in processed_files:
        return jsonify({'error': 'File not found or expired'}), 404

    file_info = processed_files[file_id]
    file_path = file_info['file_path']

    if not os.path.exists(file_path):
        return jsonify({'error': 'File no longer available'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f'processed_{file_info["original_name"]}'
    )
```

### Step 2: Register Blueprint in main.py

Add your new blueprint to the main application:

```python
# In main.py, add import
from processors.[feature_name]_processor import [feature_name]_bp

# Register blueprint (add to existing registrations)
app.register_blueprint([feature_name]_bp, url_prefix='/api/[feature_name]')

# Update services list in health endpoint
@app.route('/health')
def health_check():
    services = [
        'monthly-statements',
        'invoice-processor',
        'credit-card-batch',
        'excel-formatter',
        '[feature_name]'  # Add your new service
    ]
    return jsonify({
        'status': 'healthy',
        'services': services,
        'timestamp': time.time()
    })
```

### Step 3: Update Frontend Navigation

In `app.py`, add route for your new feature:

```python
@app.route('/[feature_name]')
def [feature_name]():
    return render_template('[feature_name].html', api_url=API_URL)
```

### Step 4: Create Frontend Template

Create `templates/[feature_name].html` using this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Feature Name] - Integration Hub</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
</head>
<body>
    <!-- Navigation (copy from existing templates and update active link) -->
    <nav class="main-nav">
        <div class="nav-container">
            <a href="/" class="nav-brand">AlaeAutomates <span style="font-size: 0.8em; opacity: 0.7; font-weight: 300;">API</span></a>
            <div class="nav-links">
                <a href="/" class="nav-link">Home</a>
                <a href="/monthly-statements" class="nav-link">Monthly Statements</a>
                <a href="/invoice-separator" class="nav-link">Invoice Separator</a>
                <a href="/credit-card-batch" class="nav-link">Credit Card Batch</a>
                <a href="/excel-formatter" class="nav-link">Excel Formatter</a>
                <a href="/[feature_name]" class="nav-link active">[Feature Name]</a>
            </div>
            <button class="mobile-nav-toggle" onclick="toggleMobileNav()" aria-label="Toggle navigation">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="6" x2="21" y2="6"></line>
                    <line x1="3" y1="12" x2="21" y2="12"></line>
                    <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
            </button>
        </div>
    </nav>

    <div class="container">
        <!-- Page Header -->
        <div class="page-header">
            <h1 class="page-title">[Feature Name]</h1>
            <p class="page-subtitle">Professional Integration Hub for [Brief Description]</p>

            <!-- Mode Toggle -->
            <div class="mode-toggle">
                <span class="mode-label" id="simLabel">Documentation</span>
                <div class="toggle-switch" id="modeToggle" onclick="toggleMode()" role="button" tabindex="0" aria-label="Toggle between documentation and live testing mode" onkeydown="if(event.key==='Enter'||event.key===' '){toggleMode()}">
                    <div class="toggle-slider"></div>
                </div>
                <span class="mode-label" id="realLabel">Live Testing</span>
            </div>
        </div>

        <!-- Status Section -->
        <div class="content-section">
            <h2 class="section-title">
                <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="m9 12 2 2 4-4"></path>
                </svg>
                System Status
            </h2>

            <div class="status-grid">
                <div class="status-card">
                    <h3>API Status</h3>
                    <div id="apiStatus" class="status-indicator status-disconnected">
                        Disconnected
                    </div>
                    <div id="apiUrl" class="api-url">
                        API: Not connected
                    </div>
                </div>
                <div class="status-card">
                    <h3>Current Mode</h3>
                    <div id="processingMode" class="status-indicator status-processing">
                        Documentation
                    </div>
                </div>
            </div>
        </div>

        <!-- Documentation Mode -->
        <div id="documentationMode">
            <div class="content-section">
                <h2 class="section-title">
                    <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <book-open x="2" y="3" width="20" height="18" rx="2" ry="2"></book-open>
                        <path d="m6 8 4 4 4-4"></path>
                    </svg>
                    API Integration Guide
                </h2>

                <div class="tab-container">
                    <div class="tab-buttons">
                        <button class="tab-button active" onclick="showTab('overview')">Overview</button>
                        <button class="tab-button" onclick="showTab('endpoints')">API Endpoints</button>
                        <button class="tab-button" onclick="showTab('workflow')">Workflow</button>
                        <button class="tab-button" onclick="showTab('examples')">Code Examples</button>
                        <button class="tab-button" onclick="showTab('security')">Security</button>
                    </div>

                    <!-- Tab Contents -->
                    <div id="overview" class="tab-content active">
                        <h3>Overview</h3>
                        <p class="overview-description">[Detailed description of what your feature does]</p>

                        <div class="feature-grid">
                            <div class="feature-item">
                                <h4>Feature 1</h4>
                                <p>Description of first key feature</p>
                            </div>
                            <div class="feature-item">
                                <h4>Feature 2</h4>
                                <p>Description of second key feature</p>
                            </div>
                            <!-- Add more features as needed -->
                        </div>
                    </div>

                    <div id="endpoints" class="tab-content">
                        <h3>API Endpoints</h3>

                        <!-- GET Endpoint -->
                        <div class="endpoint-card">
                            <div class="endpoint-header">
                                <span class="method get">GET</span>
                                <span class="endpoint-path">/api/[feature_name]</span>
                            </div>
                            <p class="endpoint-description">Get service information and capabilities</p>
                            <!-- Add request/response examples -->
                        </div>

                        <!-- POST Endpoint -->
                        <div class="endpoint-card">
                            <div class="endpoint-header">
                                <span class="method post">POST</span>
                                <span class="endpoint-path">/api/[feature_name]/process</span>
                            </div>
                            <p class="endpoint-description">Process uploaded file</p>
                            <!-- Add request/response examples -->
                        </div>
                    </div>

                    <div id="workflow" class="tab-content">
                        <h3>Integration Workflow</h3>

                        <div class="integration-steps">
                            <div class="integration-step">
                                <h4>Step 1 Title</h4>
                                <p>Description of first step</p>
                            </div>
                            <div class="integration-step">
                                <h4>Step 2 Title</h4>
                                <p>Description of second step</p>
                            </div>
                            <!-- Add more steps as needed -->
                        </div>
                    </div>

                    <div id="examples" class="tab-content">
                        <h3>Code Examples</h3>
                        <!-- Add code examples for different languages -->
                    </div>

                    <div id="security" class="tab-content">
                        <h3>Security & Best Practices</h3>
                        <!-- Add security considerations -->
                    </div>
                </div>
            </div>
        </div>

        <!-- Live Testing Mode -->
        <div id="liveTestingMode" style="display: none;">
            <div class="content-section">
                <h2 class="section-title">
                    <svg class="section-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <upload x="14" y="2" width="8" height="5" rx="1"></upload>
                        <path d="M14,2 14,8 20,8"></path>
                        <circle cx="8" cy="18" r="4"></circle>
                        <path d="M16,18 12,14 6,20"></path>
                    </svg>
                    Live [Feature Name] Testing
                </h2>

                <!-- Upload Section -->
                <div class="upload-section">
                    <div class="upload-card">
                        <h3>Upload File</h3>
                        <p>Upload a file to test the [feature name] functionality</p>

                        <div class="file-upload-area" id="fileUploadArea" onclick="document.getElementById('fileInput').click()">
                            <div class="upload-icon">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <path d="M8 12h8"></path>
                                    <path d="M12 8v8"></path>
                                </svg>
                            </div>
                            <p class="upload-text">Click to upload file or drag and drop</p>
                            <p class="upload-subtext">Supports [supported formats]</p>
                        </div>

                        <input type="file" id="fileInput" accept="[file extensions]" style="display: none;" onchange="handleFileSelect(event)">

                        <div class="upload-controls" style="display: none;" id="uploadControls">
                            <button class="btn-primary" onclick="processFile()" id="processBtn">
                                <span class="btn-text">Process File</span>
                                <span class="btn-loading" style="display: none;">
                                    <svg class="spinner" viewBox="0 0 24 24">
                                        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-dasharray="32" stroke-dashoffset="32">
                                            <animate attributeName="stroke-dasharray" dur="2s" values="0 32;16 16;0 32;0 32" repeatCount="indefinite"/>
                                            <animate attributeName="stroke-dashoffset" dur="2s" values="0;-16;-32;-32" repeatCount="indefinite"/>
                                        </circle>
                                    </svg>
                                    Processing...
                                </span>
                            </button>
                            <button class="btn-secondary" onclick="clearFile()" id="clearBtn">Clear</button>
                        </div>
                    </div>
                </div>

                <!-- Results Section -->
                <div class="results-section" id="resultsSection" style="display: none;">
                    <div class="results-card">
                        <h3>Processing Results</h3>
                        <div id="resultsContent"></div>
                    </div>
                </div>

                <!-- Download Section -->
                <div class="download-section" id="downloadSection" style="display: none;">
                    <div class="download-card">
                        <h3>Download Processed File</h3>
                        <p>Your file has been processed successfully.</p>
                        <button class="btn-success" onclick="downloadFile()" id="downloadBtn">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                            </svg>
                            Download Processed File
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global configuration
        window.API_BASE_URL = '{{ api_url }}';
        let selectedFile = null;
        let processedFileId = null;

        // Core JavaScript functions (copy from existing templates)
        function toggleMobileNav() { /* Mobile nav logic */ }
        function toggleMode() { /* Mode toggle logic */ }
        function showTab(tabName) { /* Tab switching logic */ }
        function checkAPIStatus() { /* API health check */ }

        // File handling functions
        function handleFileSelect(event) { /* File selection logic */ }
        function clearFile() { /* Clear file logic */ }
        function processFile() { /* Process file via API */ }
        function showResults(result) { /* Display results */ }
        function showError(errorMessage) { /* Display errors */ }
        function downloadFile() { /* Download processed file */ }

        // Initialize page
        document.addEventListener('DOMContentLoaded', function() {
            checkAPIStatus();
            setInterval(checkAPIStatus, 30000);
            // Add drag and drop handlers, etc.
        });
    </script>
</body>
</html>
```

### Step 5: Update All Navigation Menus

Update navigation in ALL existing template files:

1. `templates/index.html`
2. `templates/monthly_statements.html`
3. `templates/invoice_separator.html`
4. `templates/credit_card_batch.html`
5. `templates/excel_formatter.html`

Add your new feature link to each navigation:

```html
<div class="nav-links">
    <a href="/" class="nav-link">Home</a>
    <a href="/monthly-statements" class="nav-link">Monthly Statements</a>
    <a href="/invoice-separator" class="nav-link">Invoice Separator</a>
    <a href="/credit-card-batch" class="nav-link">Credit Card Batch</a>
    <a href="/excel-formatter" class="nav-link">Excel Formatter</a>
    <a href="/[feature_name]" class="nav-link">[Feature Name]</a> <!-- ADD THIS -->
</div>
```

### Step 6: Update Dependencies (if needed)

If your feature requires new Python packages, add them to `requirements.txt`:

```txt
# Add any new dependencies at the end
new-package-name==version
```

### Step 7: Test the Integration

1. Start the API: `python main.py`
2. Start the frontend: `python start_frontend.py`
3. Test all endpoints:
   - GET `/api/[feature_name]` - Service info
   - POST `/api/[feature_name]/process` - File processing
   - GET `/api/[feature_name]/download/<file_id>` - File download
4. Test frontend functionality:
   - Navigation between modes
   - File upload and processing
   - Results display
   - File download

## CSS Classes and Styling Guidelines

### Pre-defined CSS Classes Available

#### Layout Classes
- `.container` - Main content container
- `.page-header` - Page title section
- `.content-section` - Main content card
- `.section-title` - Section headings with icons

#### Navigation Classes
- `.main-nav` - Top navigation bar
- `.nav-container` - Navigation container
- `.nav-brand` - Site logo/brand
- `.nav-links` - Navigation links container
- `.nav-link` - Individual navigation link
- `.nav-link.active` - Active navigation state

#### Button Classes
- `.btn-primary` - Primary action button (blue)
- `.btn-secondary` - Secondary action button (gray)
- `.btn-success` - Success action button (green, animated)
- `.btn-loading` - Loading state content

#### Status Indicators
- `.status-indicator` - Base status indicator
- `.status-connected` - Green connected state
- `.status-disconnected` - Red disconnected state
- `.status-processing` - Yellow processing state

#### Content Organization
- `.tab-container` - Tab system container
- `.tab-buttons` - Tab button row
- `.tab-button` - Individual tab button
- `.tab-button.active` - Active tab state
- `.tab-content` - Tab content panel
- `.tab-content.active` - Visible tab panel

#### File Upload
- `.upload-section` - Upload area container
- `.upload-card` - Upload card wrapper
- `.file-upload-area` - Drag-and-drop zone
- `.upload-icon` - Upload icon container
- `.upload-text` - Primary upload text
- `.upload-subtext` - Secondary upload text
- `.upload-controls` - Upload button controls

#### Results Display
- `.results-section` - Results container
- `.results-card` - Results card wrapper
- `.result-summary` - Summary statistics grid
- `.summary-item` - Individual statistic
- `.summary-label` - Statistic label
- `.summary-value` - Statistic value
- `.summary-value.success` - Green success value
- `.summary-value.warning` - Yellow warning value
- `.summary-value.error` - Red error value

#### Integration Steps
- `.integration-steps` - Workflow steps container
- `.integration-step` - Individual workflow step (auto-numbered)

#### Feature Grids
- `.feature-grid` - Feature showcase grid
- `.feature-item` - Individual feature card

#### Code and Endpoints
- `.code-block` - Code display block
- `.endpoint-card` - API endpoint documentation
- `.endpoint-header` - Endpoint title row
- `.method` - HTTP method badge
- `.method.get` - GET method (blue)
- `.method.post` - POST method (green)
- `.endpoint-path` - API path display

### Color Variables Available

```css
/* Primary Colors */
--primary-50 to --primary-900  /* Gray scale */
--accent-50 to --accent-900    /* Blue accent scale */

/* Status Colors */
--success: #059669   /* Green */
--warning: #d97706   /* Orange */
--error: #dc2626     /* Red */

/* Surfaces */
--surface: #ffffff           /* White background */
--surface-subtle: #f8fafc   /* Light gray background */
```

## Common Patterns and Best Practices

### Error Handling Pattern
```javascript
async function processFile() {
    try {
        // Processing logic
        const result = await response.json();
        if (result.success) {
            showResults(result);
            processedFileId = result.file_id;
        } else {
            showError(result.error);
        }
    } catch (error) {
        showError(`Processing failed: ${error.message}`);
    }
}
```

### File Download Pattern
```javascript
function downloadFile() {
    if (!processedFileId) {
        alert('No file available for download.');
        return;
    }

    const downloadUrl = `${window.API_BASE_URL}/api/[feature_name]/download/${processedFileId}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = 'processed_file.ext';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
```

### API Response Pattern
```python
# Success response
return jsonify({
    'success': True,
    'message': 'Processing completed successfully',
    'file_id': file_id,
    'stats': {
        'items_processed': count,
        'processing_time': duration
    }
})

# Error response
return jsonify({
    'success': False,
    'error': 'Detailed error message'
}), 400
```

## File Organization Tips

1. **Keep related code together** - Processor logic, template, and specific styles should be cohesive
2. **Follow naming conventions** - Use consistent naming across files (snake_case for Python, kebab-case for URLs)
3. **Maintain separation of concerns** - API logic in processors, UI logic in templates, styling in CSS
4. **Document your endpoints** - Always include service info endpoint and comprehensive documentation tab
5. **Test thoroughly** - Test both API endpoints and frontend functionality before deployment

## Deployment Checklist

- [ ] Processor module created and tested
- [ ] Blueprint registered in main.py
- [ ] Frontend route added to app.py
- [ ] Template created with both modes
- [ ] Navigation updated in all templates
- [ ] Dependencies added to requirements.txt
- [ ] API endpoints tested (GET, POST, download)
- [ ] Frontend functionality tested
- [ ] Error handling implemented
- [ ] Mobile responsiveness verified
- [ ] Documentation completed

This guide ensures consistent implementation patterns across all features in the AlaeAutomates API system.