#!/usr/bin/env python
import os
import sys
import django
import requests
import json
from datetime import datetime, date

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_appointments_api():
    """Test appointments API directly"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔍 Testing Appointments API...")
    
    # Test without authentication first (since permission is AllowAny)
    response = requests.get(f"{base_url}/api/appointments/")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total appointments: {data.get('count', 0)}")
        
        if data.get('results'):
            print("\nFirst few appointments:")
            for apt in data['results'][:3]:
                print(f"- ID: {apt['id']}, Date: {apt['appointment_date']}, Status: {apt['status']}")
        else:
            print("No appointments found in results")
    else:
        print(f"Error: {response.text}")
    
    # Test specific date queries
    test_dates = ['2025-09-05', '2025-09-04', '2025-09-03']
    for test_date in test_dates:
        print(f"\n📅 Testing appointments for {test_date}:")
        response = requests.get(f"{base_url}/api/appointments/?appointment_date={test_date}")
        if response.status_code == 200:
            data = response.json()
            print(f"Count for {test_date}: {data.get('count', 0)}")
        else:
            print(f"Error for {test_date}: {response.text}")

def test_with_django_orm():
    """Test using Django ORM directly"""
    from apps.appointments.models import Appointment
    
    print("\n🔍 Testing with Django ORM...")
    
    total_count = Appointment.objects.count()
    print(f"Total appointments in DB: {total_count}")
    
    if total_count > 0:
        print("\nFirst 5 appointments:")
        for apt in Appointment.objects.all()[:5]:
            print(f"- ID: {apt.id}, Date: {apt.appointment_date}, Status: {apt.status}")
        
        # Test specific date
        date_2025_09_05 = Appointment.objects.filter(appointment_date='2025-09-05').count()
        print(f"\nAppointments on 2025-09-05: {date_2025_09_05}")
    else:
        print("No appointments found in database")

if __name__ == "__main__":
    test_with_django_orm()
    test_appointments_api()
