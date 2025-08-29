from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Permission(models.Model):
    """
    Permission model for fine-grained access control
    Format: RESOURCE:ACTION (e.g., PATIENT:CREATE, APPOINTMENT:READ)
    """
    
    RESOURCE_CHOICES = [
        ('USER', 'User Management'),
        ('PATIENT', 'Patient Management'),
        ('APPOINTMENT', 'Appointment Management'),
        ('PRESCRIPTION', 'Prescription Management'),
        ('PAYMENT', 'Payment Management'),
        ('REPORT', 'Reporting'),
        ('SYSTEM', 'System Administration'),
    ]
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('APPROVE', 'Approve'),
        ('REJECT', 'Reject'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    resource = models.CharField(
        max_length=50,
        choices=RESOURCE_CHOICES,
        verbose_name="Tài nguyên"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name="Hành động"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Mô tả"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    class Meta:
        verbose_name = "Quyền hạn"
        verbose_name_plural = "Quyền hạn"
        unique_together = ('resource', 'action')
        db_table = 'custom_permission'
    
    def __str__(self):
        return f"{self.resource}:{self.action}"
    
    @property
    def permission_name(self):
        """Return the full permission name"""
        return f"{self.resource}:{self.action}"


class Role(models.Model):
    """
    Role model for grouping permissions
    """
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('RECEPTIONIST', 'Receptionist'),
        ('PHARMACIST', 'Pharmacist'),
        ('ACCOUNTANT', 'Accountant'),
        ('PATIENT', 'Patient'),
    ]
    
    name = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True,
        verbose_name="Tên vai trò"
    )
    
    display_name = models.CharField(
        max_length=100,
        verbose_name="Tên hiển thị"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Mô tả"
    )
    
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        verbose_name="Quyền hạn"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ngày cập nhật")
    
    class Meta:
        verbose_name = "Vai trò"
        verbose_name_plural = "Vai trò"
        db_table = 'custom_role'
    
    def __str__(self):
        return self.display_name
    
    def get_permissions(self):
        """Get all permissions for this role"""
        return self.permissions.filter(is_active=True)
    
    def has_permission(self, resource, action):
        """Check if role has specific permission"""
        return self.permissions.filter(
            resource=resource,
            action=action,
            is_active=True
        ).exists()


class RolePermission(models.Model):
    """
    Intermediate model for Role-Permission relationship
    """
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name="Vai trò"
    )
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        verbose_name="Quyền hạn"
    )
    
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày cấp quyền")
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cấp bởi"
    )
    
    class Meta:
        verbose_name = "Quyền hạn vai trò"
        verbose_name_plural = "Quyền hạn vai trò"
        unique_together = ('role', 'permission')
        db_table = 'custom_role_permission'
    
    def __str__(self):
        return f"{self.role.name} - {self.permission.permission_name}"


class UserRole(models.Model):
    """
    Intermediate model for User-Role relationship
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Người dùng"
    )
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name="Vai trò"
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày phân công")
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments',
        verbose_name="Phân công bởi"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Kích hoạt"
    )
    
    class Meta:
        verbose_name = "Vai trò người dùng"
        verbose_name_plural = "Vai trò người dùng"
        unique_together = ('user', 'role')
        db_table = 'custom_user_role'
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
