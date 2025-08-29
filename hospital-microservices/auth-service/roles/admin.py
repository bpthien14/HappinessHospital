from django.contrib import admin
from .models import Permission, Role, RolePermission, UserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('resource', 'action', 'description', 'is_active', 'created_at')
    list_filter = ('resource', 'action', 'is_active', 'created_at')
    search_fields = ('resource', 'action', 'description')
    ordering = ('resource', 'action')
    
    fieldsets = (
        (None, {'fields': ('resource', 'action', 'description')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'description', 'is_active', 'created_at')
    list_filter = ('name', 'is_active', 'created_at')
    search_fields = ('name', 'display_name', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {'fields': ('name', 'display_name', 'description')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'granted_by', 'granted_at')
    list_filter = ('role', 'permission', 'granted_at')
    search_fields = ('role__name', 'permission__permission_name')
    ordering = ('role', 'permission')
    
    fieldsets = (
        (None, {'fields': ('role', 'permission', 'granted_by')}),
        ('Timestamps', {'fields': ('granted_at',), 'classes': ('collapse',)}),
    )
    
    readonly_fields = ('granted_at',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'assigned_by', 'assigned_at', 'is_active')
    list_filter = ('role', 'is_active', 'assigned_at')
    search_fields = ('user__username', 'user__email', 'role__name')
    ordering = ('user', 'role')
    
    fieldsets = (
        (None, {'fields': ('user', 'role', 'assigned_by')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('assigned_at',), 'classes': ('collapse',)}),
    )
    
    readonly_fields = ('assigned_at',)
