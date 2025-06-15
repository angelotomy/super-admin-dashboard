import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { authAPI } from '../services/api';
import './Sidebar.css';

const Sidebar = () => {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const location = useLocation();

  useEffect(() => {
    fetchAccessiblePages();
  }, []);

  const fetchAccessiblePages = async () => {
    try {
      setLoading(true);
      const response = await authAPI.getUserAccessiblePages();
      setPages(response.data);
      setError('');
    } catch (error) {
      console.error('Error fetching accessible pages:', error);
      setError('Failed to load navigation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="sidebar-loading">Loading...</div>;
  }

  if (error) {
    return <div className="sidebar-error">{error}</div>;
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>Dashboard</h2>
      </div>
      <nav className="sidebar-nav">
        {pages.map((page) => (
          <Link
            key={page.id}
            to={page.url}
            className={`sidebar-link ${location.pathname === page.url ? 'active' : ''}`}
          >
            {page.name}
          </Link>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar; 