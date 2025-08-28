// API Configuration
const API_BASE_URL = '/api';

// Global variables
let currentUser = null;
let interceptorsReady = false;
let isAuthenticated = false;
let appInitialized = false;

function isPublicPath() {
    try {
        const url = new URL(window.location.href);
        const normalizedPath = (url.pathname.endsWith('/') ? url.pathname : url.pathname + '/').toLowerCase();
        if (normalizedPath === '/login/' || normalizedPath === '/signup/') {
            return true;
        }
        // Cho phép biến thể có query next, ts...
        if (normalizedPath.includes('/login/') || normalizedPath.includes('/signup/')) {
            return true;
        }
        return false;
    } catch (e) {
        return false;
    }
}

function bootApplication() {
    if (appInitialized) {
        return;
    }
    appInitialized = true;
    // Thực thi chặn role-based ngay khi có thể (trước cả initializeAuth)
    try { earlyRoleEnforcement(); } catch (e) { /* noop */ }
    // Nếu là trang công khai, chỉ cần cập nhật navbar và gắn sự kiện, không khởi chạy luồng auth
    if (isPublicPath() || window.__PUBLIC_PAGE__ === true) {
        try { toggleNavbarByAuth(); } catch (e) { /* noop */ }
        setupGlobalEventListeners();
        return;
    }
    // Cập nhật navbar ngay khi khởi động để phản ánh trạng thái hiện tại
    try { toggleNavbarByAuth(); } catch (e) { /* noop */ }
    initializeAuth();
    setupGlobalEventListeners();
}

// Khởi tạo ngay cả khi DOMContentLoaded đã xảy ra trước đó
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootApplication);
} else {
    bootApplication();
}

// Authentication setup
function initializeAuth() {
    if (window.__PUBLIC_PAGE__ === true || isPublicPath()) {
        toggleNavbarByAuth();
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
    toggleNavbarByAuth();
    try { applyRoleBasedRestrictions(); } catch (e) { /* noop */ }
    
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
            const original = error.config || {};
            
            // Auto refresh for 401
            if (error.response?.status === 401 && !original._retry) {
                original._retry = true;
                try {
                    const refreshToken = localStorage.getItem('refresh_token');
                    if (!refreshToken) {
                        logout();
                        return Promise.reject(error);
                    }
                    const response = await axios.post('/api/auth/refresh/', { refresh: refreshToken });
                    localStorage.setItem('access_token', response.data.access);
                    return axios(original);
                } catch (refreshError) {
                    logout();
                    return Promise.reject(refreshError);
                }
            }

            // Bỏ cảnh báo mặc định (vàng) để tránh chồng thông báo. Các trang tự hiển thị lỗi cục bộ.
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
    // Toggle navbar visibility on load for non-protected pages as well
    toggleNavbarByAuth();
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
        toggleNavbarByAuth();

        window.location.replace('/login/');
    }
}

function redirectToLogin() {
    try {
        if (isPublicPath() || window.__PUBLIC_PAGE__ === true) {
            // Đang ở trang công khai, không redirect nữa
            return;
        }
    } catch (e) { /* noop */ }
    window.location.replace('/login/');
}

function toggleNavbarByAuth() {
    try {
        const hasToken = !!localStorage.getItem('access_token');
        const authNav = document.getElementById('auth-nav');
        const guestNav = document.getElementById('guest-nav');
        if (authNav) {
            authNav.style.display = hasToken ? 'flex' : 'none';
        }
        if (guestNav) {
            guestNav.style.display = hasToken ? 'none' : 'flex';
        }

        // Ensure logout button handler is bound when auth menu becomes visible
        if (hasToken) {
            const logoutBtn = document.getElementById('logout-btn');
            if (logoutBtn && !logoutBtn.__bound) {
                logoutBtn.addEventListener('click', logout);
                logoutBtn.__bound = true;
            }
        }
    } catch (e) {
        console.error('toggleNavbarByAuth error', e);
    }
}

function showAlert(message, type = 'success') {
    // Hiển thị popup góc phải (thống nhất trải nghiệm)
    try {
        HospitalApp.showAlert(message, type);
        return;
    } catch (e) { /* fallback below */ }
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 16px; right: 16px; z-index: 1060; min-width: 320px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => { if (alertDiv.parentNode) alertDiv.remove(); }, 5000);
}

// Biến đổi lỗi kỹ thuật -> thông điệp thân thiện
function friendlyError(data, fallback){
    try {
        if (!data) return fallback || 'Đã xảy ra lỗi';
        if (typeof data === 'string') return data;
        const labelMap = {
            detail: 'Thông báo',
            non_field_errors: 'Lỗi',
            chief_complaint: 'Lý do khám',
            appointment_time: 'Giờ khám',
            appointment_date: 'Ngày khám',
            doctor: 'Bác sĩ',
            patient: 'Bệnh nhân',
            username: 'Tài khoản',
            phone_number: 'Số điện thoại',
            citizen_id: 'CCCD'
        };
        const parts = [];
        Object.keys(data).forEach(k => {
            const v = Array.isArray(data[k]) ? data[k].join(', ') : data[k];
            parts.push(`${labelMap[k] || k}: ${v}`);
        });
        return parts.join('; ') || fallback || 'Đã xảy ra lỗi';
    } catch(e){ return fallback || 'Đã xảy ra lỗi'; }
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
    // Trạng thái interceptor hiện tại
    get interceptorsReady() { return interceptorsReady; },
    get isAuthenticated() { return isAuthenticated; },
    // Đăng ký callback khi axios sẵn sàng
    onAxiosReady: (cb) => {
        if (interceptorsReady) {
            try { cb(); } catch (e) { console.error(e); }
        } else {
            window.addEventListener('axiosInterceptorsReady', () => {
                try { cb(); } catch (e) { console.error(e); }
            }, { once: true });
        }
    },
    checkAuth: () => {
        const token = localStorage.getItem('access_token');
        return !!token;
    },
    getToken: () => localStorage.getItem('access_token'),
    logout,
    showAlert
};

// ===== Role-based restrictions (Reception) =====
function isReceptionUser() {
    try {
        return !!currentUser && currentUser.user_type === 'RECEPTION';
    } catch (e) { return false; }
}

function isAllowedReceptionPath(pathname) {
    try {
        const path = (pathname.endsWith('/') ? pathname : pathname + '/').toLowerCase();
        // Only allow patients and appointments pages for RECEPTION
        return path.startsWith('/patients/') || path.startsWith('/appointments/');
    } catch (e) { return false; }
}

function enforceReceptionRouteGuard() {
    try {
        if (!isAuthenticated || !isReceptionUser()) return;
        const url = new URL(window.location.href);
        if (!isAllowedReceptionPath(url.pathname)) {
            window.location.replace('/patients/');
        }
    } catch (e) { /* noop */ }
}

function filterNavbarForReception() {
    try {
        if (!isReceptionUser()) return;
        const nav = document.getElementById('navbarNav');
        if (!nav) return;

        // Chỉ lọc các mục ở menu chính bên trái, không đụng tới menu người dùng (đăng xuất)
        const mainMenu = nav.querySelector('ul.navbar-nav.me-auto');
        if (!mainMenu) return;

        const links = mainMenu.querySelectorAll('a.nav-link');
        links.forEach(a => {
            const href = (a.getAttribute('href') || '').toLowerCase();
            const isPatients = href.startsWith('/patients/');
            const isAppointments = href.startsWith('/appointments/');
            const isAllowed = isPatients || isAppointments;
            // Ẩn prescriptions nhanh (#)
            const isPrescriptionsQuick = a.id === 'prescriptions-link';
            const navItem = a.closest('.nav-item');
            if (navItem) {
                if (!isAllowed || isPrescriptionsQuick) {
                    navItem.style.display = 'none';
                }
            }
        });
    } catch (e) { /* noop */ }
}

function applyRoleBasedRestrictions() {
    // Apply both navbar filtering and route guard
    filterNavbarForReception();
    enforceReceptionRouteGuard();
}

// Early enforcement before auth init: use cached user_data if any
function earlyRoleEnforcement() {
    try {
        const raw = localStorage.getItem('user_data');
        if (!raw) return;
        const parsed = JSON.parse(raw);
        if (!parsed || !parsed.user_type) return;
        if (!currentUser) currentUser = parsed;
        // Also reflect auth state optimistically to run guards
        if (!isAuthenticated) isAuthenticated = !!localStorage.getItem('access_token');
        applyRoleBasedRestrictions();
    } catch (e) { /* noop */ }
}