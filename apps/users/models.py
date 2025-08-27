from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    USER_TYPES = [
        ('PATIENT', 'Bệnh nhân'),
        ('DOCTOR', 'Bác sĩ'),
        ('NURSE', 'Y tá'),
        ('RECEPTION', 'Lễ tân'),
        ('PHARMACIST', 'Dược sĩ'),
        ('TECHNICIAN', 'Kỹ thuật viên'),
        ('ADMIN', 'Quản trị viên'),
        ('CASHIER', 'Thu ngân'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='PATIENT')
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=[('M', 'Nam'), ('F', 'Nữ'), ('O', 'Khác')], blank=True, null=True)
    province = models.CharField(max_length=100, blank=True, null=True)
    ward = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        constraints = [
            models.CheckConstraint(check=~models.Q(username=''), name='user_username_not_blank'),
            models.CheckConstraint(check=~models.Q(first_name=''), name='user_first_name_not_blank'),
            models.CheckConstraint(check=~models.Q(last_name=''), name='user_last_name_not_blank'),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class Role(models.Model):
    ROLE_TYPES = [
        ('SYSTEM', 'System Role'),
        ('DEPARTMENT', 'Department Role'),
        ('CUSTOM', 'Custom Role'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES, default='CUSTOM')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'roles'
    
    def __str__(self):
        return self.name

class Permission(models.Model):
    RESOURCE_TYPES = [
        ('PATIENT', 'Patient Management'),
        ('APPOINTMENT', 'Appointment Management'),
        ('PRESCRIPTION', 'Prescription Management'),
        ('PAYMENT', 'Payment Management'),
        ('TESTING', 'Testing Management'),
        ('REPORT', 'Report Management'),
        ('SYSTEM', 'System Management'),
    ]
    
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('CANCEL', 'Cancel'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    resource = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    
    class Meta:
        db_table = 'permissions'
        unique_together = ['resource', 'action']
    
    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_roles'
        unique_together = ['user', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'role_permissions'
        unique_together = ['role', 'permission']
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PERMISSION_DENIED', 'Permission Denied'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    user_id_backup = models.CharField(max_length=100)  # Backup in case user is deleted
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=100)
    resource_id = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    request_data = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user_id_backup', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'timestamp']),
        ]