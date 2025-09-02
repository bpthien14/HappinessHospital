let rxPage = 1;
let rxTotal = 1;
let rxSearchTimeout; // Global timeout cho realtime search

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function(){
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initRx();
    } else {
        window.addEventListener('axiosInterceptorsReady', () => {
            initRx();
        }, { once: true });
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initRx();
            }
        }, 1500);
    }
});

function initRx(){
    if (!HospitalApp.checkAuth()) {
        location.href = '/login/';
        return;
    }
    bindRxEvents();
    loadPrescriptions();
}

function bindRxEvents(){
    const form = document.getElementById('filter-form');
    if (form) form.addEventListener('submit', function(e){ e.preventDefault(); rxPage=1; loadPrescriptions(); });
    
    // Realtime search - debounce để tránh quá nhiều request
    let searchTimeout; // Local timeout variable
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                rxPage = 1;
                loadPrescriptions();
            }, 500); // 500ms delay
        });
        
        // Enter key support
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                rxPage = 1;
                loadPrescriptions();
            }
        });
    }
    
    // Realtime filter cho dropdown
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            rxPage = 1;
            loadPrescriptions();
        });
    }
}



function buildParams(){
    const params = new URLSearchParams({ page: rxPage, page_size: 10 });
    
    // Search query - tìm theo số đơn, tên bệnh nhân, mã BN, SĐT, tên bác sĩ
    const searchQuery = (document.getElementById('search-input')?.value || '').trim();
    if (searchQuery) {
        params.append('search', searchQuery);
    }
    
    // Lọc theo dispensing status
    const statusFilter = (document.getElementById('status-filter')?.value || '').toUpperCase();
    if (statusFilter) {
        params.append('dispensing_status', statusFilter);
    }
    
    return params;
}

async function loadPrescriptions(){
    try {
        const params = buildParams();
        const res = await axios.get(`/api/prescriptions/?${params}`);
        const data = res.data || {};
        let results = data.results || [];
        
        // Lọc bỏ chỉ những đơn thuốc DRAFT (chưa hoàn thành)
        results = results.filter(p => {
            const status = (p.status || '').toUpperCase();
            return status !== 'DRAFT'; // Hiển thị tất cả trừ DRAFT
        });
        
        renderPrescriptions(results);
        updateRxPagination(data);
    } catch (e) {
        console.error('Error loading prescriptions:', e);
        // Hiển thị lỗi trong UI thay vì alert
        const container = document.getElementById('prescription-list');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Không thể tải danh sách đơn thuốc. Vui lòng thử lại.
                </div>
            `;
        }
    }
}

function renderPrescriptions(items){
    const tbody = document.getElementById('prescriptions-tbody');
    tbody.innerHTML='';
    items.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.prescription_number || '-'}</td>
            <td>${p.patient_code || '-'}</td>
            <td>${p.patient_name || '-'}</td>
            <td>${p.doctor_name || '-'}</td>
            <td><span class="badge ${statusBadge(p.dispensing_status || 'UNPAID')}">${p.dispensing_status_display || 'Chưa thanh toán'}</span></td>
            <td><span class="badge bg-light text-dark">${p.items_count ?? (p.items ? p.items.length : '-')}</span></td>
            <td>${formatCurrency(p.total_amount)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="openDispenseModal('${p.id}')"><i class="fas fa-pills"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function statusBadge(status){
    const s = String(status||'').toUpperCase();
    if (s==='UNPAID') return 'bg-danger';
    if (s==='PENDING') return 'bg-secondary';
    if (s==='PREPARED') return 'bg-primary';
    if (s==='DISPENSED') return 'bg-success';
    if (s==='CANCELLED') return 'bg-dark';
    return 'bg-light text-dark';
}

function mapRxToDispense(rxStatus){
    // Deprecated - sử dụng dispensing_status trực tiếp từ API
    const s = String(rxStatus||'').toUpperCase();
    if (s==='ACTIVE') return 'PENDING';
    if (s==='FULLY_DISPENSED') return 'DISPENSED';
    if (s==='PARTIALLY_DISPENSED') return 'PREPARED';
    if (s==='CANCELLED') return 'CANCELLED';
    return 'PENDING';
}

function toDispenseVi(status){
    const s = String(status||'').toUpperCase();
    if (s==='UNPAID') return 'Chưa thanh toán';
    if (s==='PENDING') return 'Chờ cấp thuốc';
    if (s==='PREPARED') return 'Đã chuẩn bị';
    if (s==='DISPENSED') return 'Đã cấp thuốc';
    if (s==='CANCELLED') return 'Đã hủy';
    return status;
}

function formatCurrency(v){
    if (v===null || v===undefined) return '-';
    try { return Number(v).toLocaleString('vi-VN'); } catch { return String(v); }
}

function updateRxPagination(data){
    rxTotal = Math.ceil((data.count || 0) / 10);
    const pg = document.getElementById('pg');
    pg.innerHTML='';
    const prev = document.createElement('li'); prev.className=`page-item ${rxPage===1?'disabled':''}`;
    prev.innerHTML = `<a class="page-link" href="#" onclick="changeRxPage(${rxPage-1})">Trước</a>`; pg.appendChild(prev);
    for(let i=Math.max(1, rxPage-2); i<=Math.min(rxTotal, rxPage+2); i++){
        const li=document.createElement('li'); li.className=`page-item ${i===rxPage?'active':''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="changeRxPage(${i})">${i}</a>`; pg.appendChild(li);
    }
    const next = document.createElement('li'); next.className=`page-item ${rxPage===rxTotal?'disabled':''}`;
    next.innerHTML = `<a class="page-link" href="#" onclick="changeRxPage(${rxPage+1})">Sau</a>`; pg.appendChild(next);
}

function changeRxPage(p){ if (p>=1 && p<=rxTotal){ rxPage=p; loadPrescriptions(); } }

async function openDispenseModal(id){
    // Load prescription detail then list items to allow prepare/dispense
    const modal = new bootstrap.Modal(document.getElementById('dispenseModal'));
    setDpError(''); setDpLoading(true); document.getElementById('dp-content').classList.add('d-none');
    
    try {
        const res = await axios.get(`/api/prescriptions/${id}/`);
        const p = res.data;
        window.__currentPrescription__ = p;
        
        const modalTitleEl = document.querySelector('#dispenseModal .modal-title');
        if (modalTitleEl) {
            modalTitleEl.textContent = `Chi tiết đơn thuốc #${p.prescription_number}`;
        }
        
        // Patient info - enhanced with full data
        document.getElementById('dp-patient').textContent = p.patient?.full_name || p.patient_name || '-';
        document.getElementById('dp-phone').textContent = p.patient?.phone_number || p.patient_phone || '-';
        
        const genderEl = document.getElementById('dp-gender');
        if (genderEl) {
            const g = (p.patient?.gender || '').toUpperCase();
            genderEl.textContent = g === 'M' ? 'Nam' : g === 'F' ? 'Nữ' : g === 'O' ? 'Khác' : '-';
        }
        
        const addrEl = document.getElementById('dp-address');
        if (addrEl) {
            // Sử dụng full_address property từ Patient model hoặc ghép từ các field riêng lẻ
            let fullAddr = p.patient?.full_address || '';
            if (!fullAddr && p.patient) {
                fullAddr = '';
                if (p.patient.address) fullAddr += p.patient.address;
                if (p.patient.ward) fullAddr += (fullAddr ? ', ' : '') + p.patient.ward;
                if (p.patient.province) fullAddr += (fullAddr ? ', ' : '') + p.patient.province;
            }
            addrEl.textContent = fullAddr || '-';
        }
        
        document.getElementById('dp-doctor').textContent = p.doctor_name || '-';
        document.getElementById('dp-status').textContent = p.dispensing_status_display || 'Chưa thanh toán';
        document.getElementById('dp-status').className = `badge ${statusBadge(p.dispensing_status || 'UNPAID')}`;
        document.getElementById('dp-total').textContent = formatCurrency(p.total_amount);
        
        const tbody = document.getElementById('dp-items');
        tbody.innerHTML='';
        (p.items || []).forEach(it => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td class="rx-name">
                    <div class="fw-semibold">${it.drug_name}</div>
                    <div class="text-muted small">${it.instructions || '-'}</div>
                </td>
                <td style="text-align:center; vertical-align:middle;">${it.quantity || 0}</td>
                <td style="text-align:center; white-space:nowrap; vertical-align:middle;">${formatCurrency(it.unit_price)}</td>
                <td style="text-align:center; white-space:nowrap; vertical-align:middle;">${formatCurrency(it.total_price)}</td>
            `;
            tbody.appendChild(tr);
        });
        
        // Xử lý nút chuẩn bị và cấp phát dựa trên dispensing_status mới
        const prepareBtn = document.getElementById('dp-prepare-btn');
        const dispenseBtn = document.getElementById('dp-dispense-btn');
        const dispensingStatus = p.dispensing_status || 'UNPAID';
        const allowed = canDispense();
        
        if (prepareBtn) {
            const canPrepare = dispensingStatus === 'PENDING' && allowed;
            prepareBtn.style.display = canPrepare ? 'inline-block' : 'none';
            if (canPrepare) {
                prepareBtn.onclick = () => handlePreparePrescription(p.id);
                prepareBtn.setAttribute('data-prescription-id', p.id);
            }
        }
        
        if (dispenseBtn) {
            const canDispenseNow = dispensingStatus === 'PREPARED' && allowed;
            dispenseBtn.style.display = canDispenseNow ? 'inline-block' : 'none';
            if (canDispenseNow) {
                dispenseBtn.onclick = () => handleDispensePrescription(p.id);
                dispenseBtn.setAttribute('data-prescription-id', p.id);
            }
        }
        
        setDpLoading(false); 
        document.getElementById('dp-content').classList.remove('d-none');
        modal.show();
    } catch (e){
        setDpLoading(false); 
        setDpError('Không thể tải chi tiết đơn thuốc');
        try { modal.show(); } catch(_){}
    }
}

// Permission functions
function isAdminUser(){
    try {
        const roles = Array.isArray(currentUser?.roles) ? currentUser.roles : [];
        return currentUser?.user_type === 'ADMIN' || roles.includes('ADMIN') || roles.includes('Admin');
    } catch(e){ return false; }
}

function canDispense(){
    try {
        // ADMIN có quyền PRESCRIPTION:APPROVE theo role_permissions, có thể cấp phát thuốc
        if (isAdminUser()) return true;
        if (typeof isPharmacistUser === 'function' && isPharmacistUser()) return true;
        return false;
    } catch(e){ return false; }
}

// Chuẩn bị thuốc - chuyển từ PENDING sang PREPARED
async function handlePreparePrescription(prescriptionId){
    // Hiển thị modal xác nhận
    const modal = new bootstrap.Modal(document.getElementById('confirmPrepareModal'));
    modal.show();
    
    // Gán prescription ID vào nút confirm
    const confirmBtn = document.getElementById('confirmPrepareBtn');
    confirmBtn.onclick = () => confirmPreparePrescription(prescriptionId, modal);
}

async function confirmPreparePrescription(prescriptionId, modal) {
    const confirmBtn = document.getElementById('confirmPrepareBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang xử lý...';
    
    try {
        const response = await axios.post(`/api/prescriptions/${prescriptionId}/mark_prepared/`);
        
        if (response.status === 200) {
            // Hiển thị thông báo thành công trong UI
            showSuccessMessage('Đã đánh dấu thuốc đã chuẩn bị!');
            try { 
                bootstrap.Modal.getInstance(document.getElementById('dispenseModal'))?.hide(); 
            } catch(_){}
            modal.hide();
            loadPrescriptions();
        }
    } catch (e) {
        console.error('Error preparing prescription:', e);
        const errorMsg = e.response?.data?.error || 'Không thể đánh dấu thuốc đã chuẩn bị';
        showErrorMessage(errorMsg);
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-clipboard-check me-2"></i>Xác nhận chuẩn bị';
    }
}

// Cấp phát thuốc - chuyển từ PREPARED sang DISPENSED
async function handleDispensePrescription(prescriptionId){
    // Hiển thị modal xác nhận
    const modal = new bootstrap.Modal(document.getElementById('confirmDispenseModal'));
    modal.show();
    
    // Gán prescription ID vào nút confirm
    const confirmBtn = document.getElementById('confirmDispenseBtn');
    confirmBtn.onclick = () => confirmDispensePrescription(prescriptionId, modal);
}

async function confirmDispensePrescription(prescriptionId, modal) {
    const confirmBtn = document.getElementById('confirmDispenseBtn');
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Đang xử lý...';
    
    const btn = document.getElementById('dp-dispense-btn');
    if (btn){ 
        btn.disabled = true; 
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Đang xử lý...'; 
    }
    
    try {
        const response = await axios.post(`/api/prescriptions/${prescriptionId}/mark_dispensed/`);
        
        if (response.status === 200) {
            // Hiển thị thông báo thành công trong UI
            showSuccessMessage('Đã cấp thuốc thành công!');
            try { 
                bootstrap.Modal.getInstance(document.getElementById('dispenseModal'))?.hide(); 
            } catch(_){}
            modal.hide();
            loadPrescriptions();
        }
    } catch (e) {
        console.error('Error dispensing prescription:', e);
        const errorMsg = e.response?.data?.error || 'Không thể cấp thuốc';
        showErrorMessage(errorMsg);
        
        if (btn){ 
            btn.disabled = false; 
            btn.innerHTML = '<i class="fas fa-pills me-2"></i>Cấp thuốc cho bệnh nhân'; 
        }
    } finally {
        confirmBtn.disabled = false;
        confirmBtn.innerHTML = '<i class="fas fa-hand-holding-medical me-2"></i>Xác nhận cấp thuốc';
    }
}

// Utility functions
function setDpLoading(b){
    const el = document.getElementById('dp-loading'); 
    if (el) el.style.display = b ? 'block' : 'none';
}

// UI notification functions - không dùng browser alerts
function showSuccessMessage(message) {
    createToast('success', 'Thành công', message);
}

function showErrorMessage(message) {
    createToast('danger', 'Lỗi', message);
}

function createToast(type, title, message) {
    // Tìm hoặc tạo toast container
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    // Tạo toast element
    const toastId = 'toast-' + Date.now();
    const iconClass = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle';
    const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
    
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white">
                <i class="fas ${iconClass} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    // Hiển thị toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 4000
    });
    toast.show();
    
    // Tự động xóa toast sau khi ẩn
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function setDpError(msg){
    const el = document.getElementById('dp-error'); 
    if (!el) return;
    if (msg){ 
        el.textContent = msg; 
        el.classList.remove('d-none'); 
    } else { 
        el.textContent=''; 
        el.classList.add('d-none'); 
    }
}

function formatDate(s){ 
    try { 
        return new Date(s).toLocaleString('vi-VN'); 
    } catch(_){ 
        return s || '-'; 
    } 
}