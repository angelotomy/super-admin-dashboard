// frontend/src/components/UserDashboard.js
import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './Dashboard.css';

const UserDashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await api.get('/auth/profile/');
      setUser(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-3">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div className="container-fluid">
          <div className="row align-items-center">
            <div className="col">
              <h1 className="dashboard-title">Welcome, {user?.full_name}</h1>
              <p className="dashboard-subtitle">User Dashboard</p>
            </div>
          </div>
        </div>
      </div>

      <div className="container-fluid mt-4">
        <div className="row">
          <div className="col">
            <div className="card">
              <div className="card-header">
                <h5>Your Profile</h5>
              </div>
              <div className="card-body">
                <div className="profile-info">
                  <div className="info-item">
                    <label>Username:</label>
                    <span>{user?.username}</span>
                  </div>
                  <div className="info-item">
                    <label>Email:</label>
                    <span>{user?.email}</span>
                  </div>
                  <div className="info-item">
                    <label>Full Name:</label>
                    <span>{user?.full_name}</span>
                  </div>
                  <div className="info-item">
                    <label>Role:</label>
                    <span className="badge bg-primary">Regular User</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;