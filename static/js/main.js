// API Configuration
const API_BASE_URL = '/api';
let currentUser = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupGlobalEventListeners();
});

// Authentication setup
function initializeAuth() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');
    
    if (token && userData) {
        currentUser = JSON.parse(userData);
        setupAxiosInterceptors();
        updateUserInfo();
    } else if (window.location.pathname !== '/login/') {
        redirectToLogin();
    }
}

function setupAxiosInterceptors() {
    // Request interceptor
    axios.interceptors.request.use(
        config => {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        },
        error => Promise.reject(error)
    );

    // Response interceptor for token refresh
    axios.interceptors.response.use(
        response => response,
        async error => {
            const original = error.config;
            
            if (error.response?.status === 401 && !original._retry) {
                original._retry = true;
                
                try {
                    const refreshToken = localStorage.getItem('refresh_token');
                    const response = await axios.post('/api/auth/refresh/', {
                        refresh: refreshToken
                    });
                    
                    localStorage.setItem('access_token', response.data.access);
                    return axios(original);
                } catch (refreshError) {
                    logout();
                    return Promise.reject(refreshError);
                }
            }
            
            return Promise.reject(error);
        }
    );
}

function updateUserInfo() {
    const userNameElements = document.querySelectorAll('#user-name');
    userNameElements.forEach(element => {
        element.textContent = currentUser.full_name || currentUser.username;
    });
}

function setupGlobalEventListeners() {
    // Logout handler
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}

async function logout() {
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        await axios.post('/api/auth/logout/', { refresh: refreshToken });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        redirectToLogin();
    }
}

function redirectToLogin() {
    window.location.href = '/login/';
}

// Utility functions
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('main .container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}

function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}