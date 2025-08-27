#!/usr/bin/env python3
"""
Script để tạo superuser với đầy đủ thông tin required
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

def create_superuser():
    # Kiểm tra xem đã có superuser chưa
    if User.objects.filter(is_superuser=True).exists():
        print("Superuser đã tồn tại!")
        return
    
    # Tạo superuser với đầy đủ thông tin
    user = User.objects.create_superuser(
        username='admin',
        email='admin@hospital.com',
        password='admin123',
        first_name='Admin',
        last_name='Hospital',
        user_type='ADMIN'
    )
    
    print(f"Đã tạo superuser thành công:")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Password: admin123")
    print(f"Họ tên: {user.first_name} {user.last_name}")
    print(f"Loại user: {user.get_user_type_display()}")

if __name__ == '__main__':
    create_superuser()
