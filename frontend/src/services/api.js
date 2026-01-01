/**
 * API Service Module
 * ==================
 * Handles all communication with the backend RAG API.
 * Centralizes API calls for cleaner components.
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Upload multiple PDF files
 * @param {File[]} files - Array of PDF files to upload
 * @returns {Promise<Array>} Upload results for each file
 */
export async function uploadPDFs(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch(`${API_BASE_URL}/upload-pdfs`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Handle duplicate document with specified action
 * @param {File} file - The duplicate file
 * @param {string} action - Action to take: 'use_existing', 'replace', 'cancel'
 * @returns {Promise<Object>} Result of the action
 */
export async function handleDuplicate(file, action) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('action', action);

    const response = await fetch(`${API_BASE_URL}/handle-duplicate`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error(`Failed to handle duplicate: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Ask a question about uploaded documents
 * @param {string} question - The question to ask
 * @param {number} topK - Number of chunks to retrieve (optional)
 * @returns {Promise<Object>} Answer with sources
 */
export async function askQuestion(question, topK = 5) {
    const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, top_k: topK }),
    });

    if (!response.ok) {
        throw new Error(`Failed to get answer: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get list of all uploaded documents
 * @returns {Promise<Array>} List of document info
 */
export async function getDocuments() {
    const response = await fetch(`${API_BASE_URL}/documents`);

    if (!response.ok) {
        throw new Error(`Failed to get documents: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Delete a document
 * @param {string} docId - Document ID to delete
 * @returns {Promise<Object>} Delete result
 */
export async function deleteDocument(docId) {
    const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error(`Failed to delete document: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Get system statistics
 * @returns {Promise<Object>} System stats
 */
export async function getStats() {
    const response = await fetch(`${API_BASE_URL}/stats`);

    if (!response.ok) {
        throw new Error(`Failed to get stats: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Health check
 * @returns {Promise<Object>} Health status
 */
export async function healthCheck() {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
        throw new Error(`Backend is not healthy: ${response.statusText}`);
    }

    return response.json();
}
