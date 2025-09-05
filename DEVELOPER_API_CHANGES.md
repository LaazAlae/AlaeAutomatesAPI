# API Changes Report - Updated Statement Processor

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

**This update maintains 100% API compatibility while significantly improving accuracy, user experience, and output organization.**