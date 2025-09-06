let dashboardInitialized = false;
let charts = {};

document.addEventListener('DOMContentLoaded', function() {
    
    if (!checkAuth()) {
        return; 
    }
    
    if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
        initializeDashboard();
    } else {
        window.addEventListener('axiosInterceptorsReady', initializeDashboard);
        setTimeout(() => {
            if (window.HospitalApp && window.HospitalApp.interceptorsReady) {
                initializeDashboard();
            } else {
                showAlert('Lỗi khởi tạo hệ thống', 'danger');
            }
        }, 3000);
    }
});

function initializeDashboard() {
    if (dashboardInitialized) {
        return;
    }

    dashboardInitialized = true;

    // Check and display ne        console.log('📊 Found ' + patients.length + ' total patients');
    checkNewAccountInfo();

    // Load all dashboard data
    loadAllDashboardData();
}

async function loadAllDashboardData() {
    try {
        // Load data in parallel for better performance
        await Promise.all([
            loadDashboardStats(),
            loadRecentPatients(),
            loadRecentActivities(),
            loadChartsData()
        ]);
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        showAlert('Lỗi khi tải dữ liệu dashboard', 'danger');
    }
}

async function loadDashboardStats() {
    try {
        // Load patients stats
        const patientsResponse = await axios.get('/api/patients/statistics/');
        const patientsStats = patientsResponse.data;

        updateStatCard('total-patients', patientsStats.total_patients || 0);
        updateStatCard('new-patients', patientsStats.new_patients_this_month || 0);

        // Load appointments stats for today
        const today = new Date().toISOString().split('T')[0];
        
        try {
            // Use direct appointments API to get today's count
            const appointmentsResponse = await axios.get(`/api/appointments/?appointment_date=${today}&page_size=1000`);
            const todayAppointmentsCount = appointmentsResponse.data.count || appointmentsResponse.data.results?.length || 0;
            updateStatCard('today-appointments', todayAppointmentsCount);
            
            console.log(`📅 Today (${today}): ${todayAppointmentsCount} appointments`);
        } catch (error) {
            console.warn('Direct appointments API failed, trying statistics:', error);
            // Fallback to statistics API
            try {
                const appointmentsResponse = await axios.get(`/api/appointments/statistics/?date=${today}`);
                const appointmentsStats = appointmentsResponse.data;
                updateStatCard('today-appointments', appointmentsStats.total_appointments || 0);
            } catch (statsError) {
                console.error('Both appointments APIs failed:', statsError);
                updateStatCard('today-appointments', '-');
            }
        }

        // Load prescriptions stats
        try {
            const prescriptionsResponse = await axios.get('/api/prescriptions/statistics/');
            const prescriptionsStats = prescriptionsResponse.data;
            
            // Calculate pending prescriptions (active but not fully dispensed)
            const pendingPrescriptions = prescriptionsStats.active_prescriptions - prescriptionsStats.dispensed_prescriptions;
            updateStatCard('pending-prescriptions', Math.max(0, pendingPrescriptions));
        } catch (error) {
            console.warn('Prescriptions API not available:', error);
            updateStatCard('pending-prescriptions', '-');
        }

    } catch (error) {
        console.error('❌ Error loading dashboard stats:', error);
        handleApiError(error, 'thống kê dashboard');
    }
}

function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = typeof value === 'number' ? value.toLocaleString() : value;
    }
}

async function loadRecentPatients() {
    try {
        const response = await axios.get('/api/patients/?page_size=5&ordering=-created_at');
        const patients = response.data.results;

        const tbody = document.getElementById('recent-patients-tbody');
        tbody.innerHTML = '';

        if (patients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">Chưa có bệnh nhân nào</td></tr>';
            return;
        }

        patients.forEach(patient => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${patient.patient_code}</strong></td>
                <td>${patient.full_name}</td>
                <td>${patient.phone_number || '-'}</td>
                <td>${formatDate(patient.created_at)}</td>
                <td>
                    <span class="badge ${patient.is_active ? 'bg-success' : 'bg-secondary'}">
                        ${patient.is_active ? 'Hoạt động' : 'Không hoạt động'}
                    </span>
                </td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('❌ Error loading recent patients:', error);
        handleApiError(error, 'danh sách bệnh nhân gần đây');
    }
}

async function loadRecentActivities() {
    try {
        // Generate sample activities based on recent data
        const activities = await generateRecentActivities();
        
        const container = document.getElementById('recent-activities');
        container.innerHTML = '';

        if (activities.length === 0) {
            container.innerHTML = '<div class="text-center text-muted py-4">Chưa có hoạt động nào</div>';
            return;
        }

        activities.forEach(activity => {
            const activityElement = document.createElement('div');
            activityElement.className = `activity-item ${activity.isRecent ? 'recent' : ''}`;
            activityElement.innerHTML = `
                <div class="d-flex align-items-start">
                    <i class="${activity.icon} me-3 mt-1" style="color: ${activity.color};"></i>
                    <div class="flex-grow-1">
                        <div class="activity-description">${activity.description}</div>
                        <div class="activity-time">${activity.time}</div>
                    </div>
                </div>
            `;
            container.appendChild(activityElement);
        });

    } catch (error) {
        console.error('❌ Error loading recent activities:', error);
        document.getElementById('recent-activities').innerHTML = 
            '<div class="text-center text-danger py-4">Lỗi khi tải hoạt động</div>';
    }
}

async function generateRecentActivities() {
    const activities = [];
    
    try {
        // Get recent patients
        const patientsResponse = await axios.get('/api/patients/?page_size=2&ordering=-created_at');
        const recentPatients = patientsResponse.data.results;
        
        recentPatients.forEach((patient, index) => {
            const timeAgo = calculateTimeAgo(patient.created_at);
            activities.push({
                description: `Bệnh nhân mới: ${patient.full_name} (${patient.patient_code})`,
                time: timeAgo,
                icon: 'fas fa-user-plus',
                color: '#43e97b',
                isRecent: index === 0
            });
        });
        
        // Get recent appointments
        try {
            const today = new Date().toISOString().split('T')[0];
            const appointmentsResponse = await axios.get(`/api/appointments/?page_size=2&ordering=-created_at&appointment_date=${today}`);
            const recentAppointments = appointmentsResponse.data.results;
            
            recentAppointments.forEach((appointment, index) => {
                const timeAgo = calculateTimeAgo(appointment.created_at);
                activities.push({
                    description: `Lịch hẹn mới: ${appointment.patient_name} - ${appointment.doctor_name}`,
                    time: timeAgo,
                    icon: 'fas fa-calendar-check',
                    color: '#4facfe',
                    isRecent: index === 0
                });
            });
        } catch (error) {
            console.warn('Appointments API error:', error);
        }
        
        // Get recent prescriptions
        try {
            const prescriptionsResponse = await axios.get('/api/prescriptions/?page_size=2&ordering=-created_at');
            const recentPrescriptions = prescriptionsResponse.data.results;
            
            recentPrescriptions.forEach((prescription, index) => {
                const timeAgo = calculateTimeAgo(prescription.created_at);
                activities.push({
                    description: `Đơn thuốc mới: ${prescription.patient_name} (${prescription.prescription_number})`,
                    time: timeAgo,
                    icon: 'fas fa-prescription-bottle',
                    color: '#fcb69f',
                    isRecent: index === 0
                });
            });
        } catch (error) {
            console.warn('Prescriptions API error:', error);
        }
        
        // Sort by most recent first
        activities.sort((a, b) => {
            // Simple sort by isRecent flag and then by time
            if (a.isRecent && !b.isRecent) return -1;
            if (!a.isRecent && b.isRecent) return 1;
            return 0;
        });
        
        // Keep only the 4 most recent activities
        return activities.slice(0, 4);
        
    } catch (error) {
        console.error('Error generating activities:', error);
        // Fallback to sample activities
        return [
            {
                description: 'Hệ thống đang tải dữ liệu...',
                time: 'Vừa xong',
                icon: 'fas fa-spinner',
                color: '#718096',
                isRecent: true
            }
        ];
    }
}

function calculateTimeAgo(dateString) {
    if (!dateString) return 'Không rõ';
    
    try {
        const now = new Date();
        const date = new Date(dateString);
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return `${diffMins} phút trước`;
        if (diffHours < 24) return `${diffHours} giờ trước`;
        if (diffDays < 7) return `${diffDays} ngày trước`;
        
        return date.toLocaleDateString('vi-VN');
    } catch (error) {
        console.error('Error calculating time ago:', error);
        return 'Không rõ';
    }
}

async function loadChartsData() {
    try {
        await Promise.all([
            createAppointmentsChart(),
            createAppointmentStatusChart(),
            createPrescriptionsChart()
        ]);
    } catch (error) {
        console.error('❌ Error loading charts data:', error);
    }
}

async function createAppointmentsChart() {
    try {
        showChartLoading('appointments-chart-loading');
        
        // Get appointments data from start of month to current date
        const chartData = await getAppointmentsWeeklyData();
        
        const ctx = document.getElementById('appointmentsChart').getContext('2d');
        
        if (charts.appointmentsChart) {
            charts.appointmentsChart.destroy();
        }
        
        charts.appointmentsChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Lịch hẹn cả tháng',
                    data: chartData.data,
                    borderColor: '#4facfe',
                    backgroundColor: 'rgba(79, 172, 254, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#4facfe',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                return `Ngày ${context.label}: ${context.parsed.y} lịch hẹn`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        },
                        ticks: {
                            color: '#718096'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: '#718096'
                        }
                    }
                }
            }
        });
        
        hideChartLoading('appointments-chart-loading');
        document.getElementById('appointmentsChart').style.display = 'block';
        
    } catch (error) {
        console.error('❌ Error creating appointments chart:', error);
        showChartError('appointments-chart-loading', 'Lỗi khi tải biểu đồ lịch hẹn');
    }
}

async function createAppointmentStatusChart() {
    try {
        showChartLoading('appointment-status-chart-loading');
        
        const today = new Date().toISOString().split('T')[0];
        
        let statusData = {};
        
        try {
            // Use direct appointments API to get real data
            const response = await axios.get(`/api/appointments/?appointment_date=${today}&page_size=1000`);
            const appointments = response.data.results || [];
            
            // Count appointments by status
            const statusCounts = {};
            appointments.forEach(appointment => {
                const status = appointment.status_display || appointment.status;
                statusCounts[status] = (statusCounts[status] || 0) + 1;
            });
            
            statusData = statusCounts;
            console.log(`📊 Today's appointment status data:`, statusData);
            
        } catch (error) {
            console.warn('Direct appointments API failed, trying statistics:', error);
            // Fallback to statistics API
            try {
                const response = await axios.get(`/api/appointments/statistics/?date=${today}`);
                const stats = response.data;
                statusData = stats.by_status || {};
            } catch (statsError) {
                console.warn('Stats API also failed:', statsError);
                statusData = {};
            }
        }
        
        const ctx = document.getElementById('appointmentStatusChart').getContext('2d');
        
        if (charts.appointmentStatusChart) {
            charts.appointmentStatusChart.destroy();
        }
        
        const labels = Object.keys(statusData);
        const data = Object.values(statusData);
        
        // If no data, show empty state
        if (labels.length === 0 || data.every(d => d === 0)) {
            showChartEmpty('appointment-status-chart-loading', 'Chưa có lịch hẹn nào hôm nay');
            return;
        }
        
        const colors = ['#4facfe', '#43e97b', '#667eea', '#fcb69f', '#f093fb'];
        
        charts.appointmentStatusChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 0,
                    hoverBorderWidth: 2,
                    hoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            color: '#4a5568'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        hideChartLoading('appointment-status-chart-loading');
        document.getElementById('appointmentStatusChart').style.display = 'block';
        
    } catch (error) {
        console.error('❌ Error creating appointment status chart:', error);
        showChartError('appointment-status-chart-loading', 'Lỗi khi tải biểu đồ trạng thái lịch hẹn');
    }
}

async function createPrescriptionsChart() {
    try {
        showChartLoading('prescriptions-chart-loading');
        
        let statusData = {};
        
        try {
            const response = await axios.get('/api/prescriptions/statistics/');
            const stats = response.data;
            
            // Map the API response to chart data
            statusData = {
                'Có hiệu lực': stats.active_prescriptions || 0,
                'Đã cấp thuốc': stats.dispensed_prescriptions || 0,
                'Hết hạn': stats.expired_prescriptions || 0
            };
        } catch (error) {
            console.warn('Prescriptions API not available:', error);
            // Mock data if prescriptions API is not available
            statusData = {
                'Có hiệu lực': 5,
                'Đã cấp thuốc': 12,
                'Hết hạn': 2
            };
        }
        
        const ctx = document.getElementById('prescriptionsChart').getContext('2d');
        
        if (charts.prescriptionsChart) {
            charts.prescriptionsChart.destroy();
        }
        
        const labels = Object.keys(statusData);
        const data = Object.values(statusData);
        
        // If no data, show empty state
        if (data.every(d => d === 0)) {
            showChartEmpty('prescriptions-chart-loading', 'Chưa có đơn thuốc nào');
            return;
        }
        
        const colors = ['#43e97b', '#4facfe', '#f093fb'];
        
        charts.prescriptionsChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            color: '#4a5568'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        hideChartLoading('prescriptions-chart-loading');
        document.getElementById('prescriptionsChart').style.display = 'block';
        
    } catch (error) {
        console.error('❌ Error creating prescriptions chart:', error);
        showChartError('prescriptions-chart-loading', 'Lỗi khi tải biểu đồ đơn thuốc');
    }
}

// Chart loading helpers
function showChartLoading(loadingElementId) {
    const loadingElement = document.getElementById(loadingElementId);
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
}

function hideChartLoading(loadingElementId) {
    const loadingElement = document.getElementById(loadingElementId);
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

function showChartError(loadingElementId, message) {
    const loadingElement = document.getElementById(loadingElementId);
    if (loadingElement) {
        loadingElement.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-warning mb-2" style="font-size: 2rem;"></i>
                <div class="text-muted">${message}</div>
                <button class="btn btn-sm btn-outline-secondary mt-2" onclick="refreshCharts()">
                    <i class="fas fa-sync-alt me-1"></i>Thử lại
                </button>
            </div>
        `;
        loadingElement.style.display = 'block';
    }
}

function showChartEmpty(loadingElementId, message) {
    const loadingElement = document.getElementById(loadingElementId);
    if (loadingElement) {
        loadingElement.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-chart-pie text-muted mb-2" style="font-size: 2rem; opacity: 0.3;"></i>
                <div class="text-muted">${message}</div>
            </div>
        `;
        loadingElement.style.display = 'block';
    }
}

// Refresh functions
async function refreshCharts() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Đang làm mới...';
    }
    
    try {
        // Hide all charts and show loading
        ['appointmentsChart', 'appointmentStatusChart', 'prescriptionsChart'].forEach(chartId => {
            const canvas = document.getElementById(chartId);
            if (canvas) {
                canvas.style.display = 'none';
            }
        });
        
        await loadChartsData();
        showAlert('Biểu đồ đã được cập nhật', 'success');
    } catch (error) {
        console.error('❌ Error refreshing charts:', error);
        showAlert('Lỗi khi làm mới biểu đồ', 'danger');
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Làm mới';
        }
    }
}

function generateReport() {
    showAlert('Tính năng báo cáo đang được phát triển', 'info');
}

async function getAppointmentsWeeklyData() {
    // Generate data for all days in current month
    const days = [];
    const data = [];
    
    const today = new Date();
    const currentMonth = today.getMonth();
    const currentYear = today.getFullYear();
    
    // Get last day of current month
    const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    console.log(`📅 Getting appointments for all days in month ${currentMonth + 1}/${currentYear} (1-${lastDayOfMonth})`);
    
    // Loop through all days in current month
    for (let day = 1; day <= lastDayOfMonth; day++) {
        const currentDate = new Date(currentYear, currentMonth, day);
        const dateStr = currentDate.toISOString().split('T')[0];
        
        days.push(day);
        
        try {
            // Use direct appointments API
            const response = await axios.get(`/api/appointments/?appointment_date=${dateStr}&page_size=1000`);
            const appointmentsCount = response.data.count || response.data.results?.length || 0;
            data.push(appointmentsCount);
            
            if (appointmentsCount > 0) {
                console.log(`📅 ${dateStr} (Ngày ${day}): ${appointmentsCount} lịch hẹn`);
            }
        } catch (error) {
            console.warn(`Error fetching appointments for ${dateStr}:`, error);
            data.push(0);
        }
    }
    
    console.log('📊 Monthly appointments data:', { labels: days, data: data });
    return { labels: days, data: data };
}

async function getPatientsMonthlyData() {
    try {
        console.log('📅 Getting all patients and grouping by month...');
        
        // Get all patients
        const response = await axios.get('/api/patients/?page_size=1000&ordering=created_at');
        const patients = response.data?.results || [];
        
        console.log(`� Found ${patients.length} total patients`);
        
        // Create last 6 months data
        const months = [];
        const data = [];
        
        for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            
            const year = date.getFullYear();
            const month = date.getMonth() + 1;
            const monthName = date.toLocaleDateString('vi-VN', { month: 'short' });
            
            months.push(monthName);
            
            // Count patients created in this month - simplified
            let monthlyCount = 0;
            for (let j = 0; j < patients.length; j++) {
                const patient = patients[j];
                if (patient && patient.created_at) {
                    const createdDate = new Date(patient.created_at);
                    if (createdDate.getFullYear() === year && 
                        createdDate.getMonth() + 1 === month) {
                        monthlyCount++;
                    }
                }
            }
            
            data.push(monthlyCount);
            console.log(`📊 ${monthName} ${year}: ${monthlyCount} patients`);
        }
        
            }
    
    console.log('� Monthly appointments data:', { labels: days, data: data });
    return { labels: days, data: data };
}

function handleApiError(error, context) {
        return { labels: months, data: data };
        
    } catch (error) {
        console.error('❌ Error getting patients monthly data:', error);
        // Fallback to empty data
        const months = [];
        const data = [];
        
        for (let i = 5; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            const monthName = date.toLocaleDateString('vi-VN', { month: 'short' });
            months.push(monthName);
            data.push(0);
        }
        
        return { labels: months, data: data };
    }
}

function handleApiError(error, context) {
    if (error.response?.status === 401) {
        redirectToLogin();
    } else if (error.code === 'ERR_NETWORK') {
        showAlert(`Mất kết nối tạm thời khi tải ${context}. Đang thử lại...`, 'warning');
        setTimeout(() => loadAllDashboardData(), 3000);
    } else {
        console.error(`Error loading ${context}:`, error);
    }
}

function openAddPatientModal() {
    window.location.href = '/patients/';
}

function generateReport() {
    showAlert('Tính năng báo cáo đang được phát triển', 'info');
}

// Helper function để kiểm tra authentication
function checkAuth() {
    const token = localStorage.getItem('access_token');

    if (!token) {
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
    window.location.replace('/login/');
}

function showAlert(message, type = 'info') {
    if (window.HospitalApp && window.HospitalApp.showAlert) {
        window.HospitalApp.showAlert(message, type);
        return;
    }
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid') || document.querySelector('.container') || document.querySelector('main');
    if (container) {
        try {
            container.insertBefore(alertDiv, container.firstChild);
            
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        } catch (error) {
            console.error('Error inserting alert:', error);
            document.body.appendChild(alertDiv);
        }
    } else {
        console.warn('No container found for alert, appending to body');
        document.body.appendChild(alertDiv);
    }
}

function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
    }
}

// Check and display new account information
function checkNewAccountInfo() {
    try {
        const accountInfo = localStorage.getItem('new_account_info');
        if (accountInfo) {
            const info = JSON.parse(accountInfo);

            // Display account info
            document.getElementById('account-fullname').textContent = info.fullName || '-';
            document.getElementById('account-phone').textContent = info.phoneNumber || '-';
            document.getElementById('account-username').textContent = info.username || '-';
            document.getElementById('account-password').textContent = info.password || '-';

            // Show the account info section
            document.getElementById('new-account-info').style.display = 'block';

            // Auto-hide after 30 seconds
            setTimeout(() => {
                const alertElement = document.getElementById('new-account-info');
                if (alertElement) {
                    alertElement.style.display = 'none';
                }
            }, 30000);

            // Clear the stored info
            localStorage.removeItem('new_account_info');
        }
    } catch (error) {
        console.error('Error displaying new account info:', error);
    }
}

// Cleanup charts when leaving the page
window.addEventListener('beforeunload', function() {
    Object.values(charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
});

// Auto refresh data every 5 minutes
setInterval(() => {
    if (dashboardInitialized && document.visibilityState === 'visible') {
        loadAllDashboardData();
    }
}, 5 * 60 * 1000);