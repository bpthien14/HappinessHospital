from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.contrib.auth import get_user_model
from django.db import models
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, LoginSerializer, UserProfileSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer
    
    @extend_schema(
        tags=['users'],
        summary="List all users",
        description="Retrieve a list of all users in the system"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Create new user",
        description="Create a new user account"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Get user details",
        description="Retrieve detailed information about a specific user"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Update user",
        description="Update user information"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Delete user",
        description="Delete a user account"
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        tags=['users'],
        summary="Get user profile",
        description="Retrieve current user's profile information"
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['users'],
        summary="Update user profile",
        description="Update current user's profile information"
    )
    @action(detail=False, methods=['put', 'patch'], permission_classes=[permissions.IsAuthenticated])
    def update_profile(self, request):
        """Update current user's profile"""
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['users'],
        summary="Change password",
        description="Change current user's password"
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Mật khẩu đã được thay đổi thành công'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['users'],
        summary="Search users",
        description="Search users by various criteria"
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def search(self, request):
        """Search users by various criteria"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Query parameter "q" is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(
            models.Q(username__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(email__icontains=query)
        )
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for authentication operations
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        tags=['auth'],
        summary="User login",
        description="Authenticate user and return JWT tokens",
        request=LoginSerializer,
        responses={
            200: {
                'description': 'Login successful',
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'JWT access token'},
                    'refresh': {'type': 'string', 'description': 'JWT refresh token'},
                    'user': UserSerializer
                }
            },
            400: {'description': 'Invalid credentials'}
        }
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        """User login endpoint"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['auth'],
        summary="User logout",
        description="Logout user and blacklist refresh token",
        responses={
            200: {'description': 'Logout successful'},
            400: {'description': 'Invalid token'}
        }
    )
    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """User logout endpoint"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Đăng xuất thành công'})
            else:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['auth'],
        summary="Refresh token",
        description="Get new access token using refresh token",
        responses={
            200: {
                'description': 'Token refreshed successfully',
                'type': 'object',
                'properties': {
                    'access': {'type': 'string', 'description': 'New JWT access token'}
                }
            },
            400: {'description': 'Invalid refresh token'}
        }
    )
    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        """Refresh access token"""
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            return Response({'access': str(token.access_token)})
        except Exception as e:
            return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)
