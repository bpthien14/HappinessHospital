from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Payment(models.Model):
    """Payment record linked to a prescription (Microservice version).
    
    Payment is required after a prescription is created and before dispensing.
    Note: No direct User model dependencies - uses UUID references instead
    """

    METHOD_CHOICES = [
        ("CASH", "Tiền mặt"),
        ("VNPAY", "VNPAY"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Chờ thanh toán"),
        ("PAID", "Đã thanh toán"),
        ("FAILED", "Thất bại"),
        ("REFUNDED", "Đã hoàn tiền"),
        ("CANCELLED", "Đã hủy"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships (using UUID instead of ForeignKey)
    prescription_id = models.UUIDField(
        help_text="ID của đơn thuốc từ Prescriptions Service"
    )

    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=0, 
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='VND')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    # VNPAY fields
    vnp_TxnRef = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Mã giao dịch VNPAY"
    )
    vnp_Amount = models.BigIntegerField(
        null=True, 
        blank=True, 
        help_text="Số tiền VNPAY (x100)"
    )
    vnp_OrderInfo = models.TextField(
        blank=True, 
        help_text="Mô tả đơn hàng VNPAY"
    )
    vnp_ResponseCode = models.CharField(
        max_length=10, 
        blank=True, 
        help_text="Mã phản hồi VNPAY"
    )
    vnp_TransactionNo = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Mã giao dịch ngân hàng"
    )
    vnp_BankCode = models.CharField(
        max_length=20, 
        blank=True, 
        help_text="Mã ngân hàng thanh toán"
    )
    vnp_PayDate = models.CharField(
        max_length=14, 
        blank=True, 
        help_text="Thời gian thanh toán VNPAY"
    )
    vnp_SecureHash = models.CharField(
        max_length=256, 
        blank=True, 
        help_text="Chữ ký bảo mật VNPAY"
    )
    

    # Audit (using UUID instead of ForeignKey)
    created_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người tạo từ Auth Service"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'Thanh toán'
        verbose_name_plural = 'Thanh toán'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prescription_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['vnp_TxnRef']),
        ]

    def __str__(self) -> str:
        return f"{self.prescription_id} - {self.method} - {self.amount} {self.currency} ({self.status})"

    @property
    def is_success(self) -> bool:
        return self.status == 'PAID'
    
    def save(self, *args, **kwargs):
        # Kiểm tra nếu trạng thái chuyển sang PAID
        is_new = self.pk is None
        old_status = None
        
        if not is_new:
            try:
                old_payment = Payment.objects.get(pk=self.pk)
                old_status = old_payment.status
            except Payment.DoesNotExist:
                old_status = None
        
        super().save(*args, **kwargs)
        
        # Nếu thanh toán thành công, thông báo cho Prescriptions Service
        if self.status == 'PAID' and old_status != 'PAID':
            # TODO: Send event to Prescriptions Service to update dispensing status
            pass

    @staticmethod
    def calculate_due_amount(prescription_amount: Decimal) -> Decimal:
        """Return amount patient must pay for the prescription."""
        return prescription_amount or Decimal(0)

    def get_vnpay_payment_url(self):
        """Generate VNPAY payment URL if method is VNPAY"""
        if self.method == 'VNPAY' and self.vnp_TxnRef:
            from .services import VNPayService
            vnpay_service = VNPayService()
            payment_url, _ = vnpay_service.create_payment_url(self, self.vnp_OrderInfo)
            return payment_url
        return None



class VNPayTransaction(models.Model):
    """VNPAY transaction tracking for audit purposes (Microservice version)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='vnpay_transaction'
    )
    
    # VNPAY request details
    vnp_TxnRef = models.CharField(max_length=50, unique=True)
    vnp_Amount = models.BigIntegerField()
    vnp_OrderInfo = models.TextField()
    vnp_CreateDate = models.CharField(max_length=14)
    vnp_IpAddr = models.GenericIPAddressField()
    
    # VNPAY response details
    vnp_ResponseCode = models.CharField(max_length=10, blank=True)
    vnp_TransactionNo = models.CharField(max_length=50, blank=True)
    vnp_BankCode = models.CharField(max_length=20, blank=True)
    vnp_PayDate = models.CharField(max_length=14, blank=True)
    vnp_SecureHash = models.CharField(max_length=256, blank=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20, 
        choices=Payment.STATUS_CHOICES, 
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vnpay_transactions'
        verbose_name = 'Giao dịch VNPAY'
        verbose_name_plural = 'Giao dịch VNPAY'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['vnp_TxnRef']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.vnp_TxnRef} - {self.payment.prescription_id}"


class PaymentReceipt(models.Model):
    """Cashier receipt for a payment (Microservice version)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(
        Payment, 
        on_delete=models.CASCADE, 
        related_name='receipt'
    )
    receipt_number = models.CharField(max_length=30, unique=True)
    
    # Using UUID instead of ForeignKey
    cashier_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của thu ngân từ Auth Service"
    )
    
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_receipts'
        verbose_name = 'Phiếu thu'
        verbose_name_plural = 'Phiếu thu'
        indexes = [
            models.Index(fields=['receipt_number']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.receipt_number} - {self.payment.amount} VND"

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = self.generate_receipt_number()
        super().save(*args, **kwargs)

    def generate_receipt_number(self) -> str:
        from django.utils import timezone
        today = timezone.now().date()
        prefix = f"PT{today.strftime('%Y%m%d')}"
        last = PaymentReceipt.objects.filter(
            receipt_number__startswith=prefix
        ).order_by('receipt_number').last()
        
        if last:
            try:
                last_no = int(last.receipt_number[-6:])
                next_no = last_no + 1
            except ValueError:
                next_no = 1
        else:
            next_no = 1
            
        return f"{prefix}{next_no:06d}"
