from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Department, DoctorProfile, DoctorSchedule, 
    Appointment, AppointmentStatusHistory, TimeSlot
)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'consultation_fee', 'doctor_count', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def doctor_count(self, obj):
        return obj.doctors.filter(is_active=True).count()
    doctor_count.short_description = 'Số bác sĩ'

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'specialization', 'experience_years', 'is_active']
    list_filter = ['department', 'degree', 'is_active', 'created_at']
    search_fields = ['user__full_name', 'user__username', 'specialization', 'license_number']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('user', 'department')
        }),
        ('Thông tin chuyên môn', {
            'fields': ('license_number', 'degree', 'specialization', 'experience_years')
        }),
        ('Cài đặt công việc', {
            'fields': ('max_patients_per_day', 'consultation_duration')
        }),
        ('Tiểu sử', {
            'fields': ('bio', 'achievements'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_active', 'created_at', 'updated_at')
        })
    )

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'weekday_display', 'shift_display', 'start_time', 'end_time', 'max_appointments', 'is_active']
    list_filter = ['weekday', 'shift', 'is_active', 'effective_from']
    search_fields = ['doctor__user__full_name', 'doctor__specialization']
    raw_id_fields = ['doctor']
    
    def weekday_display(self, obj):
        return obj.get_weekday_display()
    weekday_display.short_description = 'Thứ'
    
    def shift_display(self, obj):
        return obj.get_shift_display()
    shift_display.short_description = 'Ca làm việc'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'appointment_number', 'patient_link', 'doctor', 'appointment_datetime', 
        'status_badge', 'priority_badge', 'queue_number'
    ]
    list_filter = [
        'status', 'priority', 'appointment_type', 'department', 
        'appointment_date', 'created_at'
    ]
    search_fields = [
        'appointment_number', 'patient__full_name', 'patient__patient_code',
        'doctor__user__full_name'
    ]
    readonly_fields = [
        'appointment_number', 'queue_number', 'appointment_datetime',
        'is_today', 'is_past_due', 'can_cancel', 'can_checkin',
        'created_at', 'updated_at'
    ]
    raw_id_fields = ['patient', 'doctor', 'booked_by', 'confirmed_by']
    date_hierarchy = 'appointment_date'
    
    fieldsets = (
        ('Thông tin lịch hẹn', {
            'fields': ('appointment_number', 'patient', 'doctor', 'department')
        }),
        ('Thời gian', {
            'fields': (
                'appointment_date', 'appointment_time', 'appointment_datetime',
                'estimated_duration', 'queue_number'
            )
        }),
        ('Phân loại', {
            'fields': ('appointment_type', 'priority', 'status')
        }),
        ('Thông tin bệnh nhân', {
            'fields': ('chief_complaint', 'symptoms', 'notes')
        }),
        ('Quản lý', {
            'fields': ('booked_by', 'confirmed_by', 'confirmed_at'),
            'classes': ('collapse',)
        }),
        ('Check-in & Thực hiện', {
            'fields': ('checked_in_at', 'actual_start_time', 'actual_end_time'),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_today', 'is_past_due', 'can_cancel', 'can_checkin')
        }),
        ('Thời gian hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def patient_link(self, obj):
        url = reverse('admin:patients_patient_change', args=[obj.patient.id])
        return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)
    patient_link.short_description = 'Bệnh nhân'
    
    def status_badge(self, obj):
        color_map = {
            'SCHEDULED': 'info',
            'CONFIRMED': 'primary', 
            'CHECKED_IN': 'warning',
            'IN_PROGRESS': 'warning',
            'COMPLETED': 'success',
            'NO_SHOW': 'secondary',
            'CANCELLED': 'danger',
            'RESCHEDULED': 'info'
        }
        color = color_map.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Trạng thái'
    
    def priority_badge(self, obj):
        color_map = {
            'LOW': 'secondary',
            'NORMAL': 'info',
            'HIGH': 'warning', 
            'URGENT': 'danger'
        }
        color = color_map.get(obj.priority, 'info')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Ưu tiên'

@admin.register(AppointmentStatusHistory)
class AppointmentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['appointment__appointment_number', 'changed_by__username']
    readonly_fields = ['changed_at']
    raw_id_fields = ['appointment', 'changed_by']
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing