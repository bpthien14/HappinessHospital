/**
 * Doctors List Management JavaScript
 * Handles CRUD operations for doctors
 */

let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeDoctors();
    } else {
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeDoctors);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeDoctors();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializeDoctors() {
    if (checkAuth()) {
        loadDoctors();
        loadDepartments();
        setupEventListeners();
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
        // Enable save only when changed
        const ids = ['edit-username','edit-email','edit-first_name','edit-last_name','edit-phone_number','edit-is_active','edit-dob','edit-gender','edit-license-number','edit-degree','edit-department','edit-years_of_experience','edit-specializations','edit-max_patients_per_day','edit-consultation_duration','edit-bio','edit-qualifications'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const eventName = (el.tagName === 'SELECT' || el.type === 'date') ? 'change' : 'input';
            el.addEventListener(eventName, updateEditDoctorSaveState);
        });
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

function captureEditDoctorBaseline() {
    // Capture baseline from current form values instead of original data
    // This ensures we capture what was actually populated in the form
    window.__DOCTOR_EDIT_BASELINE__ = {
        username: document.getElementById('edit-username')?.value || '',
        email: document.getElementById('edit-email')?.value || '',
        first_name: document.getElementById('edit-first_name')?.value || '',
        last_name: document.getElementById('edit-last_name')?.value || '',
        phone_number: document.getElementById('edit-phone_number')?.value || '',
        is_active: document.getElementById('edit-is_active')?.value || '',
        dob: document.getElementById('edit-dob')?.value || '',
        gender: document.getElementById('edit-gender')?.value || '',
        license_number: document.getElementById('edit-license-number')?.value || '',
        degree: document.getElementById('edit-degree')?.value || '',
        department: document.getElementById('edit-department')?.value || '',
        years: document.getElementById('edit-years_of_experience')?.value || '',
        specialization: document.getElementById('edit-specializations')?.value || '',
        max_per_day: document.getElementById('edit-max_patients_per_day')?.value || '',
        duration: document.getElementById('edit-consultation_duration')?.value || '',
        bio: document.getElementById('edit-bio')?.value || '',
        qualifications: document.getElementById('edit-qualifications')?.value || ''
    };
    updateEditDoctorSaveState();
}

function updateEditDoctorSaveState() {
    try {
        const b = window.__DOCTOR_EDIT_BASELINE__ || {};
        const val = id => (document.getElementById(id)?.value || '');
        const changed = (
            b.username !== val('edit-username') ||
            b.email !== val('edit-email') ||
            b.first_name !== val('edit-first_name') ||
            b.last_name !== val('edit-last_name') ||
            b.phone_number !== val('edit-phone_number') ||
            b.is_active !== val('edit-is_active') ||
            b.dob !== val('edit-dob') ||
            b.gender !== val('edit-gender') ||
            b.license_number !== val('edit-license-number') ||
            b.degree !== val('edit-degree') ||
            String(b.department) !== val('edit-department') ||
            b.years !== val('edit-years_of_experience') ||
            b.specialization !== val('edit-specializations') ||
            b.max_per_day !== val('edit-max_patients_per_day') ||
            b.duration !== val('edit-consultation_duration') ||
            b.bio !== val('edit-bio') ||
            b.qualifications !== val('edit-qualifications')
        );
        const btn = document.getElementById('edit-doctor-save-btn');
        if (btn) btn.disabled = !changed;
    } catch (e) { /* noop */ }
}

async function loadDoctors(page = 1) {
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

        const response = await axios.get(url);

        const data = response.data;
        if (data.results) {
            currentPage = page;
            totalPages = Math.ceil(data.count / 10);
            
            renderDoctors(data.results);
            updatePagination(data);
        } else {
            console.error('❌ Invalid response format:', data);
            showAlert('Lỗi định dạng dữ liệu', 'danger');
        }
        
    } catch (error) {
        console.error('❌ Error loading doctors:', error);
        if (error.response?.status === 401) {
            window.location.href = '/auth/login/';
            return;
        }
        showAlert('Lỗi tải danh sách bác sĩ: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function loadDepartments() {
    try {
        const response = await axios.get('/api/departments/');
        
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

        // Step 1: Create User first via auth/register to ensure password_confirm and proper defaults
        const userData = {
            username: data.username,
            email: data.email,
            first_name: data.first_name,
            last_name: data.last_name,
            password: data.password,
            password_confirm: data.password,
            phone_number: data.phone_number || '',
            employee_id: data.employee_id,
            user_type: 'DOCTOR',
            date_of_birth: data.date_of_birth || null,
            gender: data.gender || 'O'
        };

        const userResponse = await axios.post('/api/auth/register/', userData);

        // Step 2: Create Doctor Profile
        // Auto-generate employee_id and license_number: BS + YY + 4 digits
        const now = new Date();
        const yy = String(now.getFullYear()).slice(2);
        const rand = Math.floor(Math.random() * 9000) + 1000; // fallback counter
        const generatedId = `BS${yy}${rand}`;
        const doctorData = {
            user: userResponse.data.user?.id || userResponse.data.id,
            department: data.department,
            license_number: generatedId,
            degree: data.degree,
            specialization: data.specializations || 'Chưa xác định',
            experience_years: parseInt(data.years_of_experience) || 0,
            max_patients_per_day: parseInt(data.max_patients_per_day) || 40,
            consultation_duration: parseInt(data.consultation_duration) || 15,
            bio: data.bio || '',
            achievements: data.qualifications || '',
            is_active: true
        };

        const doctorResponse = await axios.post('/api/doctors/', doctorData);
        
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
        
        // Prepare payloads for user and doctor profile updates
        const userPayload = {
            username: data.username,
            email: data.email,
            first_name: data.first_name,
            last_name: data.last_name,
            phone_number: data.phone_number || null,
            date_of_birth: (data.date_of_birth ? String(data.date_of_birth).slice(0,10) : null),
            gender: data.gender || 'O',
            is_active: data.is_active === 'true'
        };
        const doctorPayload = {
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

        // We need user id to update user fields
        let userId = document.getElementById('edit-doctor-id')?.dataset?.userId;
        if (!userId) {
            try {
                const detail = await axios.get(`/api/doctors/${doctorId}/`);
                userId = detail.data?.user?.id || detail.data?.user;
            } catch (err) { /* noop */ }
        }

        // Perform updates: user first (if available), then doctor profile
        if (userId) {
            try {
                await axios.patch(`/api/users/${userId}/`, userPayload);
            } catch (err) {
                if (err?.response?.status === 403 || err?.response?.status === 404) {
                    try { await axios.put('/api/auth/profile/update/', userPayload); } catch (e) { /* noop */ }
                }
            }
        }
        const response = await axios.patch(`/api/doctors/${doctorId}/`, doctorPayload);

        showAlert('Cập nhật bác sĩ thành công!', 'success');
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('editDoctorModal'));
        modal.hide();
        // Reset save button state baseline
        captureEditDoctorBaseline();
        
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
        const response = await axios.get(`/api/doctors/${doctorId}/`);
        const doctor = response.data;

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
        const response = await axios.get(`/api/doctors/${doctorId}/`);
        const doctor = response.data;

        await populateEditForm(doctor);
        
        const modal = new bootstrap.Modal(document.getElementById('editDoctorModal'));
        modal.show();

        // Add change listener to form fields to enable/disable save button
        const form = document.getElementById('edit-doctor-form');
        if (form) {
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', updateEditDoctorSaveState);
                input.addEventListener('change', updateEditDoctorSaveState);
            });

            // Clean up listeners when modal is hidden
            const modalElement = document.getElementById('editDoctorModal');
            modalElement.addEventListener('hidden.bs.modal', () => {
                inputs.forEach(input => {
                    input.removeEventListener('input', updateEditDoctorSaveState);
                    input.removeEventListener('change', updateEditDoctorSaveState);
                });
            }, { once: true });
        }
        
    } catch (error) {
        console.error('❌ Error loading doctor:', error);
        showAlert('Lỗi tải thông tin bác sĩ: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function deleteDoctor(doctorId) {
    // Removed browser confirm - use UI modal if needed

    try {
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
    
    const fullName = doctor.doctor_name || (doctor.user ? `${doctor.user.first_name || ''} ${doctor.user.last_name || ''}`.trim() : '') || 'N/A';
    
    // Update modal content with doctor details
    const fields = {
        'view-employee-id': doctor.license_number,
        'view-full-name': fullName,
        'view-email': (doctor.user?.email || doctor.email || 'Chưa cập nhật'),
        'view-phone': (doctor.user?.phone_number || doctor.phone || 'Chưa cập nhật'),
        'view-birth-date': (doctor.user?.date_of_birth || 'Chưa cập nhật'),
        'view-gender': (doctor.user?.gender === 'M' ? 'Nam' : (doctor.user?.gender === 'F' ? 'Nữ' : (doctor.user?.gender ? 'Khác' : 'Chưa cập nhật'))),
        'view-degree': formatDegree(doctor.degree),
        'view-department': doctor.department?.name || doctor.department_name || 'Chưa phân khoa',
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

    // Fetch user data if DOB/Gender missing and update
    const needsUserFetch = !(doctor.user && typeof doctor.user === 'object' && doctor.user.date_of_birth && doctor.user.gender);
    const userId = (doctor.user && typeof doctor.user !== 'object') ? doctor.user : doctor.user?.id;
    if (needsUserFetch && userId) {
        axios.get(`/api/users/${userId}/`).then(resp => {
            const u = resp.data || {};
            const dobEl = modal.querySelector('#view-birth-date');
            const genEl = modal.querySelector('#view-gender');
            if (dobEl && u.date_of_birth) dobEl.textContent = u.date_of_birth;
            if (genEl && u.gender) genEl.textContent = (u.gender === 'M' ? 'Nam' : (u.gender === 'F' ? 'Nữ' : 'Khác'));
        }).catch(() => {});
    }
}

async function populateEditForm(doctor) {
    const form = document.getElementById('edit-doctor-form');
    if (!form) return;

    // Set doctor ID
    document.getElementById('edit-doctor-id').value = doctor.id;
    
    // Populate user fields
    const setIfExists = (id, value) => { const el = document.getElementById(id); if (el) el.value = value || ''; };
    let userData = null;
    try {
        // If doctor.user is an object with fields
        if (doctor.user && typeof doctor.user === 'object') {
            userData = doctor.user;
        } else if (doctor.user) {
            // doctor.user is likely an ID -> fetch user detail
            const userResp = await axios.get(`/api/users/${doctor.user}/`);
            userData = userResp.data;
        }
    } catch (e) {
        // Fallback to available flat fields
        userData = {
            email: doctor.email,
            phone_number: doctor.phone,
            first_name: (doctor.doctor_name || '').split(' ').slice(0, -1).join(' '),
            last_name: (doctor.doctor_name || '').split(' ').slice(-1).join(' ')
        };
    }

    if (userData) {
        setIfExists('edit-first_name', userData.first_name);
        setIfExists('edit-last_name', userData.last_name);
        setIfExists('edit-email', userData.email);
        setIfExists('edit-phone_number', userData.phone_number);
        setIfExists('edit-username', userData.username);
        setIfExists('edit-employee_id', userData.employee_id || doctor.license_number);
        const idHolder = document.getElementById('edit-doctor-id');
        if (idHolder) { idHolder.dataset.userId = userData.id || ''; }
        setIfExists('edit-dob', userData.date_of_birth);
        const genderEl = document.getElementById('edit-gender'); if (genderEl) genderEl.value = userData.gender || 'O';
    }
    
    // Populate doctor profile fields
    // Reuse setter for profile fields
    setIfExists('edit-license-number', doctor.license_number);
    setIfExists('edit-degree', doctor.degree);
    // Ensure departments loaded before setting value
    try {
        const deptSelect = document.getElementById('edit-department');
        if (deptSelect && deptSelect.options.length <= 1) {
            await loadDepartments();
        }
        if (deptSelect) {
            const deptValue = String(
                doctor.department || doctor.department_id || (doctor.department && doctor.department.id) || ''
            );
            if (deptValue) {
                deptSelect.value = deptValue;
            }
            // Fallback: try match by department name if value didn't set
            if (!deptSelect.value && doctor.department_name) {
                for (let i = 0; i < deptSelect.options.length; i++) {
                    if (deptSelect.options[i].textContent === doctor.department_name) {
                        deptSelect.selectedIndex = i;
                        break;
                    }
                }
            }
        }
    } catch (e) { /* noop */ }
    setIfExists('edit-years_of_experience', doctor.experience_years);
    setIfExists('edit-specializations', doctor.specialization);
    setIfExists('edit-max_patients_per_day', doctor.max_patients_per_day);
    setIfExists('edit-consultation_duration', doctor.consultation_duration);
    const isActiveEl = document.getElementById('edit-is_active'); if (isActiveEl) isActiveEl.value = doctor.is_active ? 'true' : 'false';
    setIfExists('edit-bio', doctor.bio);
    setIfExists('edit-qualifications', doctor.achievements);

    // Capture baseline for change detection after all form fields are populated
    setTimeout(() => {
        captureEditDoctorBaseline();
    }, 100);
}