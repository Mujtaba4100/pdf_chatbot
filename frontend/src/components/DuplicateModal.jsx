/**
 * Duplicate Modal Component
 * =========================
 * Shows warning when a duplicate document is detected
 * and allows user to choose an action.
 */

function DuplicateModal({ duplicateInfo, onAction, isLoading }) {
    if (!duplicateInfo) return null;

    return (
        <div className="modal-overlay">
            <div className="modal">
                <div className="modal-header">
                    <span className="modal-icon">⚠️</span>
                    <h3>Duplicate Document Detected</h3>
                </div>
                
                <div className="modal-body">
                    <p>
                        The file <strong>"{duplicateInfo.filename}"</strong> appears 
                        to be a duplicate of an existing document.
                    </p>
                    {duplicateInfo.existing_filename && (
                        <p className="existing-file">
                            Existing file: <strong>{duplicateInfo.existing_filename}</strong>
                        </p>
                    )}
                    <p className="modal-question">
                        What would you like to do?
                    </p>
                </div>

                <div className="modal-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={() => onAction('use_existing')}
                        disabled={isLoading}
                    >
                        <span className="btn-icon">♻️</span>
                        Use Existing
                    </button>
                    <button
                        className="btn btn-warning"
                        onClick={() => onAction('replace')}
                        disabled={isLoading}
                    >
                        <span className="btn-icon">🔄</span>
                        Replace
                    </button>
                    <button
                        className="btn btn-danger"
                        onClick={() => onAction('cancel')}
                        disabled={isLoading}
                    >
                        <span className="btn-icon">❌</span>
                        Cancel
                    </button>
                </div>

                {isLoading && (
                    <div className="modal-loading">
                        <div className="spinner"></div>
                        <span>Processing...</span>
                    </div>
                )}
            </div>
        </div>
    );
}

export default DuplicateModal;
