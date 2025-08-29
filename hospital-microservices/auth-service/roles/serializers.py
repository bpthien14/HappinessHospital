from rest_framework import serializers
from .models import Permission, Role, RolePermission, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    
    permission_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Permission
        fields = [
            'id', 'resource', 'action', 'description', 'is_active',
            'created_at', 'updated_at', 'permission_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'display_name', 'description', 'is_active',
            'permissions', 'permission_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_permission_count(self, obj):
        return obj.permissions.count()


class RoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new roles"""
    
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Role
        fields = ['name', 'display_name', 'description', 'permission_ids']
    
    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)
        
        # Assign permissions
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
            for permission in permissions:
                RolePermission.objects.create(role=role, permission=permission)
        
        return role


class RoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating roles"""
    
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Role
        fields = ['display_name', 'description', 'is_active', 'permission_ids']
    
    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update role fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            # Clear existing permissions
            instance.permissions.clear()
            
            # Add new permissions
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids, is_active=True)
                for permission in permissions:
                    RolePermission.objects.create(role=instance, permission=permission)
        
        return instance


class RolePermissionSerializer(serializers.ModelSerializer):
    """Serializer for RolePermission model"""
    
    role_name = serializers.CharField(source='role.display_name', read_only=True)
    permission_name = serializers.CharField(source='permission.permission_name', read_only=True)
    
    class Meta:
        model = RolePermission
        fields = [
            'id', 'role', 'role_name', 'permission', 'permission_name',
            'granted_at', 'granted_by'
        ]
        read_only_fields = ['id', 'granted_at']


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    role_name = serializers.CharField(source='role.display_name', read_only=True)
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'user_username', 'user_full_name', 'role',
            'role_name', 'assigned_at', 'assigned_by', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_at']


class UserRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating user roles"""
    
    class Meta:
        model = UserRole
        fields = ['user', 'role', 'assigned_by']
    
    def create(self, validated_data):
        # Set assigned_by to current user if not provided
        if 'assigned_by' not in validated_data:
            validated_data['assigned_by'] = self.context['request'].user
        
        return UserRole.objects.create(**validated_data)


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user roles"""
    
    class Meta:
        model = UserRole
        fields = ['role', 'is_active']


class RoleSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for role listing"""
    
    permission_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'display_name', 'description', 'is_active', 'permission_count']
    
    def get_permission_count(self, obj):
        return obj.permissions.count()


class PermissionSummarySerializer(serializers.ModelSerializer):
    """Simplified serializer for permission listing"""
    
    class Meta:
        model = Permission
        fields = ['id', 'resource', 'action', 'description', 'is_active']
