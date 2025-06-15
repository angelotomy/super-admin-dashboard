import React, { useState, useEffect } from 'react';
import './HistoryTooltip.css';

const HistoryTooltip = ({ commentId, onClose }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchHistory();
    }, [commentId]);

    const fetchHistory = async () => {
        try {
            const response = await fetch(`/api/comments/${commentId}/history/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setHistory(data);
            }
        } catch (error) {
            console.error('Failed to fetch history:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const getActionBadge = (action) => {
        const badges = {
            'CREATE': 'badge-success',
            'EDIT': 'badge-warning',
            'DELETE': 'badge-danger'
        };
        return badges[action] || 'badge-secondary';
    };

    if (loading) {
        return (
            <div className="history-tooltip">
                <div className="d-flex justify-content-between align-items-center mb-3">
                    <h6 className="mb-0">Modification History</h6>
                    <button className="btn btn-sm btn-link" onClick={onClose}>×</button>
                </div>
                <div className="text-center">
                    <div className="spinner-border spinner-border-sm" role="status"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="history-tooltip">
            <div className="d-flex justify-content-between align-items-center mb-3">
                <h6 className="mb-0">Modification History</h6>
                <button className="btn btn-sm btn-link" onClick={onClose}>×</button>
            </div>
            
            <div className="history-timeline">
                {history.length === 0 ? (
                    <p className="text-muted">No modification history available.</p>
                ) : (
                    history.map((entry, index) => (
                        <div key={index} className="history-entry">
                            <div className="d-flex justify-content-between align-items-start mb-2">
                                <span className={`badge ${getActionBadge(entry.action)}`}>
                                    {entry.action}
                                </span>
                                <small className="text-muted">
                                    {formatDate(entry.timestamp)}
                                </small>
                            </div>
                            
                            <div className="mb-2">
                                <strong>{entry.user_name}</strong>
                                <small className="text-muted"> ({entry.user_email})</small>
                            </div>
                            
                            {entry.old_content && (
                                <div className="history-diff">
                                    <div className="old-content">
                                        <small className="text-muted">Previous:</small>
                                        <p>{entry.old_content}</p>
                                    </div>
                                    {entry.new_content && (
                                        <div className="new-content">
                                            <small className="text-muted">Updated:</small>
                                            <p>{entry.new_content}</p>
                                        </div>
                                    )}
                                </div>
                            )}
                            
                            {index < history.length - 1 && <hr />}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default HistoryTooltip;