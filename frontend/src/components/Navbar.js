// frontend/src/components/Navbar.js
import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authAPI } from '../services/api';
import './Navbar.css';
import { 
    FaTachometerAlt, FaShoppingCart, FaBullhorn, FaReceipt, 
    FaFilm, FaTag, FaUsers, FaBuilding, FaHeadset, 
    FaChartBar, FaMoneyBillWave, FaSignOutAlt, FaBars 
} from 'react-icons/fa';

const PAGE_ICONS = {
    products_list: <FaShoppingCart />,
    marketing_list: <FaBullhorn />,
    order_list: <FaReceipt />,
    media_plans: <FaFilm />,
    offer_pricing_skus: <FaTag />,
    clients: <FaUsers />,
    suppliers: <FaBuilding />,
    customer_support: <FaHeadset />,
    sales_reports: <FaChartBar />,
    finance_accounting: <FaMoneyBillWave />
};

const PAGE_DISPLAY_NAMES = {
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

const Navbar = () => {
    const [pages, setPages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [user, setUser] = useState(null);
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
        fetchAccessiblePages();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const fetchAccessiblePages = async () => {
        try {
            setLoading(true);
            const response = await authAPI.getUserAccessiblePages();
            setPages(response.data);
            setError('');
        } catch (error) {
            console.error('Error fetching accessible pages:', error);
            setError('Failed to load navigation');
        } finally {
            setLoading(false);
        }
    };

    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/" className="navbar-logo">
                    Super Admin Dashboard
                </Link>
            </div>

            <div className="navbar-menu">
                {!loading && !error && pages.map((page) => (
                    <Link
                        key={page.id}
                        to={page.url}
                        className={`navbar-item ${location.pathname === page.url ? 'active' : ''}`}
                    >
                        {page.name}
                    </Link>
                ))}
            </div>

            <div className="navbar-end">
                {user && (
                    <div className="user-info">
                        <span className="user-name">{user.email}</span>
                        <span className="user-role">{user.role === 'superadmin' ? 'Super Admin' : 'User'}</span>
                        <button onClick={handleLogout} className="logout-button">
                            Logout
                        </button>
                    </div>
                )}
            </div>
        </nav>
    );
};

export default Navbar;