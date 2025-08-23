from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Permission, UserRole, RolePermission, AuditLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'user_type', 'department', 'is_active', 'created_at']
    list_filter = ['user_type', 'department', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-created_at']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Info', {
            'fields': ('user_type', 'employee_id', 'department', 'phone_number', 
                      'date_of_birth', 'address')
        }),
        ('Metadata', {
            'fields': ('last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login_ip']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type', 
                      'employee_id', 'department'),
        }),
    )

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'role_type', 'is_active', 'created_at']
    list_filter = ['role_type', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('permissions')

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'resource', 'action']
    list_filter = ['resource', 'action']
    search_fields = ['name', 'description']

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['role', 'is_active', 'assigned_at']
    search_fields = ['user__username', 'role__name']
    raw_id_fields = ['user', 'assigned_by']

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'granted_at']
    list_filter = ['role', 'permission__resource', 'permission__action']
    search_fields = ['role__name', 'permission__name']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'resource_id', 'timestamp']
    list_filter = ['action', 'resource_type', 'timestamp']
    search_fields = ['user__username', 'resource_type', 'resource_id']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation of audit logs
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing of audit logs