from rest_framework.permissions import BasePermission
from apps.users.models import UserRole

class HasPermission(BasePermission):
    """
    Permission class that checks if user has required permissions
    """
    required_permissions = []
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        # Get required permissions from view
        required_permissions = getattr(view, 'required_permissions', [])
        if not required_permissions:
            return True
        
        # Get user permissions
        user_permissions = self.get_user_permissions(request.user)
        
        # Check if user has all required permissions
        return all(perm in user_permissions for perm in required_permissions)
    
    def get_user_permissions(self, user):
        """Get all permissions for a user"""
        permissions = set()
        
        for user_role in user.user_roles.filter(is_active=True):
            role_permissions = user_role.role.permissions.values_list(
                'permission__resource', 'permission__action'
            )
            for resource, action in role_permissions:
                permissions.add(f"{resource}:{action}")
        
        return permissions

class IsOwnerOrAdmin(BasePermission):
    """
    Permission that allows owners of an object or admins to access it
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user