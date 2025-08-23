from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.http import JsonResponse

User = get_user_model()

class JWTAuthBackend(BaseBackend):
    """
    Custom authentication backend for JWT tokens in frontend views
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Get token from Authorization header or from request
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
        else:
            # Try to get token from request data or cookies
            token = request.GET.get('token') or request.POST.get('token')
        
        if not token:
            return None
        
        try:
            # Validate token and get user
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
