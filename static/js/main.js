// API Configuration
const API_BASE_URL = '/api';

// Global variables
let currentUser = null;
let interceptorsReady = false;
let isAuthenticated = false;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
    setupGlobalEventListeners();
});

// Authentication setup
function initializeAuth() {
    if (window.location.pathname === '/login/') {
        return;
    }
    
    if (checkAuthStatus()) {
        setupApp();
    } else {
        redirectToLogin();
    }
}

function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');

    if (!token || !userData) {
        return false;
    }
    
    try {
        if (token.split('.').length !== 3) {
            return false;
        }
        
        const parsedUserData = JSON.parse(userData);
        if (!parsedUserData.username) {
            return false;
        }
        
        currentUser = parsedUserData;
        isAuthenticated = true;
        return true;
        
    } catch (error) {
        console.error('❌ Error checking auth status:', error);
        return false;
    }
}

function setupApp() {
    setupAxiosInterceptors();
    updateUserInfo();
    
    interceptorsReady = true;
    window.dispatchEvent(new CustomEvent('axiosInterceptorsReady'));
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

    axios.interceptors.response.use(
        response => response,
        async error => {
            const original = error.config;
            
            if (error.response?.status === 401 && !original._retry) {
                original._retry = true;
                
                try {
                    const refreshToken = localStorage.getItem('refresh_token');
                    if (!refreshToken) {
                        logout();
                        return Promise.reject(error);
                    }
                    
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
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}

async function logout() {    
    try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            await axios.post('/api/auth/logout/', { refresh: refreshToken });
        }
    } catch (error) {
        console.error('❌ Logout API error:', error);
    } finally {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
        
        currentUser = null;
        interceptorsReady = false;
        isAuthenticated = false;

        window.location.replace('/login/');
    }
}

function redirectToLogin() {
    window.location.replace('/login/');
}

function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('.container-fluid') || 
                     document.querySelector('.container') || 
                     document.querySelector('main') ||
                     document.body;
    
    if (container) {
        try {
            if (container === document.body) {
                container.appendChild(alertDiv);
            } else {
                container.insertBefore(alertDiv, container.firstChild);
            }
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        } catch (error) {
            console.error('Error inserting alert:', error);
            // Fallback: append vào body
            document.body.appendChild(alertDiv);
        }
    } else {
        console.warn('No container found for alert, appending to body');
        document.body.appendChild(alertDiv);
    }
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

// Export để các script khác có thể sử dụng
window.HospitalApp = {
    interceptorsReady,
    isAuthenticated,
    checkAuth: () => {
        const token = localStorage.getItem('access_token');
        return !!token;
    },
    getToken: () => localStorage.getItem('access_token'),
    logout,
    showAlert
};