/**
 * Doctor Prescriptions Management
 * UI và logic cho bác sĩ quản lý đơn thuốc
 */

// Global variables
let currentPage = 1;
let totalPages = 1;
let prescriptions = [];
let allPrescriptions = []; // Store all prescriptions for frontend filtering
let drugs = [];
let patients = [];

// Initialize when DOM is ready - Following prescriptions.js pattern
document.addEventListener('DOMContentLoaded', function(){
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initDoctorPrescriptions();
    } else {
        window.addEventListener('axiosInterceptorsReady', () => {
            initDoctorPrescriptions();
        }, { once: true });
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initDoctorPrescriptions();
            }
        }, 1500);
    }
});

function initDoctorPrescriptions(){
    if (!HospitalApp.checkAuth()) {
        location.href = '/login/';
        return;
    }
    
    // Check if user is doctor
    if (!isDoctorUser()) {
        showDoctorAccessDenied();
        return;
    }

    setupDoctorUI();
    bindDoctorEvents();
    loadPrescriptions();
    loadInitialData();
}

function bindDoctorEvents(){
    const form = document.getElementById('filter-form');
    if (form) form.addEventListener('submit', function(e){ e.preventDefault(); currentPage=1; loadPrescriptions(); });
    
    const addForm = document.getElementById('create-prescription-form');
    if (addForm) addForm.addEventListener('submit', handleAddPrescription);
    
    const addDrugBtn = document.getElementById('add-drug-btn');
    if (addDrugBtn) addDrugBtn.addEventListener('click', showDrugSelectionModal);
    
    const myPrescriptionsOnly = document.getElementById('my-prescriptions-only');
    if (myPrescriptionsOnly) myPrescriptionsOnly.addEventListener('change', function(){
        // Re-render with current data to apply frontend filtering
        if (allPrescriptions) {
            renderPrescriptions(allPrescriptions);
        }
    });
    
    // Modal event listeners
    const createModal = document.getElementById('createPrescriptionModal');
    if (createModal) {
        createModal.addEventListener('show.bs.modal', async function() {
            if (patients.length === 0) {
                await loadPatients();
            }
            if (drugs.length === 0) {
                await loadDrugs();
            }
        });
    }
}

/**
 * Check if current user is a doctor
 */
function isDoctorUser() {
    try {
        // First check if we have currentUser from main.js
        if (!currentUser) {
            // Try to get user data from localStorage
            const userData = localStorage.getItem('user_data');
            if (userData) {
                try {
                    const parsed = JSON.parse(userData);
                    currentUser = parsed;
                } catch (e) {
                    console.error('Failed to parse user_data from localStorage:', e);
                    return false;
                }
            } else {
                return false;
            }
        }
        
        // Check user_type
        if (currentUser.user_type === 'DOCTOR') {
            return true;
        }

        // Check roles array
        const roles = Array.isArray(currentUser.roles) ? currentUser.roles : [];
        const isDoctor = roles.includes('Doctor') || roles.includes('DOCTOR');

        return isDoctor;
    } catch (e) {
        console.error('Error checking doctor role:', e);
        return false;
    }
}

/**
 * Show access denied message for non-doctors
 */
function showDoctorAccessDenied() {
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.innerHTML = `
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card mt-5">
                        <div class="card-body text-center">
                            <i class="fas fa-user-md fa-3x text-muted mb-3"></i>
                            <h4>Chỉ dành cho Bác sĩ</h4>
                            <p class="text-muted">Bạn cần có quyền Bác sĩ để truy cập trang này.</p>
                            <a href="/dashboard/" class="btn btn-primary">
                                <i class="fas fa-home"></i> Về trang chủ
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}



/**
 * Setup UI specifically for doctors
 */
function setupDoctorUI() {
    // Update page title
    document.title = 'Quản lý Đơn thuốc - Bác sĩ';
    
    // Update page header
    const pageHeader = document.querySelector('h2');
    if (pageHeader) {
        pageHeader.innerHTML = `
            <i class="fas fa-prescription-bottle-alt"></i> 
            Quản lý Đơn thuốc 
            <small class="text-muted">(Bác sĩ)</small>
        `;
    }
    
    // Show doctor-specific features
    showDoctorFeatures();

    const header = document.querySelector('.card-header');
    if (header && !document.getElementById('my-appointments-only')) {
        document.getElementById('my-prescriptions-only').addEventListener('change', () => {
            // Reuse prescriptions list as proxy: filter by current doctor name
            if (allPrescriptions) renderPrescriptions(allPrescriptions);
        });
    }
}

/**
 * Show features specific to doctors
 */
function showDoctorFeatures() {
    // Show "Kê đơn thuốc mới" button
    const addButton = document.querySelector('[data-bs-target="#addPrescriptionModal"]');
    if (addButton) {
        addButton.style.display = 'block';
        addButton.innerHTML = `
            <i class="fas fa-plus"></i> Kê đơn thuốc mới
        `;
    }
    
    // Add doctor-specific filter (chỉ hiển thị đơn thuốc của mình)
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const doctorFilterContainer = document.createElement('div');
        doctorFilterContainer.className = 'col-md-12 mt-2';
        doctorFilterContainer.innerHTML = `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="my-prescriptions-only" checked>
                <label class="form-check-label" for="my-prescriptions-only">
                    Chỉ hiển thị đơn thuốc của tôi
                </label>
            </div>
        `;
        filterForm.appendChild(doctorFilterContainer);
    }
}

/**
 * Load initial data needed for the interface
 */
async function loadInitialData() {
    try {
        await loadPatients();
        await loadDrugs();
    } catch (error) {
        console.error('❌ Error loading initial data:', error);
    }
}

async function loadPatients() {
    try {
        const response = await axios.get('/api/patients/');
        patients = response.data.results || response.data || [];
        

        
        // Ensure patients is an array
        if (!Array.isArray(patients)) {
            console.error('❌ Patients data is not an array:', patients);
            patients = [];
        }

        populatePatientSelect();
    } catch (error) {
        console.error('❌ Error loading patients:', error);
        patients = []; // Reset to empty array on error
        showAlert('Không thể tải danh sách bệnh nhân', 'error');
        
        const patientSelect = document.getElementById('patient-select');
        if (patientSelect) {
            patientSelect.innerHTML = '<option value="">Không thể tải danh sách bệnh nhân</option>';
        }
    }
}

async function loadDrugs() {
    try {
        // Prefer active drugs from API
        const response = await axios.get('/api/drugs/?is_active=true');
        const raw = response.data.results || response.data || [];
        // Keep only drugs with valid id and in-stock if stock info available
        drugs = (raw || []).filter(d => d && d.id && (typeof d.current_stock !== 'number' || d.current_stock > 0));
    } catch (error) {
        console.error('❌ Error loading drugs:', error);
        drugs = [];
    }
}

/**
 * Populate patient select dropdown
 */
function populatePatientSelect() {
    const patientSelect = document.getElementById('patient-select');
    if (!patientSelect) {
        console.error('❌ Patient select element not found!');
        return;
    }

    // Check if patients array is defined
    if (!patients || !Array.isArray(patients)) {
        console.error('❌ Patients array is not defined or not an array:', patients);
        patientSelect.innerHTML = '<option value="">Lỗi tải danh sách bệnh nhân</option>';
        return;
    }
    
    patientSelect.innerHTML = '<option value="">Chọn bệnh nhân</option>';
    
    if (patients.length === 0) {
        patientSelect.innerHTML += '<option value="" disabled>Không có bệnh nhân nào</option>';
        return;
    }
    
    patients.forEach(patient => {
        const option = document.createElement('option');
        option.value = patient.id;
        // Use phone_number as primary identifier
        const identifier = patient.phone_number || patient.citizen_id || patient.patient_code || 'N/A';
        option.textContent = `${patient.full_name} - ${identifier}`;
        patientSelect.appendChild(option);
    });
}

/**
 * Handle search form submission
 */
async function handleSearch(event) {
    event.preventDefault();
    currentPage = 1;
    await loadPrescriptions();
}

function buildPrescriptionParams(){
    const params = new URLSearchParams({ page: currentPage, page_size: 10 });
    
    const searchQuery = document.getElementById('search-query')?.value || '';
    const status = document.getElementById('status-filter')?.value || '';
    const type = document.getElementById('type-filter')?.value || '';
    const dateFrom = document.getElementById('date-from')?.value || '';
    const dateTo = document.getElementById('date-to')?.value || '';
    const myPrescriptionsOnly = document.getElementById('my-prescriptions-only')?.checked;
    
    if (searchQuery) params.append('search', searchQuery);
    if (status) params.append('status', status);
    if (type) params.append('prescription_type', type);
    if (dateFrom) params.append('prescription_date__gte', dateFrom);
    if (dateTo) params.append('prescription_date__lte', dateTo);
    
    // Note: Doctor filtering is temporarily disabled due to API parameter mismatch
    // The API expects DoctorProfile ID but we only have User ID
    // For now, "My prescriptions only" will be handled in frontend filtering
    
    return params;
}

async function loadPrescriptions(page = 1){
    try {
        currentPage = page;
        
        // Show loading indicator
        const tbody = document.getElementById('prescriptions-table-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Đang tải...</span>
                        </div>
                        <p class="text-muted mt-2">Đang tải danh sách đơn thuốc...</p>
                    </td>
                </tr>
            `;
        }
        
        const params = buildPrescriptionParams();
        const response = await axios.get(`/api/prescriptions/?${params}`);
        const data = response.data || {};
        
        // Store all prescriptions for frontend filtering
        allPrescriptions = data.results || [];
        
        renderPrescriptions(data.results || []);
        updatePagination(data);
        
    } catch (error) {
        console.error('❌ Error loading prescriptions:', error);
        renderPrescriptions([]);
        updateTotalCount(0);
        
        if (error.response?.status === 401) {
            showAlert('Phiên đăng nhập đã hết hạn', 'warning');
            location.href = '/login/';
        } else {
            showAlert('Lỗi tải danh sách đơn thuốc', 'error');
        }
    }
}

/**
 * Render prescriptions table
 */
function renderPrescriptions(prescriptionsList) {
    const tbody = document.getElementById('prescriptions-table-body');
    if (!tbody) {
        console.error('❌ Table body not found');
        return;
    }
    
    if (!prescriptionsList || prescriptionsList.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="fas fa-prescription-bottle-alt fa-2x text-muted mb-2"></i>
                    <p class="text-muted">Không có đơn thuốc nào</p>
                </td>
            </tr>
        `;
        updateTotalCount(0);
        return;
    }
    
    // Apply frontend filtering for "My prescriptions only"
    const myPrescriptionsOnly = document.getElementById('my-prescriptions-only')?.checked;
    let filteredPrescriptions = prescriptionsList;
    
    if (myPrescriptionsOnly && currentUser) {
        const currentUserName = currentUser.full_name || currentUser.username || '';
        filteredPrescriptions = prescriptionsList.filter(prescription => {
            const doctorName = prescription.doctor_name || '';
            return doctorName.toLowerCase().includes(currentUserName.toLowerCase());
        });
        

    }
    
    if (filteredPrescriptions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-4">
                    <i class="fas fa-filter fa-2x text-muted mb-2"></i>
                    <p class="text-muted">${myPrescriptionsOnly ? 'Không tìm thấy đơn thuốc của bạn' : 'Không có đơn thuốc nào'}</p>
                </td>
            </tr>
        `;
        updateTotalCount(0);
        return;
    }
    
    prescriptions = filteredPrescriptions;
    tbody.innerHTML = filteredPrescriptions.map(prescription => createPrescriptionRow(prescription)).join('');
    // Cập nhật tổng theo danh sách sau khi lọc
    updateTotalCount(filteredPrescriptions.length);
}

/**
 * Create prescription table row
 */
function createPrescriptionRow(prescription) {
    const patientName = prescription.patient_name || 'N/A';
    const doctorName = prescription.doctor_name || 'N/A';
    
    const statusBadge = getStatusBadge(prescription.status);
    const typeBadge = getTypeBadge(prescription.prescription_type);
    
    return `
        <tr>
            <td>
                <strong>${escapeHtml(prescription.prescription_number || 'N/A')}</strong>
            </td>
            <td>${escapeHtml(patientName)}</td>
            <td>${escapeHtml(doctorName)}</td>
            <td>
                <strong>${formatDate(prescription.prescription_date)}</strong><br>
                <small class="text-muted">Hiệu lực đến: ${formatDate(prescription.valid_until)}</small>
            </td>
            <td>${typeBadge}</td>
            <td>${statusBadge}</td>
            <td>
                <strong>${formatCurrency(prescription.total_amount || 0)}</strong><br>
                <small class="text-muted">BN trả: ${formatCurrency(prescription.patient_payment_amount || 0)}</small>
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-outline-info" onclick="viewPrescription('${prescription.id}')" title="Xem chi tiết">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="printPrescription('${prescription.id}')" title="In đơn">
                        <i class="fas fa-print"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deletePrescription('${prescription.id}')" title="Xóa">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
}

/**
 * Get status badge HTML
 */
function getStatusBadge(status) {
    const badges = {
        'DRAFT': '<span class="badge bg-secondary">Nháp</span>',
        'ACTIVE': '<span class="badge bg-success">Có hiệu lực</span>',
        'PARTIALLY_DISPENSED': '<span class="badge bg-warning">Cấp thuốc một phần</span>',
        'FULLY_DISPENSED': '<span class="badge bg-info">Đã cấp thuốc đầy đủ</span>',
        'CANCELLED': '<span class="badge bg-danger">Đã hủy</span>',
        'EXPIRED': '<span class="badge bg-dark">Hết hạn</span>'
    };
    return badges[status] || `<span class="badge bg-light text-dark">${status}</span>`;
}

/**
 * Get type badge HTML
 */
function getTypeBadge(type) {
    const badges = {
        'OUTPATIENT': '<span class="badge bg-primary">Ngoại trú</span>',
        'INPATIENT': '<span class="badge bg-info">Nội trú</span>',
        'EMERGENCY': '<span class="badge bg-danger">Cấp cứu</span>',
        'DISCHARGE': '<span class="badge bg-success">Ra viện</span>'
    };
    return badges[type] || `<span class="badge bg-light text-dark">${type}</span>`;
}

/**
 * Handle add prescription form submission
 */
async function handleAddPrescription(event) {
    event.preventDefault();

    try {
        const formData = new FormData(event.target);
        
        // Validate required fields
        const patient = formData.get('patient');
        if (!patient) {
            showAlert('Vui lòng chọn bệnh nhân', 'warning');
            return;
        }
        
        // Get current doctor profile ID
        let doctorId = null;
        if (currentUser && currentUser.doctor_profile_id) {
            doctorId = currentUser.doctor_profile_id;
        } else if (currentUser && currentUser.id) {
            // Fetch doctor profile by current user id
            try {
                const resp = await axios.get(`/api/doctors/?search=${encodeURIComponent(currentUser.full_name || currentUser.username || '')}`);
                const list = resp.data.results || resp.data || [];
                if (Array.isArray(list) && list.length) {
                    doctorId = list[0].id;
                }
            } catch (e) { /* noop */ }
        }
        if (!doctorId) {
            showAlert('Không tìm thấy hồ sơ bác sĩ cho tài khoản hiện tại', 'error');
            return;
        }
        
        const now = new Date();
        const validFromIso = now.toISOString();
        const validUntil = new Date(now);
        validUntil.setMonth(validUntil.getMonth() + 3);
        const prescriptionData = {
            patient: patient,
            doctor: doctorId,
            prescription_type: formData.get('prescription_type') || 'OUTPATIENT',
            diagnosis: formData.get('diagnosis') || '',
            notes: formData.get('notes') || '',
            special_instructions: formData.get('special_instructions') || '',
            valid_from: validFromIso,
            valid_until: validUntil.toISOString(),
            items: []
        };
        
        // Get prescription items
        const itemRows = document.querySelectorAll('.prescription-item-row');
        
        let skippedEmptyRows = 0;
        itemRows.forEach((row, index) => {
            const drugSelect = row.querySelector('[name="drug"]');
            const quantityInput = row.querySelector('[name="quantity"]');
            const dosageInput = row.querySelector('[name="dosage"]');
            const frequencySelect = row.querySelector('[name="frequency"]');
            const routeSelect = row.querySelector('[name="route"]');
            const durationInput = row.querySelector('[name="duration"]');
            const instructionsInput = row.querySelector('[name="instructions"]');
            

            
            const drug = drugSelect?.value;
            const quantity = quantityInput?.value;
            const dosage_per_time = dosageInput?.value;
            const frequency = frequencySelect?.value;
            const route = routeSelect?.value;
            const duration = durationInput?.value;
            const instructions = instructionsInput?.value;
            
            // Backend expects Drug.id (UUID string). Do not cast to number.
            if (drug && quantity && frequency && route && instructions) {
                const item = {
                    drug: drug,
                    quantity: parseInt(quantity, 10),
                    dosage_per_time: dosage_per_time || '1 viên',
                    frequency: frequency,
                    route: route,
                    duration_days: parseInt(duration, 10) || 7,
                    instructions: instructions
                };
                
                prescriptionData.items.push(item);
            } else {
                skippedEmptyRows++;
            }
        });

        if (prescriptionData.items.length === 0) {
            showAlert('Vui lòng thêm ít nhất một loại thuốc', 'warning');
            return;
        }
        if (skippedEmptyRows > 0) {
            showAlert('Một số dòng thuốc thiếu thông tin đã bị bỏ qua', 'warning');
        }
        
        const url = '/api/prescriptions/';
        const response = await axios.post(url, prescriptionData, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        showAlert('Đơn thuốc đã được tạo thành công', 'success');
        
        // Close modal and refresh list
        let modal = bootstrap.Modal.getInstance(document.getElementById('addPrescriptionModal'));
        if (!modal) {
            modal = bootstrap.Modal.getInstance(document.getElementById('createPrescriptionModal'));
        }
        if (modal) modal.hide();
        
        // Reset form
        event.target.reset();
        const container = document.getElementById('prescription-items-container');
        if (container) container.innerHTML = '';
        
        // Reload prescriptions
        await loadPrescriptions();
        
    } catch (error) {
        console.error('❌ Error creating prescription:', error);
        console.error('❌ Error response:', error.response);
        console.error('❌ Error data:', error.response?.data);
        
        let errorMessage = 'Lỗi tạo đơn thuốc: ';
        
        if (error.response?.data) {
            if (typeof error.response.data === 'object') {
                const errors = [];
                for (const [field, messages] of Object.entries(error.response.data)) {
                    if (Array.isArray(messages)) {
                        errors.push(`${field}: ${messages.join(', ')}`);
                    } else if (typeof messages === 'object') {
                        errors.push(`${field}: ${JSON.stringify(messages)}`);
                    } else {
                        errors.push(`${field}: ${messages}`);
                    }
                }
                errorMessage += errors.join('; ');
            } else {
                errorMessage += error.response.data;
            }
        } else {
            errorMessage += error.message;
        }
        
        console.error('💥 Final error message:', errorMessage);
        showAlert(errorMessage, 'error');
    }
}

/**
 * Show drug selection modal
 */
function showDrugSelectionModal() {
    
    // For now, just add a prescription item directly
    addPrescriptionItem();
    
    // TODO: Implement actual drug selection modal with search functionality
    // const drugModal = new bootstrap.Modal(document.getElementById('drugSelectionModal'));
    // drugModal.show();
}

/**
 * Add prescription item row
 */
function addPrescriptionItem() {
    const container = document.getElementById('prescription-items-container');
    if (!container) return;
    
    const itemRow = document.createElement('div');
    itemRow.className = 'prescription-item-row mb-3 p-3 border rounded';
    itemRow.innerHTML = `
        <div class="row">
            <div class="col-md-3">
                <label class="form-label">Thuốc <span class="text-danger">*</span></label>
                <select class="form-select" name="drug" required>
                    <option value="">Chọn thuốc</option>
                    ${drugs.map(drug => `<option value="${drug.id}">${drug.name}</option>`).join('')}
                </select>
            </div>
            <div class="col-md-2">
                <label class="form-label">Số lượng <span class="text-danger">*</span></label>
                <input type="number" class="form-control" name="quantity" min="1" required>
            </div>
            <div class="col-md-2">
                <label class="form-label">Liều dùng</label>
                <input type="text" class="form-control" name="dosage" placeholder="VD: 1 viên" value="1 viên">
            </div>
            <div class="col-md-2">
                <label class="form-label">Tần suất</label>
                <select class="form-select" name="frequency">
                    <option value="1X_DAILY">1 lần/ngày</option>
                    <option value="2X_DAILY">2 lần/ngày</option>
                    <option value="3X_DAILY" selected>3 lần/ngày</option>
                    <option value="4X_DAILY">4 lần/ngày</option>
                    <option value="BEFORE_MEALS">Trước ăn</option>
                    <option value="AFTER_MEALS">Sau ăn</option>
                </select>
            </div>
            <div class="col-md-1">
                <label class="form-label">Số ngày</label>
                <input type="number" class="form-control" name="duration" min="1" value="7">
            </div>
            <div class="col-md-2">
                <label class="form-label">&nbsp;</label>
                <button type="button" class="btn btn-outline-danger d-block" onclick="removePrescriptionItem(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="row mt-2">
            <div class="col-md-3">
                <label class="form-label">Cách dùng</label>
                <select class="form-select" name="route" onchange="onRouteChange(this)">
                    <option value="ORAL" selected>Uống</option>
                    <option value="TOPICAL">Bôi ngoài da</option>
                    <option value="INJECTION_IM">Tiêm bắp</option>
                    <option value="INJECTION_IV">Tiêm tĩnh mạch</option>
                    <option value="EYE_DROPS">Nhỏ mắt</option>
                    <option value="EAR_DROPS">Nhỏ tai</option>
                    <option value="NASAL_DROPS">Nhỏ mũi</option>
                </select>
            </div>
            <div class="col-md-9">
                <label class="form-label">Hướng dẫn sử dụng <span class="text-danger">*</span></label>
                <textarea class="form-control" name="instructions" rows="2" required placeholder="VD: Uống sau ăn, uống nhiều nước...">Uống theo chỉ định của bác sĩ</textarea>
            </div>
        </div>
    `;
    
    container.appendChild(itemRow);
    // Bind route change handler for this row
    const routeSelect = itemRow.querySelector('select[name="route"]');
    if (routeSelect) {
        routeSelect.addEventListener('change', function() { onRouteChange(this); });
    }
}
function onRouteChange(selectEl) {
    try {
        const row = selectEl.closest('.prescription-item-row');
        const instructions = row.querySelector('textarea[name="instructions"]');
        const route = selectEl.value;
        const mapping = {
            'ORAL': 'Uống theo chỉ định của bác sĩ',
            'TOPICAL': 'Bôi theo chỉ định của bác sĩ',
            'INJECTION_IM': 'Tiêm bắp theo chỉ định của bác sĩ',
            'INJECTION_IV': 'Tiêm tĩnh mạch theo chỉ định của bác sĩ',
            'EYE_DROPS': 'Nhỏ mắt theo chỉ định của bác sĩ',
            'EAR_DROPS': 'Nhỏ tai theo chỉ định của bác sĩ',
            'NASAL_DROPS': 'Nhỏ mũi theo chỉ định của bác sĩ'
        };
        if (instructions && mapping[route]) {
            instructions.value = mapping[route];
        }
    } catch (e) { /* noop */ }
}

/**
 * Remove prescription item row
 */
function removePrescriptionItem(button) {
    const row = button.closest('.prescription-item-row');
    if (row) {
        row.remove();
    }
}

/**
 * View prescription details
 */
async function viewPrescription(prescriptionId) {
    try {
        const url = `/api/prescriptions/${prescriptionId}/`;
        const response = await axios.get(url);
        const prescription = response.data;
        

        
        // Check if we have the nested data
        
        // Populate modal with prescription details
        const modalTitle = document.getElementById('viewPrescriptionModalLabel');
        const modalBody = document.getElementById('prescription-details');
        const modalActions = document.getElementById('prescription-actions');
        
        if (modalTitle) {
            modalTitle.innerHTML = `
                <i class="fas fa-file-medical"></i> 
                Chi tiết đơn thuốc #${prescription.prescription_number || prescription.id}
            `;
        }
        
        if (modalBody) {
            modalBody.innerHTML = generatePrescriptionDetailsHTML(prescription);
        }
        
        if (modalActions) {
            modalActions.innerHTML = generatePrescriptionActionsHTML(prescription);
        }
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('viewPrescriptionModal'));
        modal.show();
        
    } catch (error) {
        console.error('❌ Error viewing prescription:', error);
        showAlert('Lỗi tải thông tin đơn thuốc: ' + (error.response?.data?.detail || error.message), 'error');
    }
}

/**
 * Generate prescription details HTML
 */
function generatePrescriptionDetailsHTML(prescription) {
    const statusBadge = getStatusBadge(prescription.status);
    const typeBadge = getTypeBadge(prescription.prescription_type);
    
    return `
        <div class="row mb-4">
            <!-- Basic Information -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-info-circle"></i> Thông tin cơ bản</h6>
                    </div>
                    <div class="card-body">
                        <table class="table table-borderless table-sm">
                            <tr>
                                <td class="fw-bold">Số đơn thuốc:</td>
                                <td>${prescription.prescription_number || prescription.id}</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Ngày kê đơn:</td>
                                <td>${formatDate(prescription.prescription_date)}</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Có hiệu lực đến:</td>
                                <td>${formatDate(prescription.valid_until)}</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Loại đơn:</td>
                                <td>${typeBadge}</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Trạng thái:</td>
                                <td>${statusBadge}</td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Tổng tiền:</td>
                                <td class="fw-bold text-primary">${formatCurrency(prescription.total_amount)}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <!-- Patient & Doctor Information -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-users"></i> Bệnh nhân & Bác sĩ</h6>
                    </div>
                    <div class="card-body">
                        <table class="table table-borderless table-sm">
                            <tr>
                                <td class="fw-bold">Bệnh nhân:</td>
                                <td>
                                    ${prescription.patient?.full_name || prescription.patient_name || 'N/A'}<br>
                                    <small class="text-muted">CCCD: ${prescription.patient?.citizen_id || prescription.patient_code || 'N/A'}</small>
                                </td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Bác sĩ kê đơn:</td>
                                <td>
                                    ${prescription.doctor?.full_name || prescription.doctor_name || 'N/A'}<br>
                                    <small class="text-muted">${prescription.doctor?.specialization || prescription.doctor_specialization || ''}</small>
                                </td>
                            </tr>
                            <tr>
                                <td class="fw-bold">Chẩn đoán:</td>
                                <td>${prescription.diagnosis || 'Không có'}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Prescription Items -->
        <div class="card mb-4">
            <div class="card-header">
                <h6 class="mb-0"><i class="fas fa-pills"></i> Danh sách thuốc kê đơn</h6>
            </div>
            <div class="card-body">
                ${generatePrescriptionItemsHTML(prescription.items || [])}
            </div>
        </div>
        
        <!-- Notes and Instructions -->
        <div class="row">
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-sticky-note"></i> Ghi chú của bác sĩ</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-0">${prescription.notes || 'Không có ghi chú'}</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header">
                        <h6 class="mb-0"><i class="fas fa-exclamation-triangle"></i> Hướng dẫn đặc biệt</h6>
                    </div>
                    <div class="card-body">
                        <p class="mb-0">${prescription.special_instructions || 'Không có hướng dẫn đặc biệt'}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Generate prescription items HTML
 */
function generatePrescriptionItemsHTML(items) {
    if (!items || items.length === 0) {
        return '<p class="text-muted">Không có thuốc nào trong đơn thuốc này.</p>';
    }
    
    let itemsHTML = `
        <div class="table-responsive">
            <table class="table table-bordered">
                <thead class="table-light">
                    <tr>
                        <th>STT</th>
                        <th>Tên thuốc</th>
                        <th>Số lượng</th>
                        <th>Liều dùng</th>
                        <th>Tần suất</th>
                        <th>Cách dùng</th>
                        <th>Số ngày</th>
                        <th>Hướng dẫn</th>
                        <th>Thành tiền</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    items.forEach((item, index) => {
        itemsHTML += `
            <tr>
                <td>${index + 1}</td>
                <td>
                    <strong>${item.drug?.name || item.drug_name || 'N/A'}</strong><br>
                    <small class="text-muted">${item.drug?.generic_name || item.drug_generic_name || item.drug_code || ''}</small>
                </td>
                <td>${item.quantity || 0}</td>
                <td>${item.dosage_per_time || 'N/A'}</td>
                <td>${item.frequency_display || getFrequencyText(item.frequency)}</td>
                <td>${item.route_display || getRouteText(item.route)}</td>
                <td>${item.duration_days || 0} ngày</td>
                <td>${item.instructions || 'Không có'}</td>
                <td class="fw-bold">${formatCurrency(item.total_price)}</td>
            </tr>
        `;
    });
    
    itemsHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    return itemsHTML;
}

/**
 * Generate prescription actions HTML
 */
function generatePrescriptionActionsHTML(prescription) {
    const canEdit = prescription.status === 'DRAFT' || prescription.status === 'ACTIVE';
    const canDelete = prescription.status === 'DRAFT';
    
    let actionsHTML = `
        <button type="button" class="btn btn-success" onclick="printPrescription('${prescription.id}')">
            <i class="fas fa-print"></i> In đơn thuốc
        </button>
    `;
    
    if (canEdit) {
        actionsHTML += `
            <button type="button" class="btn btn-warning" onclick="editPrescription('${prescription.id}')">
                <i class="fas fa-edit"></i> Chỉnh sửa
            </button>
        `;
    }
    
    if (canDelete) {
        actionsHTML += `
            <button type="button" class="btn btn-danger" onclick="deletePrescription('${prescription.id}')">
                <i class="fas fa-trash"></i> Xóa
            </button>
        `;
    }
    
    return actionsHTML;
}

/**
 * Get frequency text in Vietnamese
 */
function getFrequencyText(frequency) {
    const frequencyMap = {
        '1X_DAILY': '1 lần/ngày',
        '2X_DAILY': '2 lần/ngày', 
        '3X_DAILY': '3 lần/ngày',
        '4X_DAILY': '4 lần/ngày',
        'BEFORE_MEALS': 'Trước ăn',
        'AFTER_MEALS': 'Sau ăn'
    };
    return frequencyMap[frequency] || frequency || 'N/A';
}

/**
 * Get route text in Vietnamese
 */
function getRouteText(route) {
    const routeMap = {
        'ORAL': 'Uống',
        'TOPICAL': 'Bôi ngoài da',
        'INJECTION_IM': 'Tiêm bắp',
        'INJECTION_IV': 'Tiêm tĩnh mạch',
        'EYE_DROPS': 'Nhỏ mắt',
        'EAR_DROPS': 'Nhỏ tai',
        'NASAL_DROPS': 'Nhỏ mũi'
    };
    return routeMap[route] || route || 'N/A';
}

/**
 * Get prescription type text in Vietnamese
 */
function getTypeText(type) {
    const typeMap = {
        'OUTPATIENT': 'Ngoại trú',
        'INPATIENT': 'Nội trú', 
        'EMERGENCY': 'Cấp cứu',
        'DISCHARGE': 'Ra viện'
    };
    return typeMap[type] || type || 'N/A';
}

/**
 * Get status text in Vietnamese
 */
function getStatusText(status) {
    const statusMap = {
        'DRAFT': 'Nháp',
        'ACTIVE': 'Có hiệu lực',
        'PARTIALLY_DISPENSED': 'Cấp thuốc một phần',
        'FULLY_DISPENSED': 'Đã cấp thuốc đầy đủ',
        'CANCELLED': 'Đã hủy',
        'EXPIRED': 'Hết hạn'
    };
    return statusMap[status] || status || 'N/A';
}

/**
 * Edit prescription
 */
async function editPrescription(prescriptionId) {
    try {
        const url = `/api/prescriptions/${prescriptionId}/`;
        const response = await axios.get(url);
        const prescription = response.data;
        
        // For now, only allow changing status and notes
        // Replace browser prompt with a simple inline update to ACTIVE status as example
        const newStatus = 'ACTIVE';
        if (newStatus && newStatus !== prescription.status) {
            // Validate status
            const validStatuses = ['DRAFT', 'ACTIVE', 'CANCELLED'];
            if (!validStatuses.includes(newStatus.toUpperCase())) {
                showAlert('Trạng thái không hợp lệ', 'error');
                return;
            }
            
            const updateData = {
                status: newStatus.toUpperCase()
            };
            
            const updateResponse = await axios.patch(url, updateData);
            showAlert('Đơn thuốc đã được cập nhật', 'success');
            
            // Reload prescriptions
            await loadPrescriptions();
        }
        
    } catch (error) {
        console.error('❌ Error loading prescription for edit:', error);
        showAlert('Lỗi tải thông tin đơn thuốc để chỉnh sửa: ' + (error.response?.data?.detail || error.message), 'error');
    }
}

/**
 * Print prescription
 */
async function printPrescription(prescriptionId) {
    try {
        // Get prescription details first
        const url = `/api/prescriptions/${prescriptionId}/`;
        const response = await axios.get(url);
        const prescription = response.data;
        
        // Generate printable HTML
        const printHTML = generatePrintableHTML(prescription);
        
        // Create new window for printing
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        printWindow.document.write(printHTML);
        printWindow.document.close();
        
        // Wait for content to load then print
        printWindow.onload = function() {
            setTimeout(() => {
                printWindow.print();
                // Close window after printing (optional)
                printWindow.onafterprint = function() {
                    printWindow.close();
                };
            }, 500);
        };
        
    } catch (error) {
        console.error('❌ Error printing prescription:', error);
        showAlert('Lỗi in đơn thuốc: ' + (error.response?.data?.detail || error.message), 'error');
    }
}

/**
 * Generate printable HTML for prescription
 */
function generatePrintableHTML(prescription) {
    const currentDate = new Date().toLocaleDateString('vi-VN');
    const items = prescription.items || [];
    
    return `
        <!DOCTYPE html>
        <html lang="vi">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Đơn thuốc #${prescription.prescription_number || prescription.id}</title>
            <style>
                body {
                    font-family: 'Times New Roman', Times, serif;
                    margin: 0;
                    padding: 20px;
                    font-size: 14px;
                    line-height: 1.4;
                }
                .header {
                    text-align: center;
                    border-bottom: 2px solid #000;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }
                .hospital-name {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                .hospital-info {
                    font-size: 12px;
                    color: #666;
                }
                .prescription-title {
                    font-size: 20px;
                    font-weight: bold;
                    text-align: center;
                    margin: 20px 0;
                    text-transform: uppercase;
                }
                .patient-info, .doctor-info {
                    margin-bottom: 15px;
                }
                .info-row {
                    display: flex;
                    margin-bottom: 5px;
                }
                .info-label {
                    font-weight: bold;
                    width: 120px;
                    flex-shrink: 0;
                }
                .medicines-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                .medicines-table th,
                .medicines-table td {
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: left;
                }
                .medicines-table th {
                    background-color: #f5f5f5;
                    font-weight: bold;
                    text-align: center;
                }
                .medicines-table .number-col {
                    width: 40px;
                    text-align: center;
                }
                .medicines-table .quantity-col,
                .medicines-table .days-col {
                    width: 60px;
                    text-align: center;
                }
                .drug-name {
                    font-weight: bold;
                }
                .drug-ingredient {
                    font-size: 12px;
                    color: #666;
                    font-style: italic;
                }
                .total-row {
                    margin-top: 15px;
                    text-align: right;
                    font-size: 16px;
                    font-weight: bold;
                }
                .signature-section {
                    margin-top: 40px;
                    display: flex;
                    justify-content: space-between;
                }
                .signature-box {
                    text-align: center;
                    width: 200px;
                }
                .signature-title {
                    font-weight: bold;
                    margin-bottom: 60px;
                }
                .notes-section {
                    margin-top: 20px;
                    border-top: 1px solid #ddd;
                    padding-top: 15px;
                }
                .notes-title {
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                @media print {
                    body {
                        padding: 0;
                    }
                    .no-print {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <!-- Header -->
            <div class="header">
                <div class="hospital-name">BỆNH VIỆN HẠNH PHÚC</div>
                <div class="hospital-info">
                    Địa chỉ: 123 Đường ABC, Quận XYZ, TP. Hồ Chí Minh<br>
                    Điện thoại: (028) 1234-5678 | Email: info@happinesshospital.vn
                </div>
            </div>
            
            <!-- Prescription Title -->
            <div class="prescription-title">Đơn thuốc</div>
            
            <!-- Basic Info -->
            <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                <div>
                    <div class="info-row">
                        <span class="info-label">Số đơn thuốc:</span>
                        <span>${prescription.prescription_number || prescription.id}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Ngày kê đơn:</span>
                        <span>${formatDate(prescription.prescription_date)}</span>
                    </div>
                </div>
                <div>
                    <div class="info-row">
                        <span class="info-label">Loại đơn:</span>
                        <span>${getTypeText(prescription.prescription_type)}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Có hiệu lực đến:</span>
                        <span>${formatDate(prescription.valid_until)}</span>
                    </div>
                </div>
            </div>
            
            <!-- Patient Information -->
            <div class="patient-info">
                <h4 style="margin-bottom: 10px;">Thông tin bệnh nhân:</h4>
                <div class="info-row">
                    <span class="info-label">Họ và tên:</span>
                    <span>${prescription.patient?.full_name || prescription.patient_name || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">CCCD/CMND:</span>
                    <span>${prescription.patient?.citizen_id || prescription.patient_code || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Ngày sinh:</span>
                    <span>${prescription.patient?.date_of_birth ? formatDate(prescription.patient.date_of_birth) : 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Địa chỉ:</span>
                    <span>${prescription.patient?.address || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Chẩn đoán:</span>
                    <span>${prescription.diagnosis || 'Không có'}</span>
                </div>
            </div>
            
            <!-- Medicines Table -->
            <table class="medicines-table">
                <thead>
                    <tr>
                        <th class="number-col">STT</th>
                        <th>Tên thuốc / Hoạt chất</th>
                        <th class="quantity-col">Số lượng</th>
                        <th>Liều dùng</th>
                        <th>Tần suất</th>
                        <th>Cách dùng</th>
                        <th class="days-col">Số ngày</th>
                        <th>Hướng dẫn sử dụng</th>
                    </tr>
                </thead>
                <tbody>
                    ${items.map((item, index) => `
                        <tr>
                            <td class="number-col">${index + 1}</td>
                            <td>
                                <div class="drug-name">${item.drug?.name || item.drug_name || 'N/A'}</div>
                                ${(item.drug?.generic_name || item.drug_generic_name) ? 
                                    `<div class="drug-ingredient">${item.drug?.generic_name || item.drug_generic_name}</div>` : ''
                                }
                            </td>
                            <td class="quantity-col">${item.quantity || 0}</td>
                            <td>${item.dosage_per_time || 'N/A'}</td>
                            <td>${item.frequency_display || getFrequencyText(item.frequency)}</td>
                            <td>${item.route_display || getRouteText(item.route)}</td>
                            <td class="days-col">${item.duration_days || 0}</td>
                            <td>${item.instructions || 'Không có'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            
            <!-- Total Amount -->
            <div class="total-row">
                Tổng tiền: ${formatCurrency(prescription.total_amount)}
            </div>
            
            <!-- Notes -->
            ${prescription.notes || prescription.special_instructions ? `
                <div class="notes-section">
                    ${prescription.notes ? `
                        <div>
                            <div class="notes-title">Ghi chú của bác sĩ:</div>
                            <div>${prescription.notes}</div>
                        </div>
                    ` : ''}
                    ${prescription.special_instructions ? `
                        <div style="margin-top: 10px;">
                            <div class="notes-title">Hướng dẫn đặc biệt:</div>
                            <div>${prescription.special_instructions}</div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
            
            <!-- Signature Section -->
            <div class="signature-section">
                <div class="signature-box">
                    <div class="signature-title">Người nhận thuốc</div>
                    <div>(Ký, ghi rõ họ tên)</div>
                </div>
                <div class="signature-box">
                    <div class="signature-title">Bác sĩ kê đơn</div>
                    <div style="margin-top: 40px;">
                        <strong>${prescription.doctor?.full_name || prescription.doctor_name || 'N/A'}</strong><br>
                        ${prescription.doctor?.specialization || prescription.doctor_specialization || ''}
                    </div>
                </div>
            </div>
            
            <!-- Print Info -->
            <div style="margin-top: 40px; text-align: center; font-size: 12px; color: #666;">
                Đơn thuốc được in ngày ${currentDate}
            </div>
        </body>
        </html>
    `;
}

/**
 * Delete prescription
 */
async function deletePrescription(prescriptionId) {
    // Removed browser confirm - use UI modal if needed

    try {
        const url = `/api/prescriptions/${prescriptionId}/`;
        await axios.delete(url);

        showAlert('Đơn thuốc đã được xóa', 'success');
        
        // Reload prescriptions
        await loadPrescriptions();
        
    } catch (error) {
        console.error('❌ Error deleting prescription:', error);
        showAlert('Lỗi xóa đơn thuốc: ' + (error.response?.data?.message || error.message), 'error');
    }
}

/**
 * Update pagination
 */
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
                <a class="page-link" href="#" onclick="loadPrescriptions(${currentPageNum - 1})">Trước</a>
            </li>
        `;
    }
    
    // Page numbers
    for (let i = Math.max(1, currentPageNum - 2); i <= Math.min(totalPages, currentPageNum + 2); i++) {
        const isActive = i === currentPageNum;
        paginationHtml += `
            <li class="page-item ${isActive ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadPrescriptions(${i})">${i}</a>
            </li>
        `;
    }
    
    // Next button
    if (currentPageNum < totalPages) {
        paginationHtml += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadPrescriptions(${currentPageNum + 1})">Sau</a>
            </li>
        `;
    }
    
    pagination.innerHTML = paginationHtml;
}

/**
 * Update total count display
 */
function updateTotalCount(count) {
    const totalCountElement = document.getElementById('total-count');
    if (totalCountElement) {
        totalCountElement.textContent = count;
    }
}

/**
 * Utility functions
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (e) {
        return dateString;
    }
}

function formatCurrency(amount) {
    if (!amount) return '0 ₫';
    try {
        return new Intl.NumberFormat('vi-VN', {
            style: 'currency',
            currency: 'VND'
        }).format(amount);
    } catch (e) {
        return amount + ' ₫';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type = 'info') {
    // Use existing alert system from main.js if available
    if (window.AppAPI && window.AppAPI.showAlert) {
        window.AppAPI.showAlert(message, type);
        return;
    }
    // Floating toast at top-right (no browser alert)
    const containerId = 'hh-floating-notifications';
    let container = document.getElementById(containerId);
    if (!container) {
        container = document.createElement('div');
        container.id = containerId;
        container.style.position = 'fixed';
        container.style.top = '16px';
        container.style.right = '16px';
        container.style.zIndex = '1060';
        container.style.maxWidth = '350px';
        document.body.appendChild(container);
    }
    const typeClass = {
        success: 'alert-success',
        info: 'alert-info',
        warning: 'alert-warning',
        error: 'alert-danger',
        danger: 'alert-danger'
    }[type] || 'alert-info';

    const toast = document.createElement('div');
    toast.className = `alert ${typeClass} alert-dismissible fade show shadow`;
    toast.style.minWidth = '320px';
    toast.style.marginBottom = '8px';
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert"></button>
        </div>
    `;
    container.appendChild(toast);
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 5000);
}
