from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from faker import Faker
import random
from datetime import date, timedelta

User = get_user_model()
fake = Faker('vi_VN')  # Vietnamese locale

class Command(BaseCommand):
    help = 'Generate sample patient data for testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of patients to create',
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create a user for created_by field
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@hospital.com',
                    password='admin123',
                    is_superuser=True,
                    is_staff=True
                )
        except Exception as e:
            self.stdout.write(f"Error creating admin user: {e}")
            return
        
        provinces = [
            'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
            'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu'
        ]
        
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        
        for i in range(count):
            try:
                # Generate random data
                full_name = fake.name()
                birth_date = fake.date_of_birth(minimum_age=1, maximum_age=90)
                gender = random.choice(['M', 'F'])
                
                patient = Patient.objects.create(
                    full_name=full_name,
                    date_of_birth=birth_date,
                    gender=gender,
                    phone_number=self.generate_phone(),
                    email=fake.email() if random.choice([True, False]) else None,
                    address=fake.address(),
                    ward=fake.city(),
                    district=fake.city(),
                    province=random.choice(provinces),
                    citizen_id=self.generate_citizen_id(),
                    blood_type=random.choice(blood_types) if random.choice([True, False]) else None,
                    allergies=fake.text(max_nb_chars=100) if random.choice([True, False, False]) else '',
                    chronic_diseases=fake.text(max_nb_chars=100) if random.choice([True, False, False]) else '',
                    emergency_contact_name=fake.name(),
                    emergency_contact_phone=self.generate_phone(),
                    emergency_contact_relationship=random.choice(['Vợ/Chồng', 'Con', 'Cha/Mẹ', 'Anh/Chị em']),
                    has_insurance=random.choice([True, False]),
                    insurance_number=self.generate_insurance_number() if random.choice([True, False]) else None,
                    insurance_valid_from=fake.date_between(start_date='-1y', end_date='today') if random.choice([True, False]) else None,
                    insurance_valid_to=fake.date_between(start_date='today', end_date='+1y') if random.choice([True, False]) else None,
                    created_by=admin_user
                )
                
                if i % 10 == 0:
                    self.stdout.write(f'Created {i+1}/{count} patients...')
                    
            except Exception as e:
                self.stdout.write(f'Error creating patient {i+1}: {e}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} sample patients')
        )
    
    def generate_phone(self):
        """Generate Vietnamese phone number"""
        prefixes = ['090', '091', '092', '093', '094', '095', '096', '097', '098', '099']
        return random.choice(prefixes) + str(random.randint(1000000, 9999999))
    
    def generate_citizen_id(self):
        """Generate random citizen ID"""
        if random.choice([True, False]):
            return str(random.randint(100000000, 999999999))  # 9 digits
        else:
            return str(random.randint(100000000000, 999999999999))  # 12 digits
    
    def generate_insurance_number(self):
        """Generate random insurance number"""
        return 'HX' + str(random.randint(100000000000, 999999999999))