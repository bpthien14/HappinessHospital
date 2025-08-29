from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import Department, DoctorProfile, DoctorSchedule, Appointment, AppointmentStatusHistory, TimeSlot
from .serializers import (
    DepartmentSerializer, DoctorProfileSerializer, DoctorScheduleSerializer,
    AppointmentSerializer, AppointmentCreateSerializer, AppointmentUpdateSerializer, AppointmentSummarySerializer,
    AppointmentStatusHistorySerializer, TimeSlotSerializer, AvailableSlotSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    """Department management ViewSet"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @extend_schema(
        summary="List departments",
        description="Get a list of all hospital departments"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class DoctorProfileViewSet(viewsets.ModelViewSet):
    """Doctor Profile management ViewSet"""
    queryset = DoctorProfile.objects.select_related('department').all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'department', 'is_active', 'is_available']
    search_fields = ['license_number', 'specialization']
    ordering_fields = ['specialization', 'experience_years', 'created_at']
    ordering = ['specialization', 'department__name']
    
    @extend_schema(
        summary="List doctors",
        description="Get a list of all doctors with their profiles"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get available time slots",
        description="Get available time slots for a specific doctor on a specific date",
        parameters=[
            OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
        ],
        responses={200: AvailableSlotSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        """Get available time slots for a doctor"""
        doctor = self.get_object()
        date_param = request.query_params.get('date')
        
        if not date_param:
            return Response(
                {'error': 'Date parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        available_slots = TimeSlot.objects.filter(
            doctor=doctor,
            date=target_date,
            is_available=True
        ).filter(
            current_appointments__lt=models.F('max_appointments')
        )
        
        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data)

class DoctorScheduleViewSet(viewsets.ModelViewSet):
    """Doctor Schedule management ViewSet"""
    queryset = DoctorSchedule.objects.select_related('doctor', 'doctor__department').all()
    serializer_class = DoctorScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['doctor', 'date', 'shift', 'is_available']
    search_fields = ['doctor__specialization', 'doctor__license_number']
    ordering_fields = ['date', 'start_time', 'created_at']
    ordering = ['date', 'start_time']
    
    @extend_schema(
        summary="List doctor schedules",
        description="Get a list of all doctor schedules"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class AppointmentViewSet(viewsets.ModelViewSet):
    """Appointment Management ViewSet"""
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['appointment_number', 'patient_id', 'doctor_id']
    filterset_fields = ['status', 'priority', 'appointment_type', 'doctor_id', 'department_id']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at']
    ordering = ['-appointment_date', '-appointment_time']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        elif self.action == 'list':
            return AppointmentSummarySerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        # Set booked_by_id from request user if available
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            serializer.save(booked_by_id=self.request.user.id)
        else:
            serializer.save()
    
    @extend_schema(
        summary="List appointments",
        description="Get a list of all appointments with optional filtering"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create appointment",
        description="Create a new appointment"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get appointment details",
        description="Get detailed information about a specific appointment"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update appointment",
        description="Update an existing appointment"
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    @extend_schema(
        summary="Cancel appointment",
        description="Cancel an appointment (soft delete by changing status)"
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        if not appointment.can_cancel:
            return Response(
                {'error': 'Appointment cannot be cancelled'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'CANCELLED'
        appointment.save()
        
        # Create status history
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            old_status=appointment.status,
            new_status='CANCELLED',
            changed_by_id=request.user.id if request.user.is_authenticated else None,
            reason=request.data.get('reason', 'Cancelled by user')
        )
        
        return Response({'message': 'Appointment cancelled successfully'})
    
    @extend_schema(
        summary="Check-in appointment",
        description="Check-in for an appointment"
    )
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        """Check-in for an appointment"""
        appointment = self.get_object()
        
        if not appointment.can_checkin:
            return Response(
                {'error': 'Appointment cannot be checked in'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        appointment.status = 'CHECKED_IN'
        appointment.checked_in_at = timezone.now()
        appointment.save()
        
        # Create status history
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            old_status=appointment.status,
            new_status='CHECKED_IN',
            changed_by_id=request.user.id if request.user.is_authenticated else None,
            reason='Patient checked in'
        )
        
        return Response({'message': 'Appointment checked in successfully'})
    
    @extend_schema(
        summary="Get appointment statistics",
        description="Get statistics about appointments"
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get appointment statistics"""
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        
        total_appointments = Appointment.objects.count()
        today_appointments = Appointment.objects.filter(appointment_date=today).count()
        tomorrow_appointments = Appointment.objects.filter(appointment_date=tomorrow).count()
        
        # Status breakdown
        status_counts = Appointment.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Department breakdown
        department_counts = Appointment.objects.values('department_id').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return Response({
            'total_appointments': total_appointments,
            'today_appointments': today_appointments,
            'tomorrow_appointments': tomorrow_appointments,
            'status_breakdown': list(status_counts),
            'top_departments': list(department_counts)
        })

class AppointmentStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Appointment Status History ViewSet (Read-only)"""
    queryset = AppointmentStatusHistory.objects.select_related('appointment').all()
    serializer_class = AppointmentStatusHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['appointment', 'old_status', 'new_status']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']
    
    @extend_schema(
        summary="List status history",
        description="Get appointment status change history"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class TimeSlotViewSet(viewsets.ModelViewSet):
    """Time Slot management ViewSet"""
    queryset = TimeSlot.objects.select_related('doctor', 'doctor__department').all()
    serializer_class = TimeSlotSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['doctor', 'date', 'is_available']
    search_fields = ['doctor__specialization']
    ordering_fields = ['date', 'start_time', 'created_at']
    ordering = ['date', 'start_time']
    
    @extend_schema(
        summary="List time slots",
        description="Get a list of all time slots"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Create time slot",
        description="Create a new time slot for a doctor"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
