// frontend/src/services/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post('http://127.0.0.1:8000/api/accounts/token/refresh/', {
            refresh: refreshToken
          });
          localStorage.setItem('token', response.data.access);
          // Retry the original request
          error.config.headers.Authorization = `Bearer ${response.data.access}`;
          return api.request(error.config);
        } catch (refreshError) {
          // If refresh fails, logout
          localStorage.removeItem('token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } else {
        // No refresh token, logout
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email, password) => api.post('/accounts/login/', { email, password }),
  loginSuperAdmin: (email, password) => api.post('/accounts/login/superadmin/', { email, password }),
  loginUser: (email, password) => api.post('/accounts/login/user/', { email, password }),
  getProfile: () => api.get('/accounts/profile/'),
  resetPassword: (email) => api.post('/accounts/password/reset/request/', { email }),
  verifyOTP: (email, otp) => api.post('/accounts/password/reset/verify/', { email, otp }),
  resetPasswordConfirm: (email, otp, new_password) => 
    api.post('/accounts/password/reset/confirm/', { email, otp, new_password }),
  getUserAccessiblePages: () => api.get('/accounts/user-accessible-pages/'),
};

export const userAPI = {
  getUsers: () => api.get('/accounts/users/'),
  createUser: (userData) => api.post('/accounts/users/', userData),
  updateUser: (id, userData) => api.put(`/accounts/users/${id}/`, userData),
  deleteUser: (id) => api.delete(`/accounts/users/${id}/`),
  getUserPermissions: (id) => api.get(`/accounts/users/${id}/permissions/`),
};

export const permissionAPI = {
  getPages: () => api.get('/accounts/pages/'),
  updatePermissions: (data) => api.post('/accounts/permissions/update/', data),
};

export default api;