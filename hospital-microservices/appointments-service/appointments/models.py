from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date, datetime, time, timedelta
import uuid

class Department(models.Model):
    """Khoa/Phòng khám trong bệnh viện (Microservice version)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, help_text="Mã khoa (VD: TIM, NOI, NGOAI)")
    name = models.CharField(max_length=100, help_text="Tên khoa")
    description = models.TextField(blank=True, help_text="Mô tả về khoa")
    location = models.CharField(max_length=100, blank=True, help_text="Vị trí (tầng, phòng)")
    phone = models.CharField(max_length=15, blank=True, help_text="SĐT liên hệ")
    
    # Service settings
    consultation_fee = models.DecimalField(
        max_digits=10, decimal_places=0, 
        default=100000, 
        help_text="Phí khám cơ bản (VNĐ)"
    )
    average_consultation_time = models.IntegerField(
        default=30, 
        help_text="Thời gian khám trung bình (phút)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'departments'
        verbose_name = 'Khoa/Phòng khám'
        verbose_name_plural = 'Khoa/Phòng khám'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class DoctorProfile(models.Model):
    """Hồ sơ bác sĩ với thông tin chuyên môn (Microservice version)"""
    
    SPECIALIZATION_CHOICES = [
        ('INTERNAL_MEDICINE', 'Nội khoa'),
        ('SURGERY', 'Ngoại khoa'),
        ('PEDIATRICS', 'Nhi khoa'),
        ('OBSTETRICS', 'Sản khoa'),
        ('CARDIOLOGY', 'Tim mạch'),
        ('NEUROLOGY', 'Thần kinh'),
        ('ORTHOPEDICS', 'Chỉnh hình'),
        ('DERMATOLOGY', 'Da liễu'),
        ('OPHTHALMOLOGY', 'Mắt'),
        ('ENT', 'Tai mũi họng'),
        ('PSYCHIATRY', 'Tâm thần'),
        ('EMERGENCY', 'Cấp cứu'),
        ('RADIOLOGY', 'Chẩn đoán hình ảnh'),
        ('LABORATORY', 'Xét nghiệm'),
        ('PHARMACY', 'Dược'),
        ('OTHER', 'Khác'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(help_text="ID của user từ Auth Service")
    
    # Professional information
    specialization = models.CharField(
        max_length=30, 
        choices=SPECIALIZATION_CHOICES,
        help_text="Chuyên khoa"
    )
    license_number = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Số chứng chỉ hành nghề"
    )
    experience_years = models.PositiveIntegerField(
        default=0,
        help_text="Số năm kinh nghiệm"
    )
    
    # Department assignment
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        related_name='doctors'
    )
    
    # Schedule settings
    max_appointments_per_day = models.PositiveIntegerField(
        default=20,
        help_text="Số lịch hẹn tối đa mỗi ngày"
    )
    consultation_duration = models.PositiveIntegerField(
        default=30,
        help_text="Thời gian khám mỗi bệnh nhân (phút)"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_profiles'
        verbose_name = 'Hồ sơ bác sĩ'
        verbose_name_plural = 'Hồ sơ bác sĩ'
        ordering = ['specialization', 'experience_years']
    
    def __str__(self):
        return f"Dr. {self.specialization} - {self.department.name}"

class DoctorSchedule(models.Model):
    """Lịch làm việc của bác sĩ (Microservice version)"""
    
    SHIFT_CHOICES = [
        ('MORNING', 'Sáng (7:00-12:00)'),
        ('AFTERNOON', 'Chiều (13:00-17:00)'),
        ('EVENING', 'Tối (18:00-22:00)'),
        ('NIGHT', 'Đêm (22:00-7:00)'),
        ('FULL_DAY', 'Cả ngày (7:00-17:00)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    
    # Schedule details
    date = models.DateField(help_text="Ngày làm việc")
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, help_text="Ca làm việc")
    start_time = models.TimeField(help_text="Giờ bắt đầu")
    end_time = models.TimeField(help_text="Giờ kết thúc")
    
    # Availability
    is_available = models.BooleanField(default=True, help_text="Có thể đặt lịch không")
    max_appointments = models.PositiveIntegerField(
        default=20,
        help_text="Số lịch hẹn tối đa"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_schedules'
        verbose_name = 'Lịch làm việc bác sĩ'
        verbose_name_plural = 'Lịch làm việc bác sĩ'
        unique_together = ['doctor', 'date', 'shift']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.shift}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Giờ bắt đầu phải trước giờ kết thúc')

class Appointment(models.Model):
    """Lịch hẹn khám bệnh (Microservice version)"""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Đã đặt lịch'),
        ('CONFIRMED', 'Đã xác nhận'),
        ('CHECKED_IN', 'Đã check-in'),
        ('IN_PROGRESS', 'Đang khám'),
        ('COMPLETED', 'Hoàn thành'),
        ('NO_SHOW', 'Không đến'),
        ('CANCELLED', 'Đã hủy'),
        ('RESCHEDULED', 'Đã dời lịch'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Thường'),
        ('NORMAL', 'Bình thường'),
        ('HIGH', 'Ưu tiên'),
        ('URGENT', 'Khẩn cấp'),
    ]
    
    APPOINTMENT_TYPE_CHOICES = [
        ('NEW', 'Khám mới'),
        ('FOLLOW_UP', 'Tái khám'),
        ('CONSULTATION', 'Tư vấn'),
        ('CHECKUP', 'Khám sức khỏe'),
        ('EMERGENCY', 'Cấp cứu'),
    ]
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment_number = models.CharField(max_length=20, unique=True)
    
    # Relationships (using UUID instead of ForeignKey)
    patient_id = models.UUIDField(help_text="ID của bệnh nhân từ Patient Service")
    doctor_id = models.UUIDField(help_text="ID của bác sĩ")
    department_id = models.UUIDField(help_text="ID của khoa")
    
    # Appointment details
    appointment_date = models.DateField(help_text="Ngày khám")
    appointment_time = models.TimeField(help_text="Giờ khám")
    estimated_duration = models.IntegerField(default=15, help_text="Thời gian dự kiến (phút)")
    
    # Classification
    appointment_type = models.CharField(max_length=20, choices=APPOINTMENT_TYPE_CHOICES, default='NEW')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Queue management
    queue_number = models.IntegerField(help_text="Số thứ tự khám")
    
    # Patient information
    chief_complaint = models.TextField(help_text="Lý do khám chính")
    symptoms = models.TextField(blank=True, help_text="Triệu chứng kèm theo")
    notes = models.TextField(blank=True, help_text="Ghi chú thêm")
    
    # Administrative (using UUID instead of ForeignKey)
    booked_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người đặt lịch từ Auth Service"
    )
    confirmed_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người xác nhận từ Auth Service"
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Check-in information
    checked_in_at = models.DateTimeField(null=True, blank=True)
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'appointments'
        verbose_name = 'Lịch hẹn khám'
        verbose_name_plural = 'Lịch hẹn khám'
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['patient_id', 'appointment_date']),
            models.Index(fields=['doctor_id', 'appointment_date']),
            models.Index(fields=['status', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.appointment_number} - {self.appointment_date}"
    
    @property
    def appointment_datetime(self):
        """Kết hợp ngày và giờ thành datetime"""
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    @property
    def is_today(self):
        """Kiểm tra xem có phải hôm nay không"""
        return self.appointment_date == date.today()
    
    @property
    def is_past_due(self):
        """Kiểm tra xem có quá hạn không"""
        return self.appointment_date < date.today()
    
    @property
    def can_cancel(self):
        """Kiểm tra xem có thể hủy không"""
        return self.status in ['SCHEDULED', 'CONFIRMED']
    
    @property
    def can_checkin(self):
        """Kiểm tra xem có thể check-in không"""
        return self.status in ['CONFIRMED', 'SCHEDULED'] and self.is_today
    
    def save(self, *args, **kwargs):
        # Auto-generate appointment number if not provided
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
        
        # Auto-generate queue number if not provided
        if not self.queue_number:
            self.queue_number = self.get_next_queue_number()
        
        super().save(*args, **kwargs)
    
    def generate_appointment_number(self):
        """Tạo mã lịch hẹn tự động: LH + YYYYMM + 4 số"""
        from django.utils import timezone
        
        today = timezone.now()
        year_month = today.strftime('%Y%m')
        prefix = f"LH{year_month}"
        
        # Get the last appointment for this month
        last_appointment = Appointment.objects.filter(
            appointment_number__startswith=prefix
        ).order_by('appointment_number').last()
        
        if last_appointment:
            try:
                last_number = int(last_appointment.appointment_number[-4:])
                new_number = last_number + 1
            except ValueError:
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:04d}"
    
    def get_next_queue_number(self):
        """Lấy số thứ tự tiếp theo cho ngày hôm đó"""
        from django.db.models import Max
        
        max_queue = Appointment.objects.filter(
            appointment_date=self.appointment_date,
            department_id=self.department_id
        ).aggregate(Max('queue_number'))['queue_number__max']
        
        return (max_queue or 0) + 1

class AppointmentStatusHistory(models.Model):
    """Lịch sử thay đổi trạng thái lịch hẹn (Microservice version)"""
    
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    changed_by_id = models.UUIDField(
        null=True, 
        blank=True,
        help_text="ID của người thay đổi từ Auth Service"
    )
    reason = models.TextField(blank=True, help_text="Lý do thay đổi")
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'appointment_status_history'
        verbose_name = 'Lịch sử trạng thái lịch hẹn'
        verbose_name_plural = 'Lịch sử trạng thái lịch hẹn'
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.appointment.appointment_number}: {self.old_status} → {self.new_status}"

class TimeSlot(models.Model):
    """Time slots cho việc đặt lịch (Microservice version)"""
    
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='time_slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    is_available = models.BooleanField(default=True)
    max_appointments = models.IntegerField(default=1)
    current_appointments = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'time_slots'
        unique_together = ['doctor', 'date', 'start_time']
        verbose_name = 'Khung giờ khám'
        verbose_name_plural = 'Khung giờ khám'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.date} {self.start_time}-{self.end_time}"
    
    @property
    def is_fully_booked(self):
        return self.current_appointments >= self.max_appointments
    
    def can_book(self):
        return self.is_available and not self.is_fully_booked
    
    def book_appointment(self):
        """Đặt lịch hẹn cho time slot này"""
        if self.can_book():
            self.current_appointments += 1
            self.save()
            return True
        return False
    
    def cancel_appointment(self):
        """Hủy lịch hẹn cho time slot này"""
        if self.current_appointments > 0:
            self.current_appointments -= 1
            self.save()
            return True
        return False
