import React from 'react';
import { Card, Container } from 'react-bootstrap';
import CommentSection from '../Comments/CommentSection';
import './DynamicPage.css';

const PAGE_TITLES = {
    products_list: 'Products List',
    marketing_list: 'Marketing List',
    order_list: 'Order List',
    media_plans: 'Media Plans',
    offer_pricing_skus: 'Offer Pricing SKUs',
    clients: 'Clients',
    suppliers: 'Suppliers',
    customer_support: 'Customer Support',
    sales_reports: 'Sales Reports',
    finance_accounting: 'Finance & Accounting'
};

const DynamicPage = ({ pageName }) => {
    const pageTitle = PAGE_TITLES[pageName] || 'Page Not Found';

    return (
        <Container className="dynamic-page py-4">
            <Card className="page-content">
                <Card.Body>
                    <h1 className="page-title h4 mb-3">
                        {pageTitle}
                    </h1>
                    
                    <div className="page-description text-muted mb-4">
                        This is the {pageTitle.toLowerCase()} page. You can view and manage content based on your permissions.
                    </div>

                    <hr className="my-4" />

                    <div className="comments-container">
                        <h2 className="h6 mb-3">
                            Comments
                        </h2>
                        <CommentSection pageName={pageName} />
                    </div>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default DynamicPage; 