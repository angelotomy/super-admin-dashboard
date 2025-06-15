// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import Navbar from './components/Navbar';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import UserDashboard from './components/UserDashboard';
import DynamicPage from './components/DynamicPage/DynamicPage';
import 'bootstrap/dist/css/bootstrap.min.css';

const DYNAMIC_PAGES = [
    'products_list',
    'marketing_list',
    'order_list',
    'media_plans',
    'offer_pricing_skus',
    'clients',
    'suppliers',
    'customer_support',
    'sales_reports',
    'finance_accounting'
];

// Wrapper component to handle navbar rendering logic
const AppContent = () => {
    const location = useLocation();
    const isLoginPage = location.pathname === '/login';

    return (
        <div className="app-container">
            {!isLoginPage && <Navbar />}
            <div className="container-fluid mt-3">
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route
                        path="/admin"
                        element={
                            <PrivateRoute>
                                <AdminDashboard />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/dashboard"
                        element={
                            <PrivateRoute>
                                <UserDashboard />
                            </PrivateRoute>
                        }
                    />
                    {DYNAMIC_PAGES.map(pageName => (
                        <Route
                            key={pageName}
                            path={`/${pageName.replace('_', '-')}`}
                            element={
                                <PrivateRoute>
                                    <DynamicPage pageName={pageName} />
                                </PrivateRoute>
                            }
                        />
                    ))}
                    <Route path="/" element={<Navigate to="/admin" replace />} />
                </Routes>
            </div>
        </div>
    );
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <AppContent />
            </Router>
        </AuthProvider>
    );
}

export default App;