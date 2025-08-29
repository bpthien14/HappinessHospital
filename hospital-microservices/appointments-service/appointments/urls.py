from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, DoctorProfileViewSet, DoctorScheduleViewSet,
    AppointmentViewSet, AppointmentStatusHistoryViewSet, TimeSlotViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'doctors', DoctorProfileViewSet, basename='doctor')
router.register(r'schedules', DoctorScheduleViewSet, basename='schedule')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'status-history', AppointmentStatusHistoryViewSet, basename='status-history')
router.register(r'time-slots', TimeSlotViewSet, basename='time-slot')

urlpatterns = [
    path('', include(router.urls)),
]
