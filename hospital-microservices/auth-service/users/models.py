from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model for Hospital Management System
    Extends Django's AbstractUser with additional fields
    """
    
    # Phone number validation for Vietnam format
    phone_regex = RegexValidator(
        regex=r'^(\+84|84|0)[0-9]{9}$',
        message="Số điện thoại phải có định dạng: '+84xxxxxxxxx', '84xxxxxxxxx', hoặc '0xxxxxxxxx'"
    )
    
    # Additional fields
    phone_number = models.CharField(
        max_length=15,
        validators=[phone_regex],
        blank=True,
        null=True,
        verbose_name="Số điện thoại"
    )
    
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name="Ngày sinh"
    )
    
    gender = models.CharField(
        max_length=10,
        choices=[
            ('M', 'Nam'),
            ('F', 'Nữ'),
            ('O', 'Khác'),
        ],
        blank=True,
        verbose_name="Giới tính"
    )
    
    address = models.TextField(
        blank=True,
        verbose_name="Địa chỉ"
    )
    
    # Profile image URL instead of ImageField
    profile_image = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ảnh đại diện (URL)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"
        db_table = 'custom_user'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def is_doctor(self):
        """Check if user is a doctor"""
        return hasattr(self, 'doctor_profile')
    
    @property
    def is_nurse(self):
        """Check if user is a nurse"""
        return hasattr(self, 'nurse_profile')
    
    @property
    def is_patient(self):
        """Check if user is a patient"""
        return hasattr(self, 'patient_profile')
