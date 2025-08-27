from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

def home(request):
    return redirect('login')

def well_known_handler(request, path=''):
    # Handle Chrome DevTools and other .well-known requests silently
    return HttpResponse('', status=204)

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.patients.urls')),
    path('api/', include('apps.appointments.urls')),
    path('api/', include('apps.prescriptions.urls')),
    path('api/', include('apps.payments.urls')),

    # Frontend views
    path('', include('frontend.urls')),
    
    # Handle .well-known requests (Chrome DevTools, etc.)
    path('.well-known/<path:path>', well_known_handler),
    path('.well-known/', well_known_handler),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)