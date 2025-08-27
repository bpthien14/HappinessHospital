from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import date, datetime, timedelta, time
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    Department, DoctorProfile, DoctorSchedule, 
    Appointment, AppointmentStatusHistory, TimeSlot
)
from .serializers import (
    DepartmentSerializer, DoctorProfileSerializer, DoctorScheduleSerializer,
    AppointmentSerializer, AppointmentCreateSerializer, TimeSlotSerializer,
    AppointmentStatusHistorySerializer, AvailableSlotSerializer
)
from shared.permissions.base_permissions import HasPermission

class DepartmentViewSet(ModelViewSet):
    """
    Department Management ViewSet
    
    Manages hospital departments/specialties.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Cho phép đọc công khai để phục vụ portal
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action == 'create':
            self.required_permissions = ['SYSTEM:UPDATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['SYSTEM:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['SYSTEM:UPDATE']
        return super().get_permissions()

class DoctorProfileViewSet(ModelViewSet):
    """
    Doctor Profile Management ViewSet
    
    Manages doctor profiles and specializations.
    """
    queryset = DoctorProfile.objects.select_related('user', 'department').all()
    serializer_class = DoctorProfileSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'specialization', 'user__username']
    filterset_fields = ['department', 'degree', 'is_active']
    ordering_fields = ['user__first_name', 'user__last_name', 'experience_years', 'created_at']
    ordering = ['user__first_name', 'user__last_name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'available_slots']:
            # Cho phép đọc công khai để hiển thị danh sách bác sĩ và slots cho portal
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action == 'create':
            self.required_permissions = ['SYSTEM:UPDATE']
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['SYSTEM:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['SYSTEM:UPDATE']
        return super().get_permissions()
    
    # DEPRECATED: schedules action không còn cần thiết với logic đơn giản mới
    # @extend_schema(
    #     responses={200: DoctorScheduleSerializer(many=True)}
    # )
    # @action(detail=True, methods=['get'])
    # def schedules(self, request, pk=None):
    #     """Get doctor's schedules"""
    #     doctor = self.get_object()
    #     schedules = doctor.schedules.filter(is_active=True)
    #     serializer = DoctorScheduleSerializer(schedules, many=True)
    #     return Response(serializer.data)
    
    @extend_schema(
        parameters=[
            OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
        ],
        responses={200: AvailableSlotSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def available_slots(self, request, pk=None):
        """Get available time slots for a doctor on a specific date"""
        doctor = self.get_object()
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response({'error': 'Date parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if appointment_date < date.today():
            return Response({'error': 'Cannot get slots for past dates'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if doctor has reached daily limit
        existing_appointments = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
        ).count()
        
        if existing_appointments >= doctor.max_patients_per_day:
            return Response([])  # No available slots - daily limit reached
        
        # Generate simple time slots for business hours (8:00-17:00)
        available_slots = []
        start_hour = 8  # 8:00 AM
        end_hour = 17   # 5:00 PM
        duration = doctor.consultation_duration  # minutes per appointment
        
        current_time = datetime.combine(appointment_date, time(start_hour, 0))
        end_time = datetime.combine(appointment_date, time(end_hour, 0))
        
        while current_time < end_time and len(available_slots) < (doctor.max_patients_per_day - existing_appointments):
            slot_time = current_time.time()
            
            # Check if this time slot is already booked
            is_booked = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=slot_time,
                status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
            ).exists()
            
            if not is_booked:
                available_slots.append({
                    'time': slot_time,
                    'available': True,
                    'booked_count': 0,
                    'max_appointments': 1
                })
            
            current_time += timedelta(minutes=duration)
        
        serializer = AvailableSlotSerializer(available_slots, many=True)
        return Response(serializer.data)

class AppointmentViewSet(ModelViewSet):
    """
    Appointment Management ViewSet
    
    Manages appointment scheduling and status updates.
    """
    queryset = Appointment.objects.select_related(
        'patient', 'doctor__user', 'department', 'booked_by'
    ).all()
    serializer_class = AppointmentSerializer
    permission_classes = [HasPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['appointment_number', 'patient__full_name', 'patient__patient_code', 'patient__phone_number']
    filterset_fields = ['status', 'priority', 'appointment_type', 'doctor', 'department']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at']
    ordering = ['-appointment_date', '-appointment_time']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Cho phép bệnh nhân xem lịch hẹn của chính mình qua filter patient
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action == 'create':
            # Cho phép PATIENT tạo lịch hẹn từ portal (read-only APIs vẫn an toàn)
            self.permission_classes = [AllowAny]
            return [AllowAny()]
        elif self.action in ['update', 'partial_update']:
            self.required_permissions = ['APPOINTMENT:UPDATE']
        elif self.action == 'destroy':
            self.required_permissions = ['APPOINTMENT:CANCEL']
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        return AppointmentSerializer
    
    def perform_create(self, serializer):
        serializer.save(booked_by=self.request.user)
    
    def perform_update(self, serializer):
        # Track status changes
        old_instance = self.get_object()
        new_instance = serializer.save()
        
        if old_instance.status != new_instance.status:
            AppointmentStatusHistory.objects.create(
                appointment=new_instance,
                old_status=old_instance.status,
                new_status=new_instance.status,
                changed_by=self.request.user,
                reason=serializer.validated_data.get('notes', '')
            )
    
    @extend_schema(
        parameters=[
            OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
            OpenApiParameter('doctor', type=str, description='Doctor ID'),
        ]
    )
    @action(detail=False, methods=['get'])
    def today_appointments(self, request):
        """Get today's appointments"""
        today = date.today()
        queryset = self.get_queryset().filter(appointment_date=today)
        
        doctor_id = request.query_params.get('doctor')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        request={},
        responses={200: AppointmentSerializer}
    )
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an appointment"""
        appointment = self.get_object()
        
        if appointment.status != 'SCHEDULED':
            return Response(
                {'error': 'Chỉ có thể xác nhận lịch hẹn đang ở trạng thái "Đã đặt lịch"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = appointment.status
        appointment.status = 'CONFIRMED'
        appointment.confirmed_by = request.user
        appointment.confirmed_at = timezone.now()
        appointment.save()
        
        # Track status change
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            old_status=old_status,
            new_status='CONFIRMED',
            changed_by=request.user,
            reason='Xác nhận lịch hẹn'
        )
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def checkin(self, request, pk=None):
        """Check-in for appointment"""
        appointment = self.get_object()
        
        if not appointment.can_checkin:
            return Response(
                {'error': 'Không thể check-in cho lịch hẹn này'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = appointment.status
        appointment.status = 'CHECKED_IN'
        appointment.checked_in_at = timezone.now()
        appointment.save()
        
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            old_status=old_status,
            new_status='CHECKED_IN',
            changed_by=request.user,
            reason='Bệnh nhân đã check-in'
        )
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an appointment"""
        appointment = self.get_object()
        
        if not appointment.can_cancel:
            return Response(
                {'error': 'Không thể hủy lịch hẹn này'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        old_status = appointment.status
        appointment.status = 'CANCELLED'
        appointment.save()
        
        AppointmentStatusHistory.objects.create(
            appointment=appointment,
            old_status=old_status,
            new_status='CANCELLED',
            changed_by=request.user,
            reason=reason or 'Hủy lịch hẹn'
        )
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def status_history(self, request, pk=None):
        """Get appointment status history"""
        appointment = self.get_object()
        history = appointment.status_history.all()
        serializer = AppointmentStatusHistorySerializer(history, many=True)
        return Response(serializer.data)

@extend_schema(
    parameters=[
        OpenApiParameter('date', type=str, description='Date in YYYY-MM-DD format'),
        OpenApiParameter('department', type=str, description='Department ID'),
    ]
)
@api_view(['GET'])
def appointment_statistics(request):
    """
    Appointment Statistics
    
    Returns appointment statistics for dashboard.
    """
    today = date.today()
    date_param = request.query_params.get('date', today.strftime('%Y-%m-%d'))
    department_id = request.query_params.get('department')
    
    try:
        target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=400)
    
    queryset = Appointment.objects.filter(appointment_date=target_date)
    if department_id:
        queryset = queryset.filter(department_id=department_id)
    
    stats = {
        'total_appointments': queryset.count(),
        'by_status': {},
        'by_priority': {},
        'by_department': {},
        'by_appointment_type': {},
    }
    
    # Count by status
    status_counts = queryset.values('status').annotate(count=Count('id'))
    for item in status_counts:
        status_display = dict(Appointment.STATUS_CHOICES).get(item['status'], item['status'])
        stats['by_status'][status_display] = item['count']
    
    # Count by priority
    priority_counts = queryset.values('priority').annotate(count=Count('id'))
    for item in priority_counts:
        priority_display = dict(Appointment.PRIORITY_CHOICES).get(item['priority'], item['priority'])
        stats['by_priority'][priority_display] = item['count']
    
    # Count by department
    dept_counts = queryset.values('department__name').annotate(count=Count('id'))
    for item in dept_counts:
        stats['by_department'][item['department__name']] = item['count']
    
    # Count by appointment type
    type_counts = queryset.values('appointment_type').annotate(count=Count('id'))
    for item in type_counts:
        type_display = dict(Appointment.APPOINTMENT_TYPE_CHOICES).get(item['appointment_type'], item['appointment_type'])
        stats['by_appointment_type'][type_display] = item['count']
    
    return Response(stats)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_doctors_list(request):
    """Test endpoint để lấy danh sách bác sĩ không cần auth"""
    try:
        doctors = DoctorProfile.objects.select_related('user', 'department').all()
        data = []
        for doctor in doctors:
            data.append({
                'id': str(doctor.user.id),
                'username': doctor.user.username,
                'full_name': doctor.user.full_name,
                'email': doctor.user.email,
                'phone_number': doctor.user.phone_number,
                'department': doctor.department.name,
                'specialization': doctor.specialization,
                'degree': doctor.get_degree_display(),
                'experience_years': doctor.experience_years,
                'license_number': doctor.license_number,
            })
        return Response({
            'count': len(data),
            'results': data
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)