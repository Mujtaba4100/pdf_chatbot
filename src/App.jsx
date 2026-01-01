/**
 * Multi-PDF RAG System - Main App Component
 * ==========================================
 * A production-ready RAG application with:
 * - Multiple PDF upload with duplicate detection
 * - Persistent embeddings using FAISS
 * - Question answering with source citations
 */

import { useState, useEffect, useCallback } from 'react';
import './App.css';

// Components
import PDFUpload from './components/PDFUpload';
import DocumentList from './components/DocumentList';
import DuplicateModal from './components/DuplicateModal';
import QuestionAnswer from './components/QuestionAnswer';
import StatsPanel from './components/StatsPanel';
import ToastContainer from './components/Toast';

// API Service
import * as api from './services/api';

function App() {
    // State management
    const [documents, setDocuments] = useState([]);
    const [stats, setStats] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isAsking, setIsAsking] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);
    const [answer, setAnswer] = useState('');
    const [sources, setSources] = useState([]);
    const [backendConnected, setBackendConnected] = useState(false);
    
    // Duplicate handling
    const [duplicateInfo, setDuplicateInfo] = useState(null);
    const [pendingFile, setPendingFile] = useState(null);
    
    // Toast notifications
    const [toasts, setToasts] = useState([]);

    // Add toast notification
    const addToast = useCallback((message, type = 'info') => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
    }, []);

    // Remove toast notification
    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    // Check backend connection and load initial data
    useEffect(() => {
        const initializeApp = async () => {
            try {
                await api.healthCheck();
                setBackendConnected(true);
                
                // Load documents and stats
                const [docs, statsData] = await Promise.all([
                    api.getDocuments(),
                    api.getStats()
                ]);
                
                setDocuments(docs);
                setStats(statsData);
                addToast('Connected to RAG backend', 'success');
            } catch (error) {
                setBackendConnected(false);
                addToast('Cannot connect to backend. Make sure the server is running.', 'error');
            }
        };

        initializeApp();
    }, [addToast]);

    // Refresh documents and stats
    const refreshData = async () => {
        try {
            const [docs, statsData] = await Promise.all([
                api.getDocuments(),
                api.getStats()
            ]);
            setDocuments(docs);
            setStats(statsData);
        } catch (error) {
            console.error('Error refreshing data:', error);
        }
    };

    // Handle PDF upload
    const handleUpload = async (files) => {
        setIsUploading(true);
        
        try {
            const results = await api.uploadPDFs(files);
            
            let successCount = 0;
            let duplicateCount = 0;
            
            for (const result of results) {
                if (result.status === 'success') {
                    successCount++;
                    addToast(`Uploaded: ${result.filename} (${result.chunks} chunks)`, 'success');
                } else if (result.status === 'duplicate') {
                    duplicateCount++;
                    // Store duplicate info and pending file
                    setDuplicateInfo(result);
                    setPendingFile(files.find(f => f.name === result.filename));
                } else if (result.status === 'error') {
                    addToast(`Error: ${result.filename} - ${result.message}`, 'error');
                }
            }
            
            if (successCount > 0) {
                await refreshData();
            }
            
            if (duplicateCount === 0) {
                addToast(`Upload complete: ${successCount} files processed`, 'success');
            }
            
        } catch (error) {
            addToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            setIsUploading(false);
        }
    };

    // Handle duplicate action
    const handleDuplicateAction = async (action) => {
        if (!pendingFile) return;
        
        setIsUploading(true);
        
        try {
            const result = await api.handleDuplicate(pendingFile, action);
            
            if (result.status === 'success') {
                addToast(result.message, 'success');
                await refreshData();
            } else if (result.status === 'cancelled') {
                addToast('Upload cancelled', 'info');
            } else {
                addToast(result.message, 'error');
            }
        } catch (error) {
            addToast(`Error: ${error.message}`, 'error');
        } finally {
            setDuplicateInfo(null);
            setPendingFile(null);
            setIsUploading(false);
        }
    };

    // Handle asking questions
    const handleAsk = async (question) => {
        setIsAsking(true);
        setAnswer('');
        setSources([]);
        
        try {
            const result = await api.askQuestion(question);
            setAnswer(result.answer);
            setSources(result.sources);
        } catch (error) {
            addToast(`Error: ${error.message}`, 'error');
        } finally {
            setIsAsking(false);
        }
    };

    // Handle document deletion
    const handleDelete = async (docId, filename) => {
        if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }
        
        setIsDeleting(true);
        
        try {
            await api.deleteDocument(docId);
            addToast(`Deleted: ${filename}`, 'success');
            await refreshData();
        } catch (error) {
            addToast(`Error deleting: ${error.message}`, 'error');
        } finally {
            setIsDeleting(false);
        }
    };

    return (
        <div className="app">
            {/* Header */}
            <header className="app-header">
                <h1>🔍 Multi-PDF RAG System</h1>
                <p className="subtitle">
                    Upload PDFs, ask questions, get AI-powered answers with source citations
                </p>
                <div className={`connection-status ${backendConnected ? 'connected' : 'disconnected'}`}>
                    {backendConnected ? '🟢 Connected' : '🔴 Disconnected'}
                </div>
            </header>

            {/* Main Content */}
            <main className="app-main">
                {/* Left Panel - Upload & Documents */}
                <div className="panel panel-left">
                    <PDFUpload 
                        onUpload={handleUpload}
                        isLoading={isUploading}
                    />
                    
                    <DocumentList
                        documents={documents}
                        onDelete={handleDelete}
                        isLoading={isDeleting}
                    />
                    
                    <StatsPanel stats={stats} />
                </div>

                {/* Right Panel - Q&A */}
                <div className="panel panel-right">
                    <QuestionAnswer
                        onAsk={handleAsk}
                        isLoading={isAsking}
                        answer={answer}
                        sources={sources}
                    />
                </div>
            </main>

            {/* Footer */}
            <footer className="app-footer">
                <p>
                    Built with FastAPI + FAISS + SentenceTransformers + Gemini + React
                </p>
            </footer>

            {/* Modals */}
            <DuplicateModal
                duplicateInfo={duplicateInfo}
                onAction={handleDuplicateAction}
                isLoading={isUploading}
            />

            {/* Toast Notifications */}
            <ToastContainer toasts={toasts} removeToast={removeToast} />
        </div>
    );
}

export default App;
