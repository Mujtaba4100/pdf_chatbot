/**
 * Question Answer Component
 * =========================
 * Handles question input and displays answers with sources.
 */

import { useState } from 'react';

function QuestionAnswer({ onAsk, isLoading, answer, sources }) {
    const [question, setQuestion] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (question.trim() && !isLoading) {
            onAsk(question.trim());
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <div className="question-answer">
            <h2>💬 Ask Questions</h2>
            
            {/* Question Input */}
            <form onSubmit={handleSubmit} className="question-form">
                <div className="input-group">
                    <textarea
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask a question about your documents..."
                        rows={3}
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        className="btn btn-primary ask-btn"
                        disabled={!question.trim() || isLoading}
                    >
                        {isLoading ? (
                            <>
                                <div className="spinner-small"></div>
                                Thinking...
                            </>
                        ) : (
                            <>
                                <span className="btn-icon">🔍</span>
                                Ask
                            </>
                        )}
                    </button>
                </div>
                <p className="input-hint">Press Enter to ask or Shift+Enter for new line</p>
            </form>

            {/* Loading Indicator */}
            {isLoading && (
                <div className="loading-indicator">
                    <div className="loading-steps">
                        <div className="step active">
                            <span className="step-icon">🔄</span>
                            <span>Embedding question...</span>
                        </div>
                        <div className="step">
                            <span className="step-icon">🔍</span>
                            <span>Searching relevant chunks...</span>
                        </div>
                        <div className="step">
                            <span className="step-icon">🤖</span>
                            <span>Generating answer...</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Answer Display */}
            {answer && !isLoading && (
                <div className="answer-section">
                    <h3>📝 Answer</h3>
                    <div className="answer-content">
                        {answer.split('\n').map((paragraph, index) => (
                            paragraph.trim() && <p key={index}>{paragraph}</p>
                        ))}
                    </div>

                    {/* Sources */}
                    {sources && sources.length > 0 && (
                        <div className="sources-section">
                            <h4>📚 Sources</h4>
                            <div className="sources-list">
                                {sources.map((source, index) => (
                                    <div key={index} className="source-item">
                                        <span className="source-icon">📄</span>
                                        <span className="source-file">{source.file}</span>
                                        <span className="source-page">Page {source.page}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default QuestionAnswer;
