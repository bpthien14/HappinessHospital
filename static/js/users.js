let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Setup form validation and save button logic
    setupSaveButtonLogic();

    // Listen for modal open event
    const addModal = document.getElementById('addUserModal');
    if (addModal) {
        addModal.addEventListener('shown.bs.modal', function() {
            setupSaveButtonLogic();
        });
    }

    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeUsers();
    } else {
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializeUsers);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeUsers();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

// Setup save button logic
function setupSaveButtonLogic() {
    const saveBtn = document.getElementById('save-user-btn');
    if (!saveBtn) return;

    const requiredFields = ['#username','#email','#first_name','#last_name','#password','#password_confirm','#user_type'];

    window.reevaluateSaveButton = () => {
        const allRequiredFilled = requiredFields.every(selector => {
            const el = document.querySelector(selector);
            return el && el.value && el.value.toString().trim().length > 0;
        });

        // Check password confirmation
        const password = document.getElementById('password');
        const passwordConfirm = document.getElementById('password_confirm');
        const passwordsMatch = password && passwordConfirm &&
                              password.value === passwordConfirm.value &&
                              password.value.length > 0;

        saveBtn.disabled = !(allRequiredFilled && passwordsMatch);
    };

    // Listen to all required fields
    requiredFields.forEach(selector => {
        const el = document.querySelector(selector);
        if (el) {
            el.addEventListener('input', window.reevaluateSaveButton);
            el.addEventListener('change', window.reevaluateSaveButton);
        }
    });

    // Initial evaluation
    setTimeout(window.reevaluateSaveButton, 0);
}

function initializeUsers() {
    if (checkAuth()) {
        loadUsers();
        setupEventListeners();
    }
}

function setupEventListeners() {
    // Search form
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1;
        loadUsers();
    });
    
    // Realtime search
    let searchTimeout;
    const searchInput = document.getElementById('search-query');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadUsers();
            }, 500);
        });
    }
    
    // Realtime filter cho dropdowns
    const userTypeFilter = document.getElementById('user-type-filter');
    const statusFilter = document.getElementById('status-filter');
    
    if (userTypeFilter) {
        userTypeFilter.addEventListener('change', function() {
            currentPage = 1;
            loadUsers();
        });
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentPage = 1;
            loadUsers();
        });
    }

    // Add user form
    document.getElementById('add-user-form').addEventListener('submit', handleAddUser);
}

async function loadUsers() {
    try {
        // Kiểm tra authentication
        const token = localStorage.getItem('access_token');
        if (!token) {
            showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
            redirectToLogin();
            return;
        }

        const searchQuery = document.getElementById('search-query').value.trim();
        const userTypeFilter = document.getElementById('user-type-filter').value;
        const statusFilter = document.getElementById('status-filter').value;

        const params = new URLSearchParams({
            page: currentPage,
            page_size: 10
        });

        // Add search parameter if not empty
        if (searchQuery) {
            params.append('search', searchQuery);
        }

        // Handle user type filter
        if (userTypeFilter === 'NON_PATIENT') {
            params.append('exclude_user_types', 'PATIENT,ADMIN');
        } else if (userTypeFilter && userTypeFilter !== '') {
            params.append('user_type', userTypeFilter);
        }

        // Handle status filter
        if (statusFilter !== '' && statusFilter !== 'all') {
            params.append('is_active', statusFilter);
        }

        const response = await axios.get(`/api/users/?${params}`);
        displayUsers(response.data.results);
        updatePagination(response.data);

    } catch (error) {
        console.error('Error loading users:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else if (error.code === 'ERR_NETWORK') {
            showAlert('Mất kết nối tạm thời. Đang thử lại...', 'warning');
            setTimeout(loadUsers, 1000);
        } else {
            const errorMessage = error.response?.data?.detail || 'Lỗi khi tải danh sách người dùng';
            showAlert(errorMessage, 'danger');
        }
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.username}</td>
            <td>${user.full_name}</td>
            <td>
                <span class="badge ${getUserTypeBadgeClass(user.user_type)}">
                    ${getUserTypeDisplay(user.user_type)}
                </span>
            </td>
            <td>${user.email}</td>
            <td>${user.phone_number || '-'}</td>
            <td>${user.department || '-'}</td>
            <td>
                <span class="badge ${user.is_active ? 'bg-success' : 'bg-secondary'}">
                    ${user.is_active ? 'Hoạt động' : 'Vô hiệu'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1 p-0 d-inline-flex align-items-center justify-content-center" onclick="viewUser('${user.id}')" title="Xem thông tin" style="width: 32px; height: 32px;">
                    <i class="fas fa-eye fa-fw align-middle"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger p-0 d-inline-flex align-items-center justify-content-center" onclick="deleteUser('${user.id}')" title="Xóa người dùng" style="width: 32px; height: 32px;">
                    <i class="fas fa-trash fa-fw align-middle"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function getUserTypeBadgeClass(userType) {
    const classes = {
        'ADMIN': 'bg-danger',
        'DOCTOR': 'bg-primary',
        'NURSE': 'bg-info',
        'RECEPTION': 'bg-warning',
        'PHARMACIST': 'bg-success',
        'TECHNICIAN': 'bg-secondary',
        'CASHIER': 'bg-dark',
        'PATIENT': 'bg-light text-dark'
    };
    return classes[userType] || 'bg-secondary';
}

function getUserTypeDisplay(userType) {
    const displays = {
        'ADMIN': 'Quản trị viên',
        'DOCTOR': 'Bác sĩ',
        'NURSE': 'Y tá',
        'RECEPTION': 'Lễ tân',
        'PHARMACIST': 'Dược sĩ',
        'TECHNICIAN': 'Kỹ thuật viên',
        'CASHIER': 'Thu ngân',
        'PATIENT': 'Bệnh nhân'
    };
    return displays[userType] || userType;
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
        loadUsers();
    }
}

async function handleAddUser(e) {
    e.preventDefault();

    // Kiểm tra authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return;
    }

    const form = e.target;
    // Clear previous invalid marks
    Array.from(form.elements).forEach(el => el.classList && el.classList.remove('is-invalid'));

    // Client-side validation for required fields
    const requiredErrors = [];
    const invalidElements = [];
    Array.from(form.elements).forEach(el => {
        if (el.willValidate && !el.checkValidity()) {
            invalidElements.push(el);
            const label = form.querySelector(`label[for="${el.id}"]`);
            const fieldName = label ? label.textContent.replace('*','').trim() : (el.name || el.id);
            requiredErrors.push(`${fieldName}: Vui lòng nhập thông tin hợp lệ.`);
        }
    });

    // Check password confirmation
    const password = document.getElementById('password');
    const passwordConfirm = document.getElementById('password_confirm');
    if (password.value !== passwordConfirm.value) {
        requiredErrors.push('Mật khẩu xác nhận không khớp.');
        invalidElements.push(passwordConfirm);
    }

    if (requiredErrors.length) {
        invalidElements.forEach(el => el.classList && el.classList.add('is-invalid'));
        showFloatingErrors(requiredErrors);
        return;
    }

    const formData = new FormData(form);
    const userData = Object.fromEntries(formData.entries());

    // Handle empty date_of_birth
    if (userData.date_of_birth === '') {
        delete userData.date_of_birth;
    }

    try {
        await axios.post('/api/auth/register/', userData, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Close modal and refresh list
        const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
        modal.hide();
        e.target.reset();

        showFloatingNotification('Thêm người dùng thành công!', 'success', 'fas fa-check-circle', 4000);
        loadUsers();

    } catch (error) {
        console.error('Error adding user:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else {
            // Hiển thị tối đa 3 dòng lỗi ngắn gọn
            const messages = [];
            const data = error.response?.data;
            if (data && typeof data === 'object') {
                try {
                    Object.keys(data).forEach(k => {
                        const v = Array.isArray(data[k]) ? data[k].join(', ') : data[k];
                        messages.push(String(v));
                    });
                } catch (e) { /* no-op */ }
            }
            const compact = messages.slice(0, 3);
            if (!compact.length) compact.push('Lỗi khi thêm người dùng');
            showFloatingErrors(compact);
        }
    }
}

function viewUser(userId) {
    if (!checkAuth()) return;
    openViewUserModal(userId);
}

async function deleteUser(userId) {
    // Kiểm tra authentication trước khi xóa
    if (!checkAuth()) return;

    try {
        // Get user info first to show in confirmation modal
        const response = await axios.get(`/api/users/${userId}/`);
        const user = response.data;

        // Populate confirmation modal with user info
        document.getElementById('delete-user-username').textContent = user.username || '-';
        document.getElementById('delete-user-name').textContent = user.full_name || '-';
        document.getElementById('delete-user-email').textContent = user.email || '-';

        // Show confirmation modal
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteUserModal'));
        deleteModal.show();

        // Store user ID for deletion
        window._deleteUserId = userId;

    } catch (error) {
        console.error('Error loading user for deletion:', error);
        showAlert('Không thể tải thông tin người dùng', 'danger');
    }
}

async function performDeleteUser(userId) {
    let loadingToast = null;

    try {
        // Show loading notification
        loadingToast = showFloatingNotification(
            'Đang xóa người dùng...',
            'info',
            'fas fa-spinner fa-spin',
            0
        );

        await axios.delete(`/api/users/${userId}/`);

        // Remove loading notification
        if (loadingToast && loadingToast.parentNode) {
            loadingToast.remove();
        }

        // Show success notification
        showFloatingNotification(
            'Xóa người dùng thành công!',
            'success',
            'fas fa-check-circle',
            4000
        );

        // Refresh the user list
        loadUsers();

    } catch (error) {
        console.error('Error deleting user:', error);

        // Remove loading notification on error
        if (loadingToast && loadingToast.parentNode) {
            loadingToast.remove();
        }

        // Show error notification
        if (error.response?.status === 401) {
            showFloatingNotification(
                'Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại',
                'warning',
                'fas fa-exclamation-triangle',
                6000
            );
            redirectToLogin();
        } else if (error.response?.status === 403) {
            showFloatingNotification(
                'Bạn không có quyền xóa người dùng này',
                'danger',
                'fas fa-ban',
                6000
            );
        } else if (error.response?.status === 404) {
            showFloatingNotification(
                'Người dùng không tồn tại hoặc đã bị xóa',
                'warning',
                'fas fa-user-times',
                5000
            );
            loadUsers(); // Refresh to remove from list
        } else {
            showFloatingNotification(
                'Lỗi khi xóa người dùng. Vui lòng thử lại.',
                'danger',
                'fas fa-times-circle',
                6000
            );
        }
    }
}

// ===== View User Modal =====
async function openViewUserModal(userId) {
    const modalEl = document.getElementById('viewUserModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    const loading = document.getElementById('view-user-loading');
    const errorBox = document.getElementById('view-user-error');
    const content = document.getElementById('view-user-content');

    // Reset UI
    errorBox.classList.add('d-none');
    content.classList.add('d-none');
    loading.style.display = 'block';
    modal.show();

    try {
        const res = await axios.get(`/api/users/${userId}/`);
        const user = res.data;

        // Fill data
        window._currentViewUserId = userId;
        document.getElementById('vu-username').textContent = user.username || '-';
        document.getElementById('vu-full_name').textContent = user.full_name || '-';
        document.getElementById('vu-email').textContent = user.email || '-';
        document.getElementById('vu-phone').textContent = user.phone_number || '-';
        document.getElementById('vu-user_type').textContent = getUserTypeDisplay(user.user_type);
        document.getElementById('vu-employee_id').textContent = user.employee_id || '-';
        document.getElementById('vu-department').textContent = user.department || '-';
        document.getElementById('vu-is_active').textContent = user.is_active ? 'Hoạt động' : 'Vô hiệu';
        document.getElementById('vu-dob').textContent = user.date_of_birth ? formatDate(user.date_of_birth) : '-';
        document.getElementById('vu-address').textContent = user.address || '-';
        document.getElementById('vu-last_login').textContent = user.last_login ? formatDateTime(user.last_login) : '-';



        // Fill audit info
        const fmt = (s) => s ? new Date(s).toLocaleString('vi-VN') : '-';
        document.getElementById('vu-created_at').textContent = fmt(user.created_at);
        document.getElementById('vu-updated_at').textContent = fmt(user.updated_at);

        // Prefill edit form
        document.getElementById('ve-username').value = user.username || '';
        document.getElementById('ve-email').value = user.email || '';
        document.getElementById('ve-first_name').value = user.first_name || '';
        document.getElementById('ve-last_name').value = user.last_name || '';
        document.getElementById('ve-user_type').value = user.user_type || '';
        document.getElementById('ve-employee_id').value = user.employee_id || '';
        document.getElementById('ve-department').value = user.department || '';
        document.getElementById('ve-phone_number').value = user.phone_number || '';
        document.getElementById('ve-date_of_birth').value = user.date_of_birth || '';
        document.getElementById('ve-address').value = user.address || '';
        document.getElementById('ve-is_active').checked = user.is_active || false;

        // Setup tab switching
        setupEditTabToggle();

        // Setup save button state monitoring
        setupSaveButtonMonitoring();

        // Store original data for diff on save
        window._currentUserOriginal = {
            username: user.username || '',
            email: user.email || '',
            first_name: user.first_name || '',
            last_name: user.last_name || '',
            user_type: user.user_type || '',
            employee_id: user.employee_id || '',
            department: user.department || '',
            phone_number: user.phone_number || '',
            date_of_birth: user.date_of_birth || '',
            address: user.address || '',
            is_active: user.is_active || false
        };

        // Show content
        loading.style.display = 'none';
        content.classList.remove('d-none');

    } catch (error) {
        console.error('Load user detail error:', error);
        loading.style.display = 'none';
        errorBox.classList.remove('d-none');
        if (error.response?.status === 401) {
            errorBox.textContent = 'Phiên đăng nhập đã hết hạn.';
        } else {
            errorBox.textContent = 'Không thể tải thông tin người dùng.';
        }
    }
}

// Setup tab switching to show/hide save button
function setupEditTabToggle() {
    const editTab = document.getElementById('vu-edit-tab');
    const viewTab = document.getElementById('vu-view-tab');
    const saveBtn = document.getElementById('vu-save-btn');

    if (editTab && !editTab.dataset.eventBound) {
        editTab.addEventListener('click', function() {
            if (saveBtn) {
                // Show save button when switching to edit tab, but evaluate if it should be visible
                setTimeout(evaluateSaveButtonState, 100);
            }
        });
        editTab.dataset.eventBound = '1';
    }

    if (viewTab && !viewTab.dataset.eventBound) {
        viewTab.addEventListener('click', function() {
            if (saveBtn) {
                // Hide save button when switching to view tab
                saveBtn.style.display = 'none';
            }
        });
        viewTab.dataset.eventBound = '1';
    }
}

// Setup save button monitoring for changes
function setupSaveButtonMonitoring() {
    const saveBtn = document.getElementById('vu-save-btn');
    if (!saveBtn) return;

    // Hide save button by default since view tab is active
    saveBtn.style.display = 'none';

    // Get all form inputs to monitor
    const form = document.getElementById('vu-edit-form');
    if (!form) return;

    // Add event listeners to all form inputs
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', evaluateSaveButtonState);
        input.addEventListener('change', evaluateSaveButtonState);
    });

    // Initial evaluation
    setTimeout(evaluateSaveButtonState, 100);
}

// Evaluate if save button should be enabled
function evaluateSaveButtonState() {
    const saveBtn = document.getElementById('vu-save-btn');
    if (!saveBtn) return;

    // Check if we're currently on the edit tab
    const editTab = document.getElementById('vu-edit-tab');
    const isEditTabActive = editTab && editTab.classList.contains('active');

    // If not on edit tab, hide the button
    if (!isEditTabActive) {
        saveBtn.style.display = 'none';
        return;
    }

    const original = window._currentUserOriginal || {};
    const current = getCurrentFormValues();

    // Check if there are any changes
    const hasChanges = Object.keys(current).some(key => {
        const oldVal = original[key];
        const newVal = current[key];
        const normalizedOld = (oldVal === undefined ? null : oldVal);
        return String(normalizedOld) !== String(newVal);
    });

    // Show/hide and enable/disable save button based on changes
    if (hasChanges) {
        saveBtn.style.display = 'inline-block';
        saveBtn.disabled = false;
        saveBtn.textContent = 'Lưu thay đổi';
        saveBtn.classList.remove('btn-secondary');
        saveBtn.classList.add('btn-primary');
    } else {
        saveBtn.style.display = 'none';
        saveBtn.disabled = true;
        saveBtn.textContent = 'Không có thay đổi';
        saveBtn.classList.remove('btn-primary');
        saveBtn.classList.add('btn-secondary');
    }
}

// Get current form values for comparison
function getCurrentFormValues() {
    return {
        username: document.getElementById('ve-username')?.value?.trim() || '',
        email: document.getElementById('ve-email')?.value?.trim() || '',
        first_name: document.getElementById('ve-first_name')?.value?.trim() || '',
        last_name: document.getElementById('ve-last_name')?.value?.trim() || '',
        user_type: document.getElementById('ve-user_type')?.value || '',
        employee_id: document.getElementById('ve-employee_id')?.value?.trim() || '',
        department: document.getElementById('ve-department')?.value?.trim() || '',
        phone_number: document.getElementById('ve-phone_number')?.value?.trim() || '',
        date_of_birth: document.getElementById('ve-date_of_birth')?.value || '',
        address: document.getElementById('ve-address')?.value?.trim() || '',
        is_active: document.getElementById('ve-is_active')?.checked || false
    };
}

// Handle delete confirmation
document.addEventListener('click', async function(e) {
    if (e.target && e.target.id === 'confirm-delete-btn') {
        const userId = window._deleteUserId;
        if (userId) {
            // Hide the modal first
            const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteUserModal'));
            deleteModal.hide();

            // Perform deletion
            await performDeleteUser(userId);

            // Clear stored ID
            window._deleteUserId = null;
        }
    }
});

// Save changes from edit tab
document.addEventListener('click', async function(e) {
    if (e.target && e.target.id === 'vu-save-btn') {
        const tabForm = document.getElementById('vu-edit-form');
        const userId = window._currentViewUserId;
        // Build diff-only payload
        const current = getCurrentFormValues();

        const original = window._currentUserOriginal || {};
        const payload = {};
        Object.keys(current).forEach((key) => {
            const oldVal = original[key];
            const newVal = current[key];
            const normalizedOld = (oldVal === undefined ? null : oldVal);
            if (String(normalizedOld) !== String(newVal)) {
                payload[key] = newVal;
            }
        });

        // If nothing changed, just show success and return
        if (Object.keys(payload).length === 0) {
            showFloatingNotification('Không có thay đổi nào để lưu.', 'info');
            return;
        }

        try {
            // Partial update
            await axios.patch(`/api/users/${userId}/`, payload);

            // Close modal if open
            const modalEl = document.getElementById('viewUserModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // Success notification
            showFloatingNotification('Cập nhật người dùng thành công!', 'success', 'fas fa-check-circle', 4000);

            // Refresh list
            loadUsers();

        } catch (error) {
            // Clear previous invalid states
            Array.from(tabForm.elements).forEach(el => el.classList && el.classList.remove('is-invalid'));

            const msgs = [];
            const data = error.response?.data;
            if (data && typeof data === 'object') {
                Object.keys(data).forEach(field => {
                    const errors = Array.isArray(data[field]) ? data[field] : [data[field]];
                    const inputId = `ve-${field}`;
                    const el = document.getElementById(inputId);
                    if (el && el.classList) {
                        el.classList.add('is-invalid');
                    }
                    errors.forEach(err => msgs.push(`${humanizeField(field)}: ${err}`));
                });
            }

            showFloatingNotification(
                (msgs.length ? msgs.join('<br/>') : 'Không thể cập nhật.'),
                'danger',
                'fas fa-times-circle',
                6000
            );
        }
    }
});

// ===== Helpers =====
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showAlert('Vui lòng đăng nhập để tiếp tục', 'warning');
        redirectToLogin();
        return false;
    }
    return true;
}

function redirectToLogin() {
    try {
        const rawPath = window.location.pathname || '/';
        const normalizedPath = (rawPath.endsWith('/') ? rawPath : rawPath + '/').toLowerCase();
        const publicPaths = new Set(['/login/', '/signup/']);
        if (publicPaths.has(normalizedPath)) {
            return;
        }
    } catch (e) { /* noop */ }
    window.location.href = '/login/';
}

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

function showFloatingNotification(message, type = 'info', icon = null, duration = 5000) {
    const containerId = 'hh-floating-notifications';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.style.position = 'fixed';
        container.style.top = '1rem';
        container.style.right = '1rem';
        container.style.zIndex = '1060';
        container.style.maxWidth = '350px';
        document.body.appendChild(container);
    }

    const typeClasses = {
        success: 'alert-success',
        info: 'alert-info',
        warning: 'alert-warning',
        danger: 'alert-danger'
    };

    const typeIcons = {
        success: 'fas fa-check-circle',
        info: 'fas fa-info-circle',
        warning: 'fas fa-exclamation-triangle',
        danger: 'fas fa-times-circle'
    };

    const toast = document.createElement('div');
    toast.className = `alert ${typeClasses[type] || 'alert-info'} shadow-lg border-0`;
    toast.style.minWidth = '320px';
    toast.style.marginBottom = '0.5rem';

    const iconHtml = icon || typeIcons[type] || 'fas fa-info-circle';

    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${iconHtml} me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close btn-close-sm ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 300);
        }
    }, duration);

    return toast;
}

function showFloatingErrors(messages) {
    const errorMessage = `
        <div class="fw-semibold mb-1">Không thể lưu. Vui lòng kiểm tra:</div>
        <ul class="mb-0 ps-3">${messages.map(m => `<li>${m}</li>`).join('')}</ul>
    `;
    showFloatingNotification(errorMessage, 'danger', 'fas fa-exclamation-triangle', 8000);
}

function humanizeField(field) {
    const map = {
        username: 'Tên đăng nhập',
        email: 'Email',
        first_name: 'Họ',
        last_name: 'Tên',
        user_type: 'Loại người dùng',
        employee_id: 'Mã nhân viên',
        department: 'Khoa/Phòng',
        phone_number: 'Số điện thoại',
        date_of_birth: 'Ngày sinh',
        address: 'Địa chỉ',
        is_active: 'Trạng thái hoạt động'
    };
    return map[field] || field;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN');
}
