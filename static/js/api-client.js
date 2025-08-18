/**
 * API Client for Document Processing API
 * Handles communication with Railway-hosted backend
 */

class DocumentProcessingAPI {
    constructor() {
        this.baseUrl = window.API_BASE_URL || 'http://localhost:8000';
        this.sessionId = null;
    }

    // Health check
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return null;
        }
    }

    // Statement Processing API Methods
    async createSession() {
        const response = await fetch(`${this.baseUrl}/api/v1/session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        this.sessionId = data.session_id;
        return data;
    }

    async uploadFiles(pdfFile, excelFile) {
        const formData = new FormData();
        formData.append('pdf', pdfFile);
        formData.append('excel', excelFile);

        const response = await fetch(`${this.baseUrl}/api/v1/session/${this.sessionId}/upload`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }

    async processFiles() {
        const response = await fetch(`${this.baseUrl}/api/v1/session/${this.sessionId}/process`, {
            method: 'POST'
        });
        return await response.json();
    }

    async getQuestions() {
        const response = await fetch(`${this.baseUrl}/api/v1/session/${this.sessionId}/questions`);
        return await response.json();
    }

    async submitAnswers(answers) {
        const response = await fetch(`${this.baseUrl}/api/v1/session/${this.sessionId}/answers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answers })
        });
        return await response.json();
    }

    async downloadResults() {
        const response = await fetch(`${this.baseUrl}/api/v1/session/${this.sessionId}/download`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `statement_results_${this.sessionId.substring(0, 8)}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    // Invoice Processing API Methods
    async processInvoice(pdfFile) {
        const formData = new FormData();
        formData.append('file', pdfFile);

        const response = await fetch(`${this.baseUrl}/invoice-processor/`, {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }

    async downloadInvoiceResults(filename) {
        const response = await fetch(`${this.baseUrl}/invoice-processor/downloads/${filename}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    async clearInvoiceResults() {
        const response = await fetch(`${this.baseUrl}/invoice-processor/clear_results`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        return await response.json();
    }
}

// Global API instance
window.apiClient = new DocumentProcessingAPI();

// Status checker
async function checkAPIStatus() {
    const statusElement = document.getElementById('apiStatus');
    const urlElement = document.getElementById('apiUrl');
    
    if (!statusElement) return;
    
    try {
        const health = await window.apiClient.healthCheck();
        if (health && health.status === 'healthy') {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-indicator status-connected';
            if (urlElement) {
                urlElement.textContent = `API: ${window.apiClient.baseUrl}`;
            }
        } else {
            throw new Error('API not healthy');
        }
    } catch (error) {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'status-indicator status-disconnected';
        if (urlElement) {
            urlElement.textContent = `API: ${window.apiClient.baseUrl} (offline)`;
        }
    }
}

// Check API status on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    // Check every 30 seconds
    setInterval(checkAPIStatus, 30000);
});