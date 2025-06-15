import React from 'react';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Permission error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger" role="alert">
                    <h4 className="alert-heading">Access Denied</h4>
                    <p>You don't have permission to perform this action.</p>
                    <hr />
                    <p className="mb-0">
                        <button 
                            className="btn btn-primary btn-sm" 
                            onClick={() => window.location.reload()}
                        >
                            Refresh Page
                        </button>
                    </p>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;