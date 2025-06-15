import api from './api';

const SESSION_TIMEOUT = 60 * 60 * 1000; // 1 hour in milliseconds

class SessionManager {
  constructor() {
    this.setupActivityListeners();
  }

  setupActivityListeners() {
    // Track user activity
    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    events.forEach(event => {
      window.addEventListener(event, () => this.updateLastActivity());
    });

    // Check session status periodically
    setInterval(() => this.checkSession(), 60000); // Check every minute
  }

  updateLastActivity() {
    localStorage.setItem('last_activity', Date.now().toString());
  }

  async checkSession() {
    const lastActivity = parseInt(localStorage.getItem('last_activity') || '0');
    const currentTime = Date.now();

    if (currentTime - lastActivity > SESSION_TIMEOUT) {
      // Session expired
      this.logout();
      window.location.href = '/login?session=expired';
      return;
    }

    // Check if token needs refresh (every 30 minutes)
    if (currentTime - lastActivity > 30 * 60 * 1000) {
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await api.post('/auth/token/refresh/', {
            refresh: refreshToken
          });
          localStorage.setItem('token', response.data.access);
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
        this.logout();
        window.location.href = '/login';
      }
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('last_activity');
  }

  isAuthenticated() {
    const token = localStorage.getItem('token');
    const lastActivity = parseInt(localStorage.getItem('last_activity') || '0');
    return token && (Date.now() - lastActivity <= SESSION_TIMEOUT);
  }
}

export default new SessionManager(); 