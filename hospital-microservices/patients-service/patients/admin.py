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
            'fields': ('created_by_id', 'updated_by_id', 'is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def insurance_status_display(self, obj):
        status = obj.insurance_status
        if "có hiệu lực" in status:
            return format_html('<span style="color: green;">{}</span>', status)
        elif "hết hạn" in status:
            return format_html('<span style="color: red;">{}</span>', status)
        else:
            return format_html('<span style="color: orange;">{}</span>', status)
    
    insurance_status_display.short_description = 'Trạng thái BHYT'

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'medical_record_number', 'visit_date', 'visit_type', 'department', 
        'status', 'created_at'
    ]
    list_filter = ['visit_type', 'status', 'department', 'visit_date']
    search_fields = ['medical_record_number', 'chief_complaint']
    readonly_fields = ['medical_record_number', 'created_at', 'updated_at']
    ordering = ['-visit_date']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': (
                'medical_record_number', 'visit_date', 'visit_type', 'department', 'status'
            )
        }),
        ('Thông tin y tế', {
            'fields': (
                'chief_complaint', 'history_of_present_illness', 'physical_examination'
            )
        }),
        ('Dấu hiệu sinh tồn', {
            'fields': (
                'temperature', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                'heart_rate', 'respiratory_rate', 'weight', 'height'
            ),
            'classes': ('collapse',)
        }),
        ('Chẩn đoán và điều trị', {
            'fields': (
                'preliminary_diagnosis', 'final_diagnosis', 'treatment_plan', 'notes'
            ),
            'classes': ('collapse',)
        }),
        ('Tái khám', {
            'fields': ('next_appointment', 'follow_up_instructions'),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('patient_id', 'doctor_id', 'created_by_id', 'updated_by_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'document_type', 'patient_id', 'uploaded_at', 'file_size'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_at']
    ordering = ['-uploaded_at']
    
    fieldsets = (
        ('Thông tin tài liệu', {
            'fields': ('title', 'document_type', 'description')
        }),
        ('File', {
            'fields': ('file_url', 'file_size')
        }),
        ('Thông tin hệ thống', {
            'fields': ('patient_id', 'uploaded_by_id', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
