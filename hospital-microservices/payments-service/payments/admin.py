from django.contrib import admin
from .models import Payment, VNPayTransaction, PaymentReceipt


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'prescription_id', 'method', 'amount', 'currency', 
        'status', 'vnp_TxnRef', 'created_at'
    ]
    list_filter = ['method', 'status', 'currency', 'created_at']
    search_fields = ['prescription_id', 'vnp_TxnRef', 'vnp_TransactionNo']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('id', 'prescription_id', 'method', 'amount', 'currency', 'status')
        }),
        ('Thông tin VNPAY', {
            'fields': (
                'vnp_TxnRef', 'vnp_Amount', 'vnp_OrderInfo', 'vnp_ResponseCode',
                'vnp_TransactionNo', 'vnp_BankCode', 'vnp_PayDate', 'vnp_SecureHash'
            ),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_by_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VNPayTransaction)
class VNPayTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'vnp_TxnRef', 'payment', 'vnp_Amount', 'status', 
        'vnp_ResponseCode', 'created_at'
    ]
    list_filter = ['status', 'vnp_ResponseCode', 'created_at']
    search_fields = ['vnp_TxnRef', 'payment__prescription_id', 'vnp_TransactionNo']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin giao dịch', {
            'fields': ('id', 'payment', 'vnp_TxnRef', 'status')
        }),
        ('Thông tin yêu cầu', {
            'fields': ('vnp_Amount', 'vnp_OrderInfo', 'vnp_CreateDate', 'vnp_IpAddr'),
            'classes': ('collapse',)
        }),
        ('Thông tin phản hồi', {
            'fields': (
                'vnp_ResponseCode', 'vnp_TransactionNo', 'vnp_BankCode', 
                'vnp_PayDate', 'vnp_SecureHash'
            ),
            'classes': ('collapse',)
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = [
        'receipt_number', 'payment', 'cashier_id', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['receipt_number', 'payment__prescription_id']
    readonly_fields = ['id', 'receipt_number', 'created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Thông tin phiếu thu', {
            'fields': ('id', 'payment', 'receipt_number', 'cashier_id', 'note')
        }),
        ('Thông tin hệ thống', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
