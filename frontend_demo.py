#!/usr/bin/env python3
"""
Frontend Demo Server - Local Development Only
This serves the HTML templates to demonstrate API usage.
The backend API should be running on Railway.
"""

from flask import Flask, render_template
import os

# Create separate Flask app for frontend demo
frontend_app = Flask(__name__)

# Configuration
API_BASE_URL = os.environ.get('API_URL', 'https://alaeautomatesapi.up.railway.app')
LOCAL_PORT = int(os.environ.get('FRONTEND_PORT', 3000))

@frontend_app.route('/')
def home():
    return render_template('index.html', api_url=API_BASE_URL)

@frontend_app.route('/monthly-statements')
def monthly_statements():
    return render_template('monthly_statements.html', api_url=API_BASE_URL)

@frontend_app.route('/invoice-separator')
def invoice_separator():
    return render_template('invoice_separator.html', api_url=API_BASE_URL)

@frontend_app.route('/credit-card-batch')
def credit_card_batch():
    return render_template('credit_card_batch.html', api_url=API_BASE_URL)

@frontend_app.route('/excel-formatter')
def excel_formatter():
    return render_template('excel_formatter.html', api_url=API_BASE_URL)

@frontend_app.route('/excel-comparison')
def excel_comparison():
    return render_template('excel_comparison.html', api_url=API_BASE_URL)

if __name__ == '__main__':
    print("=" * 60)
    print("FRONTEND DEMO SERVER")
    print("=" * 60)
    print(f"Frontend URL: http://localhost:{LOCAL_PORT}")
    print(f"Backend API: {API_BASE_URL}")
    print("=" * 60)
    print("Available pages:")
    print(f"  Home Page: http://localhost:{LOCAL_PORT}/")
    print(f"  Monthly Statements: http://localhost:{LOCAL_PORT}/monthly-statements")
    print(f"  Invoice Separator: http://localhost:{LOCAL_PORT}/invoice-separator")
    print(f"  Credit Card Batch: http://localhost:{LOCAL_PORT}/credit-card-batch")
    print(f"  Excel Formatter: http://localhost:{LOCAL_PORT}/excel-formatter")
    print(f"  Excel Comparison: http://localhost:{LOCAL_PORT}/excel-comparison")
    print("=" * 60)
    print("NOTE: Make sure your backend API is running on Railway!")
    print("Update API_URL environment variable to point to your Railway URL")
    print("=" * 60)
    
    frontend_app.run(
        host='127.0.0.1',  # Local only
        port=LOCAL_PORT,
        debug=True  # Enable debug for local development
    )