from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import date, datetime, timedelta, time

from .models import (
    Department, DoctorProfile, DoctorSchedule, 
    Appointment, AppointmentStatusHistory, TimeSlot
)

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    doctor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = [
            'id', 'code', 'name', 'description', 'location', 'phone',
            'consultation_fee', 'average_consultation_time', 'doctor_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_doctor_count(self, obj):
        return obj.doctors.filter(is_active=True).count()

class DoctorProfileSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='user.full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    
    class Meta:
        model = DoctorProfile
        fields = [
            'id', 'user', 'doctor_name', 'email', 'phone',
            'department', 'department_name', 'department_code',
            'license_number', 'degree', 'specialization', 'experience_years',
            'max_patients_per_day', 'consultation_duration',
            'bio', 'achievements', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DoctorScheduleSerializer(serializers.ModelSerializer):
    """DEPRECATED: Không còn sử dụng với logic đơn giản mới"""
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    shift_display = serializers.CharField(source='get_shift_display', read_only=True)
    
    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'doctor_name',
            'weekday', 'weekday_display', 'shift', 'shift_display',
            'start_time', 'end_time', 'max_appointments', 'appointment_duration',
            'effective_from', 'effective_to', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_code = serializers.CharField(source='patient.patient_code', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone_number', read_only=True)
    
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_code = serializers.CharField(source='department.code', read_only=True)
    
    booked_by_name = serializers.CharField(source='booked_by.full_name', read_only=True)
    
    # Computed fields
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
            'id', 'appointment_number', 'patient', 'patient_name', 'patient_code', 'patient_phone',
            'doctor', 'doctor_name', 'doctor_specialization',
            'department', 'department_name', 'department_code',
            'appointment_date', 'appointment_time', 'appointment_datetime',
            'estimated_duration', 'appointment_type', 'appointment_type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'queue_number', 'chief_complaint', 'symptoms', 'notes',
            'booked_by', 'booked_by_name', 'confirmed_by', 'confirmed_at',
            'is_today', 'is_past_due', 'can_cancel', 'can_checkin',
            'checked_in_at', 'actual_start_time', 'actual_end_time',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'appointment_number', 'queue_number', 'appointment_datetime',
            'is_today', 'is_past_due', 'can_cancel', 'can_checkin',
            'confirmed_by', 'confirmed_at', 'checked_in_at', 'actual_start_time', 'actual_end_time',
            'created_at', 'updated_at'
        ]

class AppointmentCreateSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(
        help_text="ID của bác sĩ (có thể là UUID hoặc integer)"
    )
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'appointment_date', 'appointment_time',
            'appointment_type', 'priority', 'chief_complaint', 'symptoms', 'notes'
        ]
        read_only_fields = ['queue_number', 'appointment_number', 'department']
    
    def validate_appointment_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Không thể đặt lịch hẹn trong quá khứ")
        
        # Không cho phép đặt lịch quá xa (6 tháng)
        max_date = date.today() + timedelta(days=180)
        if value > max_date:
            raise serializers.ValidationError("Chỉ có thể đặt lịch trong vòng 6 tháng")
        
        return value
    
    def validate(self, attrs):
        doctor_id = attrs.get('doctor')
        appointment_date = attrs.get('appointment_date')
        appointment_time = attrs.get('appointment_time')
        
        if doctor_id and appointment_date:
            try:
                # Get doctor profile from UUID
                doctor = DoctorProfile.objects.get(id=doctor_id, is_active=True)
                attrs['doctor'] = doctor  # Replace UUID with object for later use
                
                # Check doctor's daily capacity (simplified logic)
                existing_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=appointment_date,
                    status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
                ).count()
                
                if existing_appointments >= doctor.max_patients_per_day:
                    raise serializers.ValidationError({
                        'doctor': f'Bác sĩ đã đủ lịch trong ngày này (tối đa {doctor.max_patients_per_day} bệnh nhân/ngày)'
                    })
                
                # Check time slot availability (simplified - only check business hours 8:00-17:00)
                if appointment_time:
                    # Basic business hours check
                    if appointment_time < time(8, 0) or appointment_time >= time(17, 0):
                        raise serializers.ValidationError({
                            'appointment_time': 'Chỉ có thể đặt lịch trong giờ làm việc (8:00-17:00)'
                        })
                    
                    # Check if time slot is already booked
                    existing_appointment = Appointment.objects.filter(
                        doctor=doctor,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time,
                        status__in=['SCHEDULED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS']
                    ).exists()
                    
                    if existing_appointment:
                        raise serializers.ValidationError({
                            'appointment_time': 'Khung giờ này đã được đặt'
                        })
                        
            except DoctorProfile.DoesNotExist:
                raise serializers.ValidationError({
                    'doctor': 'Bác sĩ không tồn tại hoặc không hoạt động'
                })
        
        return attrs

class TimeSlotSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    is_fully_booked = serializers.ReadOnlyField()
    
    class Meta:
        model = TimeSlot
        fields = [
            'id', 'doctor', 'doctor_name', 'date', 'start_time', 'end_time',
            'is_available', 'max_appointments', 'current_appointments',
            'is_fully_booked'
        ]

class AppointmentStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)
    old_status_display = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AppointmentStatusHistory
        fields = [
            'id', 'appointment', 'old_status', 'old_status_display',
            'new_status', 'new_status_display', 'changed_by', 'changed_by_name',
            'reason', 'changed_at'
        ]
    
    def get_old_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.old_status, obj.old_status)
    
    def get_new_status_display(self, obj):
        return dict(Appointment.STATUS_CHOICES).get(obj.new_status, obj.new_status)

class AvailableSlotSerializer(serializers.Serializer):
    """Serializer cho available time slots"""
    time = serializers.TimeField()
    available = serializers.BooleanField()
    booked_count = serializers.IntegerField()
    max_appointments = serializers.IntegerField()