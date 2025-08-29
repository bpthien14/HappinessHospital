from rest_framework import serializers
from .models import Department, DoctorProfile, DoctorSchedule, Appointment, AppointmentStatusHistory, TimeSlot

class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""
    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'description', 'location', 'phone',
            'consultation_fee', 'average_consultation_time',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DoctorProfileSerializer(serializers.ModelSerializer):
    """Doctor Profile serializer"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user_id', 'specialization', 'license_number', 'experience_years',
            'department', 'department_name', 'department_code',
            'max_appointments_per_day', 'consultation_duration',
            'is_active', 'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DoctorScheduleSerializer(serializers.ModelSerializer):
    """Doctor Schedule serializer"""
    doctor_name = serializers.CharField(source='doctor.specialization', read_only=True)
    department_name = serializers.CharField(source='doctor.department.name', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_name', 'department_name',
            'date', 'shift', 'start_time', 'end_time',
            'is_available', 'max_appointments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class AppointmentSerializer(serializers.ModelSerializer):
    """Full Appointment serializer"""
    appointment_datetime = serializers.ReadOnlyField()
    is_today = serializers.ReadOnlyField()
    is_past_due = serializers.ReadOnlyField()
    can_cancel = serializers.ReadOnlyField()
    can_checkin = serializers.ReadOnlyField()
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number', 'patient_id', 'doctor_id', 'department_id',
            'appointment_date', 'appointment_time', 'appointment_datetime',
            'estimated_duration', 'appointment_type', 'appointment_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'queue_number', 'chief_complaint', 'symptoms', 'notes',
            'booked_by_id', 'confirmed_by_id', 'confirmed_at',
            'is_today', 'is_past_due', 'can_cancel', 'can_checkin',
            'checked_in_at', 'actual_start_time', 'actual_end_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'appointment_number', 'queue_number', 'appointment_datetime',
            'is_today', 'is_past_due', 'can_cancel', 'can_checkin',
            'confirmed_by_id', 'confirmed_at', 'checked_in_at', 'actual_start_time', 'actual_end_time',
            'created_at', 'updated_at'
        ]

class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""
    class Meta:
        model = Appointment
        fields = [
            'patient_id', 'doctor_id', 'department_id',
            'appointment_date', 'appointment_time', 'estimated_duration',
            'appointment_type', 'priority', 'chief_complaint', 'symptoms', 'notes'
        ]
        extra_kwargs = {
            'patient_id': {'required': True},
            'doctor_id': {'required': True},
            'department_id': {'required': True},
            'appointment_date': {'required': True},
            'appointment_time': {'required': True},
            'chief_complaint': {'required': True},
        }

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""
    class Meta:
        model = Appointment
        fields = [
            'appointment_date', 'appointment_time', 'estimated_duration',
            'appointment_type', 'priority', 'status', 'chief_complaint', 'symptoms', 'notes'
        ]

class AppointmentSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for appointment lists"""
    appointment_datetime = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'appointment_number', 'patient_id', 'doctor_id', 'department_id',
            'appointment_date', 'appointment_time', 'appointment_datetime',
            'appointment_type', 'priority', 'status', 'status_display',
            'queue_number', 'created_at'
        ]

class AppointmentStatusHistorySerializer(serializers.ModelSerializer):
    """Appointment Status History serializer"""
    class Meta:
        model = AppointmentStatusHistory
        fields = [
            'id', 'appointment', 'old_status', 'new_status', 
            'changed_by_id', 'reason', 'changed_at'
        ]
        read_only_fields = ['id', 'changed_at']

class TimeSlotSerializer(serializers.ModelSerializer):
    """Time Slot serializer"""
    doctor_name = serializers.CharField(source='doctor.specialization', read_only=True)
    department_name = serializers.CharField(source='doctor.department.name', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'doctor', 'doctor_name', 'department_name',
            'date', 'start_time', 'end_time',
            'is_available', 'max_appointments', 'current_appointments',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AvailableSlotSerializer(serializers.ModelSerializer):
    """Available Time Slot serializer for booking"""
    doctor_name = serializers.CharField(source='doctor.specialization', read_only=True)
    department_name = serializers.CharField(source='doctor.department.name', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'doctor', 'doctor_name', 'department_name',
            'date', 'start_time', 'end_time',
            'max_appointments', 'current_appointments'
        ]
