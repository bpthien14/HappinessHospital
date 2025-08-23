let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Kiểm tra authentication trước khi load dữ liệu
    if (checkAuth()) {
        loadPatients();
        setupEventListeners();
    }
});

function setupEventListeners() {
    // Search form
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1;
        loadPatients();
    });
    
    // Add patient form
    document.getElementById('add-patient-form').addEventListener('submit', handleAddPatient);
    
    // Insurance checkbox
    document.getElementById('has_insurance').addEventListener('change', function() {
        const insuranceFields = document.getElementById('insurance-fields');
        insuranceFields.style.display = this.checked ? 'block' : 'none';
    });
}

async function loadPatients() {
    try {
        // Kiểm tra authentication
        const token = localStorage.getItem('access_token');
        if (!token) {
            showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
            redirectToLogin();
            return;
        }

        const searchQuery = document.getElementById('search-query').value;
        const genderFilter = document.getElementById('gender-filter').value;
        const insuranceFilter = document.getElementById('insurance-filter').value;
        
        const params = new URLSearchParams({
            page: currentPage,
            page_size: 10
        });
        
        if (searchQuery) params.append('search', searchQuery);
        if (genderFilter) params.append('gender', genderFilter);
        if (insuranceFilter) params.append('has_insurance', insuranceFilter);
        
        const response = await axios.get(`/api/patients/?${params}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        displayPatients(response.data.results);
        updatePagination(response.data);
        
    } catch (error) {
        console.error('Error loading patients:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else {
            showAlert('Lỗi khi tải danh sách bệnh nhân', 'danger');
        }
    }
}

function displayPatients(patients) {
    const tbody = document.getElementById('patients-tbody');
    tbody.innerHTML = '';
    
    patients.forEach(patient => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${patient.patient_code}</td>
            <td>${patient.full_name}</td>
            <td>${patient.age}</td>
            <td>${patient.gender === 'M' ? 'Nam' : patient.gender === 'F' ? 'Nữ' : 'Khác'}</td>
            <td>${patient.phone_number}</td>
            <td>
                <span class="badge ${patient.insurance_status.includes('có hiệu lực') ? 'bg-success' : 'bg-secondary'}">
                    ${patient.insurance_status}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="viewPatient('${patient.id}')">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning me-1" onclick="editPatient('${patient.id}')">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-outline-info" onclick="viewMedicalRecords('${patient.id}')">
                    <i class="fas fa-file-medical"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updatePagination(data) {
    totalPages = Math.ceil(data.count / 10);
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Trước</a>`;
    pagination.appendChild(prevLi);
    
    // Page numbers
    for (let i = Math.max(1, currentPage - 2); i <= Math.min(totalPages, currentPage + 2); i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="changePage(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Sau</a>`;
    pagination.appendChild(nextLi);
}

function changePage(page) {
    if (page >= 1 && page <= totalPages) {
        currentPage = page;
        loadPatients();
    }
}

async function handleAddPatient(e) {
    e.preventDefault();
    
    // Kiểm tra authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return;
    }
    
    const formData = new FormData(e.target);
    const patientData = Object.fromEntries(formData.entries());
    
    // Convert checkbox to boolean
    patientData.has_insurance = document.getElementById('has_insurance').checked;
    
    try {
        await axios.post('/api/patients/', patientData, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        // Close modal and refresh list
        const modal = bootstrap.Modal.getInstance(document.getElementById('addPatientModal'));
        modal.hide();
        e.target.reset();
        
        showAlert('Thêm bệnh nhân thành công!');
        loadPatients();
        
    } catch (error) {
        console.error('Error adding patient:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else {
            const errorMessage = error.response?.data?.detail || 'Lỗi khi thêm bệnh nhân';
            showAlert(errorMessage, 'danger');
        }
    }
}

function viewPatient(patientId) {
    // Kiểm tra authentication trước khi xem chi tiết bệnh nhân
    if (!checkAuth()) return;
    
    // Implement view patient details
    window.location.href = `/patients/${patientId}/`;
}

function editPatient(patientId) {
    // Kiểm tra authentication trước khi chỉnh sửa bệnh nhân
    if (!checkAuth()) return;
    
    // Implement edit patient
    console.log('Edit patient:', patientId);
}

function viewMedicalRecords(patientId) {
    // Implement view medical records
    console.log('View medical records:', patientId);
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