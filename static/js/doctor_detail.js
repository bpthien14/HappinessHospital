/**
 * Doctor Detail Page JavaScript
 * Handles doctor profile display and schedule management
 */

class DoctorDetailManager {
    constructor(doctorId) {
        this.doctorId = doctorId;
        this.currentWeekStart = this.getWeekStart(new Date());
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDoctorDetails();
        this.loadDoctorStats();
        this.loadRecentAppointments();
        this.loadWeeklySchedule();
    }

    setupEventListeners() {
        // Schedule navigation
        $('#prev-week').on('click', () => {
            this.currentWeekStart.setDate(this.currentWeekStart.getDate() - 7);
            this.loadWeeklySchedule();
        });

        $('#next-week').on('click', () => {
            this.currentWeekStart.setDate(this.currentWeekStart.getDate() + 7);
            this.loadWeeklySchedule();
        });

        // Add schedule form
        $('#add-schedule-form').on('submit', (e) => {
            e.preventDefault();
            this.addSchedule();
        });

        // Modal events
        $('#addScheduleModal').on('hidden.bs.modal', () => {
            this.resetForm('#add-schedule-form');
        });
    }

    async loadDoctorDetails() {
        try {
            const response = await fetch(`/api/doctors/${this.doctorId}/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load doctor details');
            }

            const doctor = await response.json();
            this.renderDoctorDetails(doctor);
            
        } catch (error) {
            console.error('Error loading doctor details:', error);
            this.showError('Không thể tải thông tin bác sĩ.');
        }
    }

    renderDoctorDetails(doctor) {
        // Update basic info
        $('#doctor-name').text(`${doctor.user?.first_name} ${doctor.user?.last_name}`);
        $('#doctor-title').text(this.formatDegree(doctor.degree));
        $('#doctor-email').text(doctor.user?.email || '-');
        $('#doctor-phone').text(doctor.user?.phone_number || '-');
        $('#doctor-department').text(doctor.department?.name || '-');
        $('#doctor-employee-id').text(doctor.user?.employee_id || '-');
        
        // Update status
        const statusBadge = $('#doctor-status');
        if (doctor.user?.is_active) {
            statusBadge.removeClass('bg-secondary').addClass('bg-success').text('Đang hoạt động');
        } else {
            statusBadge.removeClass('bg-success').addClass('bg-secondary').text('Tạm nghỉ');
        }

        // Update professional info
        $('#doctor-degree').text(this.formatDegree(doctor.degree));
        $('#doctor-experience').text(doctor.years_of_experience ? `${doctor.years_of_experience} năm` : '-');
        $('#doctor-specializations').text(doctor.specializations || '-');
        $('#doctor-qualifications').text(doctor.qualifications || 'Chưa có thông tin');
        $('#doctor-bio').text(doctor.bio || 'Chưa có thông tin');
    }

    async loadDoctorStats() {
        try {
            // Load appointment statistics
            const response = await fetch(`/api/appointments/?doctor=${this.doctorId}&page_size=1`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                $('#total-appointments').text(data.count || 0);
            }

            // You can add more specific stats calls here
            $('#completed-appointments').text('-');
            $('#pending-appointments').text('-');
            $('#total-prescriptions').text('-');
            
        } catch (error) {
            console.error('Error loading doctor stats:', error);
        }
    }

    async loadRecentAppointments() {
        try {
            const response = await fetch(`/api/appointments/?doctor=${this.doctorId}&page_size=5&ordering=-appointment_date`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load appointments');
            }

            const data = await response.json();
            this.renderRecentAppointments(data.results || []);
            
        } catch (error) {
            console.error('Error loading recent appointments:', error);
            $('#recent-appointments-body').html(`
                <tr>
                    <td colspan="6" class="text-center text-muted py-3">
                        Không thể tải danh sách lịch khám
                    </td>
                </tr>
            `);
        }
    }

    renderRecentAppointments(appointments) {
        const tbody = $('#recent-appointments-body');
        tbody.empty();

        if (!appointments || appointments.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="6" class="text-center text-muted py-3">
                        Chưa có lịch khám nào
                    </td>
                </tr>
            `);
            return;
        }

        appointments.forEach(appointment => {
            const row = this.createAppointmentRow(appointment);
            tbody.append(row);
        });
    }

    createAppointmentRow(appointment) {
        const statusBadge = this.getStatusBadge(appointment.status);
        const appointmentDate = new Date(appointment.appointment_date).toLocaleDateString('vi-VN');
        const appointmentTime = appointment.appointment_time || '-';

        return `
            <tr>
                <td>${appointmentDate}</td>
                <td>${appointmentTime}</td>
                <td>${appointment.patient?.full_name || '-'}</td>
                <td>${appointment.reason || '-'}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="viewAppointment('${appointment.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    async loadWeeklySchedule() {
        try {
            const weekEnd = new Date(this.currentWeekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);

            const response = await fetch(`/api/doctor-schedules/?doctor=${this.doctorId}&date_from=${this.formatDate(this.currentWeekStart)}&date_to=${this.formatDate(weekEnd)}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const schedules = await response.json();
                this.renderWeeklySchedule(schedules.results || schedules);
            }

            this.updateWeekLabel();
            
        } catch (error) {
            console.error('Error loading weekly schedule:', error);
        }
    }

    renderWeeklySchedule(schedules) {
        const grid = $('#schedule-grid');
        grid.empty();

        // Create time slots from 8:00 to 18:00
        const timeSlots = [];
        for (let hour = 8; hour <= 18; hour++) {
            timeSlots.push(`${hour.toString().padStart(2, '0')}:00`);
        }

        timeSlots.forEach(time => {
            const row = $(`<tr><td class="text-center fw-bold">${time}</td></tr>`);
            
            // Add 7 cells for days of week
            for (let day = 0; day < 7; day++) {
                const cell = $('<td class="schedule-cell"></td>');
                
                // Check if there's a schedule for this time and day
                const currentDate = new Date(this.currentWeekStart);
                currentDate.setDate(currentDate.getDate() + day);
                
                const daySchedules = schedules.filter(schedule => {
                    const scheduleDate = new Date(schedule.date);
                    return scheduleDate.toDateString() === currentDate.toDateString() &&
                           this.isTimeInRange(time, schedule.start_time, schedule.end_time);
                });

                if (daySchedules.length > 0) {
                    cell.addClass('bg-primary text-white');
                    cell.html('<small>Có lịch</small>');
                }

                row.append(cell);
            }
            
            grid.append(row);
        });
    }

    isTimeInRange(time, startTime, endTime) {
        return time >= startTime && time < endTime;
    }

    updateWeekLabel() {
        const weekEnd = new Date(this.currentWeekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        
        const label = `${this.formatDate(this.currentWeekStart)} - ${this.formatDate(weekEnd)}`;
        $('#current-week').text(label);
    }

    async addSchedule() {
        try {
            const formData = this.getFormData('#add-schedule-form');
            formData.doctor = this.doctorId;

            const response = await fetch('/api/doctor-schedules/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to add schedule');
            }

            $('#addScheduleModal').modal('hide');
            this.showSuccess('Đã thêm lịch khám thành công!');
            this.loadWeeklySchedule();
            
        } catch (error) {
            console.error('Error adding schedule:', error);
            this.showError(error.message || 'Không thể thêm lịch khám.');
        }
    }

    getStatusBadge(status) {
        const badges = {
            'SCHEDULED': '<span class="badge bg-primary">Đã đặt</span>',
            'CONFIRMED': '<span class="badge bg-info">Đã xác nhận</span>',
            'IN_PROGRESS': '<span class="badge bg-warning">Đang khám</span>',
            'COMPLETED': '<span class="badge bg-success">Hoàn thành</span>',
            'CANCELLED': '<span class="badge bg-danger">Đã hủy</span>',
            'NO_SHOW': '<span class="badge bg-secondary">Không đến</span>'
        };
        return badges[status] || '<span class="badge bg-secondary">Không xác định</span>';
    }

    formatDegree(degree) {
        const degrees = {
            'BACHELOR': 'Bác sĩ',
            'MASTER': 'Thạc sĩ',
            'DOCTOR': 'Tiến sĩ'
        };
        return degrees[degree] || degree;
    }

    formatDate(date) {
        return date.toLocaleDateString('vi-VN');
    }

    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
        return new Date(d.setDate(diff));
    }

    getFormData(formSelector) {
        const form = $(formSelector);
        const data = {};
        
        form.find('input, select, textarea').each(function() {
            const field = $(this);
            const name = field.attr('name');
            const value = field.val();
            
            if (name && value !== '') {
                data[name] = value;
            }
        });
        
        return data;
    }

    resetForm(formSelector) {
        $(formSelector)[0].reset();
    }

    showSuccess(message) {
        alert(message);
    }

    showError(message) {
        alert(message);
    }
}

// Global functions
function editDoctor() {
    window.location.href = `/doctors/${window.doctorId}/edit/`;
}

function viewAppointment(appointmentId) {
    window.location.href = `/appointments/${appointmentId}/`;
}

// Initialize when document is ready
$(document).ready(function() {
    if (window.doctorId) {
        window.doctorDetailManager = new DoctorDetailManager(window.doctorId);
    }
});
