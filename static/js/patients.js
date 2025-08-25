let currentPage = 1;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    // Đợi axios interceptors sẵn sàng
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializePatients();
    } else {
        // Đợi event từ main.js
        window.addEventListener('axiosInterceptorsReady', initializePatients);
        // Fallback: đợi tối đa 2 giây
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializePatients();
            } else {
                console.error('❌ Axios interceptors not ready after timeout');
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 2000);
    }
});

function initializePatients() {
    if (checkAuth()) {
        loadPatients();
        setupEventListeners();
    }
}

function setupEventListeners() {
    // Search form
    document.getElementById('search-form').addEventListener('submit', function(e) {
        e.preventDefault();
        currentPage = 1;
        loadPatients();
    });
    
    // Add patient form
    document.getElementById('add-patient-form').addEventListener('submit', handleAddPatient);
    // Dynamic enable/disable save button
    const form = document.getElementById('add-patient-form');
    const saveBtn = document.getElementById('save-patient-btn');
    const requiredSelectors = ['#full_name','#date_of_birth','#gender','#phone_number','#citizen_id','#province','#ward','#address','#emergency_contact_name','#emergency_contact_phone','#emergency_contact_relationship'];
    const watched = requiredSelectors.map(sel => document.querySelector(sel)).filter(Boolean);
    const reevaluate = () => {
        const allFilled = watched.every(el => el && el.value && el.value.toString().trim().length > 0);
        // ward must be enabled and selected
        const wardEl = document.getElementById('ward');
        const okWard = wardEl && !wardEl.disabled && wardEl.value;
        saveBtn.disabled = !(allFilled && okWard);
    };
    watched.forEach(el => el.addEventListener('input', reevaluate));
    watched.forEach(el => el.addEventListener('change', reevaluate));
    // reevaluate on modal open too
    setTimeout(reevaluate, 0);
    
    // Insurance checkbox: luôn hiển thị, chỉ disable input khi chưa chọn
    document.getElementById('has_insurance').addEventListener('change', function() {
        const insuranceFields = document.getElementById('insurance-fields');
        const numberInput = document.getElementById('insurance_number');
        insuranceFields.style.display = 'block';
        numberInput.disabled = !this.checked;
        // not required unless checked
        if (this.checked) {
            numberInput.setAttribute('required','required');
        } else {
            numberInput.removeAttribute('required');
        }
        // reevaluate after toggle
        setTimeout(reevaluate, 0);
    });

    // Địa giới hành chính: Province -> District -> Ward
    bindAdministrativeSelectors();
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
        
        const response = await axios.get(`/api/patients/?${params}`);
        displayPatients(response.data.results);
        updatePagination(response.data);
        
    } catch (error) {
        console.error('Error loading patients:', error);
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning');
            redirectToLogin();
        } else if (error.code === 'ERR_NETWORK') {
            showAlert('Mất kết nối tạm thời. Đang thử lại...', 'warning');
            setTimeout(loadPatients, 1000);
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

    // Ensure province and ward are selected (ward may be disabled by default)
    const provinceSel = document.getElementById('province');
    const wardSel = document.getElementById('ward');
    if (!provinceSel.value) {
        requiredErrors.push('Tỉnh/TP: Vui lòng chọn');
        invalidElements.push(provinceSel);
    }
    if (!wardSel.value) {
        requiredErrors.push('Phường/Xã: Vui lòng chọn');
        invalidElements.push(wardSel);
    }

    if (requiredErrors.length) {
        invalidElements.forEach(el => el.classList && el.classList.add('is-invalid'));
        showFloatingErrors(requiredErrors);
        return;
    }

    const formData = new FormData(form);
    const patientData = Object.fromEntries(formData.entries());
    // Gửi tên hiển thị thay vì mã code cho province/ward (bỏ district)
    if (provinceSel?.selectedIndex > 0) {
        patientData.province = provinceSel.options[provinceSel.selectedIndex].textContent.trim();
    }
    if (wardSel?.selectedIndex > 0) {
        patientData.ward = wardSel.options[wardSel.selectedIndex].textContent.trim();
    }
    // Mặc định Quận/Huyện khi backend chưa chỉnh
    if (!patientData.district || !patientData.district.trim()) {
        patientData.district = 'Quận 5';
    }
    
    // Convert checkbox to boolean
    patientData.has_insurance = document.getElementById('has_insurance').checked;
    
    try {
        await axios.post('/api/patients/', patientData, {
            headers: {
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
            // Hiển thị tối đa 3 dòng lỗi ngắn gọn (không nêu tên trường kỹ thuật)
            const messages = [];
            const data = error.response?.data;
            if (data && typeof data === 'object') {
                try {
                    Object.keys(data).forEach(k => {
                        const v = Array.isArray(data[k]) ? data[k].join(', ') : data[k];
                        // Chỉ lấy phần message, bỏ tên trường kỹ thuật
                        messages.push(String(v));
                    });
                } catch (e) { /* no-op */ }
            }
            const compact = messages.slice(0, 3);
            if (!compact.length) compact.push('Lỗi khi thêm bệnh nhân');
            showFloatingErrors(compact);
        }
    }
}

// ===== Địa giới hành chính Việt Nam =====
let vnAdminCache = {
    provinces: null,
    districtsByProvince: {},
    wardsByDistrict: {}
};

function bindAdministrativeSelectors() {
    const provinceSelect = document.getElementById('province');
    const wardSelect = document.getElementById('ward');
    const addressInput = document.getElementById('address');
    const provinceSearch = null;
    const wardSearch = null;

    if (!provinceSelect || !wardSelect) return;

    // Load provinces on open modal (nội bộ)
    loadProvinces().then(() => {
        // no-op
    }).catch(() => {
        showAlert('Không tải được danh sách Tỉnh/TP', 'warning');
    });

    provinceSelect.addEventListener('change', async function() {
        const provinceCode = this.value;
        // Reset lower level
        wardSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';
        wardSelect.disabled = true;
        addressInput.disabled = true;

        if (provinceCode) {
            await loadWardsByProvince(provinceCode);
            wardSelect.disabled = false;
        }
        // trigger reevaluate save button
        const saveBtn = document.getElementById('save-patient-btn');
        if (saveBtn) saveBtn.disabled = !(document.getElementById('ward').value);
    });

    wardSelect.addEventListener('change', function() {
        const wardCode = this.value;
        addressInput.disabled = !wardCode;
        if (wardCode) {
            addressInput.focus();
        }
        // trigger reevaluate save button
        const saveBtn = document.getElementById('save-patient-btn');
        if (saveBtn) {
            const requiredSelectors = ['#full_name','#date_of_birth','#gender','#phone_number','#citizen_id','#province','#ward','#address','#emergency_contact_name','#emergency_contact_phone','#emergency_contact_relationship'];
            const allFilled = requiredSelectors.every(sel => {
                const el = document.querySelector(sel);
                return el && el.value && el.value.toString().trim().length > 0;
            });
            saveBtn.disabled = !allFilled;
        }
    });
    // Quick search removed per request
}

async function loadProvinces() {
    if (vnAdminCache.provinces) {
        renderOptions(document.getElementById('province'), vnAdminCache.provinces, 'Chọn Tỉnh/Thành phố');
        return;
    }
    // Sử dụng endpoint nội bộ đọc từ vietnam-provinces
    const url = '/api/geo/provinces/';
    try {
        const res = await axios.get(url);
        const items = res.data.map(p => {
            const display = normalizeProvinceName(p.name);
            return { value: p.code, label: display, extra: p.name };
        });
        vnAdminCache.provinces = items;
        renderOptions(document.getElementById('province'), items, 'Chọn Tỉnh/Thành phố');
    } catch (e) {
        console.warn('Load provinces failed', e);
    }
}

async function loadWardsByProvince(provinceCode) {
    if (vnAdminCache.wardsByDistrict[provinceCode]) {
        renderOptions(document.getElementById('ward'), vnAdminCache.wardsByDistrict[provinceCode], 'Chọn Phường/Xã');
        return;
    }
    const url = `/api/geo/provinces/${provinceCode}/`;
    try {
        const res = await axios.get(url);
        const wards = (res.data?.wards || []).map(w => ({ value: w.code, label: w.name, extra: w.name }));
        vnAdminCache.wardsByDistrict[provinceCode] = wards;
        renderOptions(document.getElementById('ward'), wards, 'Chọn Phường/Xã');
        const pname = res.data?.name ? normalizeProvinceName(res.data.name) : '';
        document.getElementById('province').dataset.label = pname;
    } catch (e) {
        console.warn('Load wards by province failed', e);
    }
}

function renderOptions(selectEl, items, placeholder) {
    const prev = selectEl.value;
    selectEl.innerHTML = '';
    const ph = document.createElement('option');
    ph.value = '';
    ph.textContent = placeholder || 'Chọn';
    selectEl.appendChild(ph);
    items.forEach(it => {
        const opt = document.createElement('option');
        opt.value = String(it.value);
        opt.textContent = it.label;
        opt.dataset.label = it.label;
        if (String(prev) === String(it.value)) opt.selected = true;
        selectEl.appendChild(opt);
    });
}

// No hidden-field sync needed when using select directly

// ===== Helpers =====
function normalizeProvinceName(name) {
    if (!name) return name;
    // Bỏ tiền tố "Tỉnh", "Thành phố", "TP.", "TP"
    const trimmed = String(name).replace(/^\s+|\s+$/g, '');
    return trimmed.replace(/^(Tỉnh|Thành\s*phố|TP\.?)(\s+)/i, '');
}

// ===== Edit tab geo helpers =====
async function ensureEditGeoLoaded() {
    if (!vnAdminCache.provinces) {
        await loadProvinces();
    }
    renderOptions(document.getElementById('ve-province'), vnAdminCache.provinces, 'Chọn Tỉnh/Thành phố');
}

async function loadEditWardsByProvince(provinceCode) {
    if (vnAdminCache.wardsByDistrict[provinceCode]) {
        renderOptions(document.getElementById('ve-ward'), vnAdminCache.wardsByDistrict[provinceCode], 'Chọn Phường/Xã');
        return;
    }
    const url = `/api/geo/provinces/${provinceCode}/`;
    const res = await axios.get(url);
    const wards = (res.data?.wards || []).map(w => ({ value: w.code, label: w.name, extra: w.name }));
    vnAdminCache.wardsByDistrict[provinceCode] = wards;
    renderOptions(document.getElementById('ve-ward'), wards, 'Chọn Phường/Xã');
}

function setSelectByText(selectEl, text) {
    const target = String(text || '').toLowerCase();
    for (let i = 0; i < selectEl.options.length; i++) {
        const opt = selectEl.options[i];
        if ((opt.textContent || '').toLowerCase() === target) {
            selectEl.selectedIndex = i;
            break;
        }
    }
}

function viewPatient(patientId) {
    if (!checkAuth()) return;
    openViewPatientModal(patientId);
}

function editPatient(patientId) {
    // Kiểm tra authentication trước khi chỉnh sửa bệnh nhân
    if (!checkAuth()) return;
    
    // Implement edit patient
    console.log('Edit patient:', patientId);
}

function viewMedicalRecords(patientId) {
    console.log('View medical records:', patientId);
}

// ===== View Patient Modal =====
async function openViewPatientModal(patientId) {
    const modalEl = document.getElementById('viewPatientModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);
    const loading = document.getElementById('view-patient-loading');
    const errorBox = document.getElementById('view-patient-error');
    const content = document.getElementById('view-patient-content');

    // Reset UI
    errorBox.classList.add('d-none');
    content.classList.add('d-none');
    loading.style.display = 'block';
    modal.show();

    try {
        const res = await axios.get(`/api/patients/${patientId}/`);
        const p = res.data;
        // Fill data
        window._currentViewPatientId = patientId;
        document.getElementById('vp-code').textContent = p.patient_code || '-';
        document.getElementById('vp-name').textContent = p.full_name || '-';
        document.getElementById('vp-gender').textContent = p.gender === 'M' ? 'Nam' : p.gender === 'F' ? 'Nữ' : 'Khác';
        document.getElementById('vp-dob').textContent = p.date_of_birth ? formatDate(p.date_of_birth) : '-';
        document.getElementById('vp-age').textContent = p.age ?? '-';
        document.getElementById('vp-phone').textContent = p.phone_number || '-';
        document.getElementById('vp-email').textContent = p.email || '-';
        document.getElementById('vp-citizen').textContent = p.citizen_id || '-';
        document.getElementById('vp-address').textContent = p.full_address || '-';
        document.getElementById('vp-blood').textContent = p.blood_type || '-';
        document.getElementById('vp-allergies').textContent = p.allergies || '-';
        document.getElementById('vp-chronic').textContent = p.chronic_diseases || '-';

        document.getElementById('vp-emg-name').textContent = p.emergency_contact_name || '-';
        document.getElementById('vp-emg-phone').textContent = p.emergency_contact_phone || '-';
        document.getElementById('vp-emg-rel').textContent = p.emergency_contact_relationship || '-';

        const insBadge = document.getElementById('vp-ins-status');
        insBadge.textContent = p.insurance_status || '-';
        insBadge.className = `badge ${String(p.insurance_status || '').includes('có hiệu lực') ? 'bg-success' : 'bg-secondary'}`;
        document.getElementById('vp-ins-number').textContent = p.insurance_number || '-';
        const range = p.insurance_valid_from || p.insurance_valid_to ? `${p.insurance_valid_from || '?'} → ${p.insurance_valid_to || '?'}` : '-';
        document.getElementById('vp-ins-range').textContent = range;
        document.getElementById('vp-ins-hosp').textContent = p.insurance_hospital_code || '-';

        // Prefill edit form
        document.getElementById('ve-full_name').value = p.full_name || '';
        document.getElementById('ve-date_of_birth').value = p.date_of_birth || '';
        document.getElementById('ve-gender').value = p.gender || 'M';
        document.getElementById('ve-phone_number').value = p.phone_number || '';
        document.getElementById('ve-email').value = p.email || '';
        // Fill province/ward select with current values
        await ensureEditGeoLoaded();
        // set province by label
        setSelectByText(document.getElementById('ve-province'), p.province || '');
        if (document.getElementById('ve-province').value) {
            await loadEditWardsByProvince(document.getElementById('ve-province').value);
            document.getElementById('ve-ward').disabled = false;
            setSelectByText(document.getElementById('ve-ward'), p.ward || '');
        }
        document.getElementById('ve-address').value = p.address || '';
        document.getElementById('ve-citizen_id').value = p.citizen_id || '';

        // Show content
        loading.style.display = 'none';
        content.classList.remove('d-none');
    } catch (error) {
        console.error('Load patient detail error:', error);
        loading.style.display = 'none';
        errorBox.classList.remove('d-none');
        if (error.response?.status === 401) {
            errorBox.textContent = 'Phiên đăng nhập đã hết hạn.';
        } else {
            errorBox.textContent = 'Không thể tải thông tin bệnh nhân.';
        }
    }
}

// Save changes from edit tab
document.addEventListener('click', async function(e) {
    if (e.target && e.target.id === 'vp-save-btn') {
        const tabForm = document.getElementById('vp-edit-form');
        const patientId = document.getElementById('vp-code').dataset?.pid || null;
        // Gom dữ liệu
        const payload = {
            full_name: document.getElementById('ve-full_name').value.trim(),
            date_of_birth: document.getElementById('ve-date_of_birth').value || null,
            gender: document.getElementById('ve-gender').value,
            phone_number: document.getElementById('ve-phone_number').value.trim(),
            email: document.getElementById('ve-email').value.trim() || null,
            province: document.getElementById('ve-province').value.trim(),
            district: 'Quận 5',
            ward: document.getElementById('ve-ward').value.trim(),
            address: document.getElementById('ve-address').value.trim(),
            citizen_id: document.getElementById('ve-citizen_id').value.trim(),
        };
        try {
            // partial update
            const id = window._currentViewPatientId;
            await axios.patch(`/api/patients/${id}/`, payload);
            showAlert('Cập nhật bệnh nhân thành công');
            // Refresh list
            loadPatients();
        } catch (error) {
            const msgs = [];
            const data = error.response?.data;
            if (data && typeof data === 'object') {
                Object.keys(data).forEach(k => {
                    const v = Array.isArray(data[k]) ? data[k].join(', ') : data[k];
                    msgs.push(String(v));
                });
            }
            showFloatingErrors(msgs.slice(0,3).length ? msgs.slice(0,3) : ['Không thể cập nhật.']);
        }
    }
});

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

// ===== Floating errors (top-right) =====
function showFloatingErrors(messages) {
    const containerId = 'hh-floating-toasts';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.style.position = 'fixed';
        container.style.top = '1rem';
        container.style.right = '1rem';
        container.style.zIndex = '1056';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'alert alert-danger shadow';
    toast.style.minWidth = '320px';
    toast.innerHTML = `
        <div class="fw-semibold mb-1">Không thể lưu. Vui lòng kiểm tra:</div>
        <ul class="mb-0 ps-3">${messages.map(m => `<li>${m}</li>`).join('')}</ul>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('fade');
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, 5000);
}

function humanizeField(field) {
    const map = {
        full_name: 'Họ và tên',
        date_of_birth: 'Ngày sinh',
        gender: 'Giới tính',
        phone_number: 'Số điện thoại',
        email: 'Email',
        address: 'Địa chỉ',
        ward: 'Phường/Xã',
        district: 'Quận/Huyện',
        province: 'Tỉnh/TP',
        citizen_id: 'CCCD/CMND',
        emergency_contact_name: 'Tên người liên hệ',
        emergency_contact_phone: 'SĐT người liên hệ',
        emergency_contact_relationship: 'Mối quan hệ',
        insurance_number: 'Số thẻ BHYT',
        insurance_valid_from: 'BHYT hiệu lực từ',
        insurance_valid_to: 'BHYT hiệu lực đến'
    };
    return map[field] || field;
}