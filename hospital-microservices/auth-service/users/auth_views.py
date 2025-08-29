from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate
from .serializers import LoginSerializer, UserSerializer


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
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
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
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
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
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_view(request):
    """Refresh access token"""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        return Response({'access': str(token.access_token)})
    except Exception as e:
        return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)
