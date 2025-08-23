from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)
router.register(r'doctors', views.DoctorProfileViewSet)
router.register(r'appointments', views.AppointmentViewSet)

urlpatterns = [
    # Statistics endpoint
    path('appointments/statistics/', views.appointment_statistics, name='appointment-statistics'),
    
    # Include router URLs
    path('', include(router.urls)),
]
