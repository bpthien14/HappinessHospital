from django.contrib import admin
from django.utils.html import format_html
from .models import Department, DoctorProfile, DoctorSchedule, Appointment, AppointmentStatusHistory, TimeSlot

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'location', 'consultation_fee', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['specialization', 'department', 'license_number', 'experience_years', 'is_active']
    list_filter = ['specialization', 'department', 'is_active']
    search_fields = ['license_number', 'specialization']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['specialization', 'department']

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'shift', 'start_time', 'end_time', 'is_available']
    list_filter = ['date', 'shift', 'is_available', 'doctor__department']
    search_fields = ['doctor__specialization']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['date', 'start_time']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_number', 'appointment_datetime', 'status', 'priority', 'queue_number']
    list_filter = ['status', 'priority', 'appointment_type', 'appointment_date']
    search_fields = ['appointment_number', 'patient_id', 'doctor_id']
    readonly_fields = ['appointment_number', 'queue_number', 'created_at', 'updated_at']
    date_hierarchy = 'appointment_date'

@admin.register(AppointmentStatusHistory)
class AppointmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'old_status', 'new_status', 'changed_at']
    list_filter = ['changed_at', 'old_status', 'new_status']
    search_fields = ['appointment__appointment_number']
    readonly_fields = ['changed_at']
    ordering = ['-changed_at']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'start_time', 'end_time', 'is_available', 'current_appointments']
    list_filter = ['date', 'is_available', 'doctor__department']
    search_fields = ['doctor__specialization']
    readonly_fields = ['created_at']
    ordering = ['date', 'start_time']
