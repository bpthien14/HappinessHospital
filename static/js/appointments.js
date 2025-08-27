/**
 * Appointments Management JavaScript
 * Handles CRUD operations for appointments
 */

let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    console.log('📅 Appointments page: DOM loaded');
    
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        console.log('📅 Axios interceptors ready, initializing appointments');
        initializeAppointments();
    } else {
        console.log('📅 Waiting for axios interceptors...');
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeAppointments);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                console.log('📅 Axios interceptors ready after timeout, initializing appointments');
                initializeAppointments();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializeAppointments() {
    console.log('📅 Initializing appointments management');
    if (checkAuth()) {
        loadAppointments();
        loadFormData();
        setupEventListeners();
        console.log('📅 Appointments management initialized successfully');
    }
}

function setupEventListeners() {
    // Search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            currentPage = 1;
            loadAppointments();
        });
    }

    // Add appointment form
    const addForm = document.getElementById('add-appointment-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddAppointment);
    }

    // Edit appointment form
    const editForm = document.getElementById('edit-appointment-form');
    if (editForm) {
        editForm.addEventListener('submit', handleUpdateAppointment);
    }

    // Filter inputs
    ['search-query', 'status-filter', 'priority-filter', 'department-filter', 'date-filter'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', function() {
                currentPage = 1;
                loadAppointments();
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
                loadAppointments();
            }
        }
    });
}

async function loadAppointments(page = 1) {
    console.log('📅 Loading appointments, page:', page);
    
    try {
        // Lấy filters từ form
        const searchQuery = document.getElementById('search-query')?.value || '';
        const status = document.getElementById('status-filter')?.value || '';
        const priority = document.getElementById('priority-filter')?.value || '';
        const department = document.getElementById('department-filter')?.value || '';
        const date = document.getElementById('date-filter')?.value || '';

        // Build URL với params
        const params = new URLSearchParams({
            page: page,
            page_size: 10
        });

        if (searchQuery) params.append('search', searchQuery);
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);
        if (department) params.append('department', department);
        if (date) params.append('appointment_date', date);

        const url = `/api/appointments/?${params.toString()}`;
        console.log('📅 API URL:', url);

        const response = await axios.get(url);
        console.log('📅 API response:', response.data);

        const data = response.data;
        if (data.results) {
            currentPage = page;
            totalPages = Math.ceil(data.count / 10);
            
            renderAppointments(data.results);
            updatePagination(data);
            updateTotalCount(data.count);
            
            console.log(`📅 Loaded ${data.results.length} appointments`);
        } else {
            console.error('❌ Invalid response format:', data);
            showAlert('Lỗi định dạng dữ liệu', 'danger');
        }
        
    } catch (error) {
        console.error('❌ Error loading appointments:', error);
        if (error.response?.status === 401) {
            console.log('🔒 Authentication required, redirecting to login');
            window.location.href = '/auth/login/';
            return;
        }
        showAlert('Lỗi tải danh sách lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function loadFormData() {
    try {
        console.log('📋 Loading form data...');
        
        // Load departments
        const deptResponse = await axios.get('/api/departments/');
        populateSelectOptions('#department-filter', deptResponse.data.results || deptResponse.data, 'id', 'name');
        populateSelectOptions('#add-department', deptResponse.data.results || deptResponse.data, 'id', 'name');
        
        // Load patients
        const patientResponse = await axios.get('/api/patients/');
        populateSelectOptions('#add-patient', patientResponse.data.results || patientResponse.data, 'id', 'full_name');
        
        // Load doctors
        const doctorResponse = await axios.get('/api/doctors/');
        const doctors = doctorResponse.data.results || doctorResponse.data;
        populateSelectOptions('#add-doctor', doctors, 'id', (doctor) => {
            const fullName = doctor.doctor_name || 'N/A';
            return `${fullName} - ${doctor.department_name || 'Chưa phân khoa'}`;
        });
        
    } catch (error) {
        console.error('❌ Error loading form data:', error);
    }
}

function populateSelectOptions(selector, data, valueField, textField) {
    const select = document.querySelector(selector);
    if (!select || !data) return;
    
    // Keep the first option (placeholder)
    const firstOption = select.firstElementChild;
    select.innerHTML = '';
    if (firstOption) select.appendChild(firstOption);
    
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item[valueField];
        option.textContent = typeof textField === 'function' ? textField(item) : item[textField];
        select.appendChild(option);
    });
}

function renderAppointments(appointments) {
    const tbody = document.getElementById('appointments-table-body');
    if (!tbody) {
        console.error('❌ Table body not found');
        return;
    }

    if (!appointments || appointments.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="text-center py-4">
                    <i class="fas fa-calendar-alt fa-2x text-muted mb-2"></i>
                    <p class="text-muted">Không có lịch hẹn nào</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = appointments.map(appointment => createAppointmentRow(appointment)).join('');
}

function createAppointmentRow(appointment) {
    const patientName = appointment.patient_name || 'N/A';
    const doctorName = appointment.doctor_name || 'N/A';
    const departmentName = appointment.department_name || 'N/A';
    
    const statusBadge = getStatusBadge(appointment.status);
    const priorityBadge = getPriorityBadge(appointment.priority);
    const typeBadge = getTypeBadge(appointment.appointment_type);
    
    return `
        <tr>
            <td>
                <strong>${escapeHtml(appointment.appointment_number || 'N/A')}</strong>
            </td>
            <td>${escapeHtml(patientName)}</td>
            <td>${escapeHtml(doctorName)}</td>
            <td>${escapeHtml(departmentName)}</td>
            <td>
                <strong>${formatDate(appointment.appointment_date)}</strong><br>
                <small class="text-muted">${formatTime(appointment.appointment_time)}</small>
            </td>
            <td>${typeBadge}</td>
            <td>${priorityBadge}</td>
            <td>${statusBadge}</td>
            <td>
                <div class="btn-group" role="group">
                    ${getActionButtons(appointment)}
                </div>
            </td>
        </tr>
    `;
}

function getStatusBadge(status) {
    const badges = {
        'SCHEDULED': '<span class="badge bg-primary">Đã đặt lịch</span>',
        'CONFIRMED': '<span class="badge bg-info">Đã xác nhận</span>',
        'CHECKED_IN': '<span class="badge bg-success">Đã check-in</span>',
        'IN_PROGRESS': '<span class="badge bg-warning">Đang khám</span>',
        'COMPLETED': '<span class="badge bg-success">Hoàn thành</span>',
        'CANCELLED': '<span class="badge bg-danger">Đã hủy</span>',
        'NO_SHOW': '<span class="badge bg-secondary">Không đến</span>'
    };
    return badges[status] || `<span class="badge bg-light">${status}</span>`;
}

function getPriorityBadge(priority) {
    const badges = {
        'LOW': '<span class="badge bg-light text-dark">Thấp</span>',
        'NORMAL': '<span class="badge bg-secondary">Bình thường</span>',
        'HIGH': '<span class="badge bg-warning">Cao</span>',
        'URGENT': '<span class="badge bg-danger">Khẩn cấp</span>'
    };
    return badges[priority] || `<span class="badge bg-light">${priority}</span>`;
}

function getTypeBadge(type) {
    const badges = {
        'NEW': '<span class="badge bg-primary">Khám mới</span>',
        'FOLLOW_UP': '<span class="badge bg-info">Tái khám</span>',
        'CONSULTATION': '<span class="badge bg-secondary">Tư vấn</span>',
        'CHECKUP': '<span class="badge bg-success">Khám sức khỏe</span>',
        'EMERGENCY': '<span class="badge bg-danger">Cấp cứu</span>'
    };
    return badges[type] || `<span class="badge bg-light">${type}</span>`;
}

function getActionButtons(appointment) {
    let buttons = '';
    
    // View button - always available
    buttons += `<button class="btn btn-sm btn-outline-info me-1" onclick="viewAppointment('${appointment.id}')" title="Xem chi tiết">
                    <i class="fas fa-eye"></i>
                </button>`;
    
    // Edit button - available for SCHEDULED and CONFIRMED
    if (['SCHEDULED', 'CONFIRMED'].includes(appointment.status)) {
        buttons += `<button class="btn btn-sm btn-outline-warning me-1" onclick="editAppointment('${appointment.id}')" title="Chỉnh sửa">
                        <i class="fas fa-edit"></i>
                    </button>`;
    }
    
    // Confirm button - only for SCHEDULED
    if (appointment.status === 'SCHEDULED') {
        buttons += `<button class="btn btn-sm btn-outline-success me-1" onclick="confirmAppointment('${appointment.id}')" title="Xác nhận">
                        <i class="fas fa-check"></i>
                    </button>`;
    }
    
    // Check-in button - only for CONFIRMED
    if (appointment.status === 'CONFIRMED') {
        buttons += `<button class="btn btn-sm btn-outline-primary me-1" onclick="checkinAppointment('${appointment.id}')" title="Check-in">
                        <i class="fas fa-sign-in-alt"></i>
                    </button>`;
    }
    
    // Start examination button - only for CHECKED_IN
    if (appointment.status === 'CHECKED_IN') {
        buttons += `<button class="btn btn-sm btn-outline-info me-1" onclick="startExamination('${appointment.id}')" title="Bắt đầu khám">
                        <i class="fas fa-play"></i>
                    </button>`;
    }
    
    // Complete button - only for IN_PROGRESS
    if (appointment.status === 'IN_PROGRESS') {
        buttons += `<button class="btn btn-sm btn-outline-success me-1" onclick="completeAppointment('${appointment.id}')" title="Hoàn thành">
                        <i class="fas fa-check-circle"></i>
                    </button>`;
    }
    
    // Cancel button - available for SCHEDULED, CONFIRMED
    if (['SCHEDULED', 'CONFIRMED'].includes(appointment.status)) {
        buttons += `<button class="btn btn-sm btn-outline-danger me-1" onclick="cancelAppointment('${appointment.id}')" title="Hủy lịch">
                        <i class="fas fa-times"></i>
                    </button>`;
    }
    
    // Reschedule button - available for SCHEDULED, CONFIRMED
    if (['SCHEDULED', 'CONFIRMED'].includes(appointment.status)) {
        buttons += `<button class="btn btn-sm btn-outline-secondary me-1" onclick="rescheduleAppointment('${appointment.id}')" title="Dời lịch">
                        <i class="fas fa-calendar-alt"></i>
                    </button>`;
    }
    
    return buttons;
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

function updateTotalCount(count) {
    const totalElement = document.getElementById('total-count');
    if (totalElement) {
        totalElement.textContent = count;
    }
}

// CRUD Operations

async function handleAddAppointment(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        
        console.log('📅 Adding appointment:', data);
        
        const response = await axios.post('/api/appointments/', data);
        console.log('📅 Appointment added:', response.data);
        
        showAlert('Đặt lịch hẹn thành công!', 'success');
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('addAppointmentModal'));
        modal.hide();
        e.target.reset();
        
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error adding appointment:', error);
        let message = 'Lỗi đặt lịch hẹn';
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

async function handleUpdateAppointment(e) {
    e.preventDefault();
    
    try {
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        const appointmentId = data.id;
        
        delete data.id; // Remove id from data
        
        console.log('📅 Updating appointment:', appointmentId, data);
        
        const response = await axios.patch(`/api/appointments/${appointmentId}/`, data);
        console.log('📅 Appointment updated:', response.data);
        
        showAlert('Cập nhật lịch hẹn thành công!', 'success');
        
        // Close modal and reload data
        const modal = bootstrap.Modal.getInstance(document.getElementById('editAppointmentModal'));
        modal.hide();
        
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error updating appointment:', error);
        let message = 'Lỗi cập nhật lịch hẹn';
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

async function viewAppointment(appointmentId) {
    try {
        console.log('📅 Loading appointment details:', appointmentId);
        
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
        console.log('📅 Appointment data:', appointment);
        
        populateViewModal(appointment);
        
        const modal = new bootstrap.Modal(document.getElementById('viewAppointmentModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error loading appointment details:', error);
        showAlert('Lỗi tải thông tin lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function editAppointment(appointmentId) {
    try {
        console.log('📅 Loading appointment for edit:', appointmentId);
        
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
        console.log('📅 Appointment data:', appointment);
        
        populateEditForm(appointment);
        
        const modal = new bootstrap.Modal(document.getElementById('editAppointmentModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error loading appointment:', error);
        showAlert('Lỗi tải thông tin lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function confirmAppointment(appointmentId) {
    try {
        console.log('📅 Confirming appointment:', appointmentId);
        
        const response = await axios.post(`/api/appointments/${appointmentId}/confirm/`);
        console.log('📅 Appointment confirmed:', response.data);
        
        showAlert('Xác nhận lịch hẹn thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error confirming appointment:', error);
        showAlert('Lỗi xác nhận lịch hẹn: ' + (error.response?.data?.error || error.message), 'danger');
    }
}

async function checkinAppointment(appointmentId) {
    try {
        console.log('📅 Checking in appointment:', appointmentId);
        
        const response = await axios.post(`/api/appointments/${appointmentId}/checkin/`);
        console.log('📅 Appointment checked in:', response.data);
        
        showAlert('Check-in thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error checking in appointment:', error);
        showAlert('Lỗi check-in: ' + (error.response?.data?.error || error.message), 'danger');
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm('Bạn có chắc chắn muốn hủy lịch hẹn này?')) {
        return;
    }
    
    try {
        console.log('📅 Cancelling appointment:', appointmentId);
        
        const response = await axios.post(`/api/appointments/${appointmentId}/cancel/`, {
            reason: 'Hủy lịch hẹn từ giao diện quản trị'
        });
        
        showAlert('Hủy lịch hẹn thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error cancelling appointment:', error);
        showAlert('Lỗi hủy lịch hẹn: ' + (error.response?.data?.error || error.message), 'danger');
    }
}

async function startExamination(appointmentId) {
    try {
        console.log('📅 Starting examination:', appointmentId);
        
        const response = await axios.patch(`/api/appointments/${appointmentId}/`, {
            status: 'IN_PROGRESS',
            actual_start_time: new Date().toISOString()
        });
        
        showAlert('Bắt đầu khám bệnh thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error starting examination:', error);
        showAlert('Lỗi bắt đầu khám: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function completeAppointment(appointmentId) {
    if (!confirm('Bạn có chắc chắn muốn hoàn thành lịch hẹn này?')) {
        return;
    }
    
    try {
        console.log('📅 Completing appointment:', appointmentId);
        
        const response = await axios.patch(`/api/appointments/${appointmentId}/`, {
            status: 'COMPLETED',
            actual_end_time: new Date().toISOString()
        });
        
        showAlert('Hoàn thành lịch hẹn thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error completing appointment:', error);
        showAlert('Lỗi hoàn thành lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function rescheduleAppointment(appointmentId) {
    try {
        console.log('📅 Loading appointment for reschedule:', appointmentId);
        
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
        console.log('📅 Appointment data for reschedule:', appointment);
        
        // Populate edit form with current data
        populateEditForm(appointment);
        
        // Change modal title to indicate rescheduling
        const modalTitle = document.querySelector('#editAppointmentModal .modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Dời lịch hẹn';
        }
        
        const modal = new bootstrap.Modal(document.getElementById('editAppointmentModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error loading appointment for reschedule:', error);
        showAlert('Lỗi tải thông tin lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

function populateViewModal(appointment) {
    const modal = document.getElementById('viewAppointmentModal');
    if (!modal) return;
    
    const patientName = appointment.patient_name || 'N/A';
    const doctorName = appointment.doctor_name || 'N/A';
    
    const fields = {
        'view-appointment-number': appointment.appointment_number,
        'view-patient-name': patientName,
        'view-doctor-name': doctorName,
        'view-department-name': appointment.department_name,
        'view-appointment-date': formatDate(appointment.appointment_date),
        'view-appointment-time': formatTime(appointment.appointment_time),
        'view-appointment-type': getAppointmentTypeText(appointment.appointment_type),
        'view-priority': getPriorityText(appointment.priority),
        'view-status': getStatusText(appointment.status),
        'view-duration': (appointment.estimated_duration || 30) + ' phút',
        'view-created-at': formatDateTime(appointment.created_at),
        'view-booked-by': appointment.booked_by?.username || 'N/A',
        'view-reason': appointment.chief_complaint,
        'view-notes': appointment.notes || 'Không có ghi chú'
    };
    
    Object.entries(fields).forEach(([id, value]) => {
        const element = modal.querySelector(`#${id}`);
        if (element) {
            if (id === 'view-reason' || id === 'view-notes') {
                element.textContent = value || 'Không có';
            } else {
                element.textContent = value || 'Chưa cập nhật';
            }
        }
    });
}

function populateEditForm(appointment) {
    const form = document.getElementById('edit-appointment-form');
    if (!form) return;
    
    document.getElementById('edit-appointment-id').value = appointment.id;
    document.getElementById('edit-appointment-date').value = appointment.appointment_date;
    document.getElementById('edit-appointment-time').value = appointment.appointment_time;
    document.getElementById('edit-priority').value = appointment.priority;
    document.getElementById('edit-status').value = appointment.status;
    document.getElementById('edit-chief-complaint').value = appointment.chief_complaint || '';
    document.getElementById('edit-notes').value = appointment.notes || '';
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN');
}

function formatTime(timeStr) {
    if (!timeStr) return 'N/A';
    return timeStr.slice(0, 5); // HH:MM
}

function formatDateTime(datetimeStr) {
    if (!datetimeStr) return 'N/A';
    const date = new Date(datetimeStr);
    return date.toLocaleString('vi-VN');
}

function getAppointmentTypeText(type) {
    const types = {
        'CONSULTATION': 'Tư vấn',
        'FOLLOW_UP': 'Tái khám',
        'EMERGENCY': 'Cấp cứu',
        'PROCEDURE': 'Thủ thuật',
        'SURGERY': 'Phẫu thuật'
    };
    return types[type] || type;
}

function getPriorityText(priority) {
    const priorities = {
        'LOW': 'Thấp',
        'NORMAL': 'Bình thường',
        'HIGH': 'Cao',
        'URGENT': 'Khẩn cấp'
    };
    return priorities[priority] || priority;
}

function getStatusText(status) {
    const statuses = {
        'SCHEDULED': 'Đã đặt lịch',
        'CONFIRMED': 'Đã xác nhận',
        'CHECKED_IN': 'Đã check-in',
        'IN_PROGRESS': 'Đang khám',
        'COMPLETED': 'Hoàn thành',
        'CANCELLED': 'Đã hủy',
        'NO_SHOW': 'Không đến'
    };
    return statuses[status] || status;
}

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
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
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
