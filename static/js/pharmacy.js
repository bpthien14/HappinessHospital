let dgCurrentPage = 1;
let dgTotalPages = 1;

document.addEventListener('DOMContentLoaded', function() {
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializePharmacy();
    } else {
        window.addEventListener('axiosInterceptorsReady', initializePharmacy);
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializePharmacy();
            }
        }, 1500);
    }
});

function initializePharmacy() {
    if (!checkAuth()) return;
    bindEvents();
    loadCategories();
    loadEnums();
    loadDrugs();
    applyPharmacistUIRestrictions();
}

function bindEvents() {
    const form = document.getElementById('search-form');
    if (form) {
        form.addEventListener('submit', function(e){ e.preventDefault(); dgCurrentPage = 1; loadDrugs(); });
    }
    // Low-stock button removed per requirement
    const addForm = document.getElementById('add-drug-form');
    if (addForm) {
        addForm.addEventListener('input', reevaluateSaveButton);
        addForm.addEventListener('change', reevaluateSaveButton);
        addForm.addEventListener('submit', handleAddDrug);
        setTimeout(reevaluateSaveButton, 0);
    }

    // Edit form interactions
    const editForm = document.getElementById('edit-drug-form');
    if (editForm) {
        editForm.addEventListener('input', evaluateUpdateButtonState);
        editForm.addEventListener('change', evaluateUpdateButtonState);
    }
}

function isPharmacist() {
    try {
        const raw = localStorage.getItem('user_data');
        const user = raw ? JSON.parse(raw) : null;
        if (!user) return false;
        if (user.user_type === 'PHARMACIST') return true;
        const roles = Array.isArray(user.roles) ? user.roles : [];
        return roles.includes('Pharmacist') || roles.includes('PHARMACIST');
    } catch (e) { return false; }
}

function applyPharmacistUIRestrictions() {
    if (!isPharmacist()) return;
    // Ẩn nút Thêm thuốc
    const addBtn = document.getElementById('btn-add-drug');
    if (addBtn) addBtn.style.display = 'none';
}

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
    if (window.HospitalApp && window.HospitalApp.showAlert) {
        window.HospitalApp.showAlert(message, type);
        return;
    }
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        setTimeout(() => { if (alertDiv.parentNode) alertDiv.remove(); }, 5000);
    }
}

function showToast(message, type = 'info', icon = null, duration = 5000) {
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
    const typeClasses = { success: 'alert-success', info: 'alert-info', warning: 'alert-warning', danger: 'alert-danger' };
    const typeIcons = { success: 'fas fa-check-circle', info: 'fas fa-info-circle', warning: 'fas fa-exclamation-triangle', danger: 'fas fa-times-circle' };
    const toast = document.createElement('div');
    toast.className = `alert ${typeClasses[type] || 'alert-info'} shadow-lg border-0`;
    toast.style.minWidth = '320px';
    toast.style.marginBottom = '0.5rem';
    const iconHtml = icon || typeIcons[type] || 'fas fa-info-circle';
    toast.innerHTML = `<div class="d-flex align-items-center"><i class="${iconHtml} me-2"></i><div class="flex-grow-1">${message}</div><button type="button" class="btn-close btn-close-sm ms-2" onclick="this.parentElement.parentElement.remove()"></button></div>`;
    container.appendChild(toast);
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => { if (toast.parentNode) toast.remove(); }, 300);
        }
    }, duration);
    return toast;
}

// Normalize API response into an array (supports paginated and non-paginated)
function toResultsArray(data) {
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
}

async function loadCategories() {
    try {
        const res = await axios.get('/api/drug-categories/');
        const data = toResultsArray(res.data);
        const select = document.getElementById('category-filter');
        const addSelect = document.getElementById('dg-category');
        if (select) select.innerHTML = '<option value="">Tất cả</option>';
        if (addSelect) addSelect.innerHTML = '';
        if (!data || data.length === 0) {
            if (addSelect) {
                const ph = document.createElement('option');
                ph.value = '';
                ph.textContent = 'Chưa có nhóm thuốc - vui lòng tạo trước';
                addSelect.appendChild(ph);
                addSelect.disabled = true;
                toggleAddSubmit(false);
            }
        } else {
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id; opt.textContent = `${c.name}`;
                select && select.appendChild(opt.cloneNode(true));
                addSelect && addSelect.appendChild(opt);
            });
            if (addSelect) addSelect.disabled = false;
            toggleAddSubmit(true);
        }
    } catch (e) { console.warn('Load categories failed', e); }
}

function loadEnums() {
    const dosageSelect = document.getElementById('dg-dosage_form');
    const unitSelect = document.getElementById('dg-unit');
    const dosage = [
        ['TABLET','Viên nén'],['CAPSULE','Viên nang'],['SYRUP','Siro'],['INJECTION','Tiêm'],
        ['CREAM','Kem bôi'],['OINTMENT','Thuốc mỡ'],['DROPS','Nhỏ'],['SPRAY','Xịt'],['POWDER','Bột'],['SUPPOSITORY','Viên đặt']
    ];
    const units = [
        ['TABLET','Viên'],['CAPSULE','Viên nang'],['BOTTLE','Chai'],['BOX','Hộp'],['TUBE','Tuýp'],['VIAL','Lọ'],['AMPOULE','Ống'],['SACHET','Gói'],['ML','ml'],['MG','mg'],['G','g']
    ];
    if (dosageSelect && dosageSelect.options.length === 0) dosage.forEach(([v,t]) => { const o=document.createElement('option'); o.value=v; o.textContent=t; dosageSelect.appendChild(o); });
    if (unitSelect && unitSelect.options.length === 0) units.forEach(([v,t]) => { const o=document.createElement('option'); o.value=v; o.textContent=t; unitSelect.appendChild(o); });
}

async function loadDrugs() {
    try {
        const params = new URLSearchParams({ page: dgCurrentPage, page_size: 10 });
        const q = document.getElementById('search-query').value.trim();
        const cat = document.getElementById('category-filter').value;
        const stock = document.getElementById('stock-filter').value;
        if (q) params.append('search', q);
        if (cat) params.append('category', cat);
        if (stock === 'low') params.append('is_low_stock', 'true');
        if (stock === 'ok') params.append('is_low_stock', 'false');
        const res = await axios.get(`/api/drugs/?${params}`);
        renderDrugs(res.data.results || []);
        updatePagination(res.data);
    } catch (error) {
        console.error('Error loading drugs:', error);
        if (error.response?.status === 401) {
            showToast('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning', 'fas fa-exclamation-triangle', 6000);
            redirectToLogin();
        } else {
            showToast('Lỗi khi tải danh sách thuốc', 'danger');
        }
    }
}

// loadLowStock removed per requirement

function renderDrugs(drugs) {
    const tbody = document.getElementById('drugs-tbody');
    tbody.innerHTML = '';
    drugs.forEach(d => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${d.code || '-'}</td>
            <td>${d.name || '-'}</td>
            <td>${d.generic_name || '-'}</td>
            <td>${d.dosage_form_display || '-'}</td>
            <td>${d.strength || '-'}</td>
            <td><span class="badge ${Number(d.current_stock) <= 0 ? 'bg-danger' : Number(d.current_stock) <= Number(d.minimum_stock || 0) ? 'bg-warning text-dark' : 'bg-success'}">${d.current_stock ?? '-'}</span></td>
            <td>${formatCurrency(d.unit_price)}</td>
            <td><span class="badge ${statusBadgeClass(d.stock_status)}">${d.stock_status || '-'}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary me-1" onclick="openEditDrugModal('${d.id}')"><i class="fas fa-edit"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteDrug('${d.id}')"><i class="fas fa-trash"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
    // Ẩn các nút thêm/xóa khi là Dược sĩ
    if (isPharmacist()) {
        document.querySelectorAll('#drugs-table .btn-outline-danger').forEach(btn => btn.style.display = 'none');
        const addBtn = document.getElementById('btn-add-drug');
        if (addBtn) addBtn.style.display = 'none';
    }
}

function statusBadgeClass(status) {
    const s = String(status || '').toUpperCase();
    if (s.includes('HẾT')) return 'bg-danger';
    if (s.includes('SẮP')) return 'bg-warning text-dark';
    if (s.includes('DƯ')) return 'bg-info';
    return 'bg-success';
}

function updatePagination(data) {
    dgTotalPages = Math.ceil((data.count || 0) / 10);
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${dgCurrentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="changeDrugPage(${dgCurrentPage - 1})">Trước</a>`;
    pagination.appendChild(prevLi);
    for (let i = Math.max(1, dgCurrentPage - 2); i <= Math.min(dgTotalPages, dgCurrentPage + 2); i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === dgCurrentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="changeDrugPage(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${dgCurrentPage === dgTotalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="changeDrugPage(${dgCurrentPage + 1})">Sau</a>`;
    pagination.appendChild(nextLi);
}

function changeDrugPage(p) { if (p>=1 && p<=dgTotalPages) { dgCurrentPage=p; loadDrugs(); } }

function reevaluateSaveButton() {
    const required = ['dg-code','dg-name','dg-generic_name','dg-category','dg-dosage_form','dg-unit','dg-strength','dg-unit_price','dg-current_stock','dg-minimum_stock','dg-maximum_stock','dg-manufacturer','dg-country_of_origin','dg-indication'];
    const ok = required.every(id => {
        const el = document.getElementById(id);
        return el && String(el.value || '').trim().length > 0;
    });
    const btn = document.getElementById('save-drug-btn');
    if (btn) btn.disabled = !ok;
}

async function handleAddDrug(e) {
    e.preventDefault();
    const payload = collectAddDrugPayload();
    try {
        const res = await axios.post('/api/drugs/', payload, { headers: { 'Content-Type': 'application/json' } });
        const modal = bootstrap.Modal.getInstance(document.getElementById('addDrugModal'));
        if (modal) modal.hide();
        e.target.reset();
        showToast('Thêm thuốc thành công!', 'success', 'fas fa-check-circle', 4000);
        dgCurrentPage = 1;
        loadDrugs();
    } catch (error) {
        console.error('Add drug error:', error);
        if (error.response?.status === 401) {
            showToast('Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại', 'warning', 'fas fa-exclamation-triangle', 6000);
            redirectToLogin();
        } else if (error.response?.status === 403) {
            showToast('Bạn không có quyền thêm thuốc', 'danger');
        } else {
            const data = error.response?.data;
            const messages = [];
            if (data && typeof data === 'object') {
                try { Object.keys(data).forEach(k => { const v = Array.isArray(data[k]) ? data[k].join(', ') : data[k]; messages.push(String(v)); }); } catch (_) {}
            }
            showToast(messages[0] || 'Không thể thêm thuốc', 'danger');
        }
    }
}

function collectAddDrugPayload() {
    const val = id => document.getElementById(id)?.value?.trim() || '';
    const num = id => Number(document.getElementById(id)?.value || 0);
    const payload = {
        code: val('dg-code'), name: val('dg-name'), generic_name: val('dg-generic_name'), brand_name: val('dg-brand_name') || '',
        category: val('dg-category'), dosage_form: val('dg-dosage_form'), strength: val('dg-strength'), unit: val('dg-unit'),
        indication: document.getElementById('dg-indication')?.value?.trim() || '',
        contraindication: '', side_effects: '', interactions: '', dosage_adult: '', dosage_child: '', storage_condition: '',
        expiry_after_opening: null,
        unit_price: num('dg-unit_price'), insurance_price: (document.getElementById('dg-insurance_price')?.value ? num('dg-insurance_price') : null),
        current_stock: num('dg-current_stock'), minimum_stock: num('dg-minimum_stock'), maximum_stock: num('dg-maximum_stock'),
        registration_number: '', manufacturer: val('dg-manufacturer'), country_of_origin: val('dg-country_of_origin'),
        is_prescription_required: true, is_controlled_substance: false, is_active: true
    };
    return payload;
}

async function openEditDrugModal(id) {
    try {
        // show spinner, reset error
        setEditLoading(true);
        setEditError('');
        const res = await axios.get(`/api/drugs/${id}/`);
        const d = res.data;
        // preload categories/enums if needed
        await ensureEditCategories();
        if (document.getElementById('ed-dosage_form')?.options.length <= 0 || document.getElementById('ed-unit')?.options.length <= 0) {
            loadEnumsTo('ed-dosage_form', 'ed-unit');
        }
        // fill fields
        document.getElementById('ed-code').value = d.code || '';
        document.getElementById('ed-name').value = d.name || '';
        document.getElementById('ed-generic_name').value = d.generic_name || '';
        document.getElementById('ed-brand_name').value = d.brand_name || '';
        document.getElementById('ed-category').value = d.category || '';
        document.getElementById('ed-dosage_form').value = d.dosage_form || '';
        document.getElementById('ed-unit').value = d.unit || '';
        document.getElementById('ed-strength').value = d.strength || '';
        document.getElementById('ed-unit_price').value = d.unit_price || '';
        document.getElementById('ed-insurance_price').value = d.insurance_price ?? '';
        document.getElementById('ed-current_stock').value = d.current_stock ?? 0;
        document.getElementById('ed-minimum_stock').value = d.minimum_stock ?? 0;
        document.getElementById('ed-maximum_stock').value = d.maximum_stock ?? 0;
        document.getElementById('ed-manufacturer').value = d.manufacturer || '';
        document.getElementById('ed-country_of_origin').value = d.country_of_origin || '';
        document.getElementById('ed-indication').value = d.indication || '';
        document.getElementById('ed-is_active').checked = !!d.is_active;
        // store id
        document.getElementById('edit-drug-form').dataset.drugId = d.id;
        // show modal
        const modal = new bootstrap.Modal(document.getElementById('editDrugModal'));
        setEditLoading(false);
        modal.show();
        // set baseline to detect changes
        window._editDrugBaseline = collectEditDrugPayload();
        evaluateUpdateButtonState();
    } catch (e) {
        setEditLoading(false);
        setEditError('Không thể tải thông tin thuốc');
        showToast('Không thể tải thông tin thuốc', 'danger');
    }
}

async function deleteDrug(id) {
    try {
        await axios.delete(`/api/drugs/${id}/`);
        showToast('Đã xóa thuốc', 'success');
        loadDrugs();
    } catch (e) {
        if (e.response?.status === 403) {
            showToast('Bạn không có quyền xóa thuốc', 'danger');
        } else {
            showToast('Xóa thất bại', 'danger');
        }
    }
}

function formatCurrency(v) {
    if (v === null || v === undefined || v === '') return '-';
    try { return Number(v).toLocaleString('vi-VN'); } catch { return String(v); }
}

// Submit edit form
document.addEventListener('submit', async function(e) {
    if (e.target && e.target.id === 'edit-drug-form') {
        e.preventDefault();
        const id = e.target.dataset.drugId;
        if (!id) return;
        const payload = collectEditDrugPayload();
        // disable button during submit
        toggleUpdateSubmit(false);
        try {
            await axios.patch(`/api/drugs/${id}/`, payload);
            const modalEl = document.getElementById('editDrugModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            showToast('Cập nhật thuốc thành công', 'success');
            loadDrugs();
        } catch (error) {
            if (error.response?.status === 403) {
                showToast('Bạn không có quyền sửa thuốc', 'danger');
            } else {
                showToast('Không thể cập nhật thuốc', 'danger');
            }
        } finally {
            toggleUpdateSubmit(true);
        }
    }
});

function collectEditDrugPayload() {
    const val = id => document.getElementById(id)?.value?.trim() || '';
    const num = id => Number(document.getElementById(id)?.value || 0);
    return {
        code: val('ed-code'), name: val('ed-name'), generic_name: val('ed-generic_name'), brand_name: val('ed-brand_name') || '',
        category: val('ed-category'), dosage_form: val('ed-dosage_form'), strength: val('ed-strength'), unit: val('ed-unit'),
        indication: document.getElementById('ed-indication')?.value?.trim() || '',
        unit_price: num('ed-unit_price'), insurance_price: (document.getElementById('ed-insurance_price')?.value ? num('ed-insurance_price') : null),
        current_stock: num('ed-current_stock'), minimum_stock: num('ed-minimum_stock'), maximum_stock: num('ed-maximum_stock'),
        manufacturer: val('ed-manufacturer'), country_of_origin: val('ed-country_of_origin'), is_active: document.getElementById('ed-is_active')?.checked || false
    };
}

// Helpers to load categories/enums to edit form if not filled
async function loadCategoriesTo(selectId) {
    try {
        const res = await axios.get('/api/drug-categories/');
        const select = document.getElementById(selectId);
        const data = toResultsArray(res.data);
        select.innerHTML = '';
        if (!data || data.length === 0) {
            const ph = document.createElement('option');
            ph.value = '';
            ph.textContent = 'Chưa có nhóm thuốc - vui lòng tạo trước';
            select.appendChild(ph);
            select.disabled = true;
            toggleUpdateSubmit(false);
        } else {
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id; opt.textContent = `${c.name}`;
                select.appendChild(opt);
            });
            select.disabled = false;
            toggleUpdateSubmit(true);
        }
    } catch (e) {}
}

function loadEnumsTo(dosageId, unitId) {
    const dosageSelect = document.getElementById(dosageId);
    const unitSelect = document.getElementById(unitId);
    if (dosageSelect && dosageSelect.options.length === 0) {
        const dosage = [['TABLET','Viên nén'],['CAPSULE','Viên nang'],['SYRUP','Siro'],['INJECTION','Tiêm'],['CREAM','Kem bôi'],['OINTMENT','Thuốc mỡ'],['DROPS','Nhỏ'],['SPRAY','Xịt'],['POWDER','Bột'],['SUPPOSITORY','Viên đặt']];
        dosage.forEach(([v,t]) => { const o=document.createElement('option'); o.value=v; o.textContent=t; dosageSelect.appendChild(o); });
    }
    if (unitSelect && unitSelect.options.length === 0) {
        const units = [['TABLET','Viên'],['CAPSULE','Viên nang'],['BOTTLE','Chai'],['BOX','Hộp'],['TUBE','Tuýp'],['VIAL','Lọ'],['AMPOULE','Ống'],['SACHET','Gói'],['ML','ml'],['MG','mg'],['G','g']];
        units.forEach(([v,t]) => { const o=document.createElement('option'); o.value=v; o.textContent=t; unitSelect.appendChild(o); });
    }
}

// Utilities UI state
function setEditLoading(isLoading) {
    const spinner = document.getElementById('ed-loading');
    if (spinner) spinner.style.display = isLoading ? 'block' : 'none';
}
function setEditError(message) {
    const err = document.getElementById('ed-error');
    if (!err) return;
    if (message) {
        err.textContent = message;
        err.classList.remove('d-none');
    } else {
        err.textContent = '';
        err.classList.add('d-none');
    }
}
function toggleAddSubmit(enabled) {
    const btn = document.getElementById('save-drug-btn');
    if (btn) btn.disabled = !enabled;
}
function toggleUpdateSubmit(enabled) {
    const btn = document.getElementById('update-drug-btn');
    if (btn) btn.disabled = !enabled;
}
function evaluateUpdateButtonState() {
    try {
        const baseline = window._editDrugBaseline || {};
        const current = collectEditDrugPayload();
        const changed = Object.keys(current).some(k => String(current[k]) !== String(baseline[k]));
        toggleUpdateSubmit(changed);
    } catch (_) {}
}
async function ensureEditCategories() {
    const sel = document.getElementById('ed-category');
    if (!sel || sel.options.length > 0) return;
    await loadCategoriesTo('ed-category');
}


