/**
 * Document List Component
 * =======================
 * Displays all uploaded documents with delete functionality.
 */

function DocumentList({ documents, onDelete, isLoading }) {
    if (documents.length === 0) {
        return (
            <div className="document-list empty">
                <h2>📚 Uploaded Documents</h2>
                <p className="empty-message">
                    No documents uploaded yet. Upload PDFs to get started!
                </p>
            </div>
        );
    }

    // Format date nicely
    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="document-list">
            <h2>📚 Uploaded Documents ({documents.length})</h2>
            
            <div className="documents-grid">
                {documents.map((doc) => (
                    <div key={doc.doc_id} className="document-card">
                        <div className="document-icon">📄</div>
                        <div className="document-info">
                            <h4 className="document-name" title={doc.filename}>
                                {doc.filename}
                            </h4>
                            <div className="document-meta">
                                <span>📑 {doc.num_pages} pages</span>
                                <span>🧩 {doc.num_chunks} chunks</span>
                            </div>
                            <p className="document-date">
                                Uploaded: {formatDate(doc.upload_timestamp)}
                            </p>
                        </div>
                        <button
                            className="btn btn-danger btn-small"
                            onClick={() => onDelete(doc.doc_id, doc.filename)}
                            disabled={isLoading}
                            title="Delete document"
                        >
                            🗑️
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default DocumentList;
