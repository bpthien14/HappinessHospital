from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Role, Permission, UserRole

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'employee_id', 'department', 'phone_number',
            'date_of_birth', 'gender', 'province', 'ward', 'address',
            'is_active', 'last_login', 'created_at', 'updated_at', 'roles', 'permissions',
            'created_by_name', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    def get_roles(self, obj):
        return list(obj.user_roles.filter(is_active=True).values_list('role__name', flat=True))
    
    def get_permissions(self, obj):
        permissions = set()
        for user_role in obj.user_roles.filter(is_active=True):
            role_permissions = user_role.role.permissions.values_list(
                'permission__resource', 'permission__action'
            )
            for resource, action in role_permissions:
                permissions.add(f"{resource}:{action}")
        return list(permissions)

    def get_created_by_name(self, obj):
        # Get the user who created this account from AuditLog
        from .models import AuditLog
        create_log = AuditLog.objects.filter(
            resource_type='USER',
            resource_id=str(obj.id),
            action='CREATE'
        ).first()
        if create_log and create_log.user:
            return create_log.user.full_name
        return None

    def get_updated_by_name(self, obj):
        # Get the user who last updated this account from AuditLog
        from .models import AuditLog
        update_log = AuditLog.objects.filter(
            resource_type='USER',
            resource_id=str(obj.id),
            action='UPDATE'
        ).order_by('-timestamp').first()
        if update_log and update_log.user:
            return update_log.user.full_name
        return None

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'user_type', 'employee_id',
            'department', 'phone_number', 'date_of_birth', 'address',
            'gender', 'province', 'ward'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")

        # Handle date_of_birth validation
        if 'date_of_birth' in attrs and attrs['date_of_birth']:
            try:
                # Ensure date is in correct format
                if isinstance(attrs['date_of_birth'], str):
                    from datetime import datetime
                    attrs['date_of_birth'] = datetime.strptime(attrs['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                raise serializers.ValidationError({
                    'date_of_birth': 'Ngày sai định dạng. Dùng định dạng YYYY-MM-DD.'
                })



        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password.')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is not correct.')
        return value

class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'role_type', 'is_active', 'permissions']
    
    def get_permissions(self, obj):
        return list(obj.permissions.values_list('permission__name', flat=True))

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'resource', 'action', 'description']

class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserRole
        fields = [
            'id', 'role', 'role_name', 'assigned_by', 'assigned_by_username',
            'assigned_at', 'expires_at', 'is_active'
        ]