/**
 * Stats Panel Component
 * =====================
 * Displays system statistics.
 */

function StatsPanel({ stats }) {
    if (!stats) return null;

    return (
        <div className="stats-panel">
            <h3>📊 System Stats</h3>
            <div className="stats-grid">
                <div className="stat-item">
                    <span className="stat-value">{stats.total_documents}</span>
                    <span className="stat-label">Documents</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{stats.total_chunks}</span>
                    <span className="stat-label">Chunks</span>
                </div>
                <div className="stat-item">
                    <span className="stat-value">{stats.index_size}</span>
                    <span className="stat-label">Vectors</span>
                </div>
            </div>
            <p className="stats-model">
                Model: {stats.embedding_model} ({stats.embedding_dimension}D)
            </p>
        </div>
    );
}

export default StatsPanel;
