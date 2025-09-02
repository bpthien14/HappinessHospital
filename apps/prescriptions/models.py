from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid

User = get_user_model()

class DrugCategory(models.Model):
    """Nhóm thuốc (VD: Kháng sinh, Tim mạch, Tiêu hóa)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True, help_text="Mã nhóm thuốc")
    name = models.CharField(max_length=100, help_text="Tên nhóm thuốc")
    description = models.TextField(blank=True, help_text="Mô tả nhóm thuốc")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategories',
        help_text="Nhóm thuốc cha (nếu có)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'drug_categories'
        verbose_name = 'Nhóm thuốc'
        verbose_name_plural = 'Nhóm thuốc'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Drug(models.Model):
    """Thuốc trong hệ thống"""
    
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
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_drugs'
    )
    
    class Meta:
        db_table = 'drugs'
        verbose_name = 'Thuốc'
        verbose_name_plural = 'Thuốc'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['code']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} {self.strength}"
    
    @property
    def is_low_stock(self):
        """Kiểm tra thuốc sắp hết hàng"""
        return self.current_stock <= self.minimum_stock
    
    @property
    def stock_status(self):
        """Trạng thái tồn kho"""
        if self.current_stock <= 0:
            return "HẾT HÀNG"
        elif self.current_stock <= self.minimum_stock:
            return "SẮP HẾT"
        elif self.current_stock >= self.maximum_stock:
            return "DƯ THỪA"
        else:
            return "BÌNH THƯỜNG"

class Prescription(models.Model):
    """Đơn thuốc"""
    
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
    
    # Relationships
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='prescriptions'
    )
    doctor = models.ForeignKey(
        'appointments.DoctorProfile', 
        on_delete=models.CASCADE, 
        related_name='prescriptions'
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='prescriptions',
        help_text="Lịch khám liên quan (nếu có)"
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
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_prescriptions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'prescriptions'
        verbose_name = 'Đơn thuốc'
        verbose_name_plural = 'Đơn thuốc'
        ordering = ['-prescription_date']
        indexes = [
            models.Index(fields=['patient', 'prescription_date']),
            models.Index(fields=['doctor', 'prescription_date']),
            models.Index(fields=['status', 'prescription_date']),
            models.Index(fields=['prescription_number']),
        ]
    
    def __str__(self):
        return f"{self.prescription_number} - {self.patient.full_name}"
    
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
        if not self.prescription_number:
            self.prescription_number = self.generate_prescription_number()
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Tạo PrescriptionDispensing record với status UNPAID cho đơn thuốc mới
        if is_new and self.status == 'ACTIVE':
            self.create_initial_dispensing_records()
    
    def create_initial_dispensing_records(self):
        """Tạo các record dispensing ban đầu với status UNPAID"""
        for item in self.items.all():
            PrescriptionDispensing.objects.get_or_create(
                prescription=self,
                prescription_item=item,
                defaults={
                    'quantity_dispensed': 0,
                    'status': 'UNPAID',
                    'pharmacist': None,  # Sẽ được set khi có dược sĩ xử lý
                    'notes': 'Chờ thanh toán'
                }
            )
    
    def generate_prescription_number(self):
        """Tạo số đơn thuốc: DT + YYYYMMDD + 6 số"""
        from django.utils import timezone
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        prefix = f"DT{date_str}"
        
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
    
    def calculate_total_amount(self):
        """Tính tổng tiền đơn thuốc"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        return total
    
    def calculate_insurance_amounts(self):
        """Tính số tiền BHYT chi trả và bệnh nhân phải trả"""
        if not self.patient.has_insurance:
            self.insurance_covered_amount = 0
            self.patient_payment_amount = self.total_amount
            return
        
        total_covered = 0
        total_patient = 0
        
        for item in self.items.all():
            if item.drug.insurance_price:
                # BHYT chi trả theo giá BHYT
                covered = item.quantity * item.drug.insurance_price
                patient = max(0, item.total_price - covered)
            else:
                # Thuốc không có trong danh mục BHYT
                covered = 0
                patient = item.total_price
            
            total_covered += covered
            total_patient += patient
        
        self.insurance_covered_amount = total_covered
        self.patient_payment_amount = total_patient
    
    def mark_as_paid(self):
        """Đánh dấu đơn thuốc đã thanh toán - chuyển dispensing status từ UNPAID sang PENDING"""
        self.dispensing_records.filter(status='UNPAID').update(
            status='PENDING',
            notes='Đã thanh toán, chờ cấp thuốc'
        )
    
    def get_dispensing_status(self):
        """Lấy trạng thái dispensing chung của đơn thuốc"""
        dispensing_records = self.dispensing_records.all()
        if not dispensing_records.exists():
            return 'UNPAID'
        
        statuses = set(dispensing_records.values_list('status', flat=True))
        
        if 'UNPAID' in statuses:
            return 'UNPAID'
        elif all(status == 'DISPENSED' for status in statuses):
            return 'DISPENSED'
        elif 'PREPARED' in statuses:
            return 'PREPARED'
        elif 'PENDING' in statuses:
            return 'PENDING'
        elif 'CANCELLED' in statuses:
            return 'CANCELLED'
        else:
            return 'PENDING'

class PrescriptionItem(models.Model):
    """Chi tiết đơn thuốc - từng loại thuốc trong đơn"""
    
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
        
        # Update prescription total
        self.prescription.calculate_total_amount()
        self.prescription.calculate_insurance_amounts()
        self.prescription.save()

class PrescriptionDispensing(models.Model):
    """Lịch sử cấp thuốc"""
    
    STATUS_CHOICES = [
        ('UNPAID', 'Chưa thanh toán'),
        ('PENDING', 'Chờ cấp thuốc'),
        ('PREPARED', 'Đã soạn thuốc'),
        ('DISPENSED', 'Đã cấp thuốc'),
        ('CANCELLED', 'Đã hủy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='dispensing_records')
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='dispensing_records')
    
    # Dispensing details
    quantity_dispensed = models.IntegerField(validators=[MinValueValidator(1)])
    batch_number = models.CharField(max_length=50, blank=True, help_text="Số lô thuốc")
    expiry_date = models.DateField(help_text="Hạn sử dụng thuốc đã cấp")
    
    # Personnel
    pharmacist = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='dispensed_prescriptions',
        help_text="Dược sĩ cấp thuốc"
    )
    
    # Status and timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
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
        super().save(*args, **kwargs)
        
        # Update prescription item dispensed quantity
        if self.status == 'DISPENSED':
            total_dispensed = sum(
                record.quantity_dispensed 
                for record in self.prescription_item.dispensing_records.filter(status='DISPENSED')
            )
            self.prescription_item.quantity_dispensed = total_dispensed
            self.prescription_item.save()
            
            # Update prescription status
            self.update_prescription_status()
    
    def update_prescription_status(self):
        """Cập nhật trạng thái đơn thuốc dựa trên tiến độ cấp thuốc"""
        prescription = self.prescription
        all_items = prescription.items.all()
        
        if all_items:
            fully_dispensed_items = sum(1 for item in all_items if item.is_fully_dispensed)
            partially_dispensed_items = sum(1 for item in all_items if 0 < item.quantity_dispensed < item.quantity)
            
            if fully_dispensed_items == len(all_items):
                prescription.status = 'FULLY_DISPENSED'
            elif fully_dispensed_items > 0 or partially_dispensed_items > 0:
                prescription.status = 'PARTIALLY_DISPENSED'
            
            prescription.save()
    
    def mark_as_prepared(self, pharmacist=None, notes=''):
        """Đánh dấu thuốc đã chuẩn bị"""
        if self.status == 'PENDING':
            self.status = 'PREPARED'
            if pharmacist:
                self.pharmacist = pharmacist
            if notes:
                self.notes = notes
            self.save()
            return True
        return False
    
    def mark_as_dispensed(self, pharmacist=None, notes=''):
        """Đánh dấu thuốc đã cấp phát"""
        if self.status == 'PREPARED':
            self.status = 'DISPENSED'
            if pharmacist:
                self.pharmacist = pharmacist
            if notes:
                self.notes = notes
            self.save()
            
            # Cập nhật trạng thái prescription nếu tất cả items đã dispensed
            all_dispensing = self.prescription.dispensing_records.all()
            if all(d.status == 'DISPENSED' for d in all_dispensing):
                self.prescription.status = 'FULLY_DISPENSED'
                self.prescription.save()
            
            return True
        return False

class DrugInteraction(models.Model):
    """Tương tác thuốc"""
    
    SEVERITY_CHOICES = [
        ('MINOR', 'Nhẹ'),
        ('MODERATE', 'Trung bình'),
        ('MAJOR', 'Nghiêm trọng'),
        ('CONTRAINDICATED', 'Chống chỉ định tuyệt đối'),
    ]
    
    drug1 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug1')
    drug2 = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name='interactions_as_drug2')
    
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField(help_text="Mô tả tương tác")
    clinical_effect = models.TextField(help_text="Tác động lâm sàng")
    management = models.TextField(help_text="Cách xử lý")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'drug_interactions'
        unique_together = ['drug1', 'drug2']
        verbose_name = 'Tương tác thuốc'
        verbose_name_plural = 'Tương tác thuốc'
    
    def __str__(self):
        return f"{self.drug1.name} ↔ {self.drug2.name} ({self.get_severity_display()})"