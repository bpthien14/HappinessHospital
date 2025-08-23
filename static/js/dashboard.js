let dashboardInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    
    if (!checkAuth()) {
        return; 
    }
    
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeDashboard();
    } else {
        window.addEventListener('axiosInterceptorsReady', initializeDashboard);
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeDashboard();
            } else {
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 3000);
    }
});

function initializeDashboard() {
    if (dashboardInitialized) {
        return;
    }
    
    dashboardInitialized = true;
    
    loadDashboardStats();
    loadRecentPatients();
}

async function loadDashboardStats() {
    try {
        const response = await axios.get('/api/patients/statistics/');
        const stats = response.data;

        document.getElementById('total-patients').textContent = stats.total_patients || 0;
        document.getElementById('new-patients').textContent = stats.new_patients_this_month || 0;
        // TODO: Load appointment and prescription stats when those modules are implemented
        document.getElementById('today-appointments').textContent = '-';
        document.getElementById('pending-prescriptions').textContent = '-';

    } catch (error) {
        console.error('❌ Error loading dashboard stats:', error);
        if (error.response?.status === 401) {
            redirectToLogin();
        } else {
            showAlert('Lỗi khi tải thống kê dashboard', 'danger');
        }
    }
}

async function loadRecentPatients() {
    try {
        const response = await axios.get('/api/patients/?page_size=5&ordering=-created_at');
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
        console.error('❌ Error loading recent patients:', error);
        if (error.response?.status === 401) {
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
        redirectToLogin();
        return false;
    }
    
    return true;
}


function redirectToLogin() {
    window.location.replace('/login/');
}

function showAlert(message, type = 'info') {
    if (window.HospitalApp && window.HospitalApp.showAlert) {
        window.HospitalApp.showAlert(message, type);
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid') || document.querySelector('.container') || document.querySelector('main');
    if (container) {
        try {
            container.insertBefore(alertDiv, container.firstChild);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        } catch (error) {
            console.error('Error inserting alert:', error);
            document.body.appendChild(alertDiv);
        }
    } else {
        console.warn('No container found for alert, appending to body');
        document.body.appendChild(alertDiv);
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
    }
}