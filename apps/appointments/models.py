from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date, datetime, time, timedelta
import uuid

User = get_user_model()

class Department(models.Model):
    """Khoa/Phòng khám trong bệnh viện"""
    
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
    """Hồ sơ bác sĩ với thông tin chuyên môn"""
    
    DEGREE_CHOICES = [
        ('BACHELOR', 'Bác sĩ'),
        ('MASTER', 'Thạc sĩ'),
        ('DOCTOR', 'Tiến sĩ'),
        ('PROFESSOR', 'Giáo sư'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='doctor_profile',
        limit_choices_to={'user_type': 'DOCTOR'}
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='doctors')
    
    # Professional info
    license_number = models.CharField(max_length=50, unique=True, help_text="Số chứng chỉ hành nghề")
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES, help_text="Bằng cấp cao nhất")
    specialization = models.CharField(max_length=200, help_text="Chuyên khoa")
    experience_years = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Số năm kinh nghiệm"
    )
    
    # Work settings
    max_patients_per_day = models.IntegerField(default=40, help_text="Số bệnh nhân tối đa/ngày")
    consultation_duration = models.IntegerField(default=15, help_text="Thời gian khám/bệnh nhân (phút)")
    
    # Biography
    bio = models.TextField(blank=True, help_text="Tiểu sử, kinh nghiệm")
    achievements = models.TextField(blank=True, help_text="Thành tích, chứng chỉ")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'doctor_profiles'
        verbose_name = 'Hồ sơ bác sĩ'
        verbose_name_plural = 'Hồ sơ bác sĩ'
    
    def __str__(self):
        return f"BS. {self.user.full_name} - {self.specialization}"

class DoctorSchedule(models.Model):
    """Lịch làm việc của bác sĩ"""
    
    WEEKDAY_CHOICES = [
        (0, 'Thứ Hai'),
        (1, 'Thứ Ba'),
        (2, 'Thứ Tư'),
        (3, 'Thứ Năm'),
        (4, 'Thứ Sáu'),
        (5, 'Thứ Bảy'),
        (6, 'Chủ Nhật'),
    ]
    
    SHIFT_CHOICES = [
        ('MORNING', 'Ca sáng (7:00-11:30)'),
        ('AFTERNOON', 'Ca chiều (13:30-17:00)'),
        ('EVENING', 'Ca tối (18:00-21:00)'),
        ('NIGHT', 'Ca đêm (21:00-6:00)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='schedules')
    
    # Schedule timing
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, help_text="Thứ trong tuần")
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, help_text="Ca làm việc")
    start_time = models.TimeField(help_text="Giờ bắt đầu")
    end_time = models.TimeField(help_text="Giờ kết thúc")
    
    # Capacity settings
    max_appointments = models.IntegerField(default=20, help_text="Số lượt khám tối đa")
    appointment_duration = models.IntegerField(default=15, help_text="Thời gian/lượt khám (phút)")
    
    # Validity
    effective_from = models.DateField(help_text="Có hiệu lực từ ngày")
    effective_to = models.DateField(null=True, blank=True, help_text="Có hiệu lực đến ngày")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'doctor_schedules'
        unique_together = ['doctor', 'weekday', 'shift', 'effective_from']
        verbose_name = 'Lịch làm việc bác sĩ'
        verbose_name_plural = 'Lịch làm việc bác sĩ'
        ordering = ['weekday', 'start_time']
    
    def __str__(self):
        return f"{self.doctor} - {self.get_weekday_display()} {self.get_shift_display()}"
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Giờ bắt đầu phải trước giờ kết thúc')
        
        if self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError('Ngày bắt đầu phải trước ngày kết thúc')

class Appointment(models.Model):
    """Lịch hẹn khám bệnh"""
    
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
    
    # Relationships
    patient = models.ForeignKey(
        'patients.Patient', 
        on_delete=models.CASCADE, 
        related_name='appointments'
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='appointments')
    
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
    
    # Administrative
    booked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='booked_appointments',
        help_text="Người đặt lịch"
    )
    confirmed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='confirmed_appointments',
        help_text="Người xác nhận"
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
            models.Index(fields=['patient', 'appointment_date']),
            models.Index(fields=['doctor', 'appointment_date']),
            models.Index(fields=['status', 'appointment_date']),
        ]
    
    def __str__(self):
        return f"{self.appointment_number} - {self.patient.full_name} - {self.appointment_date}"
    
    @property
    def appointment_datetime(self):
        """Kết hợp ngày và giờ thành datetime"""
        return datetime.combine(self.appointment_date, self.appointment_time)
    
    @property
    def is_today(self):
        """Kiểm tra có phải lịch hẹn hôm nay"""
        return self.appointment_date == date.today()
    
    @property
    def is_past_due(self):
        """Kiểm tra đã quá giờ hẹn"""
        return self.appointment_datetime < datetime.now()
    
    @property
    def can_cancel(self):
        """Kiểm tra có thể hủy lịch"""
        if self.status in ['COMPLETED', 'CANCELLED', 'NO_SHOW']:
            return False
        # Chỉ cho phép hủy trước giờ hẹn ít nhất 2 tiếng
        return (self.appointment_datetime - datetime.now()).total_seconds() > 7200
    
    @property
    def can_checkin(self):
        """Kiểm tra có thể check-in"""
        if self.status != 'CONFIRMED':
            return False
        # Cho phép check-in trước giờ hẹn 30 phút
        time_diff = (datetime.now() - self.appointment_datetime).total_seconds()
        return -1800 <= time_diff <= 3600  # 30 phút trước đến 1 giờ sau
    
    def clean(self):
        # Validate appointment is in the future
        if self.appointment_date < date.today():
            raise ValidationError('Không thể đặt lịch hẹn trong quá khứ')
        
        # Validate doctor availability
        if hasattr(self, 'doctor') and hasattr(self, 'appointment_date'):
            weekday = self.appointment_date.weekday()
            doctor_schedules = self.doctor.schedules.filter(
                weekday=weekday,
                effective_from__lte=self.appointment_date,
                is_active=True
            ).filter(
                models.Q(effective_to__isnull=True) | 
                models.Q(effective_to__gte=self.appointment_date)
            )
            
            if not doctor_schedules.exists():
                raise ValidationError('Bác sĩ không có lịch làm việc trong ngày này')
    
    def save(self, *args, **kwargs):
        # Auto-generate appointment number
        if not self.appointment_number:
            self.appointment_number = self.generate_appointment_number()
        
        # Auto-assign queue number
        if not self.queue_number:
            self.queue_number = self.get_next_queue_number()
        
        # Set department from doctor
        if hasattr(self, 'doctor') and self.doctor and not self.department_id:
            if hasattr(self.doctor, 'department'):
                self.department = self.doctor.department
        
        super().save(*args, **kwargs)
    
    def generate_appointment_number(self):
        """Tạo số lịch hẹn: LH + YYYYMMDD + 4 số"""
        today = date.today()
        date_str = today.strftime('%Y%m%d')
        prefix = f"LH{date_str}"
        
        # Get the last appointment for today
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
        """Lấy số thứ tự tiếp theo cho ngày khám"""
        max_queue = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date=self.appointment_date
        ).aggregate(
            max_queue=models.Max('queue_number')
        )['max_queue']
        
        return (max_queue or 0) + 1

class AppointmentStatusHistory(models.Model):
    """Lịch sử thay đổi trạng thái lịch hẹn"""
    
    appointment = models.ForeignKey(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    old_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    new_status = models.CharField(max_length=20, choices=Appointment.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
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
    """Time slots cho việc đặt lịch"""
    
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