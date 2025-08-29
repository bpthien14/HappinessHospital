from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Permission, Role, RolePermission, UserRole
from .serializers import (
    PermissionSerializer, RoleSerializer, RoleCreateSerializer, RoleUpdateSerializer,
    RolePermissionSerializer, UserRoleSerializer, UserRoleCreateSerializer,
    UserRoleUpdateSerializer, RoleSummarySerializer, PermissionSummarySerializer
)


class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PermissionSummarySerializer
        return PermissionSerializer
    
    @extend_schema(
        tags=['roles'],
        summary="List all permissions",
        description="Retrieve a list of all permissions in the system"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Create new permission",
        description="Create a new permission"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get permission details",
        description="Retrieve detailed information about a specific permission"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Update permission",
        description="Update permission information"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Delete permission",
        description="Delete a permission"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get permissions by resource",
        description="Get all permissions for a specific resource"
    )
    @action(detail=False, methods=['get'])
    def by_resource(self, request):
        """Get permissions by resource"""
        resource = request.query_params.get('resource')
        if not resource:
            return Response({'error': 'Resource parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        permissions = Permission.objects.filter(resource=resource, is_active=True)
        serializer = PermissionSummarySerializer(permissions, many=True)
        return Response(serializer.data)


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RoleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RoleUpdateSerializer
        elif self.action == 'list':
            return RoleSummarySerializer
        return RoleSerializer
    
    @extend_schema(
        tags=['roles'],
        summary="List all roles",
        description="Retrieve a list of all roles in the system"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Create new role",
        description="Create a new role with permissions"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get role details",
        description="Retrieve detailed information about a specific role"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Update role",
        description="Update role information and permissions"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Delete role",
        description="Delete a role"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get role permissions",
        description="Get all permissions for a specific role"
    )
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """Get permissions for a specific role"""
        role = self.get_object()
        permissions = role.get_permissions()
        serializer = PermissionSummarySerializer(permissions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['roles'],
        summary="Check role permission",
        description="Check if a role has a specific permission"
    )
    @action(detail=True, methods=['get'])
    def has_permission(self, request, pk=None):
        """Check if role has specific permission"""
        role = self.get_object()
        resource = request.query_params.get('resource')
        action = request.query_params.get('action')
        
        if not resource or not action:
            return Response({'error': 'Resource and action parameters are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        has_perm = role.has_permission(resource, action)
        return Response({'has_permission': has_perm})


class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing role-permission relationships
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        tags=['roles'],
        summary="List all role permissions",
        description="Retrieve a list of all role-permission relationships"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Create new role permission",
        description="Assign a permission to a role"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Delete role permission",
        description="Remove a permission from a role"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class UserRoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user-role relationships
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRoleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserRoleUpdateSerializer
        return UserRoleSerializer
    
    @extend_schema(
        tags=['roles'],
        summary="List all user roles",
        description="Retrieve a list of all user-role relationships"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Create new user role",
        description="Assign a role to a user"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get user role details",
        description="Retrieve detailed information about a specific user-role relationship"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Update user role",
        description="Update user role information"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Delete user role",
        description="Remove a role from a user"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['roles'],
        summary="Get user roles",
        description="Get all roles for a specific user"
    )
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get roles for a specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'User ID parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_roles = UserRole.objects.filter(user_id=user_id, is_active=True)
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['roles'],
        summary="Get role users",
        description="Get all users for a specific role"
    )
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get users for a specific role"""
        role_id = request.query_params.get('role_id')
        if not role_id:
            return Response({'error': 'Role ID parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_roles = UserRole.objects.filter(role_id=role_id, is_active=True)
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)
