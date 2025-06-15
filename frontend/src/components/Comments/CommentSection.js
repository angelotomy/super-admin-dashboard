import React, { useState, useEffect, useCallback } from 'react';
import { Form, Button, Card, Spinner, Alert, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaEdit, FaTrash, FaHistory } from 'react-icons/fa';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import moment from 'moment';
import './CommentSection.css';

const CommentSection = ({ pageName }) => {
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [editingComment, setEditingComment] = useState(null);
    const [editText, setEditText] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [commentHistory, setCommentHistory] = useState({});
    const [permissions, setPermissions] = useState({
        canView: false,
        canEdit: false,
        canCreate: false,
        canDelete: false
    });
    const { user } = useAuth();

    const fetchComments = useCallback(async () => {
        try {
            const response = await axios.get(`/api/auth/pages/${pageName}/comments`);
            setComments(response.data);
            setLoading(false);
        } catch (err) {
            console.error('Error fetching comments:', err);
            setError('Failed to load comments');
            setLoading(false);
        }
    }, [pageName]);

    const fetchPermissions = useCallback(async () => {
        try {
            const response = await axios.get(`/api/auth/pages/${pageName}/permissions`);
            setPermissions({
                canView: response.data.can_view,
                canEdit: response.data.can_edit,
                canCreate: response.data.can_create,
                canDelete: response.data.can_delete
            });
        } catch (err) {
            console.error('Error fetching permissions:', err);
            setError('Failed to load permissions');
        }
    }, [pageName]);

    useEffect(() => {
        fetchComments();
        fetchPermissions();
    }, [fetchComments, fetchPermissions]);

    const fetchCommentHistory = async (commentId) => {
        try {
            const response = await axios.get(`/api/auth/comments/${commentId}/history`);
            setCommentHistory({
                ...commentHistory,
                [commentId]: response.data
            });
        } catch (err) {
            console.error('Error fetching comment history:', err);
        }
    };

    const handleAddComment = async (e) => {
        e.preventDefault();
        if (!newComment.trim()) return;
        
        try {
            const response = await axios.post(`/api/auth/pages/${pageName}/comments`, {
                content: newComment
            });
            setComments([response.data, ...comments]);
            setNewComment('');
        } catch (err) {
            console.error('Error adding comment:', err);
            setError('Failed to add comment');
        }
    };

    const handleEditComment = async (commentId) => {
        if (!editText.trim()) return;
        
        try {
            const response = await axios.put(`/api/auth/comments/${commentId}`, {
                content: editText
            });
            setComments(comments.map(comment => 
                comment.id === commentId ? response.data : comment
            ));
            setEditingComment(null);
            setEditText('');
            // Refresh comment history after edit
            await fetchCommentHistory(commentId);
        } catch (err) {
            console.error('Error editing comment:', err);
            setError('Failed to edit comment');
        }
    };

    const handleDeleteComment = async (commentId) => {
        try {
            await axios.delete(`/api/auth/comments/${commentId}`);
            setComments(comments.filter(comment => comment.id !== commentId));
        } catch (err) {
            console.error('Error deleting comment:', err);
            setError('Failed to delete comment');
        }
    };

    const renderModificationHistory = (comment) => {
        const history = commentHistory[comment.id] || [];
        if (!history.length) return "No modification history";
        
        return (
            <div className="history-tooltip">
                <div><strong>Original:</strong> {history[0].content}</div>
                {history.slice(1).map((modification, index) => (
                    <div key={index}>
                        <div><strong>Modified by:</strong> {modification.modified_by}</div>
                        <div><strong>At:</strong> {moment(modification.modified_at).format('MMMM Do YYYY, h:mm:ss a')}</div>
                        <div><strong>Content:</strong> {modification.content}</div>
                    </div>
                ))}
            </div>
        );
    };

    if (loading) return <div className="text-center"><Spinner animation="border" /></div>;
    if (error) return <Alert variant="danger">{error}</Alert>;
    if (!permissions.canView) return <Alert variant="warning">You don't have permission to view comments</Alert>;

    return (
        <div className="comment-section">
            {permissions.canCreate && (
                <Form onSubmit={handleAddComment} className="mb-4">
                    <Form.Group className="mb-3">
                        <Form.Control
                            as="textarea"
                            rows={2}
                            placeholder="Add a comment..."
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                        />
                    </Form.Group>
                    <Button
                        type="submit"
                        variant="primary"
                        disabled={!newComment.trim()}
                    >
                        Post Comment
                    </Button>
                </Form>
            )}

            <div className="comments-list">
                {comments.map(comment => (
                    <Card key={comment.id} className="mb-3 comment-item">
                        <Card.Body>
                            {editingComment === comment.id ? (
                                <Form className="edit-comment">
                                    <Form.Group className="mb-3">
                                        <Form.Control
                                            as="textarea"
                                            rows={2}
                                            value={editText}
                                            onChange={(e) => setEditText(e.target.value)}
                                        />
                                    </Form.Group>
                                    <div className="d-flex gap-2">
                                        <Button
                                            variant="primary"
                                            onClick={() => handleEditComment(comment.id)}
                                        >
                                            Save
                                        </Button>
                                        <Button
                                            variant="secondary"
                                            onClick={() => {
                                                setEditingComment(null);
                                                setEditText('');
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                    </div>
                                </Form>
                            ) : (
                                <>
                                    <div className="d-flex justify-content-between align-items-start mb-2">
                                        <div>
                                            <Card.Subtitle className="mb-1">{comment.user_name}</Card.Subtitle>
                                            <Card.Text className="text-muted small">
                                                {moment(comment.created_at).format('MMMM Do YYYY, h:mm:ss a')}
                                            </Card.Text>
                                        </div>
                                        <div className="d-flex gap-2">
                                            {user.is_superuser && (
                                                <OverlayTrigger
                                                    placement="left"
                                                    overlay={
                                                        <Tooltip id={`history-${comment.id}`}>
                                                            {renderModificationHistory(comment)}
                                                        </Tooltip>
                                                    }
                                                >
                                                    <Button
                                                        variant="info"
                                                        size="sm"
                                                        onClick={() => fetchCommentHistory(comment.id)}
                                                    >
                                                        <FaHistory />
                                                    </Button>
                                                </OverlayTrigger>
                                            )}
                                            {permissions.canEdit && user.id === comment.user && (
                                                <Button
                                                    variant="outline-primary"
                                                    size="sm"
                                                    onClick={() => {
                                                        setEditingComment(comment.id);
                                                        setEditText(comment.content);
                                                    }}
                                                >
                                                    <FaEdit />
                                                </Button>
                                            )}
                                            {permissions.canDelete && (user.id === comment.user || user.is_superuser) && (
                                                <Button
                                                    variant="outline-danger"
                                                    size="sm"
                                                    onClick={() => handleDeleteComment(comment.id)}
                                                >
                                                    <FaTrash />
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                    <Card.Text>{comment.content}</Card.Text>
                                </>
                            )}
                        </Card.Body>
                    </Card>
                ))}
            </div>
        </div>
    );
};

export default CommentSection; 