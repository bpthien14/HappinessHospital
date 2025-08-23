from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.appointments.models import Department, DoctorProfile, DoctorSchedule
from datetime import time, date

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample doctor schedules'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Create sample departments and doctors',
        )
    
    def handle(self, *args, **options):
        if options['create_sample_data']:
            self.create_sample_data()
        
        self.create_schedules()
    
    def create_sample_data(self):
        self.stdout.write('Creating sample departments...')
        
        # Create departments
        departments_data = [
            ('TIM', 'Khoa Tim mạch', 'Khoa chuyên về các bệnh lý tim mạch', 'Tầng 3'),
            ('NOI', 'Khoa Nội tổng hợp', 'Khoa nội tổng hợp', 'Tầng 2'),
            ('NGOAI', 'Khoa Ngoại tổng hợp', 'Khoa ngoại tổng hợp', 'Tầng 4'),
            ('SAN', 'Khoa Sản phụ khoa', 'Khoa sản phụ khoa', 'Tầng 5'),
            ('NHI', 'Khoa Nhi', 'Khoa nhi', 'Tầng 6'),
        ]
        
        for code, name, description, location in departments_data:
            dept, created = Department.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': description,
                    'location': location,
                    'consultation_fee': 150000,
                    'average_consultation_time': 30
                }
            )
            if created:
                self.stdout.write(f'Created department: {dept.name}')
        
        self.stdout.write('Creating sample doctors...')
        
        # Create sample doctors
        tim_dept = Department.objects.get(code='TIM')
        noi_dept = Department.objects.get(code='NOI')
        
        doctors_data = [
            ('doctor_tim', 'Bác sĩ Tim', 'doctor_tim@hospital.com', 'Tim123!', tim_dept, 'Tim mạch can thiệp'),
            ('doctor_noi', 'Bác sĩ Nội', 'doctor_noi@hospital.com', 'Noi123!', noi_dept, 'Nội tiết'),
        ]
        
        for username, full_name, email, password, dept, specialization in doctors_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': full_name.split()[1],
                    'last_name': full_name.split()[0],
                    'user_type': 'DOCTOR',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            
            profile, created = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept,
                    'license_number': f'BS{str(user.id)[:8].upper()}',
                    'degree': 'BACHELOR',
                    'specialization': specialization,
                    'experience_years': 5,
                    'max_patients_per_day': 40,
                    'consultation_duration': 15
                }
            )
            
            if created:
                self.stdout.write(f'Created doctor profile: {profile}')
    
    def create_schedules(self):
        self.stdout.write('Creating doctor schedules...')
        
        # Get all doctors
        doctors = DoctorProfile.objects.filter(is_active=True)
        
        if not doctors.exists():
            self.stdout.write(self.style.WARNING('No doctors found. Use --create-sample-data to create sample doctors.'))
            return
        
        today = date.today()
        
        # Standard schedules
        schedules_data = [
            # Morning shifts (Monday to Friday)
            (0, 'MORNING', time(7, 0), time(11, 30), 20, 15),  # Monday
            (1, 'MORNING', time(7, 0), time(11, 30), 20, 15),  # Tuesday
            (2, 'MORNING', time(7, 0), time(11, 30), 20, 15),  # Wednesday
            (3, 'MORNING', time(7, 0), time(11, 30), 20, 15),  # Thursday
            (4, 'MORNING', time(7, 0), time(11, 30), 20, 15),  # Friday
            
            # Afternoon shifts (Monday to Saturday)
            (0, 'AFTERNOON', time(13, 30), time(17, 0), 15, 15),  # Monday
            (1, 'AFTERNOON', time(13, 30), time(17, 0), 15, 15),  # Tuesday
            (2, 'AFTERNOON', time(13, 30), time(17, 0), 15, 15),  # Wednesday
            (3, 'AFTERNOON', time(13, 30), time(17, 0), 15, 15),  # Thursday
            (4, 'AFTERNOON', time(13, 30), time(17, 0), 15, 15),  # Friday
            (5, 'AFTERNOON', time(13, 30), time(17, 0), 10, 15),  # Saturday
        ]
        
        for doctor in doctors:
            for weekday, shift, start_time, end_time, max_appts, duration in schedules_data:
                schedule, created = DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    shift=shift,
                    effective_from=today,
                    defaults={
                        'start_time': start_time,
                        'end_time': end_time,
                        'max_appointments': max_appts,
                        'appointment_duration': duration,
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(f'Created schedule: {schedule}')
        
        self.stdout.write(self.style.SUCCESS('Successfully created doctor schedules'))