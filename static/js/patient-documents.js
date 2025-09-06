/**
 * Patient Documents Management JavaScript
 * Handles upload, view, edit, and delete operations for patient documents
 */

let currentDocuments = [];
let currentPage = 1;
const pageSize = 10;
let totalPages = 1;
let patients = [];
let selectedDocuments = new Set(); // Track selected documents

// Document type mapping
const DOCUMENT_TYPES = {
    'ID_CARD': 'CCCD/CMND',
    'INSURANCE_CARD': 'Thẻ BHYT', 
    'MEDICAL_REPORT': 'Báo cáo y tế',
    'LAB_RESULT': 'Kết quả xét nghiệm',
    'PRESCRIPTION': 'Đơn thuốc',
    'DISCHARGE_SUMMARY': 'Tóm tắt xuất viện',
    'OTHER': 'Khác'
};

// Initialize page
$(document).ready(function() {
    console.log('Patient Documents: DOM ready, initializing...');
    initializeEventHandlers();
    loadPatients();
    loadDocuments();
});

// Also try with window.onload in case jQuery isn't available
window.addEventListener('DOMContentLoaded', function() {
    console.log('Patient Documents: DOMContentLoaded, checking jQuery...');
    if (typeof $ === 'undefined') {
        console.error('jQuery not loaded! Patient documents functionality will not work.');
        return;
    }
    
    // If jQuery is available but document.ready hasn't fired yet
    setTimeout(() => {
        if (currentDocuments.length === 0) {
            console.log('Patient Documents: Force initializing...');
            initializeEventHandlers();
            loadPatients();
            loadDocuments();
        }
    }, 1000);
});

function initializeEventHandlers() {
    // Search and filter handlers
    $('#searchInput').on('input', debounce(loadDocuments, 500));
    $('#patientFilter, #documentTypeFilter').on('change', loadDocuments);
    
    // File upload handlers
    setupFileUpload();
    
    // Form handlers
    setupFormHandlers();
}

function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('documentFile');
    
    // Click to select file
    uploadArea.addEventListener('click', () => fileInput.click());
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });
    
    // File selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    // Validate file size (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showAlert('File quá lớn! Kích thước tối đa là 10MB.', 'error');
        return;
    }
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'image/jpeg', 'image/jpg', 'image/png'];
    
    if (!allowedTypes.includes(file.type)) {
        showAlert('Định dạng file không được hỗ trợ!', 'error');
        return;
    }
    
    // Show file preview
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('filePreview').style.display = 'block';
    
    // Auto-fill title if empty
    if (!document.getElementById('documentTitle').value) {
        const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
        document.getElementById('documentTitle').value = nameWithoutExt;
    }
}

function removeFile() {
    document.getElementById('documentFile').value = '';
    document.getElementById('filePreview').style.display = 'none';
}

function setupFormHandlers() {
    // Reset forms when modals are hidden
    $('#uploadDocumentModal').on('hidden.bs.modal', function () {
        document.getElementById('uploadDocumentForm').reset();
        removeFile();
    });
    
    $('#editDocumentModal').on('hidden.bs.modal', function () {
        document.getElementById('editDocumentForm').reset();
    });
}

async function loadPatients() {
    try {
        const response = await axios.get('/api/patients/');
        patients = response.data.results || response.data;
        
        // Populate patient selectors
        const patientSelectors = ['#patientFilter', '#documentPatient'];
        patientSelectors.forEach(selector => {
            const select = document.querySelector(selector);
            
            // Clear existing options (except first one for filter)
            if (selector === '#patientFilter') {
                select.innerHTML = '<option value="">Tất cả bệnh nhân</option>';
            } else {
                select.innerHTML = '<option value="">Chọn bệnh nhân</option>';
            }
            
            // Add patient options
            patients.forEach(patient => {
                const option = document.createElement('option');
                option.value = patient.id;
                option.textContent = `${patient.patient_code} - ${patient.full_name}`;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Error loading patients:', error);
        showAlert('Không thể tải danh sách bệnh nhân', 'error');
    }
}

async function loadDocuments() {
    console.log('loadDocuments: Starting...'); 
    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize
        });
        
        // Add filters
        const patientFilter = document.getElementById('patientFilter').value;
        const typeFilter = document.getElementById('documentTypeFilter').value;
        const searchQuery = document.getElementById('searchInput').value.trim();
        
        if (patientFilter) params.append('patient', patientFilter);
        if (typeFilter) params.append('document_type', typeFilter);
        if (searchQuery) params.append('search', searchQuery);
        
        console.log('loadDocuments: Making API call to /api/patient-documents/', params.toString());
        const response = await axios.get(`/api/patient-documents/?${params.toString()}`);
        console.log('loadDocuments: API response:', response.data);
        const data = response.data;
        
        currentDocuments = data.results || data;
        totalPages = Math.ceil((data.count || currentDocuments.length) / pageSize);
        
        console.log('loadDocuments: Loaded', currentDocuments.length, 'documents');
        renderDocuments();
        renderPagination();
    } catch (error) {
        console.error('Error loading documents:', error);
        showAlert('Không thể tải danh sách tài liệu', 'error');
        
        // Show empty state
        document.getElementById('documentsContainer').innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                <h5>Không thể tải danh sách tài liệu</h5>
                <p class="text-muted">Vui lòng thử lại sau</p>
                <button class="btn btn-primary" onclick="loadDocuments()">
                    <i class="fas fa-refresh"></i> Tải lại
                </button>
            </div>
        `;
    }
}

function renderDocuments() {
    const container = document.getElementById('documentsContainer');
    
    if (currentDocuments.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-file-medical fa-3x text-muted mb-3"></i>
                <h5>Không có tài liệu nào</h5>
                <p class="text-muted">Chưa có tài liệu nào được tải lên</p>
                <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#uploadDocumentModal">
                    <i class="fas fa-plus"></i> Tải lên tài liệu đầu tiên
                </button>
            </div>
        `;
        
        // Update count and hide bulk actions
        document.getElementById('documentsCount').textContent = 'Không có tài liệu nào';
        document.getElementById('bulkActions').style.display = 'none';
        return;
    }
    
    // Update count
    document.getElementById('documentsCount').textContent = `Hiển thị ${currentDocuments.length} tài liệu`;
    
    const documentsHtml = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="selectAll" onchange="toggleSelectAll()">
                <label class="form-check-label" for="selectAll">
                    Chọn tất cả
                </label>
            </div>
        </div>
    ` + currentDocuments.map(doc => `
        <div class="document-card" data-document-id="${doc.id}">
            <div class="row">
                <div class="col-auto">
                    <div class="form-check">
                        <input class="form-check-input document-checkbox" type="checkbox" 
                               value="${doc.id}" onchange="toggleDocumentSelection('${doc.id}')">
                    </div>
                </div>
                <div class="col-md-7">
                    <div class="d-flex align-items-start">
                        <div class="document-icon me-3">
                            ${getDocumentIcon(doc.file)}
                        </div>
                        <div class="flex-grow-1">
                            <div class="d-flex align-items-center mb-2">
                                <h6 class="mb-0 me-2">${escapeHtml(doc.title)}</h6>
                                <span class="badge bg-primary document-type-badge">
                                    ${DOCUMENT_TYPES[doc.document_type] || doc.document_type}
                                </span>
                            </div>
                            
                            <p class="text-muted mb-2">${getPatientName(doc.patient)}</p>
                            
                            ${doc.description ? `<p class="mb-2">${escapeHtml(doc.description)}</p>` : ''}
                            
                            <div class="file-info">
                                <i class="fas fa-user"></i> ${escapeHtml(doc.uploaded_by_name || 'N/A')} • 
                                <i class="fas fa-calendar"></i> ${formatDateTime(doc.uploaded_at)} •
                                <i class="fas fa-file"></i> ${formatFileSize(doc.file_size)}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="d-flex justify-content-end">
                        <div class="btn-group" role="group">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewDocument('${doc.id}')" title="Xem">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary" onclick="editDocument('${doc.id}')" title="Sửa">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="downloadDocument('${doc.id}')" title="Tải xuống">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDocument('${doc.id}')" title="Xóa">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = documentsHtml;
    
    // Update selection state
    updateSelectionUI();
}

function getDocumentIcon(fileUrl) {
    if (!fileUrl) return '<i class="fas fa-file fa-2x text-muted"></i>';
    
    const extension = fileUrl.split('.').pop().toLowerCase();
    
    switch (extension) {
        case 'pdf':
            return '<i class="fas fa-file-pdf fa-2x text-danger"></i>';
        case 'doc':
        case 'docx':
            return '<i class="fas fa-file-word fa-2x text-primary"></i>';
        case 'jpg':
        case 'jpeg':
        case 'png':
            return '<i class="fas fa-file-image fa-2x text-success"></i>';
        default:
            return '<i class="fas fa-file fa-2x text-muted"></i>';
    }
}

function getPatientName(patientId) {
    const patient = patients.find(p => p.id === patientId);
    return patient ? `${patient.patient_code} - ${patient.full_name}` : 'N/A';
}

function renderPagination() {
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let paginationHtml = '';
    
    // Previous button
    paginationHtml += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(1)">1</a></li>`;
        if (startPage > 2) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="changePage(${i})">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHtml += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
        paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="changePage(${totalPages})">${totalPages}</a></li>`;
    }
    
    // Next button
    paginationHtml += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="changePage(${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    pagination.innerHTML = paginationHtml;
}

function changePage(page) {
    if (page >= 1 && page <= totalPages && page !== currentPage) {
        currentPage = page;
        loadDocuments();
    }
}

async function uploadDocument() {
    const form = document.getElementById('uploadDocumentForm');
    const formData = new FormData();
    
    // Validate form
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const patient = document.getElementById('documentPatient').value;
    const documentType = document.getElementById('documentType').value;
    const title = document.getElementById('documentTitle').value.trim();
    const description = document.getElementById('documentDescription').value.trim();
    const file = document.getElementById('documentFile').files[0];
    
    // Validation
    if (!patient) {
        showAlert('Vui lòng chọn bệnh nhân', 'error');
        return;
    }
    
    if (!documentType) {
        showAlert('Vui lòng chọn loại tài liệu', 'error');
        return;
    }
    
    if (!title) {
        showAlert('Vui lòng nhập tiêu đề tài liệu', 'error');
        return;
    }
    
    if (!file) {
        showAlert('Vui lòng chọn file để tải lên', 'error');
        return;
    }
    
    // Additional file validation
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showAlert('File quá lớn! Kích thước tối đa là 10MB.', 'error');
        return;
    }
    
    const allowedTypes = [
        'application/pdf', 
        'application/msword', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'image/jpeg', 
        'image/jpg', 
        'image/png',
        'image/gif'
    ];
    
    if (!allowedTypes.includes(file.type)) {
        showAlert('Định dạng file không được hỗ trợ! Chỉ chấp nhận: PDF, DOC, DOCX, JPG, PNG, GIF', 'error');
        return;
    }
    
    // Prepare form data
    formData.append('patient', patient);
    formData.append('document_type', documentType);
    formData.append('title', title);
    if (description) {
        formData.append('description', description);
    }
    formData.append('file', file);
    
    try {
        showButtonLoading('#uploadDocumentModal .btn-primary', true);
        
        // Show upload progress
        showAlert('Đang tải lên tài liệu...', 'info');
        
        const response = await axios.post('/api/patient-documents/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                console.log('Upload progress:', percentCompleted + '%');
                
                // Update button text with progress
                const btn = document.querySelector('#uploadDocumentModal .btn-primary');
                if (btn) {
                    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Đang tải... ${percentCompleted}%`;
                }
            }
        });
        
        showAlert('Tải lên tài liệu thành công!', 'success');
        
        // Close modal and reload
        const modal = bootstrap.Modal.getInstance(document.getElementById('uploadDocumentModal'));
        modal.hide();
        
        currentPage = 1; // Reset to first page
        await loadDocuments();
        
    } catch (error) {
        console.error('Error uploading document:', error);
        
        let message = 'Không thể tải lên tài liệu';
        if (error.response?.status === 413) {
            message = 'File quá lớn! Vui lòng chọn file nhỏ hơn.';
        } else if (error.response?.status === 415) {
            message = 'Định dạng file không được hỗ trợ!';
        } else if (error.response?.data?.detail) {
            message = error.response.data.detail;
        } else if (error.response?.data?.error) {
            message = error.response.data.error;
        } else if (error.response?.data) {
            // Handle field-specific errors
            const errors = [];
            Object.keys(error.response.data).forEach(field => {
                if (Array.isArray(error.response.data[field])) {
                    errors.push(`${field}: ${error.response.data[field].join(', ')}`);
                } else {
                    errors.push(`${field}: ${error.response.data[field]}`);
                }
            });
            if (errors.length > 0) {
                message = errors.join('\n');
            }
        }
        
        showAlert(message, 'error');
    } finally {
        showButtonLoading('#uploadDocumentModal .btn-primary', false);
    }
}

async function viewDocument(documentId) {
    try {
        // Show loading state
        const modal = new bootstrap.Modal(document.getElementById('viewDocumentModal'));
        modal.show();
        
        const modalTitle = document.querySelector('#viewDocumentModal .modal-title');
        modalTitle.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Đang tải...`;
        
        const content = document.getElementById('documentViewContent');
        content.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Đang tải...</span>
                </div>
                <p class="mt-2">Đang tải thông tin tài liệu...</p>
            </div>
        `;
        
        const response = await axios.get(`/api/patient-documents/${documentId}/`);
        const document = response.data;
        
        modalTitle.innerHTML = `<i class="fas fa-eye"></i> ${escapeHtml(document.title)}`;
        
        // Check if it's an image
        const fileUrl = document.file_url || document.file;
        const extension = fileUrl.split('.').pop().toLowerCase();
        
        if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
            content.innerHTML = `
                <div class="text-center">
                    <div class="mb-3">
                        <img src="${fileUrl}" 
                             alt="${escapeHtml(document.title)}" 
                             class="document-preview img-fluid"
                             style="max-height: 500px; border: 1px solid #ddd; border-radius: 8px;"
                             onload="this.style.opacity=1"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='block'"
                             style="opacity: 0; transition: opacity 0.3s;">
                        <div style="display: none;" class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle"></i> Không thể tải ảnh
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <h6><i class="fas fa-info-circle"></i> Thông tin tài liệu:</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Bệnh nhân:</strong> ${getPatientName(document.patient)}</li>
                                <li><strong>Loại:</strong> ${DOCUMENT_TYPES[document.document_type] || document.document_type}</li>
                                <li><strong>Mô tả:</strong> ${escapeHtml(document.description) || '<em>Không có</em>'}</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Tải lên bởi:</strong> ${escapeHtml(document.uploaded_by_name || 'N/A')}</li>
                                <li><strong>Thời gian:</strong> ${formatDateTime(document.uploaded_at)}</li>
                                <li><strong>Kích thước:</strong> ${formatFileSize(document.file_size)}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        } else if (extension === 'pdf') {
            content.innerHTML = `
                <div class="text-center mb-3">
                    <div class="pdf-preview" style="border: 1px solid #ddd; border-radius: 8px; height: 500px; overflow: hidden;">
                        <iframe src="${fileUrl}" 
                                width="100%" 
                                height="100%" 
                                style="border: none;"
                                title="PDF Preview">
                            <p>Trình duyệt không hỗ trợ xem PDF. 
                               <a href="${fileUrl}" target="_blank">Click để tải xuống</a>
                            </p>
                        </iframe>
                    </div>
                </div>
                <div class="mt-3">
                    <h6><i class="fas fa-info-circle"></i> Thông tin tài liệu:</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Bệnh nhân:</strong> ${getPatientName(document.patient)}</li>
                                <li><strong>Loại:</strong> ${DOCUMENT_TYPES[document.document_type] || document.document_type}</li>
                                <li><strong>Mô tả:</strong> ${escapeHtml(document.description) || '<em>Không có</em>'}</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Tải lên bởi:</strong> ${escapeHtml(document.uploaded_by_name || 'N/A')}</li>
                                <li><strong>Thời gian:</strong> ${formatDateTime(document.uploaded_at)}</li>
                                <li><strong>Kích thước:</strong> ${formatFileSize(document.file_size)}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        } else {
            content.innerHTML = `
                <div class="text-center py-5">
                    <div class="mb-4">
                        ${getDocumentIcon(fileUrl)}
                    </div>
                    <h5 class="mt-3">${escapeHtml(document.title)}</h5>
                    <p class="text-muted">Không thể xem trước định dạng file này</p>
                    <div class="btn-group" role="group">
                        <button class="btn btn-primary" onclick="downloadDocument('${document.id}')">
                            <i class="fas fa-download"></i> Tải xuống để xem
                        </button>
                        <button class="btn btn-secondary" onclick="window.open('${fileUrl}', '_blank')">
                            <i class="fas fa-external-link-alt"></i> Mở trong tab mới
                        </button>
                    </div>
                </div>
                <div class="mt-3">
                    <h6><i class="fas fa-info-circle"></i> Thông tin tài liệu:</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Bệnh nhân:</strong> ${getPatientName(document.patient)}</li>
                                <li><strong>Loại:</strong> ${DOCUMENT_TYPES[document.document_type] || document.document_type}</li>
                                <li><strong>Mô tả:</strong> ${escapeHtml(document.description) || '<em>Không có</em>'}</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-unstyled">
                                <li><strong>Tải lên bởi:</strong> ${escapeHtml(document.uploaded_by_name || 'N/A')}</li>
                                <li><strong>Thời gian:</strong> ${formatDateTime(document.uploaded_at)}</li>
                                <li><strong>Kích thước:</strong> ${formatFileSize(document.file_size)}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Set download button
        const downloadBtn = document.getElementById('downloadDocumentBtn');
        downloadBtn.onclick = () => downloadDocument(documentId);
        
    } catch (error) {
        console.error('Error viewing document:', error);
        
        const modalTitle = document.querySelector('#viewDocumentModal .modal-title');
        modalTitle.innerHTML = `<i class="fas fa-exclamation-triangle text-danger"></i> Lỗi`;
        
        const content = document.getElementById('documentViewContent');
        content.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <h5>Không thể tải tài liệu</h5>
                <p class="text-muted">Có lỗi xảy ra khi tải thông tin tài liệu</p>
                <button class="btn btn-primary" onclick="viewDocument('${documentId}')">
                    <i class="fas fa-refresh"></i> Thử lại
                </button>
            </div>
        `;
        
        showAlert('Không thể xem tài liệu', 'error');
    }
}

async function editDocument(documentId) {
    try {
        const response = await axios.get(`/api/patient-documents/${documentId}/`);
        const document = response.data;
        
        // Populate form
        document.getElementById('editDocumentId').value = document.id;
        document.getElementById('editDocumentType').value = document.document_type;
        document.getElementById('editDocumentTitle').value = document.title;
        document.getElementById('editDocumentDescription').value = document.description || '';
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('editDocumentModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error loading document for edit:', error);
        showAlert('Không thể tải thông tin tài liệu', 'error');
    }
}

async function updateDocument() {
    const form = document.getElementById('editDocumentForm');
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    const documentId = document.getElementById('editDocumentId').value;
    const data = {
        document_type: document.getElementById('editDocumentType').value,
        title: document.getElementById('editDocumentTitle').value,
        description: document.getElementById('editDocumentDescription').value
    };
    
    try {
        showButtonLoading('#editDocumentModal .btn-primary', true);
        
        const response = await axios.patch(`/api/patient-documents/${documentId}/`, data);
        
        showAlert('Cập nhật tài liệu thành công!', 'success');
        
        // Close modal and reload
        const modal = bootstrap.Modal.getInstance(document.getElementById('editDocumentModal'));
        modal.hide();
        
        loadDocuments();
        
    } catch (error) {
        console.error('Error updating document:', error);
        
        let message = 'Không thể cập nhật tài liệu';
        if (error.response?.data?.detail) {
            message = error.response.data.detail;
        }
        
        showAlert(message, 'error');
    } finally {
        showButtonLoading('#editDocumentModal .btn-primary', false);
    }
}

async function deleteDocument(documentId) {
    try {
        // Get document info first for confirmation
        const response = await axios.get(`/api/patient-documents/${documentId}/`);
        const document = response.data;
        
        const patientName = getPatientName(document.patient);
        const docType = DOCUMENT_TYPES[document.document_type] || document.document_type;
        
        // Create detailed confirmation modal
        const confirmationHtml = `
            <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle"></i> Xác nhận xóa tài liệu
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning">
                                <i class="fas fa-warning"></i> 
                                <strong>Cảnh báo:</strong> Hành động này không thể hoàn tác!
                            </div>
                            
                            <p>Bạn có chắc muốn xóa tài liệu sau không?</p>
                            
                            <div class="card">
                                <div class="card-body">
                                    <h6 class="card-title">${escapeHtml(document.title)}</h6>
                                    <p class="card-text">
                                        <strong>Bệnh nhân:</strong> ${patientName}<br>
                                        <strong>Loại:</strong> ${docType}<br>
                                        <strong>Tải lên:</strong> ${formatDateTime(document.uploaded_at)}
                                    </p>
                                </div>
                            </div>
                            
                            <div class="mt-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="confirmDelete">
                                    <label class="form-check-label" for="confirmDelete">
                                        Tôi hiểu rằng tài liệu sẽ bị xóa vĩnh viễn
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                <i class="fas fa-times"></i> Hủy
                            </button>
                            <button type="button" class="btn btn-danger" id="confirmDeleteBtn" disabled>
                                <i class="fas fa-trash"></i> Xóa tài liệu
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('deleteConfirmModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add to body
        document.body.insertAdjacentHTML('beforeend', confirmationHtml);
        
        // Setup checkbox handler
        const checkbox = document.getElementById('confirmDelete');
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        
        checkbox.addEventListener('change', function() {
            deleteBtn.disabled = !this.checked;
        });
        
        // Setup delete handler
        deleteBtn.addEventListener('click', async function() {
            try {
                this.disabled = true;
                this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xóa...';
                
                await axios.delete(`/api/patient-documents/${documentId}/`);
                
                showAlert('Xóa tài liệu thành công!', 'success');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteConfirmModal'));
                modal.hide();
                
                // Reload documents
                await loadDocuments();
                
            } catch (error) {
                console.error('Error deleting document:', error);
                
                let message = 'Không thể xóa tài liệu';
                if (error.response?.status === 403) {
                    message = 'Bạn không có quyền xóa tài liệu này';
                } else if (error.response?.status === 404) {
                    message = 'Tài liệu không tồn tại';
                } else if (error.response?.data?.detail) {
                    message = error.response.data.detail;
                }
                
                showAlert(message, 'error');
                
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-trash"></i> Xóa tài liệu';
            }
        });
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
        modal.show();
        
        // Clean up when modal is hidden
        document.getElementById('deleteConfirmModal').addEventListener('hidden.bs.modal', function() {
            this.remove();
        });
        
    } catch (error) {
        console.error('Error loading document for delete:', error);
        
        // Fallback to simple confirm
        if (confirm('Bạn có chắc muốn xóa tài liệu này không? Hành động này không thể hoàn tác.')) {
            try {
                await axios.delete(`/api/patient-documents/${documentId}/`);
                showAlert('Xóa tài liệu thành công!', 'success');
                await loadDocuments();
            } catch (deleteError) {
                console.error('Error deleting document:', deleteError);
                showAlert('Không thể xóa tài liệu', 'error');
            }
        }
    }
}

async function downloadDocument(documentId) {
    try {
        const response = await axios.get(`/api/patient-documents/${documentId}/`);
        const document = response.data;
        
        // Create download link
        const link = document.createElement('a');
        link.href = document.file_url || document.file;
        link.download = document.title;
        link.target = '_blank';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        console.error('Error downloading document:', error);
        showAlert('Không thể tải xuống tài liệu', 'error');
    }
}

function clearFilters() {
    document.getElementById('patientFilter').value = '';
    document.getElementById('documentTypeFilter').value = '';
    document.getElementById('searchInput').value = '';
    currentPage = 1;
    loadDocuments();
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDateTime(dateTimeString) {
    if (!dateTimeString) return 'N/A';
    const date = new Date(dateTimeString);
    return date.toLocaleString('vi-VN');
}

function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showButtonLoading(selector, loading) {
    const button = document.querySelector(selector);
    if (!button) return;
    
    if (loading) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
    } else {
        button.disabled = false;
        // Restore original text based on context
        if (selector.includes('upload')) {
            button.innerHTML = '<i class="fas fa-upload"></i> Tải lên';
        } else if (selector.includes('edit')) {
            button.innerHTML = '<i class="fas fa-save"></i> Lưu thay đổi';
        }
    }
}

function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Bulk selection functions
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.document-checkbox');
    
    if (selectAll.checked) {
        // Select all
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            selectedDocuments.add(checkbox.value);
        });
    } else {
        // Deselect all
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        selectedDocuments.clear();
    }
    
    updateSelectionUI();
}

function toggleDocumentSelection(documentId) {
    if (selectedDocuments.has(documentId)) {
        selectedDocuments.delete(documentId);
    } else {
        selectedDocuments.add(documentId);
    }
    
    updateSelectionUI();
}

function updateSelectionUI() {
    const selectedCount = selectedDocuments.size;
    const totalCount = currentDocuments.length;
    
    // Update select all checkbox
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.checked = selectedCount === totalCount && totalCount > 0;
        selectAll.indeterminate = selectedCount > 0 && selectedCount < totalCount;
    }
    
    // Update bulk actions visibility
    const bulkActions = document.getElementById('bulkActions');
    const selectedCountSpan = document.getElementById('selectedCount');
    
    if (selectedCount > 0) {
        bulkActions.style.display = 'block';
        selectedCountSpan.textContent = selectedCount;
    } else {
        bulkActions.style.display = 'none';
    }
    
    // Update individual checkboxes
    document.querySelectorAll('.document-checkbox').forEach(checkbox => {
        checkbox.checked = selectedDocuments.has(checkbox.value);
    });
}

function clearSelection() {
    selectedDocuments.clear();
    updateSelectionUI();
}

async function bulkDeleteDocuments() {
    if (selectedDocuments.size === 0) {
        showAlert('Vui lòng chọn ít nhất một tài liệu để xóa', 'warning');
        return;
    }
    
    const selectedIds = Array.from(selectedDocuments);
    const selectedDocs = currentDocuments.filter(doc => selectedIds.includes(doc.id));
    
    // Create confirmation modal
    const confirmationHtml = `
        <div class="modal fade" id="bulkDeleteModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle"></i> Xác nhận xóa ${selectedDocuments.size} tài liệu
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <i class="fas fa-warning"></i> 
                            <strong>Cảnh báo:</strong> Hành động này không thể hoàn tác!
                        </div>
                        
                        <p>Bạn có chắc muốn xóa <strong>${selectedDocuments.size}</strong> tài liệu đã chọn không?</p>
                        
                        <div class="mb-3" style="max-height: 200px; overflow-y: auto;">
                            ${selectedDocs.map(doc => `
                                <div class="card mb-2">
                                    <div class="card-body py-2">
                                        <small>
                                            <strong>${escapeHtml(doc.title)}</strong><br>
                                            ${getPatientName(doc.patient)} - ${DOCUMENT_TYPES[doc.document_type]}
                                        </small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="confirmBulkDelete">
                            <label class="form-check-label" for="confirmBulkDelete">
                                Tôi hiểu rằng tất cả tài liệu đã chọn sẽ bị xóa vĩnh viễn
                            </label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times"></i> Hủy
                        </button>
                        <button type="button" class="btn btn-danger" id="confirmBulkDeleteBtn" disabled>
                            <i class="fas fa-trash"></i> Xóa ${selectedDocuments.size} tài liệu
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('bulkDeleteModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', confirmationHtml);
    
    // Setup handlers
    const checkbox = document.getElementById('confirmBulkDelete');
    const deleteBtn = document.getElementById('confirmBulkDeleteBtn');
    
    checkbox.addEventListener('change', function() {
        deleteBtn.disabled = !this.checked;
    });
    
    deleteBtn.addEventListener('click', async function() {
        try {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xóa...';
            
            // Delete documents one by one
            let deletedCount = 0;
            let errors = [];
            
            for (const docId of selectedIds) {
                try {
                    await axios.delete(`/api/patient-documents/${docId}/`);
                    deletedCount++;
                } catch (error) {
                    errors.push(docId);
                    console.error(`Error deleting document ${docId}:`, error);
                }
            }
            
            // Show results
            if (deletedCount > 0) {
                showAlert(`Đã xóa thành công ${deletedCount} tài liệu!`, 'success');
            }
            
            if (errors.length > 0) {
                showAlert(`Không thể xóa ${errors.length} tài liệu`, 'warning');
            }
            
            // Close modal and reload
            const modal = bootstrap.Modal.getInstance(document.getElementById('bulkDeleteModal'));
            modal.hide();
            
            clearSelection();
            await loadDocuments();
            
        } catch (error) {
            console.error('Bulk delete error:', error);
            showAlert('Có lỗi xảy ra khi xóa tài liệu', 'error');
            
            this.disabled = false;
            this.innerHTML = `<i class="fas fa-trash"></i> Xóa ${selectedDocuments.size} tài liệu`;
        }
    });
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('bulkDeleteModal'));
    modal.show();
    
    // Clean up
    document.getElementById('bulkDeleteModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

async function downloadSelectedDocuments() {
    if (selectedDocuments.size === 0) {
        showAlert('Vui lòng chọn ít nhất một tài liệu để tải xuống', 'warning');
        return;
    }
    
    const selectedIds = Array.from(selectedDocuments);
    const selectedDocs = currentDocuments.filter(doc => selectedIds.includes(doc.id));
    
    showAlert(`Đang tải xuống ${selectedDocuments.size} tài liệu...`, 'info');
    
    // Download documents one by one
    for (const doc of selectedDocs) {
        try {
            const link = document.createElement('a');
            link.href = doc.file_url || doc.file;
            link.download = doc.title;
            link.target = '_blank';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Small delay between downloads
            await new Promise(resolve => setTimeout(resolve, 500));
            
        } catch (error) {
            console.error(`Error downloading document ${doc.id}:`, error);
            showAlert(`Không thể tải xuống: ${doc.title}`, 'warning');
        }
    }
    
    showAlert(`Đã bắt đầu tải xuống ${selectedDocuments.size} tài liệu!`, 'success');
}

// Quick actions
async function refreshDocuments() {
    showAlert('Đang làm mới danh sách...', 'info');
    clearSelection();
    currentPage = 1;
    await loadDocuments();
    showAlert('Đã làm mới danh sách tài liệu!', 'success');
}

function exportDocumentsList() {
    if (currentDocuments.length === 0) {
        showAlert('Không có tài liệu nào để xuất', 'warning');
        return;
    }
    
    // Create CSV content
    const headers = ['Tiêu đề', 'Loại tài liệu', 'Bệnh nhân', 'Mô tả', 'Tải lên bởi', 'Thời gian', 'Kích thước'];
    const csvContent = [
        headers.join(','),
        ...currentDocuments.map(doc => [
            `"${(doc.title || '').replace(/"/g, '""')}"`,
            `"${DOCUMENT_TYPES[doc.document_type] || doc.document_type}"`,
            `"${getPatientName(doc.patient)}"`,
            `"${(doc.description || '').replace(/"/g, '""')}"`,
            `"${doc.uploaded_by_name || 'N/A'}"`,
            `"${formatDateTime(doc.uploaded_at)}"`,
            `"${formatFileSize(doc.file_size)}"`
        ].join(','))
    ].join('\n');
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `danh-sach-tai-lieu-${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showAlert('Đã xuất danh sách tài liệu!', 'success');
}

function showDocumentStats() {
    if (currentDocuments.length === 0) {
        showAlert('Không có dữ liệu để thống kê', 'warning');
        return;
    }
    
    // Calculate stats
    const stats = {
        total: currentDocuments.length,
        byType: {},
        totalSize: 0,
        uploadedThisMonth: 0
    };
    
    const thisMonth = new Date().getMonth();
    const thisYear = new Date().getFullYear();
    
    currentDocuments.forEach(doc => {
        // Count by type
        const type = doc.document_type;
        stats.byType[type] = (stats.byType[type] || 0) + 1;
        
        // Total size
        stats.totalSize += doc.file_size || 0;
        
        // This month uploads
        const uploadDate = new Date(doc.uploaded_at);
        if (uploadDate.getMonth() === thisMonth && uploadDate.getFullYear() === thisYear) {
            stats.uploadedThisMonth++;
        }
    });
    
    // Create stats modal
    const statsHtml = `
        <div class="modal fade" id="documentStatsModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-chart-bar"></i> Thống kê tài liệu
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card bg-primary text-white mb-3">
                                    <div class="card-body text-center">
                                        <h3>${stats.total}</h3>
                                        <p class="mb-0">Tổng số tài liệu</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card bg-success text-white mb-3">
                                    <div class="card-body text-center">
                                        <h3>${stats.uploadedThisMonth}</h3>
                                        <p class="mb-0">Tải lên tháng này</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mb-3">
                            <div class="card-body text-center">
                                <h4>${formatFileSize(stats.totalSize)}</h4>
                                <p class="mb-0">Tổng dung lượng</p>
                            </div>
                        </div>
                        
                        <h6>Phân bố theo loại tài liệu:</h6>
                        <div class="list-group">
                            ${Object.entries(stats.byType).map(([type, count]) => `
                                <div class="list-group-item d-flex justify-content-between align-items-center">
                                    ${DOCUMENT_TYPES[type] || type}
                                    <span class="badge bg-primary rounded-pill">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Đóng</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    const existingModal = document.getElementById('documentStatsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', statsHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('documentStatsModal'));
    modal.show();
    
    // Clean up
    document.getElementById('documentStatsModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}
