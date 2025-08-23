document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    loadRecentPatients();
});

async function loadDashboardStats() {
    try {
        const response = await axios.get('/api/patients/statistics/');
        const stats = response.data;
        
        document.getElementById('total-patients').textContent = stats.total_patients;
        document.getElementById('new-patients').textContent = stats.new_patients_this_month;
        // TODO: Load appointment and prescription stats when those modules are implemented
        document.getElementById('today-appointments').textContent = '-';
        document.getElementById('pending-prescriptions').textContent = '-';
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

async function loadRecentPatients() {
    try {
        const response = await axios.get('/api/patients/?page_size=5&ordering=-created_at');
        const patients = response.data.results;
        
        const tbody = document.getElementById('recent-patients-tbody');
        tbody.innerHTML = '';
        
        if (patients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">Chưa có bệnh nhân nào</td></tr>';
            return;
        }
        
        patients.forEach(patient => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${patient.patient_code}</td>
                <td>${patient.full_name}</td>
                <td>${formatDate(patient.created_at)}</td>
            `;
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading recent patients:', error);
        document.getElementById('recent-patients-tbody').innerHTML = 
            '<tr><td colspan="3" class="text-center text-danger">Lỗi khi tải dữ liệu</td></tr>';
    }
}

function openAddPatientModal() {
    window.location.href = '/patients/';
}