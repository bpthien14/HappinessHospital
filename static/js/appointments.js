/**
 * Appointments Management JavaScript
 * Handles CRUD operations for appointments
 */

let currentPage = 1;
let totalPages = 1;
let allAppointments = [];

document.addEventListener('DOMContentLoaded', function() {
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeAppointments();
    } else {
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeAppointments);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeAppointments();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializeAppointments() {
    if (checkAuth()) {
        loadAppointments();
        loadFormData();
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
            loadAppointments();
        });
    }

    // Add appointment form
    const addForm = document.getElementById('add-appointment-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddAppointment);
        // Set default VN date for add form
        try {
            const dateInput = document.getElementById('add-appointment-date');
            if (dateInput) {
                dateInput.value = getVietnamDateString();
            }
            const timeInput = document.getElementById('add-appointment-time');
            if (timeInput) {
                timeInput.placeholder = 'Chọn bác sĩ và ngày để gợi ý giờ';
            }
        } catch (e) { /* noop */ }
        // Load slots when doctor/date changes
        const addDoctor = document.getElementById('add-doctor');
        const addDate = document.getElementById('add-appointment-date');
        if (addDoctor) addDoctor.addEventListener('change', loadAddTimeSlots);
        if (addDate) addDate.addEventListener('change', loadAddTimeSlots);
        // Department -> Doctors linkage (Reception only)
        const isReception = (JSON.parse(localStorage.getItem('user_data') || '{}').user_type === 'RECEPTION');
        if (isReception) {
            const addDept = document.getElementById('add-department');
            if (addDept) addDept.addEventListener('change', loadAddDoctors);
        }
    }

    // Edit appointment form
    const editForm = document.getElementById('edit-appointment-form');
    if (editForm) {
        editForm.addEventListener('submit', handleUpdateAppointment);
        // Track changes to enable/disable save button
        ['edit-appointment-date','edit-appointment-time','edit-priority','edit-chief-complaint','edit-notes']
            .forEach(id => {
                const el = document.getElementById(id);
                if (el) el.addEventListener('input', updateEditSaveState);
            });
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
        const link = e.target.closest('.pagination .page-link');
        if (link) {
            e.preventDefault();
            const page = parseInt(link.dataset.page, 10);
            if (page && page !== currentPage) {
                currentPage = page;
                loadAppointments(currentPage);
            }
        }
    });

    // My appointments only toggle
    const myOnly = document.getElementById('my-appointments-only');
    if (myOnly) {
        myOnly.addEventListener('change', function() {
            currentPage = 1;
            loadAppointments();
        });
    }
}

async function loadAppointments(page = 1) {
    try {
        // Lấy filters từ form
        const searchQuery = document.getElementById('search-query')?.value || '';
        const status = document.getElementById('status-filter')?.value || '';
        const priority = document.getElementById('priority-filter')?.value || '';
        const department = document.getElementById('department-filter')?.value || '';
        const date = document.getElementById('date-filter')?.value || '';
        const myOnlyChecked = document.getElementById('my-appointments-only')?.checked || false;

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

        // Thêm filter doctor nếu checkbox bật và có doctor_profile_id
        let appliedApiDoctorFilter = false;
        if (myOnlyChecked) {
            try {
                const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
                const doctorProfileId = userData?.doctor_profile_id || userData?.doctor?.id;
                if (doctorProfileId) {
                    params.append('doctor', doctorProfileId);
                    appliedApiDoctorFilter = true;
                }
            } catch (e) { /* noop */ }
        }

        const url = `/api/appointments/?${params.toString()}`;

        const response = await axios.get(url);

        const data = response.data;
        if (data.results || Array.isArray(data)) {
            currentPage = page;
            const items = data.results || data;
            allAppointments = Array.isArray(items) ? items : [];

            // Frontend filter theo bác sĩ nếu không áp dụng được filter qua API
            let visibleAppointments = allAppointments;
            if (myOnlyChecked && !appliedApiDoctorFilter) {
                try {
                    const userData = JSON.parse(localStorage.getItem('user_data') || '{}');
                    const currentDoctorName = userData?.full_name || userData?.username || '';
                    if (currentDoctorName) {
                        visibleAppointments = allAppointments.filter(a =>
                            String(a.doctor_name || '').toLowerCase().includes(String(currentDoctorName).toLowerCase())
                        );
                    }
                } catch (e) { /* noop */ }
            }

            const totalCount = appliedApiDoctorFilter ? (data.count || visibleAppointments.length || 0)
                                                     : (myOnlyChecked ? visibleAppointments.length : (data.count || visibleAppointments.length || 0));
            const pageSize = visibleAppointments.length || 1;
            totalPages = Math.max(1, Math.ceil((data.count || pageSize) / (pageSize || 1)));

            renderAppointments(visibleAppointments);
            updatePagination({ count: totalCount, pageSize });
            updateTotalCount(totalCount);
        } else {
            console.error('❌ Invalid response format:', data);
            showAlert('Lỗi định dạng dữ liệu', 'danger');
        }
        
    } catch (error) {
        console.error('❌ Error loading appointments:', error);
        if (error.response?.status === 401) {
            window.location.href = '/auth/login/';
            return;
        }
        showAlert('Lỗi tải danh sách lịch hẹn: ' + (error.response?.data?.detail || error.message), 'danger');
    }
}

async function loadFormData() {
    try {

        
        // Load departments
        const deptResponse = await axios.get('/api/departments/');
        populateSelectOptions('#department-filter', deptResponse.data.results || deptResponse.data, 'id', 'name');
        populateSelectOptions('#add-department', deptResponse.data.results || deptResponse.data, 'id', 'name');
        
        // Load patients
        const patientResponse = await axios.get('/api/patients/');
        const patients = patientResponse.data.results || patientResponse.data;
        populateSelectOptions('#add-patient', patients, 'id', (p) => {
            const phone = p.phone_number || 'N/A';
            const name = p.full_name || 'Chưa rõ tên';
            return `${phone} - ${name}`;
        });
        
        // Reception: require department before doctors; Others: preload all doctors
        const isReception = (JSON.parse(localStorage.getItem('user_data') || '{}').user_type === 'RECEPTION');
        if (isReception) {
            const addDoctor = document.querySelector('#add-doctor');
            if (addDoctor) {
                addDoctor.innerHTML = '<option value="">Chọn khoa trước</option>';
                addDoctor.disabled = true;
            }
        } else {
            // Load doctors
            const doctorResponse = await axios.get('/api/doctors/');
            const doctors = doctorResponse.data.results || doctorResponse.data;
            populateSelectOptions('#add-doctor', doctors, 'id', (doctor) => {
                const fullName = doctor.doctor_name || 'N/A';
                return `${fullName} - ${doctor.department_name || 'Chưa phân khoa'}`;
            });
        }
        
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

// ===== Time slots for Add Appointment (align with portal logic) =====
async function loadAddTimeSlots() {
    try {
        const doctorId = document.getElementById('add-doctor')?.value;
        const date = document.getElementById('add-appointment-date')?.value;
        const timeSelect = document.getElementById('add-appointment-time');
        if (!timeSelect) return;
        if (!doctorId || !date) {
            timeSelect.innerHTML = '<option value="">Chọn bác sĩ và ngày để gợi ý giờ</option>';
            timeSelect.disabled = true;
            return;
        }
        const resp = await axios.get(`/api/doctors/${doctorId}/available_slots/?date=${date}`);
        const slots = resp.data || [];
        // Lọc slot hợp lệ theo quy tắc 15 phút nếu là hôm nay
        const vnNow = getVietnamNow();
        const selectedDate = new Date(date + 'T00:00:00');
        const isToday = selectedDate.toDateString() === vnNow.toDateString();
        const available = slots.filter(s => {
            if (!isToday) return true;
            const [hh, mm] = (s.time || '').split(':').map(Number);
            const slotTime = new Date(vnNow);
            slotTime.setHours(hh || 0, mm || 0, 0, 0);
            const minTime = new Date(vnNow.getTime() + 15 * 60 * 1000);
            return slotTime >= minTime;
        });
        timeSelect.innerHTML = '';
        if (available.length === 0) {
            timeSelect.innerHTML = '<option value="">Không còn giờ phù hợp</option>';
            timeSelect.disabled = true;
            return;
        }
        available.forEach(s => {
            const t = String(s.time || '').slice(0,5);
            const opt = document.createElement('option');
            opt.value = t;
            opt.textContent = t;
            timeSelect.appendChild(opt);
        });
        timeSelect.disabled = false;
        // Chọn option đầu tiên
        timeSelect.value = available[0] ? String(available[0].time || '').slice(0,5) : '';
    } catch (e) {
        const timeSelect = document.getElementById('add-appointment-time');
        if (timeSelect) {
            timeSelect.innerHTML = '<option value="">Lỗi tải khung giờ</option>';
            timeSelect.disabled = true;
        }
    }
}

function getVietnamNow() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    return new Date(utc + 7 * 3600000);
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
    const isReception = (window.currentUser && window.currentUser.user_type === 'RECEPTION') ||
                        (window.HospitalApp && HospitalApp.isAuthenticated && JSON.parse(localStorage.getItem('user_data') || '{}').user_type === 'RECEPTION');
    const isDoctor = (JSON.parse(localStorage.getItem('user_data') || '{}').user_type === 'DOCTOR');
    
    const parts = [];
    // View
    parts.push(`<button class="btn btn-sm btn-outline-info me-1" onclick="viewAppointment('${appointment.id}')" title="Xem chi tiết"><i class="fas fa-eye"></i></button>`);
    // Edit (reception only)
    if ([ 'SCHEDULED', 'CONFIRMED' ].includes(appointment.status) && isReception) {
        parts.push(`<button class="btn btn-sm btn-outline-warning me-1" onclick="editAppointment('${appointment.id}')" title="Chỉnh sửa"><i class="fas fa-edit"></i></button>`);
    }
    // Confirm (doctors only)
    if (appointment.status === 'SCHEDULED' && isDoctor) {
        parts.push(`<button class="btn btn-sm btn-outline-success me-1" onclick="confirmAppointment('${appointment.id}')" title="Xác nhận"><i class="fas fa-check"></i></button>`);
    }
    // Check-in (reception only)
    if (appointment.status === 'CONFIRMED' && isReception) {
        parts.push(`<button class="btn btn-sm btn-outline-primary me-1" onclick="checkinAppointment('${appointment.id}')" title="Check-in"><i class="fas fa-sign-in-alt"></i></button>`);
    }
    // Start exam (doctors only)
    if (appointment.status === 'CHECKED_IN' && isDoctor) {
        parts.push(`<button class="btn btn-sm btn-outline-info me-1" onclick="startExamination('${appointment.id}')" title="Bắt đầu khám"><i class="fas fa-play"></i></button>`);
    }
    // Complete (doctors only)
    if (appointment.status === 'IN_PROGRESS' && isDoctor) {
        parts.push(`<button class="btn btn-sm btn-outline-success me-1" onclick="completeAppointment('${appointment.id}')" title="Hoàn thành"><i class="fas fa-check-circle"></i></button>`);
    }
    // Remove duplicate reschedule button: use Edit for rescheduling
    // Cancel - ALWAYS append last if allowed
    if ([ 'SCHEDULED', 'CONFIRMED' ].includes(appointment.status)) {
        parts.push(`<button class="btn btn-sm btn-outline-danger" onclick="cancelAppointment('${appointment.id}')" title="Hủy lịch"><i class="fas fa-times"></i></button>`);
    }

    buttons += parts.join('');
    return buttons;
}

function updatePagination(data) {
    const pagination = document.getElementById('pagination-container');
    if (!pagination) return;

    const count = data.count || 0;
    const pageSize = 10;
    const totalPagesCalc = Math.max(1, Math.ceil(count / pageSize));
    const currentPageNum = currentPage;

    if (totalPagesCalc <= 1) {
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
    for (let i = Math.max(1, currentPageNum - 2); i <= Math.min(totalPagesCalc, currentPageNum + 2); i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPageNum ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }

    // Next button
    if (currentPageNum < totalPagesCalc) {
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

        const response = await axios.post('/api/appointments/', data);
        
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
        // Ensure appointment_time is HH:MM
        if (data.appointment_time) data.appointment_time = String(data.appointment_time).slice(0,5);

        const response = await axios.patch(`/api/appointments/${appointmentId}/`, data);
        
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

function updateEditSaveState() {
    try {
        const baseline = window.__EDIT_BASELINE__ || {};
        const date = document.getElementById('edit-appointment-date')?.value || '';
        const time = document.getElementById('edit-appointment-time')?.value || '';
        const priority = document.getElementById('edit-priority')?.value || '';
        const complaint = document.getElementById('edit-chief-complaint')?.value || '';
        const notes = document.getElementById('edit-notes')?.value || '';
        const changed = (
            baseline.date !== date ||
            baseline.time !== time ||
            baseline.priority !== priority ||
            (baseline.complaint || '') !== (complaint || '') ||
            (baseline.notes || '') !== (notes || '')
        );
        const btn = document.getElementById('edit-save-btn');
        if (btn) btn.disabled = !changed;
    } catch (e) { /* noop */ }
}

async function loadEditTimeSlots(doctorId, date, cb) {
    try {
        if (!doctorId || !date) return cb && cb([]);
        const resp = await axios.get(`/api/doctors/${doctorId}/available_slots/?date=${date}`);
        const slots = resp.data || [];
        const vnNow = getVietnamNow();
        const selectedDate = new Date(date + 'T00:00:00');
        const isToday = selectedDate.toDateString() === vnNow.toDateString();
        const available = slots.filter(s => {
            if (!isToday) return true;
            const [hh, mm] = String(s.time || '').split(':').map(Number);
            const slotTime = new Date(vnNow);
            slotTime.setHours(hh || 0, mm || 0, 0, 0);
            const minTime = new Date(vnNow.getTime() + 15 * 60 * 1000);
            return slotTime >= minTime;
        });
        cb && cb(available);
    } catch (e) { cb && cb([]); }
}

async function viewAppointment(appointmentId) {
    try {
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
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
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
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
        const response = await axios.post(`/api/appointments/${appointmentId}/confirm/`);
        
        showAlert('Xác nhận lịch hẹn thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error confirming appointment:', error);
        showAlert('Lỗi xác nhận lịch hẹn: ' + (error.response?.data?.error || error.message), 'danger');
    }
}

async function checkinAppointment(appointmentId) {
    try {
        const response = await axios.post(`/api/appointments/${appointmentId}/checkin/`);
        
        showAlert('Check-in thành công!', 'success');
        loadAppointments();
        
    } catch (error) {
        console.error('❌ Error checking in appointment:', error);
        let msg = 'Lỗi check-in';
        if (error.response?.data?.error) msg += `: ${error.response.data.error}`;
        else if (error.response?.data?.detail) msg += `: ${error.response.data.detail}`;
        showAlert(msg, 'danger');
    }
}

async function cancelAppointment(appointmentId) {
    // Removed browser confirm - use UI modal if needed

    try {
        
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
    // Removed browser confirm - use UI modal if needed

    try {
        
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
        const response = await axios.get(`/api/appointments/${appointmentId}/`);
        const appointment = response.data;
        
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
    document.getElementById('edit-doctor-id').value = appointment.doctor;
    // Prepare time select with available slots
    const timeSelect = document.getElementById('edit-appointment-time');
    if (timeSelect) {
        timeSelect.innerHTML = '<option value="">Đang tải khung giờ...</option>';
        timeSelect.disabled = true;
        loadEditTimeSlots(appointment.doctor, appointment.appointment_date, (slots) => {
            timeSelect.innerHTML = '';
            if (!slots || slots.length === 0) {
                timeSelect.innerHTML = '<option value="">Không còn giờ phù hợp</option>';
                timeSelect.disabled = true;
            } else {
                slots.forEach(s => {
                    const t = String(s.time || '').slice(0,5);
                    const opt = document.createElement('option');
                    opt.value = t;
                    opt.textContent = t;
                    timeSelect.appendChild(opt);
                });
                timeSelect.disabled = false;
                // Preselect current time if still available
                const currentTime = (appointment.appointment_time || '').slice(0,5);
                timeSelect.value = currentTime && slots.some(s => String(s.time).startsWith(currentTime))
                    ? currentTime
                    : String(slots[0].time || '').slice(0,5);
            }
        });
    }
    document.getElementById('edit-priority').value = appointment.priority;
    document.getElementById('edit-chief-complaint').value = appointment.chief_complaint || '';
    document.getElementById('edit-notes').value = appointment.notes || '';
    // Save baseline for change detection
    window.__EDIT_BASELINE__ = {
        date: appointment.appointment_date,
        time: (appointment.appointment_time || '').slice(0,5),
        priority: appointment.priority,
        complaint: appointment.chief_complaint || '',
        notes: appointment.notes || ''
    };
    updateEditSaveState();
}

// Utility functions
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('vi-VN');
}

function formatTime(timeStr) {
    if (!timeStr) return 'N/A';
    try { return timeStr.slice(0, 5); } catch (e) { return 'N/A'; }
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
        window.location.href = '/auth/login/';
        return false;
    }
    return true;
}

// Load doctors for add form after selecting department (Reception)
async function loadAddDoctors() {
    try {
        const deptId = document.getElementById('add-department')?.value;
        const addDoctor = document.getElementById('add-doctor');
        if (!addDoctor) return;
        if (!deptId) {
            addDoctor.innerHTML = '<option value="">Chọn khoa trước</option>';
            addDoctor.disabled = true;
            return;
        }
        const doctorResponse = await axios.get(`/api/doctors/?department=${deptId}`);
        const doctors = doctorResponse.data.results || doctorResponse.data;
        addDoctor.disabled = false;
        populateSelectOptions('#add-doctor', doctors, 'id', (doctor) => {
            const fullName = doctor.doctor_name || 'N/A';
            const deptName = doctor.department_name || 'Chưa phân khoa';
            return `${fullName} - ${deptName}`;
        });
        // Reset time suggestion when doctor list changes
        await loadAddTimeSlots();
    } catch (e) {
        // noop
    }
}

// Helper for Vietnam date string
function getVietnamDateString() {
    const now = new Date();
    const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
    const vn = new Date(utc + 7 * 3600000);
    const y = vn.getFullYear();
    const m = String(vn.getMonth() + 1).padStart(2, '0');
    const d = String(vn.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}
