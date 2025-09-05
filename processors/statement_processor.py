#!/usr/bin/env python3
"""
Enhanced Statement Processing System
====================================

Integrates the minimal processor improvements into a class-based architecture
suitable for web API usage. Maintains the clean formatting and enhanced 
features while providing proper encapsulation for different input sources.

Key Features:
- Enhanced company name extraction with 4 regex patterns
- Improved fuzzy matching with 60%+ threshold  
- Interactive Q&A system with back navigation
- Professional output formatting
- API-compatible class structure

Version: 4.0 - Enhanced Production Ready
"""

import fitz
import json
import re
import os
import sys
import gc
import logging
from datetime import datetime
from pathlib import Path
from difflib import get_close_matches, SequenceMatcher
from PyPDF2 import PdfReader, PdfWriter
from openpyxl import load_workbook
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import OrderedDict


class StatementProcessor:
    """
    Enhanced statement processor with improved extraction methods.
    
    Integrates the minimal processor improvements while maintaining
    class-based architecture for API compatibility.
    """
    
    # Enhanced patterns from minimal processor
    PATTERNS = {
        'page': re.compile(r'Page\s*(\d+)\s*of\s*(\d+)', re.IGNORECASE),
        'total_due_subtotal': re.compile(r'Subtotal\s+\$[\d,]+\.\d{2}\s+([^\n\r]+?)\s+Total Due\s+\$[\d,]+\.\d{2}', re.IGNORECASE | re.MULTILINE),
        'total_due_multiline': re.compile(r'([^\n\r]+\n[^\n\r]*?)\s+Total Due\s+\$[\d,]+\.\d{2}', re.IGNORECASE | re.MULTILINE),
        'total_due_line': re.compile(r'(\S[^\n\r]*?)\s+Total Due\s+\$[\d,]+\.\d{2}', re.IGNORECASE | re.MULTILINE),
        'business_suffix': re.compile(r'\b(?:inc|incorporated|corp|corporation|llc|ltd|limited|llp|lp|pc|pa|pllc|plc|co|company|companies|enterprise|enterprises|group|groups|holding|holdings|international|intl|global|solutions|services|systems|technologies|tech|industries|foundation|trust|association|society|institute|center|centre|organization|org)\b', re.IGNORECASE),
        'clean_text': re.compile(r'[\s,.()\-_&]+'),
        'whitespace': re.compile(r'\s+')
    }
    
    US_STATES = frozenset([
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID",
        "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS",
        "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK",
        "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", 
        "WV", "WI", "WY", "DC"
    ])
    
    START_MARKERS = ["914.949.9618", "302.703.8961", "www.unitedcorporate.com", "AR@UNITEDCORPORATE.COM"]
    END_MARKER = "STATEMENT OF OPEN INVOICE(S)"
    SKIP_LINES = {"Statement Date:", "Total Due:", "www.unitedcorporate.com", "Amount", "Invoice Number", "Description", "Invoice Date", "Invoice Number Description Invoice Date Amount"}
    
    def __init__(self, pdf_path: str, excel_path: str):
        """Initialize processor with file paths for API usage."""
        self.pdf_path = Path(pdf_path)
        self.excel_path = Path(excel_path)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Validate file paths immediately
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
        
        # Load and pre-process DNM companies for O(1) lookups
        self.dnm_companies, self.normalized_company_map = self._load_dnm_companies()
        
        # Cache for processed pages to avoid reprocessing
        self._processed_pages: Set[int] = set()
        
        # Extraction logging for analysis
        self.extraction_log = []
        
        # Memory optimization
        gc.collect()
    


    def _load_dnm_companies(self) -> Tuple[List[str], Dict[str, str]]:
        """Load and pre-process DNM companies for O(1) lookups."""
        try:
            workbook = load_workbook(self.excel_path, read_only=True)
            worksheet = workbook['10-2018']
            
            companies = []
            normalized_map = {}
            
            # Skip first 3 rows (2 header rows + 1 for 0-indexing)
            for row in worksheet.iter_rows(min_row=4, max_col=1, values_only=True):
                cell_value = row[0]
                if cell_value and str(cell_value).strip() and not str(cell_value).lower().startswith('name'):
                    company = str(cell_value).strip()
                    companies.append(company)
                    
                    # Create normalized mapping for O(1) lookups
                    normalized = str(company).lower().strip()
                    normalized = self.PATTERNS['business_suffix'].sub('', normalized)
                    normalized = self.PATTERNS['clean_text'].sub('', normalized).strip()
                    if normalized:
                        normalized_map[normalized] = company
            
            workbook.close()
            return companies, normalized_map
            
        except Exception as e:
            raise RuntimeError(f"Failed to load DNM companies: {e}")
    


    def _find_company_match(self, company_name: str) -> Tuple[Optional[str], List[Dict[str, str]]]:
        """Enhanced company matching with improved fuzzy logic."""
        # O(1) exact match check
        if company_name in self.dnm_companies:
            return company_name, []
        
        # O(1) normalized exact match
        normalized = str(company_name).lower().strip()
        normalized = self.PATTERNS['business_suffix'].sub('', normalized)
        normalized = self.PATTERNS['clean_text'].sub('', normalized).strip()
        
        if normalized in self.normalized_company_map:
            return self.normalized_company_map[normalized], []
        
        # Enhanced fuzzy matching: Check ALL companies above 60% threshold
        similar_matches = []
        if normalized:
            for norm_company, original_company in self.normalized_company_map.items():
                similarity_score = SequenceMatcher(None, normalized, norm_company).ratio() * 100
                if similarity_score >= 60.0:
                    similar_matches.append({
                        "company_name": original_company,
                        "percentage": f"{round(similarity_score, 1)}%"
                    })
            
            # Sort by similarity score (highest first)
            similar_matches.sort(key=lambda x: float(x["percentage"].replace('%', '')), reverse=True)
        
        return None, similar_matches
    


    def _detect_location(self, text: str) -> str:
        """Detect location using optimized state detection."""
        text_upper = f" {text.upper()} "
        return "National" if any(f" {state} " in text_upper for state in self.US_STATES) else "Foreign"
    


    def _determine_destination_enhanced(self, exact_match: Optional[str], text: str, location: str, 
                            pages: int, best_percentage: float, has_email: bool) -> str:
        """Enhanced destination logic with improved accuracy."""
        if exact_match:
            return "DNM"
        if has_email:
            return "DNM"
        if best_percentage >= 90.0:
            return "DNM"
        
        if location == "Foreign":
            return "Foreign"
        return "Natio Single" if pages == 1 else "Natio Multi"
    


    def _extract_company_name_enhanced(self, text: str, lines: List[str]) -> Tuple[str, str, bool, str]:
        """Enhanced company name extraction using 4 patterns in priority order."""
        fallback_company = lines[0].strip() if lines else "Unknown"
        extraction_method, fallback_used, fallback_reason = "unknown", False, ""
        
        # Pattern 1: Subtotal pattern (highest priority)
        match = self.PATTERNS['total_due_subtotal'].search(text)
        if match:
            company = self.PATTERNS['whitespace'].sub(' ', match.group(1).strip()).strip()
            if company.startswith("Amount "):
                company = company[7:].strip()
            extraction_method = "subtotal_pattern"
        else:
            # Pattern 2: Multiline pattern
            match = self.PATTERNS['total_due_multiline'].search(text)
            if match:
                company = self.PATTERNS['whitespace'].sub(' ', match.group(1).replace('\n', ' ').strip()).strip()
                if company.startswith("Amount "):
                    company = company[7:].strip()
                extraction_method = "multiline_pattern"
                
                # Fallback if too long
                if len(company) > 100:
                    match = self.PATTERNS['total_due_line'].search(text)
                    if match:
                        company = self.PATTERNS['whitespace'].sub(' ', match.group(1).strip()).strip()
                        extraction_method = "line_pattern"
                    if len(company) > 100:
                        company, extraction_method, fallback_used, fallback_reason = fallback_company, "fallback", True, "Pattern extracted text too long"
            else:
                # Pattern 3: Line pattern
                match = self.PATTERNS['total_due_line'].search(text)
                if match:
                    company = self.PATTERNS['whitespace'].sub(' ', match.group(1).strip()).strip()
                    if company.startswith("Amount "):
                        company = company[7:].strip()
                    extraction_method = "line_pattern"
                    
                    if len(company) > 100:
                        company, extraction_method, fallback_used, fallback_reason = fallback_company, "fallback", True, "Line pattern too long"
                else:
                    # Pattern 4: Fallback to first line
                    company, extraction_method, fallback_used, fallback_reason = fallback_company, "fallback", True, "No patterns found"
        
        return company, extraction_method, fallback_used, fallback_reason
    


    def _extract_statement_data(self, text: str, page_num: int) -> Optional[Dict[str, Any]]:
        """Enhanced statement data extraction with improved company name detection."""
        # Parse page information
        page_match = self.PATTERNS['page'].search(text)
        current_page, total_pages = (int(page_match.group(1)), int(page_match.group(2))) if page_match else (1, 1)
        
        # Find content boundaries
        start_pos = min((text.find(marker) for marker in self.START_MARKERS if marker in text), default=-1)
        end_pos = text.find(self.END_MARKER)
        
        if start_pos == -1 or end_pos == -1 or start_pos >= end_pos:
            return None
        
        # Extract and clean content
        content = text[start_pos:end_pos]
        for marker in self.START_MARKERS:
            content = content.replace(marker, '')
        
        lines = [
            line.strip() for line in content.splitlines()
            if line.strip() and not any(skip in line for skip in self.SKIP_LINES)
        ]
        
        if not lines:
            return None
        
        # Enhanced company name extraction
        fallback_company = lines[0].strip()
        company, extraction_method, fallback_used, fallback_reason = self._extract_company_name_enhanced(text, lines)
        
        # Log extraction differences for analysis
        if company.strip() != fallback_company.strip():
            self.extraction_log.append({
                'page_num': page_num, 'current_page': current_page, 'total_pages': total_pages,
                'old_method': fallback_company, 'new_method': company,
                'extraction_method': extraction_method, 'match': company.strip() == fallback_company.strip()
            })
        
        # Process remaining content
        rest_text = "\n".join(lines[1:])
        location = self._detect_location(rest_text)
        exact_match, similar_matches = self._find_company_match(company)
        
        # Calculate page information
        if total_pages == 1:
            page_range = str(page_num)
            first_page = page_num
        else:
            start_page = page_num - (current_page - 1)
            page_range = "-".join(map(str, range(start_page, start_page + total_pages)))
            first_page = start_page
        
        # Determine processing flags
        has_email = "email" in rest_text.lower()
        best_match = similar_matches[0] if similar_matches else None
        best_percentage = float(best_match["percentage"].replace('%', '')) if best_match else 0
        is_high_confidence = best_percentage >= 90.0
        
        manual_required = False
        ask_question = False
        
        if not (has_email or is_high_confidence or exact_match):
            manual_required = len(similar_matches) > 0
            if manual_required:
                ask_question = best_percentage < 90.0
        
        # Determine destination
        destination = self._determine_destination_enhanced(exact_match, rest_text, location, total_pages, best_percentage, has_email)
        
        # Build result with enhanced data
        result = OrderedDict()
        result["company_name"] = company
        if company.strip() != fallback_company.strip():
            result["unusedCompanyName"] = fallback_company
        result["exact_match"] = exact_match
        result["similar_matches"] = similar_matches
        result["manual_required"] = manual_required
        result["ask_question"] = ask_question
        result["rest_of_lines"] = rest_text
        result["location"] = location
        result["paging"] = f"page {current_page} of {total_pages}"
        result["number_of_pages"] = str(total_pages)
        result["page_number_in_uploaded_pdf"] = page_range
        result["first_page_number"] = first_page
        result["destination"] = destination
        result["extraction_method"] = extraction_method
        result["fallbackUsed"] = fallback_used
        if fallback_used:
            result["fallbackReason"] = fallback_reason
            
        return result
    


    def extract_statements(self) -> List[Dict[str, Any]]:
        """Extract all statements from PDF with enhanced processing."""
        try:
            doc = fitz.open(str(self.pdf_path))
            statements = []
            
            print(f"Processing {len(doc)} pages with {len(self.dnm_companies)} DNM companies loaded...")
            
            for page_idx in range(len(doc)):
                page_num = page_idx + 1
                
                if page_num in self._processed_pages:
                    continue
                
                page_text = doc.load_page(page_idx).get_text()
                
                # Check for statement boundaries
                page_match = self.PATTERNS['page'].search(page_text)
                if not page_match:
                    continue
                
                start_pos = min((page_text.find(marker) for marker in self.START_MARKERS if marker in page_text), default=-1)
                end_pos = page_text.find(self.END_MARKER)
                if start_pos == -1 or end_pos == -1:
                    continue
                
                # Enhanced: Jump to last page for multi-page statements
                total_pages = int(page_match.group(2))
                current_page = int(page_match.group(1))
                start_page = page_num - (current_page - 1)
                last_page_num = start_page + total_pages - 1
                
                if last_page_num <= len(doc):
                    # Process the last page (most efficient for company extraction)
                    last_page_text = doc.load_page(last_page_num - 1).get_text()
                    statement_data = self._extract_statement_data(last_page_text, last_page_num)
                    
                    if statement_data:
                        statements.append(statement_data)
                        print(f" Extracted: {statement_data['company_name']}")
                        
                        # Mark all pages as processed
                        self._processed_pages.update(range(start_page, last_page_num + 1))
            
            doc.close()
            
            # Add extraction log to results for analysis
            for statement in statements:
                statement['_extraction_log'] = self.extraction_log
            
            return statements
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract statements: {e}")
    


    def process_interactive_questions(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhanced interactive question processing with back navigation."""
        questions_needed = [stmt for stmt in statements if stmt.get('ask_question', False)]
        
        if not questions_needed:
            print("No manual questions required.")
            return statements
        
        print(f"\nFound {len(questions_needed)} companies requiring manual review:")
        
        skip_all = False
        history = []  # Track history for back navigation
        i = 0  # Current question index
        
        while i < len(questions_needed):
            if skip_all:
                for j in range(i, len(questions_needed)):
                    questions_needed[j]['user_answered'] = 'skip'
                break
            
            statement = questions_needed[i]
            company_name = statement.get('company_name', 'Unknown')
            similar_matches = statement.get('similar_matches', [])
            
            if similar_matches:
                best_match = similar_matches[0]
                print(f"\nQuestion {i + 1} of {len(questions_needed)}:")
                print(f"Company '{company_name}' is similar to '{best_match['company_name']}' ({best_match['percentage']})")
                print("Are they the same company? (y/n/s to skip all/p to go back)")
                
                while True:
                    try:
                        response = input("> ").strip().lower()
                        
                        if response == 'y':
                            # Save current state to history before making changes
                            history.append({
                                'index': i,
                                'statement_state': {
                                    'destination': statement.get('destination'),
                                    'user_answered': statement.get('user_answered')
                                }
                            })
                            
                            statement['destination'] = 'DNM'
                            statement['user_answered'] = 'yes'
                            print(f" Marked '{company_name}' as DNM")
                            i += 1
                            break
                            
                        elif response == 'n':
                            # Save current state to history before making changes
                            history.append({
                                'index': i,
                                'statement_state': {
                                    'destination': statement.get('destination'),
                                    'user_answered': statement.get('user_answered')
                                }
                            })
                            
                            statement['user_answered'] = 'no'
                            print(f" Kept '{company_name}' as {statement['destination']}")
                            i += 1
                            break
                            
                        elif response == 's':
                            skip_all = True
                            statement['user_answered'] = 'skip'
                            print(" Skipping remaining questions")
                            break
                            
                        elif response == 'p':
                            if not history:
                                print("No previous questions to go back to")
                                continue
                            
                            # Restore previous state
                            previous = history.pop()
                            prev_index = previous['index']
                            prev_state = previous['statement_state']
                            
                            # Restore the previous statement's state
                            prev_statement = questions_needed[prev_index]
                            prev_statement['destination'] = prev_state['destination']
                            if 'user_answered' in prev_state and prev_state['user_answered'] is not None:
                                prev_statement['user_answered'] = prev_state['user_answered']
                            elif 'user_answered' in prev_statement:
                                del prev_statement['user_answered']
                            
                            i = prev_index  # Go back to previous question
                            print(f"↩ Going back to question {i + 1}")
                            break
                            
                        else:
                            print("Please enter 'y', 'n', 's', or 'p'")
                            
                    except (KeyboardInterrupt, EOFError):
                        print("\nOperation cancelled.")
                        sys.exit(0)
        
        return statements
    


    def create_split_pdfs(self, statements: List[Dict[str, Any]]) -> Dict[str, int]:
        """Create split PDFs with enhanced organization."""
        # Group statements by destination
        destinations = {"DNM": [], "Foreign": [], "Natio Single": [], "Natio Multi": []}
        
        for statement in statements:
            dest = statement.get('destination', '').strip()
            if dest in destinations:
                destinations[dest].append(statement)
        
        # Create output PDFs
        output_files = {
            "DNM": "DNM.pdf",
            "Foreign": "Foreign.pdf", 
            "Natio Single": "natioSingle.pdf",
            "Natio Multi": "natioMulti.pdf"
        }
        
        results = {}
        
        try:
            reader = PdfReader(str(self.pdf_path))
            total_pages = len(reader.pages)
            
            for dest, statements_list in destinations.items():
                if not statements_list:
                    continue
                
                writer = PdfWriter()
                pages_added = 0
                
                for statement in statements_list:
                    page_range = statement.get('page_number_in_uploaded_pdf', '')
                    for page_str in page_range.split('-'):
                        try:
                            page_num = int(page_str.strip()) - 1  # Convert to 0-based index
                            if 0 <= page_num < total_pages:
                                writer.add_page(reader.pages[page_num])
                                pages_added += 1
                        except ValueError:
                            continue
                
                if pages_added > 0:
                    output_path = output_files[dest]
                    with open(output_path, 'wb') as f:
                        writer.write(f)
                    results[dest] = pages_added
                    print(f" Created {output_path} with {pages_added} pages")
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Failed to create split PDFs: {e}")
    


    def save_results(self, statements: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """Save processing results with enhanced metadata."""
        if not output_path:
            today = datetime.now().strftime("%b%d%Y").lower()
            output_path = f"{today}.json"
            
            counter = 1
            while os.path.exists(output_path):
                output_path = f"{today}-{counter}.json"
                counter += 1
        
        # Extract and clean logs
        extraction_log = []
        for statement in statements:
            if '_extraction_log' in statement:
                extraction_log.extend(statement['_extraction_log'])
                del statement['_extraction_log']
        
        data = {
            "dnm_companies": self.dnm_companies,
            "extracted_statements": statements,
            "total_statements_found": len(statements),
            "processing_timestamp": datetime.now().isoformat(),
            "extraction_comparison_log": {
                "total_statements_with_different_extractions": len(extraction_log),
                "extraction_details": extraction_log,
                "summary": {
                    "extraction_methods_used": list(set(comp['extraction_method'] for comp in extraction_log)),
                    "pages_with_multiline_extraction": len([c for c in extraction_log if c['extraction_method'] == 'multiline_pattern']),
                    "pages_with_subtotal_extraction": len([c for c in extraction_log if c['extraction_method'] == 'subtotal_pattern']),
                    "pages_with_improved_accuracy": len([c for c in extraction_log if c['extraction_method'] != 'fallback'])
                }
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f" Results saved to {output_path}")
            return output_path
            
        except Exception as e:
            raise RuntimeError(f"Failed to save results: {e}")
    


    def run_complete_workflow(self, skip_questions: bool = False) -> bool:
        """Execute the complete enhanced workflow."""
        try:
            print("=" * 60)
            print("       ENHANCED STATEMENT PROCESSOR")
            print("=" * 60)
            print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Step 1: Extract statements
            print(" Step 1: Extracting statements from PDF...")
            statements = self.extract_statements()
            print(f" Extracted {len(statements)} statements")
            
            # Step 2: Process interactive questions (skip if requested)
            if not skip_questions:
                print("\n Step 2: Processing manual questions...")
                statements = self.process_interactive_questions(statements)
                print(" Manual questions processed")
            else:
                print("\n Step 2: Skipping interactive questions...")
                print(" Questions skipped for analysis")
            
            # Step 3: Save results
            print("\n Step 3: Saving results...")
            output_file = self.save_results(statements)
            print(" Results saved")
            
            if not skip_questions:
                # Step 4: Create split PDFs
                print("\n Step 4: Creating destination PDFs...")
                split_results = self.create_split_pdfs(statements)
                print(" PDFs created successfully")
                
                # Final summary
                print("\n" + "=" * 60)
                print(" WORKFLOW COMPLETED SUCCESSFULLY!")
                print("=" * 60)
                
                print(f"Total statements processed: {len(statements)}")
                print(f"JSON output: {output_file}")
                print("PDF outputs created:")
                for dest, pages in split_results.items():
                    print(f"  • {dest}: {pages} pages")
            else:
                # Analysis mode summary
                print("\n" + "=" * 60)
                print(" EXTRACTION COMPLETED FOR ANALYSIS")
                print("=" * 60)
                
                manual_count = sum(1 for s in statements if s.get('manual_required', False))
                ask_count = sum(1 for s in statements if s.get('ask_question', False))
                
                print(f"Total statements processed: {len(statements)}")
                print(f"Manual review required: {manual_count}")
                print(f"Ask question required: {ask_count}")
                print(f"JSON output: {output_file}")
            
            print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            print(f"\n Workflow failed: {e}")
            return False


# Standalone execution support (for testing)
def main() -> int:
    """Main entry point for standalone testing."""
    if len(sys.argv) < 3:
        print("Usage: python statement_processor.py <pdf_path> <excel_path>")
        return 1
    
    try:
        pdf_path = sys.argv[1]
        excel_path = sys.argv[2]
        
        processor = StatementProcessor(pdf_path, excel_path)
        skip_questions = '--skip-questions' in sys.argv
        success = processor.run_complete_workflow(skip_questions)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())