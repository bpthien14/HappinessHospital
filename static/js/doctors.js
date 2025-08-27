/**
 * Doctors List Management JavaScript
 * Handles CRUD operations for doctors
 */

let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    console.log('🩺 Doctors page: DOM loaded');
    
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        console.log('🩺 Axios interceptors ready, initializing doctors');
        initializeDoctors();
    } else {
        console.log('🩺 Waiting for axios interceptors...');
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeDoctors);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                console.log('🩺 Axios interceptors ready after timeout, initializing doctors');
                initializeDoctors();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializeDoctors() {
    console.log('🩺 Initializing doctors management');
    if (checkAuth()) {
        loadDoctors();
        loadDepartments();
        setupEventListeners();
        console.log('🩺 Doctors management initialized successfully');
    }
}

function setupEventListeners() {
    // Search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentPage = 1;
            loadDoctors();
        });
    }

    // Add doctor form
    const addForm = document.getElementById('add-doctor-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddDoctor);
    }

    // Edit doctor form
    const editForm = document.getElementById('edit-doctor-form');
    if (editForm) {
        editForm.addEventListener('submit', handleUpdateDoctor);
    }

    // Filter inputs
    ['search-query', 'department-filter', 'degree-filter', 'status-filter'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', function() {
                currentPage = 1;
                loadDoctors();
            });
        }
    });

    // Pagination click handlers
    document.addEventListener('click', function(e) {
        if (e.target.matches('.pagination .page-link')) {
            e.preventDefault();
            const page = parseInt(e.target.dataset.page);
            if (page && page !== currentPage) {
                currentPage = page;
                loadDoctors();
            }
        }
    });
}

async function loadDoctors(page = 1) {
    console.log('🩺 Loading doctors, page:', page);
    
    try {
        // Lấy filters từ form
        const searchQuery = document.getElementById('search-query')?.value || '';
        const department = document.getElementById('department-filter')?.value || '';
        const degree = document.getElementById('degree-filter')?.value || '';
        const status = document.getElementById('status-filter')?.value || '';

        // Build URL với params
        const params = new URLSearchParams({
            page: page,
            page_size: 10
        });

        if (searchQuery) params.append('search', searchQuery);
        if (department) params.append('department', department);
        if (degree) params.append('degree', degree);
        if (status) params.append('is_active', status);

        const url = `/api/doctors/?${params.toString()}`;
        console.log('🩺 API URL:', url);

        const response = await axios.get(url);
        console.log('🩺 API response:', response.data);

        const data = response.data;
        if (data.results) {
            currentPage = page;
            totalPages = Math.ceil(data.count / 10);
            
            renderDoctors(data.results);
            updatePagination(data);
            
            console.log(`🩺 Loaded ${data.results.length} doctors`);
        } else {
            console.error('❌ Invalid response format:', data);
            showAlert('Lỗi định dạng dữ liệu', 'danger');
        }
        
    } catch (error) {
        console.error('❌ Error loading doctors:', error);
        if (error.response?.status === 401) {
            console.log('🔒 Authentication required, redirecting to login');
            window.location.href = '/auth/login/';
            return;
        }
        showAlert('Lỗi tải danh sách bác sĩ: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function loadDepartments() {
    try {
        console.log('🏥 Loading departments...');
        const response = await axios.get('/api/departments/');
        console.log('🏥 Departments response:', response.data);
        
        const departments = response.data.results || response.data;
        populateDepartmentSelects(departments);
        
    } catch (error) {
        console.error('❌ Error loading departments:', error);
        // Không hiện alert cho departments vì không critical
    }
}

function populateDepartmentSelects(departments) {
    const selects = ['#department-filter', '#department', '#add-department', '#edit-department'];
    
    selects.forEach(selector => {
        const select = document.querySelector(selector);
        if (select) {
            console.log(`🏥 Populating ${selector} with ${departments.length} departments`);
            // Clear existing options (except first one)
            const firstOption = select.firstElementChild;
            select.innerHTML = '';
            if (firstOption) select.appendChild(firstOption);
            
            // Add department options
            departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                option.textContent = dept.name;
                select.appendChild(option);
            });
        } else {
            console.log(`⚠️ Selector ${selector} not found`);
        }
    });
}

function renderDoctors(doctors) {
    const tbody = document.getElementById('doctors-table-body');
    if (!tbody) {
        console.error('❌ Table body not found');
        return;
    }

    if (!doctors || doctors.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-user-md fa-2x text-muted mb-2"></i>
                    <p class="text-muted">Không có bác sĩ nào</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = doctors.map(doctor => createDoctorRow(doctor)).join('');
}

function createDoctorRow(doctor) {
    const departmentName = doctor.department_name || 'Chưa phân khoa';
    const statusBadge = doctor.is_active 
        ? '<span class="badge bg-success">Đang hoạt động</span>'
        : '<span class="badge bg-secondary">Tạm nghỉ</span>';
    
    // Get data from API response
    const fullName = doctor.doctor_name || 'N/A';
    const email = doctor.email || 'N/A';
    const phone = doctor.phone || 'N/A';
    
    return `
        <tr>
            <td>
                <strong>${escapeHtml(doctor.license_number || 'N/A')}</strong>
            </td>
            <td>
                <div>
                    <strong>${escapeHtml(fullName)}</strong>
                    <br>
                    <small class="text-muted">${formatDegree(doctor.degree)}</small>
                </div>
            </td>
            <td>${escapeHtml(departmentName)}</td>
            <td>${escapeHtml(doctor.specialization || 'Chưa cập nhật')}</td>
            <td>
                <i class="fas fa-phone text-primary"></i> ${escapeHtml(phone)}<br>
                <i class="fas fa-envelope text-secondary"></i> ${escapeHtml(email)}
            </td>
            <td>${doctor.experience_years || 0} năm</td>
            <td>${statusBadge}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-info" onclick="viewDoctor(${doctor.id})" title="Xem chi tiết">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="editDoctor(${doctor.id})" title="Chỉnh sửa">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDoctor(${doctor.id})" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

function formatDegree(degree) {
    const degrees = {
        'BACHELOR': 'BS.',
        'MASTER': 'ThS.',
        'DOCTOR': 'TS.'
    };
    return degrees[degree] || '';
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination-container');
    if (!pagination) return;

    const totalPages = Math.ceil(data.count / 10);
    const currentPageNum = currentPage;

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let paginationHtml = '';

    // Previous button
    if (currentPageNum > 1) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${currentPageNum - 1}">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;
    }

    // Page numbers
    for (let i = Math.max(1, currentPageNum - 2); i <= Math.min(totalPages, currentPageNum + 2); i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPageNum ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }

    // Next button
    if (currentPageNum < totalPages) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${currentPageNum + 1}">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;
    }

    pagination.innerHTML = paginationHtml;
}

// Utility functions
function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.log('🔒 No access token, redirecting to login');
        window.location.href = '/auth/login/';
        return false;
    }
    return true;
}

// CRUD Operations

async function handleAddDoctor(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        
        console.log('🩺 Form data received:', data);
        
        // Step 1: Create User first
        const userData = {
            username: data.username,
            email: data.email,
            first_name: data.first_name,
            last_name: data.last_name,
            password: data.password,
            phone_number: data.phone_number || '',
            employee_id: data.employee_id,
            user_type: 'DOCTOR'
        };
        
        console.log('🩺 Creating user:', userData);
        const userResponse = await axios.post('/api/users/', userData);
        console.log('🩺 User created:', userResponse.data);
        
        // Step 2: Create Doctor Profile
        const doctorData = {
            user: userResponse.data.id,
            department: data.department,
            license_number: data.license_number,
            degree: data.degree,
            specialization: data.specializations || 'Chưa xác định',
            experience_years: parseInt(data.years_of_experience) || 0,
            max_patients_per_day: parseInt(data.max_patients_per_day) || 40,
            consultation_duration: parseInt(data.consultation_duration) || 15,
            bio: data.bio || '',
            achievements: data.qualifications || '',
            is_active: true
        };
        
        console.log('🩺 Creating doctor profile:', doctorData);
        const doctorResponse = await axios.post('/api/doctors/', doctorData);
        console.log('🩺 Doctor profile created:', doctorResponse.data);
        
        showAlert('Thêm bác sĩ thành công!', 'success');
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('addDoctorModal'));
        modal.hide();
        e.target.reset();
        
        loadDoctors();
        
    } catch (error) {
        console.error('❌ Error adding doctor:', error);
        let message = 'Lỗi thêm bác sĩ';
        if (error.response?.data) {
            if (typeof error.response.data === 'string') {
                message += ': ' + error.response.data;
            } else if (error.response.data.detail) {
                message += ': ' + error.response.data.detail;
            } else {
                // Handle field errors
                const errors = Object.entries(error.response.data)
                    .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                    .join('; ');
                message += ': ' + errors;
            }
        }
        showAlert(message, 'danger');
    }
}

async function handleUpdateDoctor(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const doctorId = data.doctor_id;
        
        // Remove doctor_id from data
        delete data.doctor_id;
        
        // Convert form field names to API field names
        const updateData = {
            license_number: data.license_number,
            degree: data.degree,
            department: data.department,
            specialization: data.specializations,
            experience_years: parseInt(data.years_of_experience) || 0,
            max_patients_per_day: parseInt(data.max_patients_per_day) || 40,
            consultation_duration: parseInt(data.consultation_duration) || 15,
            bio: data.bio || '',
            achievements: data.qualifications || '',
            is_active: data.is_active === 'true'
        };
        
        console.log('🩺 Updating doctor:', doctorId, updateData);
        
        const response = await axios.patch(`/api/doctors/${doctorId}/`, updateData);
        console.log('🩺 Doctor updated:', response.data);
        
        showAlert('Cập nhật bác sĩ thành công!', 'success');
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('editDoctorModal'));
        modal.hide();
        
        loadDoctors();
        
    } catch (error) {
        console.error('❌ Error updating doctor:', error);
        let message = 'Lỗi cập nhật bác sĩ';
        if (error.response?.data) {
            if (typeof error.response.data === 'string') {
                message += ': ' + error.response.data;
            } else if (error.response.data.detail) {
                message += ': ' + error.response.data.detail;
            } else {
                const errors = Object.entries(error.response.data)
                    .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : msgs}`)
                    .join('; ');
                message += ': ' + errors;
            }
        }
        showAlert(message, 'danger');
    }
}

async function viewDoctor(doctorId) {
    try {
        console.log('🩺 Loading doctor details:', doctorId);
        
        const response = await axios.get(`/api/doctors/${doctorId}/`);
        const doctor = response.data;
        
        console.log('🩺 Doctor data:', doctor);
        
        populateViewModal(doctor);
        
        const modal = new bootstrap.Modal(document.getElementById('viewDoctorModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error loading doctor details:', error);
        showAlert('Lỗi tải thông tin bác sĩ: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function editDoctor(doctorId) {
    try {
        console.log('🩺 Loading doctor for edit:', doctorId);
        
        const response = await axios.get(`/api/doctors/${doctorId}/`);
        const doctor = response.data;
        
        console.log('🩺 Doctor data:', doctor);
        
        populateEditForm(doctor);
        
        const modal = new bootstrap.Modal(document.getElementById('editDoctorModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error loading doctor:', error);
        showAlert('Lỗi tải thông tin bác sĩ: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function deleteDoctor(doctorId) {
    if (!confirm('Bạn có chắc chắn muốn xóa bác sĩ này?\n\nLưu ý: Hành động này không thể hoàn tác!')) {
        return;
    }
    
    try {
        console.log('🩺 Deleting doctor:', doctorId);
        
        await axios.delete(`/api/doctors/${doctorId}/`);
        
        showAlert('Xóa bác sĩ thành công!', 'success');
        loadDoctors(); // Reload the list
        
    } catch (error) {
        console.error('❌ Error deleting doctor:', error);
        let message = 'Lỗi xóa bác sĩ';
        if (error.response?.data?.detail) {
            message += ': ' + error.response.data.detail;
        } else if (error.response?.status === 400) {
            message += ': Không thể xóa bác sĩ này do có dữ liệu liên quan';
        }
        showAlert(message, 'danger');
    }
}

function populateViewModal(doctor) {
    const modal = document.getElementById('viewDoctorModal');
    if (!modal) return;
    
    const fullName = doctor.user ? `${doctor.user.first_name} ${doctor.user.last_name}`.trim() : 'N/A';
    
    // Update modal content with doctor details
    const fields = {
        'view-employee-id': doctor.license_number,
        'view-full-name': fullName,
        'view-email': doctor.user?.email,
        'view-phone': doctor.user?.phone_number,
        'view-birth-date': doctor.user?.date_of_birth || 'Chưa cập nhật',
        'view-gender': doctor.user?.gender === 'M' ? 'Nam' : (doctor.user?.gender === 'F' ? 'Nữ' : 'Khác'),
        'view-degree': formatDegree(doctor.degree),
        'view-department': doctor.department?.name || 'Chưa phân khoa',
        'view-specializations': doctor.specialization,
        'view-experience': (doctor.experience_years || 0) + ' năm',
        'view-license': doctor.license_number,
        'view-status': doctor.is_active ? 'Đang hoạt động' : 'Tạm nghỉ'
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = modal.querySelector(`#${id}`);
        if (element) {
            element.textContent = value || 'Chưa cập nhật';
        }
    });
}

function populateEditForm(doctor) {
    const form = document.getElementById('edit-doctor-form');
    if (!form) return;
    
    console.log('🩺 Populating edit form with:', doctor);
    
    // Set doctor ID
    document.getElementById('edit-doctor-id').value = doctor.id;
    
    // Populate user fields
    if (doctor.user) {
        document.getElementById('edit-first_name').value = doctor.user.first_name || '';
        document.getElementById('edit-last_name').value = doctor.user.last_name || '';
        document.getElementById('edit-email').value = doctor.user.email || '';
        document.getElementById('edit-phone_number').value = doctor.user.phone_number || '';
        document.getElementById('edit-username').value = doctor.user.username || '';
        document.getElementById('edit-employee_id').value = doctor.user.employee_id || '';
    }
    
    // Populate doctor profile fields
    document.getElementById('edit-license-number').value = doctor.license_number || '';
    document.getElementById('edit-degree').value = doctor.degree || '';
    document.getElementById('edit-department').value = doctor.department?.id || '';
    document.getElementById('edit-years_of_experience').value = doctor.experience_years || '';
    document.getElementById('edit-specializations').value = doctor.specialization || '';
    document.getElementById('edit-max_patients_per_day').value = doctor.max_patients_per_day || '';
    document.getElementById('edit-consultation_duration').value = doctor.consultation_duration || '';
    document.getElementById('edit-is_active').value = doctor.is_active ? 'true' : 'false';
    document.getElementById('edit-bio').value = doctor.bio || '';
    document.getElementById('edit-qualifications').value = doctor.achievements || '';
}