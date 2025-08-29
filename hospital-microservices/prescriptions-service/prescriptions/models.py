from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date, datetime, time, timedelta
import uuid

class DrugCategory(models.Model):
    """Danh mục thuốc"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, help_text="Mã danh mục (VD: ANTIBIOTIC, ANALGESIC)")
    name = models.CharField(max_length=100, help_text="Tên danh mục")
    description = models.TextField(blank=True, help_text="Mô tả danh mục")
    
    # Control
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drug_categories'
        verbose_name = 'Danh mục thuốc'
        verbose_name_plural = 'Danh mục thuốc'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Drug(models.Model):
    """Thuốc trong hệ thống (Microservice version)"""
    
    UNIT_CHOICES = [
        ('TABLET', 'Viên'),
        ('CAPSULE', 'Viên nang'),
        ('BOTTLE', 'Chai'),
        ('BOX', 'Hộp'),
        ('TUBE', 'Tuýp'),
        ('VIAL', 'Lọ'),
        ('AMPOULE', 'Ống thuốc tiêm'),
        ('SACHET', 'Gói'),
        ('ML', 'ml'),
        ('MG', 'mg'),
        ('G', 'g'),
    ]
    
    FORM_CHOICES = [
        ('TABLET', 'Viên nén'),
        ('CAPSULE', 'Viên nang'),
        ('SYRUP', 'Siro'),
        ('INJECTION', 'Tiêm'),
        ('CREAM', 'Kem bôi'),
        ('OINTMENT', 'Thuốc mỡ'),
        ('DROPS', 'Thuốc nhỏ mắt/tai/mũi'),
        ('SPRAY', 'Xịt'),
        ('POWDER', 'Bột'),
        ('SUPPOSITORY', 'Viên đặt'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    code = models.CharField(max_length=50, unique=True, help_text="Mã thuốc")
    name = models.CharField(max_length=200, help_text="Tên thuốc")
    generic_name = models.CharField(max_length=200, help_text="Tên hoạt chất")
    brand_name = models.CharField(max_length=200, blank=True, help_text="Tên thương mại")
    
    # Classification
    category = models.ForeignKey(DrugCategory, on_delete=models.CASCADE, related_name='drugs')
    
    # Physical Properties
    dosage_form = models.CharField(max_length=20, choices=FORM_CHOICES, help_text="Dạng bào chế")
    strength = models.CharField(max_length=100, help_text="Hàm lượng (VD: 500mg, 10ml)")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, help_text="Đơn vị tính")
    
    # Medical Information
    indication = models.TextField(help_text="Chỉ định sử dụng")
    contraindication = models.TextField(blank=True, help_text="Chống chỉ định")
    side_effects = models.TextField(blank=True, help_text="Tác dụng phụ")
    interactions = models.TextField(blank=True, help_text="Tương tác thuốc")
    dosage_adult = models.TextField(blank=True, help_text="Liều dùng người lớn")
    dosage_child = models.TextField(blank=True, help_text="Liều dùng trẻ em")
    
    # Storage & Handling
    storage_condition = models.TextField(blank=True, help_text="Điều kiện bảo quản")
    expiry_after_opening = models.IntegerField(
        null=True, blank=True, 
        help_text="Hạn sử dụng sau khi mở (ngày)"
    )
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=0, 
        help_text="Đơn giá (VNĐ)"
    )
    insurance_price = models.DecimalField(
        max_digits=10, decimal_places=0,
        null=True, blank=True,
        help_text="Giá BHYT (VNĐ)"
    )
    
    # Inventory
    current_stock = models.IntegerField(default=0, help_text="Tồn kho hiện tại")
    minimum_stock = models.IntegerField(default=10, help_text="Tồn kho tối thiểu")
    maximum_stock = models.IntegerField(default=1000, help_text="Tồn kho tối đa")
    
    # Regulatory
    registration_number = models.CharField(
        max_length=50, blank=True, 
        help_text="Số đăng ký thuốc"
    )
    manufacturer = models.CharField(max_length=200, help_text="Nhà sản xuất")
    country_of_origin = models.CharField(max_length=100, help_text="Nước sản xuất")
    
    # Control
    is_prescription_required = models.BooleanField(
        default=True, 
        help_text="Cần đơn thuốc"
    )
    is_controlled_substance = models.BooleanField(
        default=False, 
        help_text="Thuốc kiểm soát đặc biệt"
    )
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người tạo từ Auth Service"
    )
    
    class Meta:
        db_table = 'drugs'
        verbose_name = 'Thuốc'
        verbose_name_plural = 'Thuốc'
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def stock_status(self):
        """Trạng thái tồn kho"""
        if self.current_stock <= 0:
            return "HẾT HÀNG"
        elif self.current_stock <= self.minimum_stock:
            return "SẮP HẾT"
        else:
            return "BÌNH THƯỜNG"
    
    def save(self, *args, **kwargs):
        # Auto-generate code if not provided
        if not self.code:
            self.code = self.generate_drug_code()
        super().save(*args, **kwargs)
    
    def generate_drug_code(self):
        """Tạo mã thuốc tự động: TH + 6 số"""
        from django.db.models import Max
        
        last_drug = Drug.objects.filter(
            code__startswith='TH'
        ).order_by('code').last()
        
        if last_drug:
            try:
                last_number = int(last_drug.code[2:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"TH{new_number:06d}"

class Prescription(models.Model):
    """Đơn thuốc (Microservice version)"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Nháp'),
        ('ACTIVE', 'Có hiệu lực'),
        ('PARTIALLY_DISPENSED', 'Cấp thuốc một phần'),
        ('FULLY_DISPENSED', 'Đã cấp thuốc đầy đủ'),
        ('CANCELLED', 'Đã hủy'),
        ('EXPIRED', 'Hết hạn'),
    ]
    
    TYPE_CHOICES = [
        ('OUTPATIENT', 'Ngoại trú'),
        ('INPATIENT', 'Nội trú'),
        ('EMERGENCY', 'Cấp cứu'),
        ('DISCHARGE', 'Ra viện'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription_number = models.CharField(max_length=30, unique=True)
    
    # Relationships (using UUID instead of ForeignKey)
    patient_id = models.UUIDField(help_text="ID của bệnh nhân từ Patient Service")
    doctor_id = models.UUIDField(help_text="ID của bác sĩ từ Appointment Service")
    appointment_id = models.UUIDField(
        null=True, blank=True,
        help_text="ID của lịch hẹn từ Appointment Service"
    )
    
    # Prescription Details
    prescription_date = models.DateTimeField(auto_now_add=True)
    prescription_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='OUTPATIENT')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Medical Information
    diagnosis = models.TextField(help_text="Chẩn đoán")
    notes = models.TextField(blank=True, help_text="Ghi chú của bác sĩ")
    special_instructions = models.TextField(blank=True, help_text="Hướng dẫn đặc biệt")
    
    # Validity
    valid_from = models.DateTimeField(help_text="Có hiệu lực từ")
    valid_until = models.DateTimeField(help_text="Có hiệu lực đến")
    
    # Financial
    total_amount = models.DecimalField(
        max_digits=12, decimal_places=0, 
        default=0, 
        help_text="Tổng tiền thuốc (VNĐ)"
    )
    insurance_covered_amount = models.DecimalField(
        max_digits=12, decimal_places=0, 
        default=0, 
        help_text="Số tiền BHYT chi trả (VNĐ)"
    )
    patient_payment_amount = models.DecimalField(
        max_digits=12, decimal_places=0, 
        default=0, 
        help_text="Số tiền bệnh nhân trả (VNĐ)"
    )
    
    # Tracking
    created_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người tạo từ Auth Service"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'Đơn thuốc'
        verbose_name_plural = 'Đơn thuốc'
        ordering = ['-prescription_date']
        indexes = [
            models.Index(fields=['patient_id', 'prescription_date']),
            models.Index(fields=['doctor_id', 'prescription_date']),
            models.Index(fields=['status', 'prescription_date']),
            models.Index(fields=['prescription_number']),
        ]
    
    def __str__(self):
        return f"{self.prescription_number}"
    
    @property
    def is_valid(self):
        """Kiểm tra đơn thuốc còn hiệu lực"""
        from django.utils import timezone
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until and self.status == 'ACTIVE'
    
    @property
    def days_until_expiry(self):
        """Số ngày còn lại trước khi hết hạn"""
        from django.utils import timezone
        if self.valid_until > timezone.now():
            return (self.valid_until - timezone.now()).days
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-generate prescription number if not provided
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        
        # Calculate amounts if not set
        if self.total_amount == 0:
            self.calculate_amounts()
        
        super().save(*args, **kwargs)
    
    def generate_prescription_number(self):
        """Tạo mã đơn thuốc tự động: DT + YYYYMMDD + 6 số"""
        from django.utils import timezone
        
        today = timezone.now()
        year_month_day = today.strftime('%Y%m%d')
        prefix = f"DT{year_month_day}"
        
        # Get the last prescription for this date
        last_prescription = Prescription.objects.filter(
            prescription_number__startswith=prefix
        ).order_by('prescription_number').last()
        
        if last_prescription:
            try:
                last_number = int(last_prescription.prescription_number[-6:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:06d}"
    
    def calculate_amounts(self):
        """Tính toán các khoản tiền"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        
        # Calculate insurance amount (80% of total for now)
        self.insurance_covered_amount = total * 0.8
        self.patient_payment_amount = total - self.insurance_covered_amount

class PrescriptionItem(models.Model):
    """Chi tiết đơn thuốc - từng loại thuốc trong đơn (Microservice version)"""
    
    FREQUENCY_CHOICES = [
        ('1X_DAILY', '1 lần/ngày'),
        ('2X_DAILY', '2 lần/ngày'),  
        ('3X_DAILY', '3 lần/ngày'),
        ('4X_DAILY', '4 lần/ngày'),
        ('EVERY_4H', 'Mỗi 4 giờ'),
        ('EVERY_6H', 'Mỗi 6 giờ'),
        ('EVERY_8H', 'Mỗi 8 giờ'),
        ('EVERY_12H', 'Mỗi 12 giờ'),
        ('AS_NEEDED', 'Khi cần thiết'),
        ('BEFORE_MEALS', 'Trước ăn'),
        ('AFTER_MEALS', 'Sau ăn'),
        ('WITH_MEALS', 'Trong bữa ăn'),
        ('BEDTIME', 'Trước khi đi ngủ'),
    ]
    
    ROUTE_CHOICES = [
        ('ORAL', 'Uống'),
        ('TOPICAL', 'Bôi ngoài da'),
        ('INJECTION_IM', 'Tiêm bắp'),
        ('INJECTION_IV', 'Tiêm tĩnh mạch'),
        ('INJECTION_SC', 'Tiêm dưới da'),
        ('INHALATION', 'Hít'),
        ('EYE_DROPS', 'Nhỏ mắt'),
        ('EAR_DROPS', 'Nhỏ tai'),
        ('NASAL_DROPS', 'Nhỏ mũi'),
        ('RECTAL', 'Đặt hậu môn'),
        ('VAGINAL', 'Đặt âm đạo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='prescription_items')
    
    # Dosage Information
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)], 
        help_text="Số lượng thuốc"
    )
    dosage_per_time = models.CharField(
        max_length=100, 
        help_text="Liều dùng mỗi lần (VD: 1 viên, 5ml)"
    )
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, help_text="Tần suất dùng")
    route = models.CharField(max_length=20, choices=ROUTE_CHOICES, help_text="Đường dùng thuốc")
    duration_days = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Số ngày sử dụng"
    )
    
    # Instructions
    instructions = models.TextField(help_text="Hướng dẫn sử dụng chi tiết")
    special_notes = models.TextField(blank=True, help_text="Ghi chú đặc biệt")
    
    # Pricing (snapshot tại thời điểm kê đơn)
    unit_price = models.DecimalField(max_digits=10, decimal_places=0, help_text="Đơn giá tại thời điểm kê đơn")
    total_price = models.DecimalField(max_digits=10, decimal_places=0, help_text="Thành tiền")
    
    # Dispensing tracking
    quantity_dispensed = models.IntegerField(default=0, help_text="Số lượng đã cấp")
    is_substitutable = models.BooleanField(default=True, help_text="Có thể thay thế thuốc tương đương")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prescription_items'
        verbose_name = 'Chi tiết đơn thuốc'
        verbose_name_plural = 'Chi tiết đơn thuốc'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.drug.name} - {self.quantity} {self.drug.unit}"
    
    @property
    def quantity_remaining(self):
        """Số lượng thuốc còn lại chưa cấp"""
        return self.quantity - self.quantity_dispensed
    
    @property
    def is_fully_dispensed(self):
        """Đã cấp thuốc đầy đủ"""
        return self.quantity_dispensed >= self.quantity
    
    @property
    def dispensing_progress(self):
        """Tiến độ cấp thuốc (%)"""
        if self.quantity == 0:
            return 0
        return (self.quantity_dispensed / self.quantity) * 100
    
    def save(self, *args, **kwargs):
        # Capture current drug price
        if not self.unit_price:
            self.unit_price = self.drug.unit_price
        
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        
        super().save(*args, **kwargs)
        
        # Update prescription amounts
        self.prescription.calculate_amounts()
        self.prescription.save()

class PrescriptionDispensing(models.Model):
    """Lịch sử cấp thuốc (Microservice version)"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Chờ cấp thuốc'),
        ('PREPARED', 'Đã soạn thuốc'),
        ('DISPENSED', 'Đã cấp thuốc'),
        ('RETURNED', 'Đã trả lại'),
        ('CANCELLED', 'Đã hủy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='dispensing_records')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='dispensing_records')
    
    # Dispensing details
    quantity_dispensed = models.IntegerField(validators=[MinValueValidator(1)])
    batch_number = models.CharField(max_length=50, blank=True, help_text="Số lô thuốc")
    expiry_date = models.DateField(help_text="Hạn sử dụng thuốc đã cấp")
    
    # Personnel (using UUID instead of ForeignKey)
    pharmacist_id = models.UUIDField(
        help_text="ID của dược sĩ từ Auth Service"
    )
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    dispensed_at = models.DateTimeField(auto_now_add=True)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Ghi chú khi cấp thuốc")
    
    class Meta:
        db_table = 'prescription_dispensing'
        verbose_name = 'Lịch sử cấp thuốc'
        verbose_name_plural = 'Lịch sử cấp thuốc'
        ordering = ['-dispensed_at']
    
    def __str__(self):
        return f"{self.prescription.prescription_number} - {self.prescription_item.drug.name} - {self.quantity_dispensed}"
    
    def save(self, *args, **kwargs):
        # Update prescription item dispensing progress
        if self.status == 'DISPENSED':
            self.prescription_item.quantity_dispensed += self.quantity_dispensed
            self.prescription_item.save()
        
        super().save(*args, **kwargs)
