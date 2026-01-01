/**
 * PDF Upload Component
 * ====================
 * Handles multiple PDF file uploads with drag-and-drop support.
 */

import { useState, useRef } from 'react';

function PDFUpload({ onUpload, isLoading }) {
    const [dragActive, setDragActive] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);
    const fileInputRef = useRef(null);

    // Handle drag events
    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    // Handle drop event
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const files = Array.from(e.dataTransfer.files).filter(
            file => file.type === 'application/pdf'
        );
        
        if (files.length > 0) {
            setSelectedFiles(prev => [...prev, ...files]);
        }
    };

    // Handle file input change
    const handleFileChange = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(prev => [...prev, ...files]);
    };

    // Remove a file from selection
    const removeFile = (index) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    // Clear all selected files
    const clearFiles = () => {
        setSelectedFiles([]);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Handle upload
    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;
        
        await onUpload(selectedFiles);
        clearFiles();
    };

    return (
        <div className="pdf-upload">
            <h2>📄 Upload PDFs</h2>
            
            {/* Drag and Drop Zone */}
            <div
                className={`drop-zone ${dragActive ? 'active' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />
                <div className="drop-zone-content">
                    <span className="drop-icon">📁</span>
                    <p>Drag & drop PDF files here</p>
                    <p className="drop-hint">or click to browse</p>
                </div>
            </div>

            {/* Selected Files List */}
            {selectedFiles.length > 0 && (
                <div className="selected-files">
                    <h4>Selected Files ({selectedFiles.length})</h4>
                    <ul>
                        {selectedFiles.map((file, index) => (
                            <li key={index}>
                                <span className="file-name">{file.name}</span>
                                <span className="file-size">
                                    ({(file.size / 1024 / 1024).toFixed(2)} MB)
                                </span>
                                <button
                                    className="remove-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeFile(index);
                                    }}
                                >
                                    ✕
                                </button>
                            </li>
                        ))}
                    </ul>
                    
                    <div className="upload-actions">
                        <button
                            className="btn btn-secondary"
                            onClick={clearFiles}
                            disabled={isLoading}
                        >
                            Clear All
                        </button>
                        <button
                            className="btn btn-primary"
                            onClick={handleUpload}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Uploading...' : 'Upload PDFs'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default PDFUpload;
