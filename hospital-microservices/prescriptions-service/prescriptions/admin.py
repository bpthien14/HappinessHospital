from django.contrib import admin
from django.utils.html import format_html
from .models import DrugCategory, Drug, Prescription, PrescriptionItem, PrescriptionDispensing

@admin.register(DrugCategory)
class DrugCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'category', 'dosage_form', 'strength', 
        'unit_price', 'current_stock', 'stock_status', 'is_active'
    ]
    list_filter = [
        'category', 'dosage_form', 'is_prescription_required', 
        'is_controlled_substance', 'is_active', 'created_at'
    ]
    search_fields = ['code', 'name', 'generic_name', 'brand_name', 'manufacturer']
    readonly_fields = [
        'stock_status', 'created_at', 'updated_at'
    ]
    ordering = ['name']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('code', 'name', 'generic_name', 'brand_name', 'category')
        }),
        ('Đặc tính', {
            'fields': ('dosage_form', 'strength', 'unit')
        }),
        ('Thông tin y tế', {
            'fields': ('indication', 'contraindication', 'side_effects', 'interactions')
        }),
        ('Liều dùng', {
            'fields': ('dosage_adult', 'dosage_child')
        }),
        ('Bảo quản', {
            'fields': ('storage_condition', 'expiry_after_opening')
        }),
        ('Giá cả', {
            'fields': ('unit_price', 'insurance_price')
        }),
        ('Tồn kho', {
            'fields': ('current_stock', 'minimum_stock', 'maximum_stock')
        }),
        ('Quy định', {
            'fields': ('registration_number', 'manufacturer', 'country_of_origin')
        }),
        ('Kiểm soát', {
            'fields': ('is_prescription_required', 'is_controlled_substance', 'is_active')
        }),
        ('Thời gian hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def stock_status(self, obj):
        status_colors = {
            'HẾT HÀNG': 'red',
            'SẮP HẾT': 'orange',
            'BÌNH THƯỜNG': 'green',
        }
        color = status_colors.get(obj.stock_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px;">{}</span>',
            color, obj.stock_status
        )
    stock_status.short_description = 'Trạng thái tồn kho'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        'prescription_number', 'prescription_date', 'prescription_type', 
        'status', 'total_amount', 'is_valid'
    ]
    list_filter = [
        'status', 'prescription_type', 'prescription_date', 'created_at'
    ]
    search_fields = [
        'prescription_number', 'patient_id', 'doctor_id', 'diagnosis'
    ]
    readonly_fields = [
        'prescription_number', 'prescription_date', 'is_valid', 'days_until_expiry',
        'total_amount', 'insurance_covered_amount', 'patient_payment_amount',
        'created_at', 'updated_at'
    ]
    date_hierarchy = 'prescription_date'
    
    fieldsets = (
        ('Thông tin đơn thuốc', {
            'fields': ('prescription_number', 'patient_id', 'doctor_id', 'appointment_id')
        }),
        ('Phân loại', {
            'fields': ('prescription_type', 'status')
        }),
        ('Thông tin y tế', {
            'fields': ('diagnosis', 'notes', 'special_instructions')
        }),
        ('Hiệu lực', {
            'fields': ('valid_from', 'valid_until', 'is_valid', 'days_until_expiry')
        }),
        ('Tài chính', {
            'fields': ('total_amount', 'insurance_covered_amount', 'patient_payment_amount')
        }),
        ('Thời gian hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = [
        'prescription', 'drug', 'quantity', 'dosage_per_time', 
        'frequency', 'duration_days', 'total_price', 'is_fully_dispensed'
    ]
    list_filter = [
        'frequency', 'route', 'is_substitutable', 'created_at'
    ]
    search_fields = [
        'prescription__prescription_number', 'drug__name', 'drug__code'
    ]
    readonly_fields = [
        'total_price', 'quantity_remaining', 'dispensing_progress', 'created_at'
    ]
    ordering = ['prescription', 'created_at']
    
    fieldsets = (
        ('Thông tin đơn thuốc', {
            'fields': ('prescription', 'drug')
        }),
        ('Liều dùng', {
            'fields': ('quantity', 'dosage_per_time', 'frequency', 'route', 'duration_days')
        }),
        ('Hướng dẫn', {
            'fields': ('instructions', 'special_notes')
        }),
        ('Giá cả', {
            'fields': ('unit_price', 'total_price')
        }),
        ('Cấp thuốc', {
            'fields': ('quantity_dispensed', 'is_substitutable')
        }),
        ('Thống kê', {
            'fields': ('quantity_remaining', 'dispensing_progress', 'is_fully_dispensed')
        }),
        ('Thời gian hệ thống', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(PrescriptionDispensing)
class PrescriptionDispensingAdmin(admin.ModelAdmin):
    list_display = [
        'prescription', 'prescription_item', 'quantity_dispensed', 
        'status', 'pharmacist_id', 'dispensed_at'
    ]
    list_filter = [
        'status', 'dispensed_at'
    ]
    search_fields = [
        'prescription__prescription_number', 'prescription_item__drug__name'
    ]
    readonly_fields = [
        'dispensed_at'
    ]
    ordering = ['-dispensed_at']
    
    fieldsets = (
        ('Thông tin cấp thuốc', {
            'fields': ('prescription', 'prescription_item', 'quantity_dispensed')
        }),
        ('Chi tiết', {
            'fields': ('batch_number', 'expiry_date')
        }),
        ('Nhân viên', {
            'fields': ('pharmacist_id',)
        }),
        ('Trạng thái', {
            'fields': ('status', 'notes')
        }),
        ('Thời gian hệ thống', {
            'fields': ('dispensed_at',),
            'classes': ('collapse',)
        }),
    )
