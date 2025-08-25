from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import uuid
from datetime import date

User = get_user_model()

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Nam'),
        ('F', 'Nữ'),
        ('O', 'Khác'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    # Primary Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_code = models.CharField(max_length=20, unique=True, help_text="Mã bệnh nhân tự động")
    
    # Personal Information
    full_name = models.CharField(max_length=255, help_text="Họ và tên đầy đủ")
    date_of_birth = models.DateField(help_text="Ngày sinh")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, help_text="Giới tính")
    
    # Contact Information
    phone_validator = RegexValidator(
        regex=r'^(\+84|0)[3|5|7|8|9](\d{8})$',
        message="Số điện thoại phải chuẩn định dạng Việt Nam và đủ 10 số"
    )
    phone_number = models.CharField(
        max_length=15, 
        validators=[phone_validator],
        unique=True,
        help_text="Số điện thoại liên lạc"
    )
    email = models.EmailField(blank=True, null=True, help_text="Email (không bắt buộc)")
    
    # Address Information
    address = models.TextField(help_text="Địa chỉ thường trú")
    ward = models.CharField(max_length=100, help_text="Phường/Xã")
    district = models.CharField(max_length=100, help_text="Quận/Huyện")
    province = models.CharField(max_length=100, help_text="Tỉnh/Thành phố")
    
    # Identity Information
    citizen_id = models.CharField(
        max_length=12,
        unique=True,
        validators=[RegexValidator(
            regex=r'^\d{12}$',
            message="CCCD phải có đúng 12 số"
        )],
        help_text="Số CCCD"
    )
    
    # Medical Information
    blood_type = models.CharField(
        max_length=3, 
        choices=BLOOD_TYPE_CHOICES, 
        blank=True, 
        null=True,
        help_text="Nhóm máu"
    )
    allergies = models.TextField(blank=True, help_text="Dị ứng (nếu có)")
    chronic_diseases = models.TextField(blank=True, help_text="Bệnh mãn tính (nếu có)")
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, help_text="Tên người liên hệ khẩn cấp")
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[phone_validator],
        help_text="SĐT người liên hệ khẩn cấp"
    )
    emergency_contact_relationship = models.CharField(
        max_length=100,
        help_text="Mối quan hệ với bệnh nhân"
    )
    
    # Insurance Information
    has_insurance = models.BooleanField(default=False, help_text="Có BHYT")
    insurance_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="Số thẻ BHYT"
    )
    insurance_valid_from = models.DateField(blank=True, null=True, help_text="BHYT hiệu lực từ")
    insurance_valid_to = models.DateField(blank=True, null=True, help_text="BHYT hiệu lực đến")
    insurance_hospital_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Mã nơi đăng ký KCB ban đầu"
    )
    
    # System Information
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_patients',
        help_text="Người tạo hồ sơ"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_patients',
        help_text="Người cập nhật cuối"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True, help_text="Trạng thái hoạt động")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
        verbose_name = 'Bệnh nhân'
        verbose_name_plural = 'Bệnh nhân'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['patient_code']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['citizen_id']),
            models.Index(fields=['full_name']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.patient_code} - {self.full_name}"
    
    @property
    def age(self):
        """Tính tuổi từ ngày sinh"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_address(self):
        """Địa chỉ đầy đủ"""
        return f"{self.address}, {self.ward}, {self.district}, {self.province}"
    
    @property
    def insurance_status(self):
        """Trạng thái BHYT"""
        if not self.has_insurance:
            return "Không có BHYT"
        
        if not self.insurance_valid_to:
            return "BHYT không xác định hạn"
        
        today = date.today()
        if today > self.insurance_valid_to:
            return "BHYT hết hạn"
        elif today < self.insurance_valid_from:
            return "BHYT chưa có hiệu lực"
        else:
            return "BHYT có hiệu lực"
    
    def save(self, *args, **kwargs):
        # Auto-generate patient code if not provided
        if not self.patient_code:
            self.patient_code = self.generate_patient_code()
        super().save(*args, **kwargs)
    
    def generate_patient_code(self):
        """Tạo mã bệnh nhân tự động: BN + YYYYMM + 4 số"""
        from django.utils import timezone
        
        today = timezone.now()
        year_month = today.strftime('%Y%m')
        prefix = f"BN{year_month}"
        
        # Get the last patient code for this month
        last_patient = Patient.objects.filter(
            patient_code__startswith=prefix
        ).order_by('patient_code').last()
        
        if last_patient:
            try:
                last_number = int(last_patient.patient_code[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"

class MedicalRecord(models.Model):
    VISIT_TYPES = [
        ('OUTPATIENT', 'Ngoại trú'),
        ('INPATIENT', 'Nội trú'),
        ('EMERGENCY', 'Cấp cứu'),
        ('CHECKUP', 'Khám sức khỏe'),
    ]
    
    STATUS_CHOICES = [
        ('WAITING', 'Chờ khám'),
        ('IN_PROGRESS', 'Đang khám'),
        ('COMPLETED', 'Hoàn thành'),
        ('CANCELLED', 'Hủy'),
    ]
    
    # Primary Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    medical_record_number = models.CharField(max_length=20, unique=True)
    
    # Relationships
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records',
        help_text="Bệnh nhân"
    )
    doctor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='medical_records',
        help_text="Bác sĩ khám"
    )
    
    # Visit Information
    visit_date = models.DateTimeField(help_text="Ngày giờ khám")
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES, help_text="Loại khám")
    department = models.CharField(max_length=100, help_text="Khoa/Phòng khám")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    
    # Medical Information
    chief_complaint = models.TextField(help_text="Lý do khám (triệu chứng chính)")
    history_of_present_illness = models.TextField(blank=True, help_text="Bệnh sử")
    physical_examination = models.TextField(blank=True, help_text="Khám lâm sàng")
    
    # Vital Signs
    temperature = models.FloatField(null=True, blank=True, help_text="Nhiệt độ (°C)")
    blood_pressure_systolic = models.IntegerField(null=True, blank=True, help_text="Huyết áp tâm thu")
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True, help_text="Huyết áp tâm trương")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Nhịp tim (bpm)")
    respiratory_rate = models.IntegerField(null=True, blank=True, help_text="Nhịp thở")
    weight = models.FloatField(null=True, blank=True, help_text="Cân nặng (kg)")
    height = models.FloatField(null=True, blank=True, help_text="Chiều cao (cm)")
    
    # Diagnosis and Treatment
    preliminary_diagnosis = models.TextField(blank=True, help_text="Chẩn đoán sơ bộ")
    final_diagnosis = models.TextField(blank=True, help_text="Chẩn đoán cuối cùng")
    treatment_plan = models.TextField(blank=True, help_text="Kế hoạch điều trị")
    notes = models.TextField(blank=True, help_text="Ghi chú của bác sĩ")
    
    # Follow-up
    next_appointment = models.DateTimeField(null=True, blank=True, help_text="Hẹn tái khám")
    follow_up_instructions = models.TextField(blank=True, help_text="Hướng dẫn tái khám")
    
    # System Information
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_medical_records'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_medical_records'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'medical_records'
        verbose_name = 'Hồ sơ bệnh án'
        verbose_name_plural = 'Hồ sơ bệnh án'
        ordering = ['-visit_date']
        indexes = [
            models.Index(fields=['patient', 'visit_date']),
            models.Index(fields=['doctor', 'visit_date']),
            models.Index(fields=['visit_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.medical_record_number} - {self.patient.full_name} - {self.visit_date.strftime('%d/%m/%Y')}"
    
    @property
    def blood_pressure(self):
        """Huyết áp dạng chuỗi"""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @property
    def bmi(self):
        """Chỉ số BMI"""
        if self.weight and self.height:
            height_m = self.height / 100
            return round(self.weight / (height_m ** 2), 2)
        return None
    
    def save(self, *args, **kwargs):
        # Auto-generate medical record number if not provided
        if not self.medical_record_number:
            self.medical_record_number = self.generate_record_number()
        super().save(*args, **kwargs)
    
    def generate_record_number(self):
        """Tạo số hồ sơ bệnh án: HSB + YYYYMMDD + 4 số"""
        from django.utils import timezone
        
        today = timezone.now()
        date_str = today.strftime('%Y%m%d')
        prefix = f"HSB{date_str}"
        
        # Get the last record for today
        last_record = MedicalRecord.objects.filter(
            medical_record_number__startswith=prefix
        ).order_by('medical_record_number').last()
        
        if last_record:
            try:
                last_number = int(last_record.medical_record_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"

class PatientDocument(models.Model):
    DOCUMENT_TYPES = [
        ('ID_CARD', 'CCCD/CMND'),
        ('INSURANCE_CARD', 'Thẻ BHYT'),
        ('MEDICAL_REPORT', 'Báo cáo y tế'),
        ('LAB_RESULT', 'Kết quả xét nghiệm'),
        ('PRESCRIPTION', 'Đơn thuốc'),
        ('DISCHARGE_SUMMARY', 'Tóm tắt xuất viện'),
        ('OTHER', 'Khác'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='documents',
        help_text="Bệnh nhân"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, help_text="Loại tài liệu")
    title = models.CharField(max_length=255, help_text="Tiêu đề tài liệu")
    description = models.TextField(blank=True, help_text="Mô tả")
    file = models.FileField(upload_to='patient_documents/%Y/%m/', help_text="File tài liệu")
    file_size = models.PositiveIntegerField(help_text="Kích thước file (bytes)")
    
    # System Information
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="Người tải lên"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'patient_documents'
        verbose_name = 'Tài liệu bệnh nhân'
        verbose_name_plural = 'Tài liệu bệnh nhân'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.title}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)