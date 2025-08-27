let currentPage = 1;
let totalPages = 1;



document.addEventListener('DOMContentLoaded', function() {
    // Đợi một chút để đảm bảo modal DOM được render
    setTimeout(() => {
        initEmergencyContactToggle();
        setupSaveButtonLogic();
    }, 100);
    
    // Listen for modal open event
    const addModal = document.getElementById('addPatientModal');
    if (addModal) {
        addModal.addEventListener('shown.bs.modal', function() {
            initEmergencyContactToggle();
            setupSaveButtonLogic();
        });
    }
    
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

// Khởi tạo toggle Liên hệ khẩn cấp - hoạt động độc lập
function initEmergencyContactToggle() {
    const toggle = document.getElementById('enable_emergency_contact');
    if (!toggle) return;
    
    const inputs = [
        document.getElementById('emergency_contact_name'),
        document.getElementById('emergency_contact_phone'),
        document.getElementById('emergency_contact_relationship')
    ].filter(Boolean);
    
    const setInputEnabled = (inputEl, enabled) => {
        if (!inputEl) return;
        if (enabled) {
            inputEl.disabled = false;
            inputEl.removeAttribute('disabled');
        } else {
            inputEl.disabled = true;
            inputEl.setAttribute('disabled', 'disabled');
        }
    };
    
    const syncEmergencyInputs = (enabled) => {
        inputs.forEach(input => {
            setInputEnabled(input, enabled);
            if (!enabled) input.value = '';
        });
        // Trigger save button reevaluation if available
        if (window.reevaluateSaveButton) {
            setTimeout(window.reevaluateSaveButton, 0);
        }
    };
    
    // Set initial state
    syncEmergencyInputs(toggle.checked);
    
    // Listen for changes
    toggle.addEventListener('change', function() {
        syncEmergencyInputs(this.checked);
    });
}

// Setup save button logic
function setupSaveButtonLogic() {
    const saveBtn = document.getElementById('save-patient-btn');
    if (!saveBtn) return;
    
    const requiredFields = ['#full_name','#date_of_birth','#gender','#phone_number','#citizen_id','#province','#ward','#address'];
    
    window.reevaluateSaveButton = () => {
        const allRequiredFilled = requiredFields.every(selector => {
            const el = document.querySelector(selector);
            return el && el.value && el.value.toString().trim().length > 0;
        });
        
        const wardEl = document.getElementById('ward');
        const wardOk = wardEl && !wardEl.disabled && wardEl.value;
        
        saveBtn.disabled = !(allRequiredFilled && wardOk);
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
    
    // Insurance checkbox: enable/disable input and clear when unchecked
    const insuranceCheckbox = document.getElementById('has_insurance');
    if (insuranceCheckbox) {
        insuranceCheckbox.addEventListener('change', function() {
            const numberInput = document.getElementById('insurance_number');
            if (numberInput) {
                if (this.checked) {
                    numberInput.disabled = false;
                    numberInput.removeAttribute('disabled');
                } else {
                    numberInput.disabled = true;
                    numberInput.setAttribute('disabled', 'disabled');
                    numberInput.value = '';
                }
            }
            // reevaluate after toggle
            if (window.reevaluateSaveButton) setTimeout(window.reevaluateSaveButton, 0);
        });
    }

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
            showFloatingNotification('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning', 'fas fa-exclamation-triangle', 6000);
            redirectToLogin();
        } else if (error.code === 'ERR_NETWORK') {
            showAlert('Mất kết nối tạm thời. Đang thử lại...', 'warning');
            setTimeout(loadPatients, 1000);
        } else {
            showFloatingNotification('Lỗi khi tải danh sách bệnh nhân', 'danger', 'fas fa-times-circle', 6000);
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
                <button class="btn btn-sm btn-outline-primary me-1 p-0 d-inline-flex align-items-center justify-content-center" onclick="viewPatient('${patient.id}')" title="Xem thông tin" style="width: 32px; height: 32px;">
                    <i class="fas fa-eye fa-fw align-middle"></i>
                </button>
                <button class="btn btn-sm btn-outline-info me-1 p-0 d-inline-flex align-items-center justify-content-center" onclick="viewMedicalRecords('${patient.id}')" title="Hồ sơ y tế" style="width: 32px; height: 32px;">
                    <i class="fas fa-file-medical fa-fw align-middle"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger p-0 d-inline-flex align-items-center justify-content-center" onclick="deletePatient('${patient.id}')" title="Xóa bệnh nhân" style="width: 32px; height: 32px;">
                    <i class="fas fa-trash fa-fw align-middle"></i>
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
    // Gửi tên hiển thị thay vì mã code cho province/ward (đã bỏ district)
    if (provinceSel?.selectedIndex > 0) {
        patientData.province = provinceSel.options[provinceSel.selectedIndex].textContent.trim();
    }
    if (wardSel?.selectedIndex > 0) {
        patientData.ward = wardSel.options[wardSel.selectedIndex].textContent.trim();
    }
    // Không gửi hoặc gán mặc định bất kỳ giá trị Quận/Huyện nào
    
    // Convert checkbox to boolean
    patientData.has_insurance = document.getElementById('has_insurance').checked;

    // Nếu không bật liên hệ khẩn cấp, remove các field rỗng khỏi payload
    const emergencyEnabled = document.getElementById('enable_emergency_contact')?.checked;
    if (!emergencyEnabled) {
        delete patientData.emergency_contact_name;
        delete patientData.emergency_contact_phone;
        delete patientData.emergency_contact_relationship;
    }
    
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
        
        showFloatingNotification('Thêm bệnh nhân thành công!', 'success', 'fas fa-check-circle', 4000);
        loadPatients();
        
    } catch (error) {
        console.error('Error adding patient:', error);
        if (error.response?.status === 401) {
            showFloatingNotification('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning', 'fas fa-exclamation-triangle', 6000);
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
        if (window.reevaluateSaveButton) window.reevaluateSaveButton();
    });

    wardSelect.addEventListener('change', function() {
        const wardCode = this.value;
        addressInput.disabled = !wardCode;
        if (wardCode) {
            addressInput.focus();
        }
        // trigger reevaluate save button
        if (window.reevaluateSaveButton) window.reevaluateSaveButton();
    });
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
    
    // Setup province change event for edit form
    const editProvinceSelect = document.getElementById('ve-province');
    if (editProvinceSelect && !editProvinceSelect.dataset.eventBound) {
        editProvinceSelect.addEventListener('change', async function() {
            const provinceCode = this.value;
            const wardSelect = document.getElementById('ve-ward');
            const addressInput = document.getElementById('ve-address');
            
            // Reset lower level
            wardSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';
            wardSelect.value = '';
            wardSelect.disabled = true;
            addressInput.value = '';
            addressInput.disabled = true;

            if (provinceCode) {
                await loadEditWardsByProvince(provinceCode);
                wardSelect.disabled = false;
            }
        });
        editProvinceSelect.dataset.eventBound = '1';
    }
    
    // Setup ward change event for edit form
    const editWardSelect = document.getElementById('ve-ward');
    if (editWardSelect && !editWardSelect.dataset.eventBound) {
        editWardSelect.addEventListener('change', function() {
            const wardCode = this.value;
            const addressInput = document.getElementById('ve-address');
            addressInput.disabled = !wardCode;
            if (wardCode) {
                addressInput.focus();
            }
        });
        editWardSelect.dataset.eventBound = '1';
    }
}

async function loadEditWardsByProvince(provinceCode) {
    if (vnAdminCache.wardsByDistrict[provinceCode]) {
        renderOptions(document.getElementById('ve-ward'), vnAdminCache.wardsByDistrict[provinceCode], 'Chọn Phường/Xã');
        return;
    }
    
    try {
        const url = `/api/geo/provinces/${provinceCode}/`;
        const res = await axios.get(url);
        const wards = (res.data?.wards || []).map(w => ({ value: w.code, label: w.name, extra: w.name }));
        vnAdminCache.wardsByDistrict[provinceCode] = wards;
        renderOptions(document.getElementById('ve-ward'), wards, 'Chọn Phường/Xã');
    } catch (error) {
        console.error('Error loading wards for province:', provinceCode, error);
        // Fallback: create empty options
        renderOptions(document.getElementById('ve-ward'), [], 'Không thể tải xã/phường');
    }
}

// Setup edit emergency contact toggle
function setupEditEmergencyToggle() {
    const toggle = document.getElementById('ve-enable_emergency_contact');
    if (!toggle || toggle.dataset.eventBound) return;
    
    const inputs = [
        document.getElementById('ve-emergency_contact_name'),
        document.getElementById('ve-emergency_contact_phone'),
        document.getElementById('ve-emergency_contact_relationship')
    ].filter(Boolean);
    
    const setInputEnabled = (inputEl, enabled) => {
        if (!inputEl) return;
        if (enabled) {
            inputEl.disabled = false;
            inputEl.removeAttribute('disabled');
        } else {
            inputEl.disabled = true;
            inputEl.setAttribute('disabled', 'disabled');
        }
    };
    
    const syncInputs = (enabled) => {
        inputs.forEach(input => {
            setInputEnabled(input, enabled);
            if (!enabled) input.value = '';
        });
    };
    
    // Set initial state
    syncInputs(toggle.checked);
    
    // Listen for changes
    toggle.addEventListener('change', function() {
        syncInputs(this.checked);
        // Trigger save button state evaluation
        setTimeout(evaluateSaveButtonState, 100);
    });
    
    toggle.dataset.eventBound = '1';
}

// Setup edit insurance toggle
function setupEditInsuranceToggle() {
    const toggle = document.getElementById('ve-has_insurance');
    if (!toggle || toggle.dataset.eventBound) return;
    
    const input = document.getElementById('ve-insurance_number');
    if (!input) return;
    
    const setInputEnabled = (inputEl, enabled) => {
        if (!inputEl) return;
        if (enabled) {
            inputEl.disabled = false;
            inputEl.removeAttribute('disabled');
        } else {
            inputEl.disabled = true;
            inputEl.setAttribute('disabled', 'disabled');
        }
    };
    
    const syncInputs = (enabled) => {
        setInputEnabled(input, enabled);
        if (!enabled) input.value = '';
    };
    
    // Set initial state
    syncInputs(toggle.checked);
    
    // Listen for changes
    toggle.addEventListener('change', function() {
        syncInputs(this.checked);
        // Trigger save button state evaluation
        setTimeout(evaluateSaveButtonState, 100);
    });
    
    toggle.dataset.eventBound = '1';
}

// Setup tab switching to show/hide save button
function setupEditTabToggle() {
    const editTab = document.getElementById('vp-edit-tab');
    const viewTab = document.getElementById('vp-view-tab');
    const saveBtn = document.getElementById('vp-save-btn');
    
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
    const saveBtn = document.getElementById('vp-save-btn');
    if (!saveBtn) return;
    
    // Hide save button by default since view tab is active
    saveBtn.style.display = 'none';
    
    // Get all form inputs to monitor
    const form = document.getElementById('vp-edit-form');
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
    const saveBtn = document.getElementById('vp-save-btn');
    if (!saveBtn) return;
    
    // Check if we're currently on the edit tab
    const editTab = document.getElementById('vp-edit-tab');
    const isEditTabActive = editTab && editTab.classList.contains('active');
    
    // If not on edit tab, hide the button
    if (!isEditTabActive) {
        saveBtn.style.display = 'none';
        return;
    }
    
    const original = window._currentPatientOriginal || {};
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
        full_name: document.getElementById('ve-full_name')?.value?.trim() || '',
        date_of_birth: document.getElementById('ve-date_of_birth')?.value || null,
        gender: document.getElementById('ve-gender')?.value || '',
        phone_number: document.getElementById('ve-phone_number')?.value?.trim() || '',
        email: (document.getElementById('ve-email')?.value?.trim() || null),
        province: document.getElementById('ve-province')?.value?.trim() || '',
        ward: document.getElementById('ve-ward')?.value?.trim() || '',
        address: document.getElementById('ve-address')?.value?.trim() || '',
        citizen_id: document.getElementById('ve-citizen_id')?.value?.trim() || '',
        blood_type: document.getElementById('ve-blood_type')?.value || null,
        allergies: (document.getElementById('ve-allergies')?.value?.trim() || null),
        chronic_diseases: (document.getElementById('ve-chronic_diseases')?.value?.trim() || null),
        has_insurance: document.getElementById('ve-has_insurance')?.checked || false,
        insurance_number: document.getElementById('ve-insurance_number')?.value?.trim() || null,
        emergency_contact_name: document.getElementById('ve-emergency_contact_name')?.value?.trim() || null,
        emergency_contact_phone: document.getElementById('ve-emergency_contact_phone')?.value?.trim() || null,
        emergency_contact_relationship: document.getElementById('ve-emergency_contact_relationship')?.value?.trim() || null,
    };
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

async function deletePatient(patientId) {
    // Kiểm tra authentication trước khi xóa bệnh nhân
    if (!checkAuth()) return;
    
    try {
        // Get patient info first to show in confirmation modal
        const response = await axios.get(`/api/patients/${patientId}/`);
        const patient = response.data;
        
        // Populate confirmation modal with patient info
        document.getElementById('delete-patient-code').textContent = patient.patient_code || '-';
        document.getElementById('delete-patient-name').textContent = patient.full_name || '-';
        document.getElementById('delete-patient-phone').textContent = patient.phone_number || '-';
        
        // Show confirmation modal
        const deleteModal = new bootstrap.Modal(document.getElementById('deletePatientModal'));
        deleteModal.show();
        
        // Store patient ID for deletion
        window._deletePatientId = patientId;
        
    } catch (error) {
        console.error('Error loading patient for deletion:', error);
        showAlert('Không thể tải thông tin bệnh nhân', 'danger');
    }
}

async function performDeletePatient(patientId) {
    let loadingToast = null;
    
    try {
        // Show loading notification in top-right corner
        loadingToast = showFloatingNotification(
            'Đang xóa bệnh nhân...', 
            'info', 
            'fas fa-spinner fa-spin', 
            0 // Don't auto-remove
        );
        
        await axios.delete(`/api/patients/${patientId}/`);
        
        // Remove loading notification
        if (loadingToast && loadingToast.parentNode) {
            loadingToast.remove();
        }
        
        // Show success notification
        showFloatingNotification(
            'Xóa bệnh nhân thành công!', 
            'success', 
            'fas fa-check-circle', 
            4000
        );
        
        // Refresh the patient list
        loadPatients();
        
    } catch (error) {
        console.error('Error deleting patient:', error);
        
        // Remove loading notification on error
        if (loadingToast && loadingToast.parentNode) {
            loadingToast.remove();
        }
        
        // Show error notification in top-right corner
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
                'Bạn không có quyền xóa bệnh nhân này', 
                'danger', 
                'fas fa-ban', 
                6000
            );
        } else if (error.response?.status === 404) {
            showFloatingNotification(
                'Bệnh nhân không tồn tại hoặc đã bị xóa', 
                'warning', 
                'fas fa-user-times', 
                5000
            );
            loadPatients(); // Refresh to remove from list
        } else {
            showFloatingNotification(
                'Lỗi khi xóa bệnh nhân. Vui lòng thử lại.', 
                'danger', 
                'fas fa-times-circle', 
                6000
            );
        }
    }
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
        
        // Set province first
        const provinceSelect = document.getElementById('ve-province');
        const wardSelect = document.getElementById('ve-ward');
        const addressInput = document.getElementById('ve-address');
        
        // Find and set province by name
        const provinceOption = Array.from(provinceSelect.options).find(opt => 
            opt.text === p.province || opt.value === p.province
        );
        if (provinceOption) {
            provinceSelect.value = provinceOption.value;
            
            // Load wards for this province
            await loadEditWardsByProvince(provinceOption.value);
            wardSelect.disabled = false;
            
            // Find and set ward by name
            const wardOption = Array.from(wardSelect.options).find(opt => 
                opt.text === p.ward || opt.value === p.ward
            );
            if (wardOption) {
                wardSelect.value = wardOption.value;
                addressInput.disabled = false;
            }
        }
        
        document.getElementById('ve-address').value = p.address || '';
        document.getElementById('ve-citizen_id').value = p.citizen_id || '';
        
        // Fill additional fields
        document.getElementById('ve-blood_type').value = p.blood_type || '';
        document.getElementById('ve-allergies').value = p.allergies || '';
        document.getElementById('ve-chronic_diseases').value = p.chronic_diseases || '';
        
        // Fill emergency contact fields
        const hasEmergencyContact = p.emergency_contact_name || p.emergency_contact_phone || p.emergency_contact_relationship;
        document.getElementById('ve-enable_emergency_contact').checked = !!hasEmergencyContact;
        document.getElementById('ve-emergency_contact_name').value = p.emergency_contact_name || '';
        document.getElementById('ve-emergency_contact_phone').value = p.emergency_contact_phone || '';
        document.getElementById('ve-emergency_contact_relationship').value = p.emergency_contact_relationship || '';
        
        // Fill insurance fields
        document.getElementById('ve-has_insurance').checked = !!p.has_insurance;
        document.getElementById('ve-insurance_number').value = p.insurance_number || '';
        
        // Setup toggles and tabs
        setupEditEmergencyToggle();
        setupEditInsuranceToggle();
        setupEditTabToggle();
        
        // Ensure address field is enabled if ward is selected
        if (wardSelect.value) {
            addressInput.disabled = false;
        }
        
        // Setup save button state monitoring
        setupSaveButtonMonitoring();

        // Store original data for diff on save
        window._currentPatientOriginal = {
            full_name: p.full_name || '',
            date_of_birth: p.date_of_birth || null,
            gender: p.gender || '',
            phone_number: p.phone_number || '',
            email: p.email || null,
            province: p.province || '',
            ward: p.ward || '',
            address: p.address || '',
            citizen_id: p.citizen_id || '',
            blood_type: p.blood_type || null,
            allergies: p.allergies || null,
            chronic_diseases: p.chronic_diseases || null,
            has_insurance: !!p.has_insurance,
            insurance_number: p.insurance_number || null,
            emergency_contact_name: p.emergency_contact_name || null,
            emergency_contact_phone: p.emergency_contact_phone || null,
            emergency_contact_relationship: p.emergency_contact_relationship || null,
        };

        // Show content
        loading.style.display = 'none';
        content.classList.remove('d-none');

        // Fill audit info in view tab
        const fmt = (s) => s ? new Date(s).toLocaleString() : '-';
        document.getElementById('vp-created-by').textContent = p.created_by_name || '-';
        document.getElementById('vp-updated-by').textContent = p.updated_by_name || p.created_by_name || '-';
        document.getElementById('vp-created-at').textContent = fmt(p.created_at);
        document.getElementById('vp-updated-at').textContent = fmt(p.updated_at);
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

// Handle delete confirmation
document.addEventListener('click', async function(e) {
    if (e.target && e.target.id === 'confirm-delete-btn') {
        const patientId = window._deletePatientId;
        if (patientId) {
            // Hide the modal first
            const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deletePatientModal'));
            deleteModal.hide();
            
            // Perform deletion
            await performDeletePatient(patientId);
            
            // Clear stored ID
            window._deletePatientId = null;
        }
    }
});

// Save changes from edit tab
document.addEventListener('click', async function(e) {
    if (e.target && e.target.id === 'vp-save-btn') {
        const tabForm = document.getElementById('vp-edit-form');
        const patientId = document.getElementById('vp-code').dataset?.pid || null;
        // Build diff-only payload
        const current = getCurrentFormValues();

        // Emergency contact fields
        const emergencyEnabled = document.getElementById('ve-enable_emergency_contact')?.checked;
        if (emergencyEnabled) {
            current.emergency_contact_name = document.getElementById('ve-emergency_contact_name').value.trim() || null;
            current.emergency_contact_phone = document.getElementById('ve-emergency_contact_phone').value.trim() || null;
            current.emergency_contact_relationship = document.getElementById('ve-emergency_contact_relationship').value.trim() || null;
        } else {
            current.emergency_contact_name = null;
            current.emergency_contact_phone = null;
            current.emergency_contact_relationship = null;
        }

        // Insurance fields
        current.has_insurance = document.getElementById('ve-has_insurance')?.checked || false;
        if (current.has_insurance) {
            current.insurance_number = document.getElementById('ve-insurance_number').value.trim() || null;
        } else {
            current.insurance_number = null;
        }

        const original = window._currentPatientOriginal || {};
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
            // partial update
            const id = window._currentViewPatientId;
            await axios.patch(`/api/patients/${id}/`, payload);
            // Close modal if open
            const modalEl = document.getElementById('viewPatientModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
            // Success notification (top-right)
            showFloatingNotification('Cập nhật bệnh nhân thành công!', 'success', 'fas fa-check-circle', 4000);
            // Refresh list
            loadPatients();
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

// ===== Floating notifications (top-right) =====
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

// ===== Floating errors (top-right) =====
function showFloatingErrors(messages) {
    const errorMessage = `
        <div class="fw-semibold mb-1">Không thể lưu. Vui lòng kiểm tra:</div>
        <ul class="mb-0 ps-3">${messages.map(m => `<li>${m}</li>`).join('')}</ul>
    `;
    showFloatingNotification(errorMessage, 'danger', 'fas fa-exclamation-triangle', 8000);
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
        // district removed
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

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN');
}