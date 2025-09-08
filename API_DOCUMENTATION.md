# AlaeAutomates API - Complete Documentation

## **What This API Does**

This API provides three main services:

### Statement Processing
Processes PDF bank statements and matches company names against a Do Not Mail (DNM) list from an Excel file. It automatically extracts company information from PDF pages and determines which companies should be excluded from mailings.

### Invoice Processing  
Extracts invoice numbers from PDF files and splits them into separate documents based on invoice number patterns (P/R followed by 6-8 digits).

### Credit Card Batch Processing
Processes Excel files with credit card data and generates enhanced JavaScript automation code for Legacy Edge browsers. Automatically cleans data, removes headers and totals, and creates robust automation scripts with safety checks.

# API Changes Report - Updated Friday, September 5th, 2025

## Summary
The statement processor has been updated with the improved minimal version that provides better accuracy, enhanced user interaction, and cleaner output formatting while maintaining full API compatibility.

## Key Improvements

### 1. Enhanced Company Name Extraction
- **4 regex patterns in priority order**: subtotal → multiline → line → fallback
- **Smarter extraction logic**: Handles multi-line company names and complex PDF layouts
- **Fallback tracking**: Records when and why fallback methods are used
- **Extraction comparison logs**: Detailed logging of extraction method changes

### 2. Improved Interactive Questions
- **Back navigation**: Users can go back to previous questions with 'p' option
- **History tracking**: Maintains state history for undo functionality
- **Enhanced options**: y/n/s/p (yes/no/skip all/previous)
- **Better user feedback**: Clear confirmation messages for each action

### 3. Professional Output Format
- **Timestamped folders**: All outputs organized in `output_YYYYMMDD_HHMMSS` folders
- **Step-by-step progress**: Clear workflow indicators with emojis and status messages
- **Comprehensive JSON**: Includes extraction logs and processing metadata
- **Clean formatting**: Well-organized sections with proper spacing

### 4. API Compatibility
- **No breaking changes**: All existing API endpoints remain unchanged
- **Same data structures**: JSON responses maintain identical format
- **Backward compatible**: Existing frontends will continue to work without modification

## Technical Changes

### Data Structure Additions
```json
{
  "extraction_method": "subtotal_pattern|multiline_pattern|line_pattern|fallback",
  "fallbackUsed": boolean,
  "fallbackReason": "string (when fallback is used)",
  "unusedCompanyName": "string (original first line when pattern extraction differs)",
  "_extraction_log": [
    {
      "page_num": int,
      "current_page": int, 
      "total_pages": int,
      "old_method": "string",
      "new_method": "string", 
      "extraction_method": "string",
      "match": boolean
    }
  ]
}
```

### New Features
- **Enhanced regex patterns** for better company name detection
- **Last-page optimization** for multi-page statement processing  
- **Professional CLI output** with progress indicators and emojis
- **History-based navigation** in interactive questions
- **Comprehensive extraction logging** for analysis and debugging

## Frontend Integration Notes

### No Changes Required
- All existing API calls will work unchanged
- JSON response format remains compatible
- Error handling stays the same
- File upload/download processes unchanged

### Optional Enhancements
If you want to leverage the new features:

1. **Display extraction method info**:
   ```javascript
   if (statement.extraction_method !== 'fallback') {
     showImprovedExtraction(statement.extraction_method);
   }
   ```

2. **Show unused company names**:
   ```javascript
   if (statement.unusedCompanyName) {
     showAlternativeName(statement.unusedCompanyName);
   }
   ```

3. **Access extraction logs**:
   ```javascript
   const logs = data.extraction_comparison_log;
   displayExtractionStats(logs.summary);
   ```

## Performance Improvements

- **O(n) complexity maintained** with optimized pattern matching
- **Last-page jumping** reduces PDF processing time for multi-page statements
- **Pre-compiled regex patterns** for faster text extraction
- **Memory efficient** with proper cleanup and garbage collection

## Quality Assurance

- **Comprehensive error handling** for all edge cases
- **Input validation** for all file types and formats  
- **Graceful fallbacks** when pattern matching fails
- **Professional user experience** with clear progress indicators

## Migration Instructions

### For API Consumers
**No action required** - the API remains fully backward compatible.

### For Direct Script Users  
The processor script now provides:
- Better visual feedback during processing
- More accurate company name extraction
- Enhanced interactive question system with back navigation
- Organized output in timestamped folders

Simply replace the old processor script with the new one and enjoy the improved experience!

---

# API Changes Report - Updated Sunday, September 8th, 2025

## CRITICAL BREAKING CHANGES - Immediate Action Required

### ️ Major Change: Individual Company Questioning System

**What Changed:**
- **Previous**: Asked only about the highest percentage match company (e.g., "Is ABC Corp the same as ABC Corporation (85%)?")
- **New**: Asks about EVERY similar company individually above 50% threshold

**Example of New Behavior:**
```
OLD SYSTEM:
Question 1: Is 'ABC Corp' the same as 'ABC Corporation' (85%)?
[Shows: ABC Corporation (85%), ABC Industries (72%), ABC Holdings (65%)]
[Only asks about the 85% match]

NEW SYSTEM:
Question 1: Is 'ABC Corp' the same as 'ABC Corporation' (85%)?
Question 2: Is 'ABC Corp' the same as 'ABC Industries Inc' (72%)?
Question 3: Is 'ABC Corp' the same as 'ABC Holdings LLC' (65%)?
[Asks about each match individually]
```

### New API Response Structure

**BREAKING CHANGE: New Fields Added to Statement Objects**

```json
{
  "company_name": "ABC Corp",
  "similar_matches": [...],
  "company_equivalences": [
    {
      "dnm_company": "ABC Corporation",
      "percentage": "85.5%",
      "user_confirmed": true
    },
    {
      "dnm_company": "ABC Industries Inc", 
      "percentage": "72.1%",
      "user_confirmed": false
    },
    {
      "dnm_company": "ABC Holdings LLC",
      "percentage": "65.8%", 
      "user_confirmed": true
    }
  ],
  "user_answered": "yes|no",
  // ... existing fields remain unchanged
}
```

### Threshold Changes

- **Similarity threshold**: Lowered from 60% to 50%
- **Auto-classification removed**: No more automatic DNM classification for 90%+ matches
- **All matches questioned**: Every company above 50% similarity now requires user input

### Frontend Integration Impact

**REQUIRED CHANGES for all frontends:**

1. **Question Structure - BREAKING CHANGE**
   ```javascript
   // OLD: Flat array of simple questions
   const data = await api.getQuestions();
   data.questions.forEach(q => {
     // q.company_name, q.similar_to, q.percentage
   });
   
   // NEW: Grouped by extracted company with multiple similarity questions
   const data = await api.getQuestions();
   data.companies_requiring_review.forEach(company => {
     console.log(`Questions for: ${company.extracted_company}`);
     company.questions.forEach(q => {
       // Ask: Is company.extracted_company same as q.dnm_company (q.similarity_percentage)?
       askUser(`Is ${company.extracted_company} same as ${q.dnm_company} (${q.similarity_percentage})?`, q.question_id);
     });
   });
   ```

2. **Answer Submission - BREAKING CHANGE**
   ```javascript
   // OLD: Company name keys
   {
     "answers": {
       "ABC Corp": "yes",
       "XYZ Company": "no"
     }
   }
   
   // NEW: Question ID keys
   {
     "answers": {
       "q001": "yes",  // Abar Abstract = Joe Abstract
       "q002": "no",   // Abar Abstract ≠ Mama Abstract  
       "q003": "yes",  // Abar Abstract = Rachid Abstract Services
       "q004": "no",   // XYZ Corp ≠ XYZ Corporation
       "q005": "skip"  // XYZ Corp ? XYZ Industries (skipped)
     }
   }
   ```

3. **New Company Management Features Available**
   ```javascript
   // Access detailed company equivalences
   statement.company_equivalences.forEach(equiv => {
     if (equiv.user_confirmed) {
       // This extracted company = this DNM company
       addToCompanyMapping(statement.company_name, equiv.dnm_company);
     }
   });
   ```

### New Frontend Capabilities

## **Company Equivalence Management Page - Complete Implementation Guide**

The new API structure enables you to build a comprehensive company management interface where users can:
- **View all company equivalences** from their previous answers
- **Modify wrong decisions** without re-processing the entire document
- **See confidence scores** for each mapping
- **Prevent duplicate questions** by reading from the equivalence history

### **Complete Company Management Data Structure**

```javascript
// Extract complete company equivalence data from API response
const buildCompanyManagementData = (statements) => {
  const companyMappings = {};
  
  statements.forEach(statement => {
    const extractedCompany = statement.company_name;
    const equivalences = statement.company_equivalences || [];
    
    if (equivalences.length > 0) {
      companyMappings[extractedCompany] = {
        // Core identification
        statementId: statement.statement_id,
        extractedCompany: extractedCompany,
        pageInfo: statement.page_number_in_uploaded_pdf,
        destination: statement.destination,
        
        // All similarity decisions
        equivalences: equivalences.map(eq => ({
          dnmCompany: eq.dnm_company,
          percentage: eq.percentage,
          userConfirmed: eq.user_confirmed,
          isMatch: eq.user_confirmed,
          confidence: parseFloat(eq.percentage.replace('%', ''))
        })),
        
        // Quick access arrays
        confirmedMatches: equivalences
          .filter(eq => eq.user_confirmed === true)
          .map(eq => eq.dnm_company),
        
        rejectedMatches: equivalences
          .filter(eq => eq.user_confirmed === false)
          .map(eq => eq.dnm_company),
          
        // Analytics
        totalQuestionsAnswered: equivalences.length,
        highestConfidence: Math.max(...equivalences.map(eq => 
          parseFloat(eq.percentage.replace('%', ''))
        )),
        matchCount: equivalences.filter(eq => eq.user_confirmed).length
      };
    }
  });
  
  return companyMappings;
};
```

### **Company Management UI Components**

**1. Company Overview Table:**
```javascript
const CompanyManagementTable = ({ companyMappings }) => {
  return (
    <table className="company-management-table">
      <thead>
        <tr>
          <th>Extracted Company</th>
          <th>Page</th>
          <th>Destination</th>
          <th>DNM Matches</th>
          <th>Rejections</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(companyMappings).map(([extractedCompany, data]) => (
          <tr key={extractedCompany}>
            <td><strong>{extractedCompany}</strong></td>
            <td>{data.pageInfo}</td>
            <td>
              <span className={`destination ${data.destination.toLowerCase()}`}>
                {data.destination}
              </span>
            </td>
            <td>
              <div className="matches">
                {data.confirmedMatches.map(match => (
                  <span key={match} className="match confirmed">{match}</span>
                ))}
              </div>
            </td>
            <td>
              <div className="rejections">
                {data.rejectedMatches.map(reject => (
                  <span key={reject} className="match rejected">{reject}</span>
                ))}
              </div>
            </td>
            <td>
              <button onClick={() => editCompanyEquivalences(extractedCompany, data)}>
                Edit Decisions
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
```

**2. Individual Company Editor Modal:**
```javascript
const CompanyEquivalenceEditor = ({ extractedCompany, data, onSave, onClose }) => {
  const [equivalences, setEquivalences] = useState(data.equivalences);
  
  const toggleEquivalence = (index) => {
    const updated = [...equivalences];
    updated[index].userConfirmed = !updated[index].userConfirmed;
    setEquivalences(updated);
  };
  
  const saveChanges = async () => {
    // Update via API
    await updateCompanyEquivalences(data.statementId, equivalences);
    onSave(extractedCompany, equivalences);
  };
  
  return (
    <div className="equivalence-editor-modal">
      <div className="modal-content">
        <h3>Edit Decisions for: {extractedCompany}</h3>
        <p>Page: {data.pageInfo} | Current Destination: {data.destination}</p>
        
        <div className="equivalences-list">
          {equivalences.map((eq, index) => (
            <div key={index} className="equivalence-item">
              <div className="question">
                Is <strong>{extractedCompany}</strong> the same as{' '}
                <strong>{eq.dnmCompany}</strong>?
                <span className="confidence">({eq.percentage})</span>
              </div>
              
              <div className="decision-controls">
                <label>
                  <input
                    type="radio"
                    name={`decision-${index}`}
                    checked={eq.userConfirmed === true}
                    onChange={() => {
                      const updated = [...equivalences];
                      updated[index].userConfirmed = true;
                      setEquivalences(updated);
                    }}
                  />
                  Yes - Same Company
                </label>
                
                <label>
                  <input
                    type="radio"
                    name={`decision-${index}`}
                    checked={eq.userConfirmed === false}
                    onChange={() => {
                      const updated = [...equivalences];
                      updated[index].userConfirmed = false;
                      setEquivalences(updated);
                    }}
                  />
                  No - Different Company
                </label>
              </div>
            </div>
          ))}
        </div>
        
        <div className="modal-actions">
          <button onClick={saveChanges} className="save-btn">
            Save Changes
          </button>
          <button onClick={onClose} className="cancel-btn">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
```

### **API Endpoint for Updating Company Equivalences**

```javascript
// New API endpoint needed: PATCH /api/statement-processor/{session_id}/equivalences
const updateCompanyEquivalences = async (statementId, updatedEquivalences) => {
  const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/equivalences`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      statement_id: statementId,
      equivalences: updatedEquivalences.map(eq => ({
        dnm_company: eq.dnmCompany,
        percentage: eq.percentage,
        user_confirmed: eq.userConfirmed
      }))
    })
  });
  return response.json();
};
```

### **Preventing Duplicate Questions - Answer Memory System**

```javascript
// Check if question was already answered in previous sessions
const checkPreviousAnswers = (extractedCompany, dnmCompany, previousMappings) => {
  if (previousMappings[extractedCompany]) {
    const existingDecision = previousMappings[extractedCompany].equivalences
      .find(eq => eq.dnmCompany === dnmCompany);
    
    if (existingDecision) {
      return {
        previouslyAnswered: true,
        decision: existingDecision.userConfirmed,
        confidence: existingDecision.percentage
      };
    }
  }
  return { previouslyAnswered: false };
};

// Use in question processing
const filterQuestionsWithMemory = (questions, previousMappings) => {
  return questions.companies_requiring_review.map(company => ({
    ...company,
    questions: company.questions.filter(q => {
      const memory = checkPreviousAnswers(
        company.extracted_company, 
        q.dnm_company, 
        previousMappings
      );
      
      if (memory.previouslyAnswered) {
        console.log(`Skipping: ${company.extracted_company} vs ${q.dnm_company} - previously answered: ${memory.decision}`);
        return false; // Don't ask again
      }
      return true; // Ask this question
    })
  })).filter(company => company.questions.length > 0);
};
```

### **Complete Integration Example**

```javascript
class CompanyManagementSystem {
  constructor(apiBase, sessionId) {
    this.apiBase = apiBase;
    this.sessionId = sessionId;
    this.companyMappings = {};
  }
  
  // Load all company data
  async loadCompanyData() {
    const response = await fetch(`${this.apiBase}/api/statement-processor/${this.sessionId}/results`);
    const data = await response.json();
    this.companyMappings = buildCompanyManagementData(data.extracted_statements);
    return this.companyMappings;
  }
  
  // Get questions with memory filtering
  async getFilteredQuestions() {
    const questions = await fetch(`${this.apiBase}/api/statement-processor/${this.sessionId}/questions`);
    const questionsData = await questions.json();
    
    // Filter out questions already answered
    return filterQuestionsWithMemory(questionsData, this.companyMappings);
  }
  
  // Update specific company equivalences
  async updateCompanyDecisions(extractedCompany, newEquivalences) {
    const statementId = this.companyMappings[extractedCompany].statementId;
    
    const response = await fetch(`${this.apiBase}/api/statement-processor/${this.sessionId}/equivalences`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        statement_id: statementId,
        equivalences: newEquivalences
      })
    });
    
    // Update local cache
    this.companyMappings[extractedCompany].equivalences = newEquivalences;
    return response.json();
  }
}
```

### **CSS Styling Example**

```css
.company-management-table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.company-management-table th,
.company-management-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.destination.dnm { background-color: #e8f5e8; color: #2e7d2e; }
.destination.foreign { background-color: #fff3cd; color: #856404; }
.destination.natio { background-color: #d1ecf1; color: #0c5460; }

.match.confirmed {
  background-color: #d4edda;
  color: #155724;
  padding: 4px 8px;
  border-radius: 4px;
  margin: 2px;
  display: inline-block;
}

.match.rejected {
  background-color: #f8d7da;
  color: #721c24;
  padding: 4px 8px;
  border-radius: 4px;
  margin: 2px;
  display: inline-block;
}

.equivalence-editor-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.equivalence-item {
  border: 1px solid #ddd;
  padding: 15px;
  margin: 10px 0;
  border-radius: 5px;
}

.decision-controls {
  margin-top: 10px;
}

.decision-controls label {
  display: block;
  margin: 5px 0;
  cursor: pointer;
}
```

### Migration Required - Action Items

**IMMEDIATE CHANGES NEEDED:**

1. **Update Question Handling Logic**
   - Expect significantly more questions (3-5x increase)
   - Update progress indicators to handle higher question counts
   - Modify UI to show individual company pair questions

2. **Modify Answer Collection**
   - Change from company-level to pair-level answers
   - Update answer submission format
   - Handle new question flow structure

3. **Add Company Management Features (Optional but Recommended)**
   - Build pages to show company equivalence mappings
   - Display all variations of same company
   - Show user decision history

4. **Update Loading/Progress Indicators**
   - Account for increased processing time due to more questions
   - Update progress bars to reflect new question counts
   - Add estimated completion time based on new question volume

### Backward Compatibility

**NOT MAINTAINED** - This is a breaking change that requires frontend updates.

**Why Breaking Changes Were Necessary:**
- Previous system only captured limited company matching data
- New system provides granular company equivalence mappings
- Enables advanced company name management features
- Provides much richer data for business intelligence

### Testing Your Integration

**Test Cases to Verify:**

1. **Question Volume**: Verify your UI can handle 3-5x more questions
2. **Answer Format**: Test new answer submission format  
3. **Response Parsing**: Ensure you can parse new `company_equivalences` field
4. **Progress Indicators**: Verify progress tracking works with higher question counts
5. **Error Handling**: Test error handling with new response structure

### Benefits of This Update

- **Granular Data**: Know exactly which DNM companies match which extracted names
- **Better Decision Making**: Users can specify different relationships for different companies
- **Frontend Opportunities**: Build advanced company name management interfaces
- **Business Intelligence**: Rich data for analyzing company name patterns
- **Future-Proofing**: Foundation for automatic answer memory implementation

---

**This update provides significantly more detailed company matching data but requires frontend changes to handle the new question structure and response format.**

### **Statement Processing Features:**
- **Enhanced company name extraction** using 4 regex patterns in priority order (subtotal, multiline, line, fallback)
- **Individual company questioning** with 50%+ threshold for comprehensive similarity analysis
- **Granular company equivalence mapping** - ask about each similar company individually
- **Interactive Q&A system** with back navigation and history tracking (y/n/s/p options)
- **Timestamped output folders** with JSON results and extraction comparison logs
- **Optimized last-page jumping** for multi-page statements (more efficient processing)
- **Professional workflow display** with step-by-step progress indicators
- **Production ready** - Error handling, memory management, CORS support

### **Invoice Processing Features:**
- **Extracts invoice numbers** from PDF files using regex patterns
- **Splits PDFs** into separate files by invoice number
- **Batch processing** for multiple invoices in one file
- **ZIP download** of separated invoice files
- **Error handling** for files without invoice numbers

### **Credit Card Batch Processing Features:**
- **Excel file processing** with automatic header and total removal
- **Data validation** and cleaning for credit card information
- **Enhanced JavaScript generation** with safety checks and element visibility verification
- **Legacy Edge compatibility** with modern security enhancements
- **Robust automation** that fills all fields simultaneously without sequential delays
- **Error recovery** with timeout protection and safe element interaction

## **Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │ Statement       │
│   Upload Files  │───▶│   app.py        │───▶│ Processor       │
│   Handle Q&A    │◀───│   REST/JSON     │◀───│ Core Logic      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Workflow:**
1. **Upload** PDF statement + Excel DNM list
2. **Process** PDF pages to extract company information  
3. **Match** companies against DNM list using fuzzy matching
4. **Review** uncertain matches through interactive questions
5. **Download** results as split PDFs + JSON summary

##  **API Integration Guide**

### **Base URL**
```
Production: https://alaeautomatesapi.up.railway.app
Local: http://localhost:8000
```

### **Authentication**
No authentication required. API uses session-based processing for file handling.

### **CORS Policy**  
```javascript
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Content-Type,Authorization  
Access-Control-Allow-Methods: GET,PUT,POST,DELETE,OPTIONS
```

##  **API Endpoints Reference**

### **Endpoints Overview**
- **Health Check**: `/health`
- **Invoice Processing**: `/api/invoice-processor` 
- **Statement Processing**: `/api/statement-processor`
- **Credit Card Batch**: `/api/credit-card-batch`

**Services Available:**
- Invoice Processing: Invoice number extraction and splitting
- Statement Processing: PDF statement analysis with DNM matching
- Credit Card Batch: Excel processing and automation code generation

### **1. Health Check**
```http
GET /health
```
**Response:**
```json
{
  "status": "running",
  "service": "Document Processing API",
  "version": "2.0", 
  "port": 8000,
  "sessions": 0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### **2. Create Processing Session**
```http
POST /api/statement-processor
```
**Response:**
```json
{
  "status": "success",
  "session_id": "uuid-4-format"
}
```

### **3. Upload Files**
```http
POST /api/statement-processor/{session_id}/upload
Content-Type: multipart/form-data
```
**Form Data:**
- `pdf`: PDF bank statement file
- `excel`: Excel DNM list file (.xlsx)

**Response:**
```json
{
  "status": "success", 
  "message": "Files uploaded successfully",
  "files": {
    "pdf": {"name": "statement.pdf", "size": 1024000},
    "excel": {"name": "dnm_list.xlsx", "size": 50000}
  }
}
```

### **4. Process Files**
```http
POST /api/statement-processor/{session_id}/process
```
**Response:**
```json
{
  "status": "success",
  "message": "Processing completed",
  "total_statements": 150,
  "questions_needed": 12
}
```

### **5. Get Manual Review Questions**
```http
GET /api/statement-processor/{session_id}/questions
```
**Response:**
```json
{
  "status": "success",
  "companies_requiring_review": [
    {
      "statement_id": "stmt-001",
      "extracted_company": "Abar Abstract",
      "current_destination": "Foreign",
      "page_info": "page 1 of 1",
      "questions": [
        {
          "question_id": "q001",
          "dnm_company": "Joe Abstract",
          "similarity_percentage": "78.5%"
        },
        {
          "question_id": "q002", 
          "dnm_company": "Mama Abstract",
          "similarity_percentage": "72.1%"
        },
        {
          "question_id": "q003",
          "dnm_company": "Rachid Abstract Services",
          "similarity_percentage": "65.3%"
        }
      ]
    },
    {
      "statement_id": "stmt-002",
      "extracted_company": "XYZ Corp Inc",
      "current_destination": "Natio Single", 
      "page_info": "page 2 of 1",
      "questions": [
        {
          "question_id": "q004",
          "dnm_company": "XYZ Corporation",
          "similarity_percentage": "85.2%"
        },
        {
          "question_id": "q005",
          "dnm_company": "XYZ Industries LLC", 
          "similarity_percentage": "67.8%"
        }
      ]
    }
  ],
  "total_questions": 5,
  "total_companies_to_review": 2
}
```

### **6. Submit Answers**
```http
POST /api/statement-processor/{session_id}/answers
Content-Type: application/json
```
**Request Body:**
```json
{
  "answers": {
    "q001": "yes",
    "q002": "no",
    "q003": "yes", 
    "q004": "no",
    "q005": "skip"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Answers applied successfully", 
  "answers_processed": 5,
  "companies_updated": 2,
  "dnm_matches_created": 2
}
```

### **7. Download Results**
```http
GET /api/statement-processor/{session_id}/download
```
**Response:** File download (TXT containing processing results)

### **8. Session Status**
```http
GET /api/statement-processor/{session_id}/status
```
**Response:**
```json
{
  "status": "success",
  "session": {
    "session_id": "uuid",
    "status": "completed",
    "created_at": "2024-01-15T10:00:00Z",
    "statements_count": 150,
    "questions_count": 12
  }
}
```

## **Invoice Processor API Endpoints**

### **1. Upload and Process Invoice**
```http
POST /api/invoice-processor
Content-Type: multipart/form-data
```
**Form Data:**
- `file`: PDF file containing invoices

**Response:**
```json
{
  "message": "Invoices separated successfully. Find PDF files in your downloads.",
  "success": true,
  "zip_filename": "InvoiceGroup1075938_1204657_1204661_1207520_1207522_1213466_1242170.zip",
  "download_url": "/api/invoice-processor/downloads/InvoiceGroup1075938_1204657_1204661_1207520_1207522_1213466_1242170.zip"
}
```

### **2. Download Separated Invoices**
```http
GET /api/invoice-processor/downloads/{zip_filename}
```
**Response:** ZIP file download containing separated invoice PDFs

### **3. Clear Results**
```http
POST /api/invoice-processor/clear_results
```
**Response:**
```json
{
  "status": "success"
}
```

### **4. Delete All Results**
```http
POST /api/invoice-processor/delete_separate_results
```
**Response:**
```json
{
  "status": "success"
}
```

##  **Frontend Integration Examples**

### **React Integration**

```javascript
import React, { useState } from 'react';

const StatementProcessor = () => {
  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});

  const API_BASE = 'https://your-app.railway.app';

  // Step 1: Create session
  const createSession = async () => {
    const response = await fetch(`${API_BASE}/api/statement-processor`, {
      method: 'POST'
    });
    const data = await response.json();
    setSessionId(data.session_id);
    return data.session_id;
  };

  // Step 2: Upload files  
  const uploadFiles = async (pdfFile, excelFile) => {
    const formData = new FormData();
    formData.append('pdf', pdfFile);
    formData.append('excel', excelFile);

    const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  };

  // Step 3: Process files
  const processFiles = async () => {
    const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/process`, {
      method: 'POST'
    });
    return response.json();
  };

  // Step 4: Get questions
  const getQuestions = async () => {
    const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/questions`);
    const data = await response.json();
    setQuestions(data.questions);
    return data;
  };

  // Step 5: Submit answers
  const submitAnswers = async () => {
    const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/answers`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ answers })
    });
    return response.json();
  };

  // Step 6: Download results
  const downloadResults = async () => {
    const response = await fetch(`${API_BASE}/api/statement-processor/${sessionId}/download`);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `results_${sessionId.substring(0,8)}.txt`;
    a.click();
  };

  return (
    <div>
      {/* File upload UI */}
      {/* Questions UI */}
      {/* Download UI */}
    </div>
  );
};

export default StatementProcessor;
```

### **Pure JavaScript Integration**

```javascript
class StatementProcessorAPI {
  constructor(baseUrl = 'https://your-app.railway.app') {
    this.baseUrl = baseUrl;
    this.sessionId = null;
  }

  async createSession() {
    const response = await fetch(`${this.baseUrl}/api/statement-processor`, {
      method: 'POST'
    });
    const data = await response.json();
    this.sessionId = data.session_id;
    return data;
  }

  async uploadFiles(pdfFile, excelFile) {
    const formData = new FormData();
    formData.append('pdf', pdfFile);
    formData.append('excel', excelFile);

    const response = await fetch(`${this.baseUrl}/api/statement-processor/${this.sessionId}/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }

  async processFiles() {
    const response = await fetch(`${this.baseUrl}/api/statement-processor/${this.sessionId}/process`, {
      method: 'POST'
    });
    return response.json();
  }

  async getQuestions() {
    const response = await fetch(`${this.baseUrl}/api/statement-processor/${this.sessionId}/questions`);
    return response.json();
  }

  async submitAnswers(answers) {
    const response = await fetch(`${this.baseUrl}/api/statement-processor/${this.sessionId}/answers`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ answers })
    });
    return response.json();
  }

  async downloadResults() {
    const response = await fetch(`${this.baseUrl}/api/statement-processor/${this.sessionId}/download`);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `statement_results_${this.sessionId.substring(0,8)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

// Usage
const api = new StatementProcessorAPI();
await api.createSession();
await api.uploadFiles(pdfFile, excelFile); 
await api.processFiles();
const questions = await api.getQuestions();
// ... handle questions UI ...
await api.submitAnswers(userAnswers);
await api.downloadResults();
```

### **Python Client Integration**

```python
import requests
import json

class StatementProcessorClient:
    def __init__(self, base_url="https://your-app.railway.app"):
        self.base_url = base_url
        self.session_id = None
    
    def create_session(self):
        response = requests.post(f"{self.base_url}/api/statement-processor")
        data = response.json()
        self.session_id = data["session_id"]
        return data
    
    def upload_files(self, pdf_path, excel_path):
        files = {
            'pdf': open(pdf_path, 'rb'),
            'excel': open(excel_path, 'rb')
        }
        response = requests.post(
            f"{self.base_url}/api/statement-processor/{self.session_id}/upload",
            files=files
        )
        return response.json()
    
    def process_files(self):
        response = requests.post(
            f"{self.base_url}/api/statement-processor/{self.session_id}/process"
        )
        return response.json()
    
    def get_questions(self):
        response = requests.get(
            f"{self.base_url}/api/statement-processor/{self.session_id}/questions"
        )
        return response.json()
    
    def submit_answers(self, answers):
        response = requests.post(
            f"{self.base_url}/api/statement-processor/{self.session_id}/answers",
            json={"answers": answers}
        )
        return response.json()
    
    def download_results(self, save_path):
        response = requests.get(
            f"{self.base_url}/api/statement-processor/{self.session_id}/download"
        )
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path

# Usage Example
client = StatementProcessorClient()
client.create_session()
client.upload_files("statement.pdf", "dnm_list.xlsx")
client.process_files()

questions = client.get_questions()
answers = {}
for q in questions["questions"]:
    # Handle manual review - show question to user
    user_choice = input(f"Is {q['company_name']} same as {q['similar_to']}? (yes/no/skip): ")
    answers[q['company_name']] = user_choice

client.submit_answers(answers)
client.download_results("results.txt")
```

##  **Performance & Optimization**

### **Time Complexity: O(n)**
- **Pre-compiled regex patterns** for fast text extraction
- **Efficient fuzzy matching** using optimized string algorithms  
- **Memory management** with temporary file cleanup
- **Batch processing** for large PDF files

### **Resource Usage**
- **Memory**: ~50MB base + ~1MB per PDF page
- **CPU**: Moderate during processing, idle during Q&A
- **Storage**: Temporary files cleaned automatically

### **Railway Free Tier Optimization**
- **Memory limit**: 512MB (well within bounds)
- **CPU limit**: Shared CPU (optimized for efficiency)
- **Network**: 100GB bandwidth/month
- **Sleep mode**: Handles cold starts gracefully

##  **Security & Best Practices**

### **File Validation**
```python
# Validate file types
ALLOWED_PDF = {'pdf'}
ALLOWED_EXCEL = {'xlsx', 'xls'}

def validate_file(file, allowed_types):
    if '.' not in file.filename:
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    return ext in allowed_types
```

### **Error Handling**
```javascript
// Frontend error handling
try {
  const response = await fetch('/api/statement-processor', {method: 'POST'});
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data = await response.json();
  if (data.status !== 'success') {
    throw new Error(data.error || 'API error');
  }
  return data;
} catch (error) {
  console.error('API call failed:', error);
  // Handle error in UI
}
```

### **Rate Limiting & Sessions**
- **Session-based processing** prevents interference
- **Automatic cleanup** of temporary files
- **Memory management** prevents resource exhaustion
- **CORS properly configured** for browser security

##  **Deployment Guide**

### **Railway Deployment**

1. **Prepare files:**
```bash
# Main API file should be named app.py
cp real_processing_api.py app.py  # For real processing
```

2. **Create Procfile:**
```
web: python app.py
```

3. **Create railway.json:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "herokuish"
  },
  "deploy": {
    "startCommand": "python app.py",
    "restartPolicyType": "ON_FAILURE", 
    "restartPolicyMaxRetries": 10
  }
}
```

4. **Requirements:**
```txt
Flask==2.3.3
PyMuPDF==1.23.5
PyPDF2==3.0.1
openpyxl==3.1.2
thefuzz==0.19.0
```

5. **Deploy:**
```bash
git add .
git commit -m "Deploy Statement Processing API"
git push origin main
# Connect to Railway and deploy
```

##  **Testing**

### **Local Testing**
```bash
# Start the API
python app.py

# Test health endpoint  
curl http://localhost:8000/health

# Test session creation
curl -X POST http://localhost:8000/api/statement-processor
```

### **Integration Testing**
Use the provided test API for frontend development:
```bash
# Start test API (returns simulated data)
python minimal_test_api.py  # Port 8000

# Start real API (processes actual files)  
python real_processing_api.py  # Port 9000
```

### **Frontend Testing**
Use the frontend demo server for complete testing environment with:
- **Documentation mode**: API reference and examples
- **Live testing mode**: Real file uploads and processing
- **Interactive Q&A**: Manual review simulation
- **Download testing**: Result file generation

##  **Complete Integration Workflow**

### **1. Session Lifecycle**
```
Create Session → Upload Files → Process → Get Questions → Submit Answers → Download Results
     ↓              ↓             ↓           ↓              ↓                ↓
  session_id    file storage   extraction   manual_review   finalization    cleanup
```

### **2. Error Recovery**
- **Network errors**: Retry with exponential backoff
- **File errors**: Validate before upload
- **Processing errors**: Check session status
- **Timeout errors**: Increase timeout for large files

### **3. UI/UX Recommendations**
- **Progress indicators** during processing
- **File validation** before upload  
- **Question batching** for large datasets
- **Auto-save** answers during review
- **Download confirmation** with file info

##  **API Response Status Codes**

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Session or endpoint not found |
| 500 | Server Error | Internal processing error |

## 🆘 **Troubleshooting**

### **Common Issues**

**1. "Session not found" Error**
- Verify session_id is correct
- Check if session expired (server restart)
- Create new session if needed

**2. File Upload Fails**
- Verify file types (PDF + Excel only)
- Check file size limits 
- Ensure proper Content-Type headers

**3. Processing Stuck**
- Check API response error messages
- Verify PDF is text-readable
- Ensure Excel has proper DNM format

**4. Questions Not Loading**
- Verify processing completed successfully
- Check network connectivity
- Try refreshing session status

**5. Download Issues**
- Ensure answers were submitted
- Check browser popup blockers
- Verify session is finalized

---

**This API is production-ready and optimized for Railway's free tier with enterprise-grade features and complete documentation for seamless integration! **