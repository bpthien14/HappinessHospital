from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'gender', 'address',
            'profile_image', 'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'gender', 'address'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Mật khẩu xác nhận không khớp")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'gender', 'address', 'profile_image'
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Mật khẩu mới xác nhận không khớp")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mật khẩu cũ không đúng")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Thông tin đăng nhập không đúng')
            if not user.is_active:
                raise serializers.ValidationError('Tài khoản đã bị khóa')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Vui lòng nhập đầy đủ thông tin đăng nhập')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display"""
    
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'phone_number',
            'date_of_birth', 'age', 'gender', 'address', 'profile_image',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.date_of_birth.year - ((today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day))
        return None
