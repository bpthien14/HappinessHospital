#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, date, time

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def create_sample_appointment_today():
    """Create a sample appointment for today to test chart"""
    from apps.appointments.models import Appointment, DoctorProfile, Department
    from apps.patients.models import Patient
    from apps.users.models import User
    
    # Get or create a patient
    try:
        patient = Patient.objects.first()
        if not patient:
            print("❌ No patients found. Please create a patient first.")
            return
        
        # Get or create a doctor
        doctor = DoctorProfile.objects.first()
        if not doctor:
            print("❌ No doctors found. Please create a doctor first.")
            return
            
        # Get or create a department
        department = Department.objects.first()
        if not department:
            print("❌ No departments found. Please create a department first.")
            return
        
        # Get a user to book the appointment
        user = User.objects.filter(is_staff=True).first()
        if not user:
            print("❌ No staff users found.")
            return
        
        # Create appointment for today
        today = date.today()
        appointment_time = time(10, 0)  # 10:00 AM
        
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            department=department,
            appointment_date=today,
            appointment_time=appointment_time,
            appointment_type='REGULAR',
            status='SCHEDULED',
            priority='NORMAL',
            notes='Test appointment for dashboard chart',
            booked_by=user
        )
        
        print(f"✅ Created appointment for today ({today}):")
        print(f"   - ID: {appointment.id}")
        print(f"   - Patient: {patient.full_name}")
        print(f"   - Doctor: {doctor.user.get_full_name()}")
        print(f"   - Time: {appointment_time}")
        print(f"   - Status: {appointment.status}")
        
    except Exception as e:
        print(f"❌ Error creating appointment: {e}")

if __name__ == "__main__":
    create_sample_appointment_today()
