// frontend/src/components/CommentSystem.js

import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import './CommentSystem.css';

const CommentSystem = ({ pageName, pageDisplayName, permissions }) => {
    const { user, token } = useContext(AuthContext);
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [editingComment, setEditingComment] = useState(null);
    const [editContent, setEditContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Fetch comments when component loads
    useEffect(() => {
        fetchComments();
    }, [pageName]);

    const fetchComments = async () => {
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/pages/${pageName}/comments/`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                setComments(data);
            } else {
                setError('Failed to load comments');
            }
        } catch (err) {
            setError('Error loading comments');
        } finally {
            setLoading(false);
        }
    };

    // Add a new comment
    const handleAddComment = async (e) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/pages/${pageName}/comments/`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: newComment })
            });

            if (response.ok) {
                const newCommentData = await response.json();
                setComments([newCommentData, ...comments]); // Add to top
                setNewComment(''); // Clear form
                setError('');
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to add comment');
            }
        } catch (err) {
            setError('Error adding comment');
        }
    };

    // Edit a comment
    const handleEditComment = async (commentId) => {
        if (!editContent.trim()) return;

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/comments/${commentId}/`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: editContent })
            });

            if (response.ok) {
                const updatedComment = await response.json();
                setComments(comments.map(comment => 
                    comment.id === commentId ? updatedComment : comment
                ));
                setEditingComment(null);
                setEditContent('');
                setError('');
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to edit comment');
            }
        } catch (err) {
            setError('Error editing comment');
        }
    };

    // Delete a comment
    const handleDeleteComment = async (commentId) => {
        if (!window.confirm('Are you sure you want to delete this comment?')) return;

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/comments/${commentId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                }
            });

            if (response.ok) {
                setComments(comments.filter(comment => comment.id !== commentId));
                setError('');
            } else {
                const errorData = await response.json();
                setError(errorData.error || 'Failed to delete comment');
            }
        } catch (err) {
            setError('Error deleting comment');
        }
    };

    // Start editing a comment
    const startEditing = (comment) => {
        setEditingComment(comment.id);
        setEditContent(comment.content);
    };

    // Cancel editing
    const cancelEditing = () => {
        setEditingComment(null);
        setEditContent('');
    };

    if (loading) {
        return (
            <div className="comment-system-loading">
                <div className="spinner"></div>
                <p>Loading comments...</p>
            </div>
        );
    }

    return (
        <div className="comment-system">
            <div className="comment-system-header">
                <h2>{pageDisplayName}</h2>
                <p className="page-description">
                    This is the {pageDisplayName.toLowerCase()} page. 
                    {permissions.can_view && " You can view comments."}
                    {permissions.can_create && " You can add comments."}
                    {permissions.can_edit && " You can edit comments."}
                    {permissions.can_delete && " You can delete comments."}
                </p>
            </div>

            {error && (
                <div className="error-message">
                    <i className="fas fa-exclamation-triangle"></i>
                    {error}
                </div>
            )}

            {/* Add Comment Form - Only show if user can create */}
            {permissions.can_create && (
                <div className="add-comment-section">
                    <h3>Add a Comment</h3>
                    <form onSubmit={handleAddComment} className="add-comment-form">
                        <textarea
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="What would you like to share about this page?"
                            rows="3"
                            className="comment-input"
                        />
                        <button 
                            type="submit" 
                            className="btn btn-primary"
                            disabled={!newComment.trim()}
                        >
                            <i className="fas fa-plus"></i> Add Comment
                        </button>
                    </form>
                </div>
            )}

            {/* Comments List */}
            <div className="comments-section">
                <h3>Comments ({comments.length})</h3>
                
                {comments.length === 0 ? (
                    <div className="no-comments">
                        <i className="fas fa-comments"></i>
                        <p>No comments yet. {permissions.can_create ? "Be the first to add one!" : ""}</p>
                    </div>
                ) : (
                    <div className="comments-list">
                        {comments.map(comment => (
                            <div key={comment.id} className="comment-card">
                                <div className="comment-header">
                                    <div className="comment-author">
                                        <i className="fas fa-user-circle"></i>
                                        <span className="author-name">{comment.user_name}</span>
                                        <span className="author-email">({comment.user_email})</span>
                                    </div>
                                    <div className="comment-date">
                                        {new Date(comment.created_at).toLocaleDateString()} at{' '}
                                        {new Date(comment.created_at).toLocaleTimeString()}
                                        {comment.modified_at !== comment.created_at && (
                                            <span className="modified-indicator">
                                                <i className="fas fa-edit"></i> Edited
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <div className="comment-content">
                                    {editingComment === comment.id ? (
                                        // Edit mode
                                        <div className="edit-comment-form">
                                            <textarea
                                                value={editContent}
                                                onChange={(e) => setEditContent(e.target.value)}
                                                rows="3"
                                                className="comment-input"
                                            />
                                            <div className="edit-actions">
                                                <button 
                                                    onClick={() => handleEditComment(comment.id)}
                                                    className="btn btn-success btn-sm"
                                                    disabled={!editContent.trim()}
                                                >
                                                    <i className="fas fa-save"></i> Save
                                                </button>
                                                <button 
                                                    onClick={cancelEditing}
                                                    className="btn btn-secondary btn-sm"
                                                >
                                                    <i className="fas fa-times"></i> Cancel
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        // View mode
                                        <p className="comment-text">{comment.content}</p>
                                    )}
                                </div>

                                {/* Action buttons */}
                                {editingComment !== comment.id && (
                                    <div className="comment-actions">
                                        {permissions.can_edit && (
                                            <button 
                                                onClick={() => startEditing(comment)}
                                                className="btn btn-outline-primary btn-sm"
                                            >
                                                <i className="fas fa-edit"></i> Edit
                                            </button>
                                        )}
                                        
                                        {permissions.can_delete && (
                                            <button 
                                                onClick={() => handleDeleteComment(comment.id)}
                                                className="btn btn-outline-danger btn-sm"
                                            >
                                                <i className="fas fa-trash"></i> Delete
                                            </button>
                                        )}

                                        {user?.is_superuser && (
                                            <button 
                                                className="btn btn-outline-info btn-sm"
                                                title="View modification history"
                                            >
                                                <i className="fas fa-history"></i> History
                                            </button>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CommentSystem;