from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class JWTAuthMiddleware(MiddlewareMixin):
    """
    Middleware to add user context from JWT token to request
    """
    
    def process_request(self, request):
        # Skip for certain paths
        exempt_paths = [
            '/api/auth/login/',
            '/api/auth/register/',
            '/api/auth/refresh/',
            '/admin/',
            '/static/',
            '/media/'
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
        
        # Get token from header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Validate token and get user
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            # Add user context to request
            request.user = user
            request.token = validated_token
            
        except (InvalidToken, TokenError):
            pass  # Let DRF handle authentication
        
        return None

    def process_response(self, request, response):
        # Only log authenticated requests to API endpoints
        if (hasattr(request, 'user') and 
            request.user.is_authenticated and 
            request.path.startswith('/api/')):
            
            # Map HTTP methods to actions
            method_action_map = {
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE',
                'GET': 'READ'
            }
            
            action = method_action_map.get(request.method, 'UNKNOWN')
            
            # Extract resource type from path
            path_parts = request.path.strip('/').split('/')
            resource_type = path_parts[1].upper() if len(path_parts) > 1 else 'UNKNOWN'
            
            # Prepare request data (filter sensitive info)
            request_data = None
            if hasattr(request, 'data') and request.method in ['POST', 'PUT', 'PATCH']:
                request_data = {k: v for k, v in request.data.items() 
                               if k not in ['password', 'token', 'refresh']}
            
            # Log the action (commented out until AuditLog model is available)
            # try:
            #     AuditLog.objects.create(
            #         user=request.user,
            #         user_id_backup=str(request.user.id),
            #         action=action,
            #         resource_type=resource_type,
            #         ip_address=self.get_client_ip(request),
            #         user_agent=request.META.get('HTTP_USER_AGENT', ''),
            #         request_data=request_data,
            #         response_status=response.status_code
            #     )
            # except Exception:
            #     pass  # Don't break the response if logging fails
        
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip