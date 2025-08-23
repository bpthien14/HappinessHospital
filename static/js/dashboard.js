document.addEventListener('DOMContentLoaded', function() {
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeDashboard();
    } else {
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeDashboard);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeDashboard();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializeDashboard() {
    console.log('🚀 Initializing dashboard...');
    // Kiểm tra authentication trước khi load dữ liệu
    if (checkAuth()) {
        loadDashboardStats();
        loadRecentPatients();
    }
}

async function loadDashboardStats() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return;
    }
    try {

        const response = await axios.get(`/api/patients/statistics/`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        document.getElementById('total-patients').textContent = stats.total_patients;
        document.getElementById('new-patients').textContent = stats.new_patients_this_month;
        // TODO: Load appointment and prescription stats when those modules are implemented
        document.getElementById('today-appointments').textContent = '-';
        document.getElementById('pending-prescriptions').textContent = '-';
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else {
            showAlert('Lỗi khi tải thống kê dashboard', 'danger');
        }
    }
}

async function loadRecentPatients() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return;
    }
    try {
        const response = await axios.get('/api/patients/?page_size=5&ordering=-created_at', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        const patients = response.data.results;
        
        const tbody = document.getElementById('recent-patients-tbody');
        tbody.innerHTML = '';
        
        if (patients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Chưa có bệnh nhân nào</td></tr>';
            return;
        }
        
        patients.forEach(patient => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${patient.patient_code}</td>
                <td>${patient.full_name}</td>
                <td>${formatDate(patient.created_at)}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading recent patients:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else {
            document.getElementById('recent-patients-tbody').innerHTML = 
                '<tr><td colspan="3" class="text-center text-danger">Lỗi khi tải dữ liệu</td></tr>';
        }
    }
}

function openAddPatientModal() {
    window.location.href = '/patients/';
}

// Helper function để kiểm tra authentication
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return false;
    }
    return true;
}

// Helper function để redirect đến login
function redirectToLogin() {
    window.location.href = '/login/';
}

// Helper function để hiển thị alert
function showAlert(message, type = 'info') {
    // Sử dụng HospitalApp.showAlert nếu có
    if (window.HospitalApp && window.HospitalApp.showAlert) {
        window.HospitalApp.showAlert(message, type);
        return;
    }
    
    // Fallback: tạo alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Thêm vào đầu trang
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Tự động ẩn sau 5 giây
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}