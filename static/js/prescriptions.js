let rxPage = 1;
let rxTotal = 1;

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
    const btn = document.getElementById('btn-refresh');
    if (btn) btn.addEventListener('click', function(){ loadPrescriptions(); });
}

function buildParams(){
    const params = new URLSearchParams({ page: rxPage, page_size: 10 });
    const s = document.getElementById('status-filter').value;
    if (s) params.append('status', s); // mapped to dispensing status via backend filtering if available
    // optional date range (the API supports extra filters via custom endpoint; fallback to base list if not)
    return params;
}

async function loadPrescriptions(){
    try {
        const params = buildParams();
        const res = await axios.get(`/api/prescriptions/?${params}`);
        const data = res.data || {};
        renderPrescriptions(data.results || []);
        updateRxPagination(data);
    } catch (e) {
        console.error('Error loading prescriptions:', e);
        HospitalApp.showAlert('Không thể tải danh sách đơn thuốc', 'danger');
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
            <td><span class="badge ${statusBadge(mapRxToDispense(p.status))}">${toDispenseVi(mapRxToDispense(p.status))}</span></td>
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
    if (s==='PENDING') return 'bg-secondary';
    if (s==='PREPARED') return 'bg-primary';
    if (s==='DISPENSED') return 'bg-success';
    if (s==='RETURNED') return 'bg-warning text-dark';
    if (s==='CANCELLED') return 'bg-dark';
    return 'bg-light text-dark';
}

function mapRxToDispense(rxStatus){
    const s = String(rxStatus||'').toUpperCase();
    if (s==='ACTIVE') return 'PENDING';
    if (s==='FULLY_DISPENSED') return 'DISPENSED';
    if (s==='PARTIALLY_DISPENSED') return 'PREPARED';
    if (s==='CANCELLED') return 'CANCELLED';
    return 'PENDING';
}

function toDispenseVi(status){
    const s = String(status||'').toUpperCase();
    if (s==='PENDING') return 'Chờ cấp thuốc';
    if (s==='PREPARED') return 'Đã soạn thuốc';
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
        const modalTitleEl = document.querySelector('#dispenseModal .modal-title');
        if (modalTitleEl) {
            modalTitleEl.textContent = `Chi tiết đơn thuốc #${p.prescription_number}`;
        }
        document.getElementById('dp-patient').textContent = p.patient_name;
        document.getElementById('dp-phone').textContent = p.patient_phone || '-';
        document.getElementById('dp-address').textContent = p.patient_address || '-';
        document.getElementById('dp-doctor').textContent = p.doctor_name || '-';
        document.getElementById('dp-status').textContent = toDispenseVi(mapRxToDispense(p.status));
        document.getElementById('dp-status').className = `badge ${statusBadge(mapRxToDispense(p.status))}`;
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
        setDpLoading(false); document.getElementById('dp-content').classList.remove('d-none');
        modal.show();
    } catch (e){
        setDpLoading(false); setDpError('Không thể tải chi tiết đơn thuốc');
        try { modal.show(); } catch(_){}
    }
}

async function dispenseItem(prescriptionItemId, btn){
    // Collect row data
    const tr = btn.closest('tr');
    const qty = Number(tr.querySelector('[data-dp-qty]').value || 0);
    const batch = tr.querySelector('[data-dp-batch]').value.trim();
    const exp = tr.querySelector('[data-dp-exp]').value;
    if (!qty || qty <= 0) { HospitalApp.showAlert('Số lượng cấp phải > 0', 'warning'); return; }
    try {
        btn.disabled = true;
        await axios.post('/api/dispensing/', {
            prescription_item: prescriptionItemId,
            quantity_dispensed: qty,
            batch_number: batch || '',
            expiry_date: exp
        });
        HospitalApp.showAlert('Cấp thuốc thành công', 'success');
        // reload current prescriptions list
        loadPrescriptions();
        // refresh current row UI quickly
        btn.classList.remove('btn-primary'); btn.classList.add('btn-success');
    } catch (e){
        HospitalApp.showAlert((e.response?.data?.error) || 'Không thể cấp thuốc', 'danger');
        btn.disabled = false;
    }
}

function setDpLoading(b){
    const el = document.getElementById('dp-loading'); if (el) el.style.display = b ? 'block' : 'none';
}
function setDpError(msg){
    const el = document.getElementById('dp-error'); if (!el) return;
    if (msg){ el.textContent = msg; el.classList.remove('d-none'); }
    else { el.textContent=''; el.classList.add('d-none'); }
}

function formatDate(s){ try { return new Date(s).toLocaleString('vi-VN'); } catch(_){ return s || '-'; } }

function buildParams(){
    const params = new URLSearchParams({ page: rxPage, page_size: 10 });
    const s = document.getElementById('status-filter').value;
    if (s) params.append('status', s); // mapped to dispensing status via backend filtering if available
    // optional date range (the API supports extra filters via custom endpoint; fallback to base list if not)
    return params;
}

async function loadPrescriptions(){
    try {
        const params = buildParams();
        const res = await axios.get(`/api/prescriptions/?${params}`);
        const data = res.data || {};
        renderPrescriptions(data.results || []);
        updateRxPagination(data);
    } catch (e) {
        console.error('Error loading prescriptions:', e);
        HospitalApp.showAlert('Không thể tải danh sách đơn thuốc', 'danger');
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
            <td><span class="badge ${statusBadge(mapRxToDispense(p.status))}">${toDispenseVi(mapRxToDispense(p.status))}</span></td>
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
    if (s==='PENDING') return 'bg-secondary';
    if (s==='PREPARED') return 'bg-primary';
    if (s==='DISPENSED') return 'bg-success';
    if (s==='RETURNED') return 'bg-warning text-dark';
    if (s==='CANCELLED') return 'bg-dark';
    return 'bg-light text-dark';
}

function mapRxToDispense(rxStatus){
    const s = String(rxStatus||'').toUpperCase();
    if (s==='ACTIVE') return 'PENDING';
    if (s==='FULLY_DISPENSED') return 'DISPENSED';
    if (s==='PARTIALLY_DISPENSED') return 'PREPARED';
    if (s==='CANCELLED') return 'CANCELLED';
    return 'PENDING';
}

function toDispenseVi(status){
    const s = String(status||'').toUpperCase();
    if (s==='PENDING') return 'Chờ cấp thuốc';
    if (s==='PREPARED') return 'Đã soạn thuốc';
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
        const modalTitleEl = document.querySelector('#dispenseModal .modal-title');
        if (modalTitleEl) {
            modalTitleEl.textContent = `Chi tiết đơn thuốc #${p.prescription_number}`;
        }
        document.getElementById('dp-patient').textContent = p.patient_name;
        document.getElementById('dp-phone').textContent = p.patient_phone || '-';
        document.getElementById('dp-address').textContent = p.patient_address || '-';
        document.getElementById('dp-doctor').textContent = p.doctor_name || '-';
        document.getElementById('dp-status').textContent = toDispenseVi(mapRxToDispense(p.status));
        document.getElementById('dp-status').className = `badge ${statusBadge(mapRxToDispense(p.status))}`;
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
        setDpLoading(false); document.getElementById('dp-content').classList.remove('d-none');
        modal.show();
    } catch (e){
        setDpLoading(false); setDpError('Không thể tải chi tiết đơn thuốc');
        try { modal.show(); } catch(_){}
    }
}

async function dispenseItem(prescriptionItemId, btn){
    // Collect row data
    const tr = btn.closest('tr');
    const qty = Number(tr.querySelector('[data-dp-qty]').value || 0);
    const batch = tr.querySelector('[data-dp-batch]').value.trim();
    const exp = tr.querySelector('[data-dp-exp]').value;
    if (!qty || qty <= 0) { HospitalApp.showAlert('Số lượng cấp phải > 0', 'warning'); return; }
    try {
        btn.disabled = true;
        await axios.post('/api/dispensing/', {
            prescription_item: prescriptionItemId,
            quantity_dispensed: qty,
            batch_number: batch || '',
            expiry_date: exp
        });
        HospitalApp.showAlert('Cấp thuốc thành công', 'success');
        // reload current prescriptions list
        loadPrescriptions();
        // refresh current row UI quickly
        btn.classList.remove('btn-primary'); btn.classList.add('btn-success');
    } catch (e){
        HospitalApp.showAlert((e.response?.data?.error) || 'Không thể cấp thuốc', 'danger');
        btn.disabled = false;
    }
}

function setDpLoading(b){
    const el = document.getElementById('dp-loading'); if (el) el.style.display = b ? 'block' : 'none';
}
function setDpError(msg){
    const el = document.getElementById('dp-error'); if (!el) return;
    if (msg){ el.textContent = msg; el.classList.remove('d-none'); }
    else { el.textContent=''; el.classList.add('d-none'); }
}

function formatDate(s){ try { return new Date(s).toLocaleString('vi-VN'); } catch(_){ return s || '-'; } }