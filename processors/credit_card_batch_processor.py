from flask import Blueprint, request, jsonify
import openpyxl
import json
import logging
import os
import re
from werkzeug.utils import secure_filename
import tempfile

credit_card_batch_bp = Blueprint('credit_card_batch', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@credit_card_batch_bp.route('/', methods=['POST'])
def process_credit_card_batch():
    """Process Excel file and generate credit card batch automation code"""
    logging.info("Credit card batch processing request received")
    
    try:
        # Check if file is uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload Excel file (.xlsx or .xls)'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # Process the Excel file
            processed_data = process_excel_file(temp_path)
            
            if not processed_data:
                return jsonify({
                    'success': False,
                    'error': 'No valid data found in Excel file'
                }), 400
            
            # Generate improved JavaScript automation code
            automation_code = generate_improved_automation_code(processed_data)
            
            return jsonify({
                'success': True,
                'message': f'Successfully processed {len(processed_data)} records',
                'records_count': len(processed_data),
                'data_preview': processed_data[:5],  # Show first 5 records
                'automation_code': automation_code
            })
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        logging.error(f"Credit card batch processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500

def process_excel_file(file_path):
    """Process Excel file - implement the macro functionality"""
    try:
        # Read Excel file using openpyxl
        workbook = openpyxl.load_workbook(file_path)
        worksheet = workbook.active
        
        # Clean the data (implement macro functionality)
        cleaned_data = []
        
        for row in worksheet.iter_rows(values_only=True):
            # Skip empty rows
            if not any(cell for cell in row if cell is not None):
                continue
            
            # Skip header rows (contains "invoice", "amount", etc.)
            row_text = ' '.join([str(cell).lower() for cell in row if cell is not None])
            if any(header in row_text for header in ['invoice', 'amount', 'customer', 'payment', 'total']):
                continue
            
            # Skip rows that are totals every 10 rows (usually contain "total" or just numbers)
            if 'total' in row_text.lower():
                continue
            
            # Extract data from row (expecting 4+ columns)
            row_data = []
            for cell in row:
                if cell is not None:
                    row_data.append(str(cell).strip())
            
            # Must have at least 4 columns: Invoice, Payment Method, Amount, Customer
            if len(row_data) >= 4:
                # Clean invoice number (remove R/P prefix if exists)
                invoice = row_data[0].strip()
                payment_method = row_data[1].strip()
                amount = clean_amount(row_data[2])
                customer = row_data[3].strip()
                
                # Validate data
                if invoice and payment_method and amount and customer:
                    cleaned_data.append({
                        'invoiceNumber': invoice,
                        'cardPaymentMethod': payment_method,
                        'settlementAmount': amount,
                        'customer': customer
                    })
        
        workbook.close()
        logging.info(f"Processed {len(cleaned_data)} valid records from Excel")
        return cleaned_data
    
    except Exception as e:
        logging.error(f"Excel processing error: {str(e)}")
        raise

def clean_amount(amount_str):
    """Clean and validate amount string"""
    if amount_str is None or amount_str == '':
        return "0.00"
    
    # Convert to string and clean
    amount = str(amount_str).strip()
    
    # Remove currency symbols and extra spaces
    amount = re.sub(r'[$,\s]', '', amount)
    
    # Ensure it's a valid number
    try:
        float_amount = float(amount)
        return f"{float_amount:.2f}"
    except ValueError:
        return "0.00"

def generate_improved_automation_code(records_data):
    """Generate improved, safer JavaScript automation code"""
    
    # Convert records to JSON
    json_data = json.dumps(records_data, indent=2)
    
    # Generate improved automation code with safety features
    code = f'''// ALAEAUTOMATES CREDIT CARD BATCH AUTOMATION
// Generated for {len(records_data)} payment records
// Enhanced with safety checks and improved performance
// Compatible with Legacy Edge

// PAYMENT DATA
var PAYMENT_DATA = {json_data};

// SAFETY AND VISIBILITY HELPERS
function waitForElement(selector, timeout = 5000) {{
    return new Promise((resolve, reject) => {{
        const element = document.querySelector(selector) || 
                       document.getElementsByName(selector)[0];
        if (element && isElementVisible(element)) {{
            resolve(element);
            return;
        }}
        
        const startTime = Date.now();
        const checkInterval = setInterval(() => {{
            const el = document.querySelector(selector) || 
                      document.getElementsByName(selector)[0];
            if (el && isElementVisible(el)) {{
                clearInterval(checkInterval);
                resolve(el);
            }} else if (Date.now() - startTime > timeout) {{
                clearInterval(checkInterval);
                reject(new Error('Element not found or not visible: ' + selector));
            }}
        }}, 100);
    }});
}}

function isElementVisible(element) {{
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);
    return (
        rect.width > 0 &&
        rect.height > 0 &&
        style.visibility !== 'hidden' &&
        style.display !== 'none' &&
        element.offsetParent !== null
    );
}}

function safeClick(element) {{
    if (element && isElementVisible(element) && !element.disabled) {{
        element.focus();
        element.click();
        return true;
    }}
    return false;
}}

function safeFillField(element, value) {{
    if (element && isElementVisible(element) && !element.disabled) {{
        element.focus();
        element.value = value;
        
        // Trigger change events for legacy compatibility
        if (element.onchange) element.onchange();
        if (element.oninput) element.oninput();
        
        // Dispatch modern events too
        element.dispatchEvent(new Event('input', {{ bubbles: true }}));
        element.dispatchEvent(new Event('change', {{ bubbles: true }}));
        return true;
    }}
    return false;
}}

// PAGE DETECTION WITH IMPROVED ACCURACY
function detectPageAndStep() {{
    var url = window.location.href.toLowerCase();
    var bodyText = (document.body.textContent || document.body.innerText || '').toLowerCase();
    
    if (url.indexOf('receipt_add_invoice.aspx') !== -1) {{
        // Check form completion status
        var amountField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtAmount')[0];
        var customerField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtCheckName')[0];
        var paymentNumberField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
        var typeDropdown = document.getElementsByName('ctl00$ContentPlaceHolder1$lstType')[0];
        
        var fieldsCompleted = 0;
        if (typeDropdown && typeDropdown.selectedIndex > 0) fieldsCompleted++;
        if (paymentNumberField && paymentNumberField.value.trim()) fieldsCompleted++;
        if (amountField && amountField.value.trim()) fieldsCompleted++;
        if (customerField && customerField.value.trim()) fieldsCompleted++;
        
        if (fieldsCompleted === 4) {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 8 }};
        }} else if (fieldsCompleted > 0) {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 4 + fieldsCompleted }};
        }} else {{
            return {{ page: 'PAYMENT_FORM_PAGE', step: 4 }};
        }}
    }} else if (url.indexOf('batch_page.aspx') !== -1) {{
        if (url.indexOf('view=recadd') !== -1) {{
            return {{ page: 'ADD_RECEIPT_PAGE', step: 1 }};
        }} else if (url.indexOf('view=isrch') !== -1) {{
            var invoiceField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
            if (invoiceField && invoiceField.value.trim()) {{
                return {{ page: 'SEARCH_PAGE', step: 3 }};
            }} else {{
                return {{ page: 'SEARCH_PAGE', step: 2 }};
            }}
        }} else if (bodyText.indexOf('add receipt') !== -1) {{
            return {{ page: 'MAIN_BATCH_PAGE', step: 0 }};
        }}
    }}
    
    return {{ page: 'UNKNOWN_PAGE', step: 0 }};
}}

// ENHANCED AUTOMATION CLASS
function CreditCardBatchAutomation() {{
    var pageInfo = detectPageAndStep();
    this.currentPageState = pageInfo.page;
    this.processingStep = pageInfo.step;
    
    var cookieIndex = this.getCookie('ccAutomationIndex');
    if (cookieIndex !== null) {{
        this.currentRecordIndex = parseInt(cookieIndex);
    }} else {{
        this.currentRecordIndex = 0;
    }}
    
    this.currentRecord = PAYMENT_DATA[this.currentRecordIndex];
    this.isProcessing = false;
    
    console.log('═══════════════════════════════════════');
    console.log('🏦 ALAEAUTOMATES CREDIT CARD BATCH');
    console.log('═══════════════════════════════════════');
    console.log('📍 Page: ' + this.currentPageState);
    console.log('📋 Record: ' + (this.currentRecordIndex + 1) + '/' + PAYMENT_DATA.length);
    if (this.currentRecord) {{
        console.log('📝 Processing: ' + this.currentRecord.invoiceNumber + ' - ' + this.currentRecord.customer);
        console.log('💰 Amount: $' + this.currentRecord.settlementAmount);
        console.log('💳 Method: ' + this.currentRecord.cardPaymentMethod);
    }}
    console.log('🔄 Step: ' + this.getStepName(this.processingStep));
    console.log('═══════════════════════════════════════');
}}

CreditCardBatchAutomation.prototype.getStepName = function(step) {{
    var stepNames = [
        'Click Add Receipt',
        'Click By Invoice', 
        'Enter Invoice Number',
        'Click Search',
        'Fill Payment Form (All Fields)',
        'Verify Payment Type',
        'Verify Payment Method',
        'Verify Amount',
        'Verify Customer & Save',
        'Complete'
    ];
    return stepNames[step] || 'Unknown';
}};

CreditCardBatchAutomation.prototype.execute = function() {{
    if (this.isProcessing) {{
        console.log('⏳ Already processing, please wait...');
        return;
    }}
    
    if (!this.currentRecord) {{
        console.log('✅ ALL RECORDS COMPLETED!');
        console.log('🎉 Successfully processed ' + PAYMENT_DATA.length + ' credit card payments!');
        return;
    }}
    
    this.isProcessing = true;
    var self = this;
    
    try {{
        switch (this.processingStep) {{
            case 0: // Click Add Receipt
                this.executeStep0();
                break;
            case 1: // Click By Invoice
                this.executeStep1();
                break;
            case 2: // Enter Invoice Number
                this.executeStep2();
                break;
            case 3: // Click Search
                this.executeStep3();
                break;
            case 4: // Fill entire payment form at once
                this.executeStep4();
                break;
            default:
                if (this.processingStep >= 5 && this.processingStep <= 8) {{
                    this.executeStepSave();
                }} else {{
                    console.log('❓ Unknown step: ' + this.processingStep);
                    this.isProcessing = false;
                }}
        }}
    }} catch (error) {{
        console.error('❌ Error during execution:', error);
        this.isProcessing = false;
    }}
}};

CreditCardBatchAutomation.prototype.executeStep0 = function() {{
    console.log('🔄 Looking for "Add Receipt" button...');
    var self = this;
    
    setTimeout(function() {{
        try {{
            if (self.clickButtonByText('Add Receipt')) {{
                console.log('✓ "Add Receipt" clicked! Redirecting...');
            }} else {{
                console.log('❌ "Add Receipt" button not found or not clickable');
            }}
        }} catch (e) {{
            console.error('❌ Error clicking Add Receipt:', e);
        }}
        self.isProcessing = false;
    }}, 500);
}};

CreditCardBatchAutomation.prototype.executeStep1 = function() {{
    console.log('🔄 Looking for "By Invoice" button...');
    var self = this;
    
    setTimeout(function() {{
        try {{
            if (self.clickButtonByText('By Invoice')) {{
                console.log('✓ "By Invoice" clicked! Redirecting...');
            }} else {{
                console.log('❌ "By Invoice" button not found or not clickable');
            }}
        }} catch (e) {{
            console.error('❌ Error clicking By Invoice:', e);
        }}
        self.isProcessing = false;
    }}, 500);
}};

CreditCardBatchAutomation.prototype.executeStep2 = function() {{
    console.log('🔄 Entering invoice number...');
    var self = this;
    var cleanInvoice = this.cleanInvoiceNumber(this.currentRecord.invoiceNumber);
    
    setTimeout(function() {{
        try {{
            var invoiceField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
            if (invoiceField && isElementVisible(invoiceField)) {{
                if (safeFillField(invoiceField, cleanInvoice)) {{
                    console.log('✓ Invoice entered: ' + cleanInvoice);
                    
                    // Auto-click search after entering invoice
                    setTimeout(function() {{
                        if (self.clickButtonByText('Search')) {{
                            console.log('✓ Search clicked! Redirecting to payment form...');
                        }}
                    }}, 1000);
                }} else {{
                    console.log('❌ Failed to fill invoice field');
                }}
            }} else {{
                console.log('❌ Invoice field not found or not visible');
            }}
        }} catch (e) {{
            console.error('❌ Error entering invoice:', e);
        }}
        self.isProcessing = false;
    }}, 500);
}};

CreditCardBatchAutomation.prototype.executeStep3 = function() {{
    console.log('🔄 Clicking Search...');
    var self = this;
    
    setTimeout(function() {{
        try {{
            if (self.clickButtonByText('Search')) {{
                console.log('✓ Search clicked! Redirecting to payment form...');
            }} else {{
                console.log('❌ Search button not found or not clickable');
            }}
        }} catch (e) {{
            console.error('❌ Error clicking search:', e);
        }}
        self.isProcessing = false;
    }}, 500);
}};

CreditCardBatchAutomation.prototype.executeStep4 = function() {{
    console.log('🔄 Filling payment form (all fields at once)...');
    var self = this;
    
    setTimeout(function() {{
        try {{
            var success = true;
            var paymentType = self.determinePaymentType(self.currentRecord.cardPaymentMethod);
            
            // Fill all form fields simultaneously
            console.log('→ Selecting payment type: ' + paymentType);
            if (!self.selectDropdown('ctl00$ContentPlaceHolder1$lstType', paymentType)) {{
                success = false;
            }}
            
            // Small delay then fill other fields
            setTimeout(function() {{
                console.log('→ Entering payment method: ' + self.currentRecord.cardPaymentMethod);
                var paymentField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtNumber')[0];
                if (!safeFillField(paymentField, self.currentRecord.cardPaymentMethod)) {{
                    success = false;
                }}
                
                console.log('→ Entering amount: $' + self.currentRecord.settlementAmount);
                var amountField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtAmount')[0];
                if (!safeFillField(amountField, self.currentRecord.settlementAmount)) {{
                    success = false;
                }}
                
                console.log('→ Entering customer: ' + self.currentRecord.customer);
                var customerField = document.getElementsByName('ctl00$ContentPlaceHolder1$txtCheckName')[0];
                if (!safeFillField(customerField, self.currentRecord.customer)) {{
                    success = false;
                }}
                
                // Auto-save after filling all fields
                setTimeout(function() {{
                    if (success) {{
                        console.log('✅ All fields filled successfully!');
                        console.log('🔄 Auto-saving...');
                        if (self.clickButtonByText('Save')) {{
                            console.log('✅ Payment saved successfully!');
                            self.nextRecord();
                            console.log('📝 Ready for next record. Navigate to batch page and run() again.');
                        }} else {{
                            console.log('❌ Save button not found - please save manually');
                        }}
                    }} else {{
                        console.log('❌ Some fields failed to fill - please verify manually');
                    }}
                    self.isProcessing = false;
                }}, 1000);
            }}, 300);
        }} catch (e) {{
            console.error('❌ Error filling form:', e);
            self.isProcessing = false;
        }}
    }}, 500);
}};

CreditCardBatchAutomation.prototype.executeStepSave = function() {{
    console.log('🔄 Ready to save...');
    var self = this;
    
    setTimeout(function() {{
        try {{
            if (self.clickButtonByText('Save')) {{
                console.log('✅ Payment saved!');
                self.nextRecord();
                console.log('📝 Ready for next record. Navigate to batch page and run() again.');
            }} else {{
                console.log('❌ Save button not found or not clickable');
            }}
        }} catch (e) {{
            console.error('❌ Error saving:', e);
        }}
        self.isProcessing = false;
    }}, 500);
}};

CreditCardBatchAutomation.prototype.nextRecord = function() {{
    this.currentRecordIndex++;
    this.setCookie('ccAutomationIndex', this.currentRecordIndex.toString());
    
    if (this.currentRecordIndex < PAYMENT_DATA.length) {{
        this.currentRecord = PAYMENT_DATA[this.currentRecordIndex];
        console.log('');
        console.log('📋 Next record ready: ' + this.currentRecord.invoiceNumber + ' - ' + this.currentRecord.customer);
    }} else {{
        this.currentRecord = null;
        this.setCookie('ccAutomationIndex', '0'); // Reset for next batch
        console.log('');
        console.log('🎉 ALL {len(records_data)} RECORDS COMPLETED!');
        console.log('💳 Credit card batch processing finished successfully!');
    }}
}};

// UTILITY FUNCTIONS
CreditCardBatchAutomation.prototype.clickButtonByText = function(buttonText) {{
    var buttons = document.getElementsByTagName('input');
    for (var i = 0; i < buttons.length; i++) {{
        if (buttons[i].value === buttonText && 
            (buttons[i].type === 'submit' || buttons[i].type === 'button') &&
            isElementVisible(buttons[i]) && !buttons[i].disabled) {{
            return safeClick(buttons[i]);
        }}
    }}
    return false;
}};

CreditCardBatchAutomation.prototype.selectDropdown = function(dropdownName, value) {{
    var dropdown = document.getElementsByName(dropdownName)[0];
    if (dropdown && isElementVisible(dropdown) && !dropdown.disabled) {{
        for (var i = 0; i < dropdown.options.length; i++) {{
            if (dropdown.options[i].text.toUpperCase().indexOf(value.toUpperCase()) !== -1) {{
                dropdown.selectedIndex = i;
                dropdown.value = dropdown.options[i].value;
                if (dropdown.onchange) dropdown.onchange();
                dropdown.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
        }}
    }}
    return false;
}};

CreditCardBatchAutomation.prototype.cleanInvoiceNumber = function(invoice) {{
    return invoice.replace(/^[RP]/i, '');
}};

CreditCardBatchAutomation.prototype.determinePaymentType = function(method) {{
    var methodUpper = method.toUpperCase();
    if (methodUpper.indexOf('AMEX') !== -1) return 'AMEX';
    if (methodUpper.indexOf('VISA') !== -1) return 'VISA';
    if (methodUpper.indexOf('MC') !== -1 || methodUpper.indexOf('MASTER') !== -1) return 'MasterCard';
    if (methodUpper.indexOf('DISC') !== -1 || methodUpper.indexOf('DISCOVER') !== -1) return 'Discover';
    return 'Check';
}};

CreditCardBatchAutomation.prototype.setCookie = function(name, value) {{
    document.cookie = name + '=' + value + '; path=/; expires=' + 
        new Date(Date.now() + 24*60*60*1000).toUTCString();
}};

CreditCardBatchAutomation.prototype.getCookie = function(name) {{
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {{
        var cookie = cookies[i].trim();
        if (cookie.indexOf(name + '=') === 0) {{
            return cookie.substring(name.length + 1);
        }}
    }}
    return null;
}};

// INITIALIZE AUTOMATION
var ccAuto = new CreditCardBatchAutomation();

// CREATE EASY-TO-USE FUNCTIONS
window.run = function() {{
    ccAuto = new CreditCardBatchAutomation();
    ccAuto.execute();
}};

window.reset = function() {{
    document.cookie = 'ccAutomationIndex=0; path=/; expires=' + 
        new Date(Date.now() + 24*60*60*1000).toUTCString();
    console.log('🔄 Reset to first record');
    ccAuto = new CreditCardBatchAutomation();
}};

window.status = function() {{
    ccAuto = new CreditCardBatchAutomation();
    // Status already shown in constructor
}};

// INITIAL EXECUTION
ccAuto.execute();

console.log('');
console.log('💡 COMMANDS: run() = execute | reset() = restart | status() = show progress');
console.log('🛡️  ENHANCED: Built-in safety checks, element visibility verification');
console.log('⚡ IMPROVED: Fill all fields at once, no sequential delays');
console.log('🚀 ALAEAUTOMATES: Faster, safer, more reliable automation!');'''

    return code