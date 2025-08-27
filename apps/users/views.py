from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone

from .models import User, Role, Permission, UserRole, AuditLog
from apps.patients.models import Patient
from .serializers import (
    UserSerializer, UserCreateSerializer, LoginSerializer,
    ChangePasswordSerializer, RoleSerializer, PermissionSerializer,
    UserRoleSerializer
)
from shared.permissions.base_permissions import IsOwnerOrAdmin, HasPermission

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            user = User.objects.get(username=request.data['username'])
            AuditLog.objects.create(
                user=user,
                user_id_backup=str(user.id),
                action='LOGIN',
                resource_type='AUTH',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                response_status=200
            )
            
            # Update last login IP
            user.last_login_ip = request.META.get('REMOTE_ADDR')
            user.save(update_fields=['last_login_ip'])
            
            # Add user info to response
            user_serializer = UserSerializer(user)
            response.data['user'] = user_serializer.data
        
        return response

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    # Force default user_type to PATIENT regardless of client input
    data = request.data.copy()
    if 'user_type' not in data or not data.get('user_type'):
        data['user_type'] = 'PATIENT'

    # Pre-check uniqueness for phone (username) and citizen_id (patient)
    phone_number = data.get('phone_number') or data.get('username')
    citizen_id = data.get('citizen_id')

    # Check duplicate username by phone and phone_number field
    if phone_number:
        if User.objects.filter(username=str(phone_number)).exists() or \
           User.objects.filter(phone_number=str(phone_number)).exists():
            return Response({'phone_number': ['Số điện thoại đã được đăng ký tài khoản.']}, status=status.HTTP_400_BAD_REQUEST)

    # Check duplicate patient citizen_id if provided
    if citizen_id:
        if Patient.objects.filter(citizen_id=str(citizen_id)).exists():
            return Response({'citizen_id': ['CCCD/CMND đã tồn tại trong hệ thống.']}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserCreateSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Log user creation
        AuditLog.objects.create(
            user=user,
            user_id_backup=str(user.id),
            action='CREATE',
            resource_type='USER',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            response_status=201
        )
        
        # Create Patient record right after user creation (best-effort)
        try:
            # Map fields from registration payload
            full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            patient_payload = {
                'full_name': full_name,
                'date_of_birth': data.get('date_of_birth'),
                'gender': data.get('gender'),
                'phone_number': phone_number or '',
                'email': data.get('email') or None,
                'address': data.get('address') or '',
                'ward': data.get('ward') or '',
                'province': data.get('province') or '',
                'citizen_id': citizen_id or '',
                'created_by': user,
                'updated_by': user,
            }

            # Normalize missing optional fields to None when empty
            for key in ['email']:
                if not patient_payload[key]:
                    patient_payload[key] = None

            # Create Patient (will raise if invalid)
            Patient.objects.create(**patient_payload)
        except Exception:
            # Do not fail registration if patient creation fails
            pass

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_type': user.user_type,
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        # Log logout
        AuditLog.objects.create(
            user=request.user,
            user_id_backup=str(request.user.id),
            action='LOGOUT',
            resource_type='AUTH',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            response_status=200
        )
        
        return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

@api_view(['PUT'])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        # Log profile update
        AuditLog.objects.create(
            user=request.user,
            user_id_backup=str(request.user.id),
            action='UPDATE',
            resource_type='USER',
            resource_id=str(request.user.id),
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            request_data=request.data,
            response_status=200
        )
        
        return Response(serializer.data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Update session auth hash to keep user logged in
        update_session_auth_hash(request, user)
        
        # Log password change
        AuditLog.objects.create(
            user=request.user,
            user_id_backup=str(request.user.id),
            action='UPDATE',
            resource_type='PASSWORD',
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            response_status=200
        )
        
        return Response({'message': 'Password updated successfully'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['user_type', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'employee_id', 'department']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by exclude_user_types (for NON_PATIENT option)
        exclude_user_types = self.request.query_params.get('exclude_user_types')
        if exclude_user_types:
            # Split by comma and exclude multiple user types
            exclude_types = exclude_user_types.split(',')
            queryset = queryset.exclude(user_type__in=exclude_types)

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            self.required_permissions = ['USER:READ']
        elif self.action == 'create':
            self.required_permissions = ['USER:CREATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['USER:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['USER:DELETE']
        
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        user = self.get_object()
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id)
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role,
                defaults={'assigned_by': request.user}
            )
            
            if created:
                return Response({'message': f'Role {role.name} assigned to {user.username}'})
            else:
                return Response({'message': 'User already has this role'}, 
                              status=status.HTTP_400_BAD_REQUEST)
                
        except Role.DoesNotExist:
            return Response({'error': 'Role not found'}, 
                          status=status.HTTP_404_NOT_FOUND)

class RoleViewSet(ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [HasPermission]
    
    def get_permissions(self):
        self.required_permissions = ['SYSTEM:READ']
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.required_permissions = ['SYSTEM:UPDATE']
        
        return super().get_permissions()

class PermissionViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [HasPermission]
    
    def get_permissions(self):
        self.required_permissions = ['SYSTEM:READ']
        return super().get_permissions()