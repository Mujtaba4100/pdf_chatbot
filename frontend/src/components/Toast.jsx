/**
 * Toast Notification Component
 * ============================
 * Displays temporary notification messages.
 */

import { useEffect } from 'react';

function Toast({ message, type, onClose }) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose();
        }, 5000);

        return () => clearTimeout(timer);
    }, [onClose]);

    const getIcon = () => {
        switch (type) {
            case 'success':
                return '✅';
            case 'error':
                return '❌';
            case 'warning':
                return '⚠️';
            default:
                return 'ℹ️';
        }
    };

    return (
        <div className={`toast toast-${type}`}>
            <span className="toast-icon">{getIcon()}</span>
            <span className="toast-message">{message}</span>
            <button className="toast-close" onClick={onClose}>✕</button>
        </div>
    );
}

function ToastContainer({ toasts, removeToast }) {
    return (
        <div className="toast-container">
            {toasts.map((toast) => (
                <Toast
                    key={toast.id}
                    message={toast.message}
                    type={toast.type}
                    onClose={() => removeToast(toast.id)}
                />
            ))}
        </div>
    );
}

export { Toast, ToastContainer };
export default ToastContainer;
