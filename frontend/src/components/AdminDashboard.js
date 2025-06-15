// frontend/src/components/AdminDashboard.js
import React, { useState, useEffect } from 'react';
import { userAPI, permissionAPI } from '../services/api';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [pages, setPages] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const initialFormState = {
    email: '',
    firstName: '',
    lastName: '',
    role: 'user',
    password: ''
  };
  const [formData, setFormData] = useState(initialFormState);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      const [usersResponse, pagesResponse] = await Promise.all([
        userAPI.getUsers(),
        permissionAPI.getPages()
      ]);
      
      // Initialize permissions for each user if they don't exist
      const usersWithPermissions = usersResponse.data.map(user => ({
        ...user,
        permissions: user.permissions || {}
      }));
      
      setUsers(usersWithPermissions);
      setPages(pagesResponse.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      setError('');
      setLoading(true);
      
      const userData = {
        email: formData.email,
        first_name: formData.firstName,
        last_name: formData.lastName,
        role: formData.role,
        password: formData.password,
        username: formData.email.split('@')[0]
      };
      
      const response = await userAPI.createUser(userData);
      
      if (response.data) {
        await fetchData();
        setFormData(initialFormState);
        setIsRightPanelOpen(false);
        setError(`User created successfully! Password: ${response.data.password}`);
      }
    } catch (error) {
      console.error('Error creating user:', error);
      setError(error.response?.data?.error || 'Failed to create user. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePermissions = async (userId, pageId, newPermissions) => {
    try {
      setError('');
      const permissionData = {
        user_id: userId,
        page_id: pageId,
        can_view: newPermissions.view || false,
        can_edit: newPermissions.edit || false,
        can_create: newPermissions.create || false,
        can_delete: newPermissions.delete || false
      };
      
      await permissionAPI.updatePermissions(permissionData);
      
      setUsers(users.map(user => {
        if (user.id === userId) {
          return {
            ...user,
            permissions: {
              ...user.permissions,
              [pageId]: {
                can_view: newPermissions.view || false,
                can_edit: newPermissions.edit || false,
                can_create: newPermissions.create || false,
                can_delete: newPermissions.delete || false
              }
            }
          };
        }
        return user;
      }));
      
      await fetchData();
    } catch (error) {
      console.error('Error updating permissions:', error);
      setError(error.response?.data?.error || 'Failed to update permissions. Please try again.');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        setError('');
        setLoading(true);
        const response = await userAPI.deleteUser(userId);
        
        if (response.data?.message) {
          setError(response.data.message);
          await fetchData(); // Refresh the user list
        }
      } catch (error) {
        console.error('Error deleting user:', error);
        setError(error.response?.data?.error || 'Failed to delete user. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };

  const openRightPanel = (user = null) => {
    setSelectedUser(user);
    if (user) {
      setFormData({
        email: user.email || '',
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        role: user.role || 'user',
        password: '' // Always reset password when editing
      });
    } else {
      setFormData(initialFormState);
    }
    setIsRightPanelOpen(true);
  };

  const getPermissionLabel = (permissions, userRole) => {
    if (userRole === 'superadmin') return 'Full Access';
    if (!permissions) return 'No Access';
    if (permissions.delete) return 'Delete';
    if (permissions.create) return 'Create';
    if (permissions.edit) return 'Edit';
    if (permissions.view) return 'View';
    return 'No Access';
  };

  const getPermissionColor = (permissions, userRole) => {
    if (userRole === 'superadmin') return 'permission-delete';
    if (!permissions) return 'permission-none';
    if (permissions.delete) return 'permission-delete';
    if (permissions.create) return 'permission-create';
    if (permissions.edit) return 'permission-edit';
    if (permissions.view) return 'permission-view';
    return 'permission-none';
  };

  if (loading) {
    return (
      <div className="admin-dashboard loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <div className={`main-content ${!isRightPanelOpen ? 'full-width' : ''}`}>
        <div className="dashboard-header">
          <h1>User Management</h1>
          <button 
            className="btn-primary"
            onClick={() => openRightPanel()}
          >
            Add New User
          </button>
        </div>

        {error && (
          <div className={`alert ${error.includes('successfully') ? 'alert-success' : 'alert-danger'} mb-4`} role="alert">
            {error}
          </div>
        )}

        <div className="users-table-container">
          <table className="users-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                {pages.map(page => (
                  <th key={page.id || page._id}>{page.name}</th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id || user._id}>
                  <td>{user.first_name} {user.last_name}</td>
                  <td>{user.email}</td>
                  <td>
                    <span className={`badge ${user.role === 'superadmin' ? 'badge-admin' : 'badge-user'}`}>
                      {user.role === 'superadmin' ? 'Super Admin' : 'User'}
                    </span>
                  </td>
                  {pages.map(page => {
                    const pageId = page.id || page._id;
                    const userPermissions = user.permissions[pageId] || {};
                    
                    return (
                      <td key={`${user.id}-${pageId}`} className="permission-cell">
                        <div 
                          className={`permission-indicator ${getPermissionColor(userPermissions, user.role)}`}
                          onClick={() => openRightPanel(user)}
                        >
                          {getPermissionLabel(userPermissions, user.role)}
                        </div>
                      </td>
                    );
                  })}
                  <td className="actions">
                    <button 
                      className="btn-icon"
                      onClick={() => openRightPanel(user)}
                      title="Edit User"
                    >
                      Edit
                    </button>
                    <button 
                      className="btn-icon"
                      onClick={() => handleDeleteUser(user.id || user._id)}
                      title="Delete User"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right Panel */}
      <div className={`right-panel ${isRightPanelOpen ? 'open' : ''}`}>
        <div className="right-panel-header">
          <h2>{selectedUser ? 'Edit User' : 'Add New User'}</h2>
          <button 
            className="btn-close"
            onClick={() => setIsRightPanelOpen(false)}
          >
            ×
          </button>
        </div>
        
        <div className="right-panel-content">
          <form onSubmit={handleCreateUser} className="user-form">
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>First Name</label>
              <input
                type="text"
                value={formData.firstName}
                onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input
                type="text"
                value={formData.lastName}
                onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
                minLength="8"
                placeholder="Minimum 8 characters"
              />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
              >
                <option value="user">Regular User</option>
                <option value="superadmin">Super Admin</option>
              </select>
            </div>
            <button type="submit" className="btn-primary">
              {selectedUser ? 'Update User' : 'Create User'}
            </button>
          </form>

          {selectedUser && (
            <div className="permissions-section">
              <h3>Page Permissions</h3>
              {pages.map(page => (
                <div key={page.id} className="page-permissions">
                  <h4>{page.name}</h4>
                  <div className="permission-toggles">
                    {['view', 'edit', 'create', 'delete'].map(perm => (
                      <label key={perm} className="permission-toggle">
                        <input
                          type="checkbox"
                          checked={selectedUser.permissions[page.id]?.[`can_${perm}`] || false}
                          onChange={(e) => {
                            const newPermissions = {
                              ...selectedUser.permissions[page.id],
                              [perm]: e.target.checked
                            };
                            handleUpdatePermissions(selectedUser.id, page.id, newPermissions);
                          }}
                          disabled={selectedUser.role === 'superadmin'}
                        />
                        {perm.charAt(0).toUpperCase() + perm.slice(1)}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;