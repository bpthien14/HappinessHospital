from django.contrib import admin
from django.utils.html import format_html
from .models import Patient, MedicalRecord, PatientDocument

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'patient_code', 'full_name', 'age', 'gender', 'phone_number',
        'insurance_status_display', 'is_active', 'created_at'
    ]
    list_filter = [
        'gender', 'has_insurance', 'is_active', 'province', 'created_at'
    ]
    search_fields = [
        'full_name', 'patient_code', 'phone_number', 'citizen_id', 'insurance_number'
    ]
    readonly_fields = ['patient_code', 'age', 'full_address', 'insurance_status', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': (
                'patient_code', 'full_name', 'date_of_birth', 'age', 'gender'
            )
        }),
        ('Thông tin liên lạc', {
            'fields': (
                'phone_number', 'email', 'address', 'ward', 'province', 'full_address'
            )
        }),
        ('Giấy tờ tùy thân', {
            'fields': ('citizen_id',)
        }),
        ('Thông tin y tế', {
            'fields': ('blood_type', 'allergies', 'chronic_diseases'),
            'classes': ('collapse',)
        }),
        ('Liên hệ khẩn cấp', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Bảo hiểm y tế', {
            'fields': (
                'has_insurance', 'insurance_number', 'insurance_valid_from', 
                'insurance_valid_to', 'insurance_hospital_code', 'insurance_status'
            )
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_by', 'updated_by', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def insurance_status_display(self, obj):
        status = obj.insurance_status
        if status == "BHYT có hiệu lực":
            return format_html('<span style="color: green;">{}</span>', status)
        elif status == "BHYT hết hạn":
            return format_html('<span style="color: red;">{}</span>', status)
        else:
            return format_html('<span style="color: gray;">{}</span>', status)
    
    insurance_status_display.short_description = 'Trạng thái BHYT'

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'medical_record_number', 'patient', 'doctor', 'visit_date', 'visit_type', 'status'
    ]
    list_filter = ['visit_type', 'status', 'department', 'visit_date']
    search_fields = [
        'medical_record_number', 'patient__full_name', 'patient__patient_code', 'doctor__full_name'
    ]
    readonly_fields = ['medical_record_number', 'blood_pressure', 'bmi', 'created_at', 'updated_at']
    ordering = ['-visit_date']
    raw_id_fields = ['patient', 'doctor']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': (
                'medical_record_number', 'patient', 'doctor', 'visit_date', 'visit_type', 'department', 'status'
            )
        }),
        ('Thông tin khám', {
            'fields': ('chief_complaint', 'history_of_present_illness', 'physical_examination')
        }),
        ('Sinh hiệu', {
            'fields': (
                'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_pressure',
                'heart_rate', 'respiratory_rate', 'weight', 'height', 'bmi'
            ),
            'classes': ('collapse',)
        }),
        ('Chẩn đoán và điều trị', {
            'fields': ('preliminary_diagnosis', 'final_diagnosis', 'treatment_plan', 'notes')
        }),
        ('Tái khám', {
            'fields': ('next_appointment', 'follow_up_instructions'),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'patient', 'document_type', 'file_size_display', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'patient__full_name', 'patient__patient_code']
    readonly_fields = ['file_size', 'uploaded_at']
    raw_id_fields = ['patient']
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024 * 1024:
                return f"{obj.file_size // 1024} KB"
            else:
                return f"{obj.file_size // (1024 * 1024)} MB"
        return "-"
    
    file_size_display.short_description = 'Kích thước'