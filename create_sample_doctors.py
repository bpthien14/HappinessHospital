#!/usr/bin/env python3
"""
Script để tạo user bác sĩ mẫu
"""
import os
import django
import sys

# Thêm thư mục project vào Python path
sys.path.append('/Users/adriannguyen/Desktop/DEV/HCMUS/UDPT/HappinessHospital')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.appointments.models import Department, DoctorProfile

def create_sample_doctor():
    try:
        # Tạo hoặc lấy department
        department, created = Department.objects.get_or_create(
            code='TIM',
            defaults={
                'name': 'Khoa Tim mạch',
                'description': 'Khoa chuyên về các bệnh tim mạch',
                'location': 'Tầng 3, Phòng 301-310',
                'phone': '0123456789',
                'consultation_fee': 200000,
                'average_consultation_time': 45
            }
        )
        
        if created:
            print(f"✅ Đã tạo khoa: {department.name}")
        else:
            print(f"📋 Khoa đã tồn tại: {department.name}")

        # Kiểm tra xem user đã tồn tại chưa
        if User.objects.filter(username='bs_nguyen').exists():
            print("⚠️ User bác sĩ 'bs_nguyen' đã tồn tại!")
            return

        # Tạo user bác sĩ
        doctor_user = User.objects.create_user(
            username='bs_nguyen',
            email='bs.nguyen@hospital.com',
            password='doctor123',
            first_name='Nguyễn Văn',
            last_name='Minh',
            user_type='DOCTOR',
            employee_id='BS001',
            department=department.name,
            phone_number='0987654321'
        )
        
        print(f"✅ Đã tạo user bác sĩ: {doctor_user.username}")

        # Tạo doctor profile
        doctor_profile = DoctorProfile.objects.create(
            user=doctor_user,
            department=department,
            degree='MASTER',
            specializations='Tim mạch, Nội khoa',
            years_of_experience=8,
            qualifications='Thạc sĩ Y khoa - Đại học Y Hà Nội, Chứng chỉ Tim mạch quốc tế',
            bio='Bác sĩ Nguyễn Văn Minh có 8 năm kinh nghiệm trong lĩnh vực tim mạch. Từng công tác tại Bệnh viện Bạch Mai và có nhiều công trình nghiên cứu về bệnh tim mạch.',
            license_number='BS-HN-2016-001',
            is_available=True
        )

        print(f"✅ Đã tạo doctor profile thành công!")
        print(f"👨‍⚕️ Thông tin bác sĩ:")
        print(f"   - Username: {doctor_user.username}")
        print(f"   - Password: doctor123")
        print(f"   - Họ tên: {doctor_user.first_name} {doctor_user.last_name}")
        print(f"   - Email: {doctor_user.email}")
        print(f"   - Mã NV: {doctor_user.employee_id}")
        print(f"   - Khoa: {department.name}")
        print(f"   - Bằng cấp: {doctor_profile.get_degree_display()}")
        print(f"   - Chuyên khoa: {doctor_profile.specializations}")

        # Tạo thêm một bác sĩ nữa
        if not User.objects.filter(username='bs_le').exists():
            # Tạo thêm department
            department2, created2 = Department.objects.get_or_create(
                code='NOI',
                defaults={
                    'name': 'Khoa Nội tổng hợp',
                    'description': 'Khoa nội tổng hợp',
                    'location': 'Tầng 2, Phòng 201-220',
                    'phone': '0123456788',
                    'consultation_fee': 150000,
                    'average_consultation_time': 30
                }
            )

            doctor_user2 = User.objects.create_user(
                username='bs_le',
                email='bs.le@hospital.com',
                password='doctor123',
                first_name='Lê Thị',
                last_name='Hoa',
                user_type='DOCTOR',
                employee_id='BS002',
                department=department2.name,
                phone_number='0987654322'
            )

            doctor_profile2 = DoctorProfile.objects.create(
                user=doctor_user2,
                department=department2,
                degree='BACHELOR',
                specializations='Nội tổng hợp, Tiêu hóa',
                years_of_experience=5,
                qualifications='Bác sĩ Y khoa - Đại học Y Dược TP.HCM',
                bio='Bác sĩ Lê Thị Hoa chuyên về nội tổng hợp với 5 năm kinh nghiệm.',
                license_number='BS-HCM-2019-002',
                is_available=True
            )

            print(f"✅ Đã tạo thêm bác sĩ: {doctor_user2.username}")

    except Exception as e:
        print(f"❌ Lỗi khi tạo bác sĩ: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_sample_doctor()
