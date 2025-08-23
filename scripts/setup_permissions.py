#!/usr/bin/env python3
"""
Script setup permissions cho Hospital Management System
Dựa trên nghiệp vụ thực tế từ các biểu đồ luồng
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import Permission, Role, User
from apps.users.models import UserRole

def create_permissions():
    """Tạo tất cả permissions cần thiết cho hệ thống"""
    
    permissions_data = [
        # === PATIENT MANAGEMENT ===
        ('PATIENT:CREATE', 'Tạo bệnh nhân mới', 'PATIENT', 'CREATE'),
        ('PATIENT:READ', 'Xem thông tin bệnh nhân', 'PATIENT', 'READ'),
        ('PATIENT:UPDATE', 'Cập nhật thông tin bệnh nhân', 'PATIENT', 'UPDATE'),
        ('PATIENT:DELETE', 'Xóa bệnh nhân', 'PATIENT', 'DELETE'),
        ('PATIENT:SEARCH', 'Tìm kiếm bệnh nhân', 'PATIENT', 'SEARCH'),
        ('PATIENT:EXPORT', 'Xuất dữ liệu bệnh nhân', 'PATIENT', 'EXPORT'),
        
        # === MEDICAL RECORDS ===
        ('MEDICAL_RECORD:CREATE', 'Tạo hồ sơ y tế', 'MEDICAL_RECORD', 'CREATE'),
        ('MEDICAL_RECORD:READ', 'Xem hồ sơ y tế', 'MEDICAL_RECORD', 'READ'),
        ('MEDICAL_RECORD:UPDATE', 'Cập nhật hồ sơ y tế', 'MEDICAL_RECORD', 'UPDATE'),
        ('MEDICAL_RECORD:DELETE', 'Xóa hồ sơ y tế', 'MEDICAL_RECORD', 'DELETE'),
        ('MEDICAL_RECORD:APPROVE', 'Duyệt hồ sơ y tế', 'MEDICAL_RECORD', 'APPROVE'),
        
        # === APPOINTMENTS ===
        ('APPOINTMENT:CREATE', 'Tạo lịch khám', 'APPOINTMENT', 'CREATE'),
        ('APPOINTMENT:READ', 'Xem lịch khám', 'APPOINTMENT', 'READ'),
        ('APPOINTMENT:UPDATE', 'Cập nhật lịch khám', 'APPOINTMENT', 'UPDATE'),
        ('APPOINTMENT:DELETE', 'Xóa lịch khám', 'APPOINTMENT', 'DELETE'),
        ('APPOINTMENT:ASSIGN_DOCTOR', 'Phân bổ bác sĩ', 'APPOINTMENT', 'ASSIGN_DOCTOR'),
        ('APPOINTMENT:CANCEL', 'Hủy lịch khám', 'APPOINTMENT', 'CANCEL'),
        
        # === PRESCRIPTIONS ===
        ('PRESCRIPTION:CREATE', 'Kê đơn thuốc', 'PRESCRIPTION', 'CREATE'),
        ('PRESCRIPTION:READ', 'Xem đơn thuốc', 'PRESCRIPTION', 'READ'),
        ('PRESCRIPTION:UPDATE', 'Cập nhật đơn thuốc', 'PRESCRIPTION', 'UPDATE'),
        ('PRESCRIPTION:DELETE', 'Xóa đơn thuốc', 'PRESCRIPTION', 'DELETE'),
        ('PRESCRIPTION:APPROVE', 'Duyệt đơn thuốc', 'PRESCRIPTION', 'APPROVE'),
        ('PRESCRIPTION:PREPARE', 'Soạn thuốc', 'PRESCRIPTION', 'PREPARE'),
        ('PRESCRIPTION:DISPENSE', 'Cấp phát thuốc', 'PRESCRIPTION', 'DISPENSE'),
        ('PRESCRIPTION:UPDATE_STATUS', 'Cập nhật trạng thái đơn thuốc', 'PRESCRIPTION', 'UPDATE_STATUS'),
        
        # === TESTING (CLS) ===
        ('TESTING:CREATE', 'Tạo chỉ định xét nghiệm', 'TESTING', 'CREATE'),
        ('TESTING:READ', 'Xem kết quả xét nghiệm', 'TESTING', 'READ'),
        ('TESTING:UPDATE', 'Cập nhật kết quả xét nghiệm', 'TESTING', 'UPDATE'),
        ('TESTING:DELETE', 'Xóa xét nghiệm', 'TESTING', 'DELETE'),
        ('TESTING:PERFORM', 'Thực hiện xét nghiệm', 'TESTING', 'PERFORM'),
        ('TESTING:APPROVE', 'Duyệt kết quả xét nghiệm', 'TESTING', 'APPROVE'),
        
        # === PAYMENTS & BHYT ===
        ('PAYMENT:CREATE', 'Tạo thanh toán', 'PAYMENT', 'CREATE'),
        ('PAYMENT:READ', 'Xem thanh toán', 'PAYMENT', 'READ'),
        ('PAYMENT:UPDATE', 'Cập nhật thanh toán', 'PAYMENT', 'UPDATE'),
        ('PAYMENT:DELETE', 'Xóa thanh toán', 'PAYMENT', 'DELETE'),
        ('PAYMENT:APPROVE', 'Duyệt thanh toán', 'PAYMENT', 'APPROVE'),
        ('BHYT:VERIFY', 'Xác thực thẻ BHYT', 'BHYT', 'VERIFY'),
        ('BHYT:SETTLEMENT', 'Quyết toán BHYT', 'BHYT', 'SETTLEMENT'),
        ('BHYT:READ', 'Xem thông tin BHYT', 'BHYT', 'READ'),
        
        # === USER MANAGEMENT ===
        ('USER:CREATE', 'Tạo user mới', 'USER', 'CREATE'),
        ('USER:READ', 'Xem thông tin user', 'USER', 'READ'),
        ('USER:UPDATE', 'Cập nhật user', 'USER', 'UPDATE'),
        ('USER:DELETE', 'Xóa user', 'USER', 'DELETE'),
        ('USER:ASSIGN_ROLE', 'Phân quyền user', 'USER', 'ASSIGN_ROLE'),
        
        # === ROLE MANAGEMENT ===
        ('ROLE:CREATE', 'Tạo role mới', 'ROLE', 'CREATE'),
        ('ROLE:READ', 'Xem thông tin role', 'ROLE', 'READ'),
        ('ROLE:UPDATE', 'Cập nhật role', 'ROLE', 'UPDATE'),
        ('ROLE:DELETE', 'Xóa role', 'ROLE', 'DELETE'),
        ('ROLE:ASSIGN_PERMISSION', 'Phân quyền cho role', 'ROLE', 'ASSIGN_PERMISSION'),
        
        # === REPORTS & ANALYTICS ===
        ('REPORT:READ', 'Xem báo cáo', 'REPORT', 'READ'),
        ('REPORT:CREATE', 'Tạo báo cáo', 'REPORT', 'CREATE'),
        ('REPORT:EXPORT', 'Xuất báo cáo', 'REPORT', 'EXPORT'),
        ('REPORT:APPROVE', 'Duyệt báo cáo', 'REPORT', 'APPROVE'),
        
        # === NOTIFICATIONS ===
        ('NOTIFICATION:CREATE', 'Tạo thông báo', 'NOTIFICATION', 'CREATE'),
        ('NOTIFICATION:READ', 'Xem thông báo', 'NOTIFICATION', 'READ'),
        ('NOTIFICATION:SEND', 'Gửi thông báo', 'NOTIFICATION', 'SEND'),
        ('NOTIFICATION:MANAGE', 'Quản lý thông báo', 'NOTIFICATION', 'MANAGE'),
        
        # === SYSTEM ADMIN ===
        ('SYSTEM:CONFIG', 'Cấu hình hệ thống', 'SYSTEM', 'CONFIG'),
        ('SYSTEM:BACKUP', 'Sao lưu dữ liệu', 'SYSTEM', 'BACKUP'),
        ('SYSTEM:RESTORE', 'Khôi phục dữ liệu', 'SYSTEM', 'RESTORE'),
        ('SYSTEM:LOG', 'Xem log hệ thống', 'SYSTEM', 'LOG'),
    ]
    
    created_permissions = []
    for name, desc, resource, action in permissions_data:
        permission, created = Permission.objects.get_or_create(
            name=name,
            defaults={
                'description': desc,
                'resource': resource,
                'action': action
            }
        )
        created_permissions.append(permission)
        if created:
            print(f"✅ Created permission: {name}")
        else:
            print(f"ℹ️  Permission already exists: {name}")
    
    print(f"\n📊 Total permissions: {len(created_permissions)}")
    return created_permissions

def create_roles():
    """Tạo các roles với quyền phù hợp theo nghiệp vụ"""
    
    roles_data = [
        {
            'name': 'Super Admin',
            'description': 'Quản trị viên hệ thống - Toàn quyền',
            'role_type': 'SYSTEM',
            'permissions': ['*']  # Tất cả permissions
        },
        {
            'name': 'Hospital Admin',
            'description': 'Quản trị viên bệnh viện - Quản lý toàn bộ bệnh viện',
            'role_type': 'HOSPITAL',
            'permissions': [
                'PATIENT:*', 'MEDICAL_RECORD:*', 'APPOINTMENT:*', 'PRESCRIPTION:*',
                'TESTING:*', 'PAYMENT:*', 'BHYT:*', 'USER:*', 'ROLE:*',
                'REPORT:*', 'NOTIFICATION:*', 'SYSTEM:CONFIG', 'SYSTEM:LOG'
            ]
        },
        {
            'name': 'Department Head',
            'description': 'Trưởng khoa - Quản lý khoa/phòng ban',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ', 'PATIENT:UPDATE', 'PATIENT:SEARCH',
                'MEDICAL_RECORD:READ', 'MEDICAL_RECORD:UPDATE', 'MEDICAL_RECORD:APPROVE',
                'APPOINTMENT:READ', 'APPOINTMENT:UPDATE', 'APPOINTMENT:ASSIGN_DOCTOR',
                'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE', 'PRESCRIPTION:APPROVE',
                'TESTING:READ', 'TESTING:UPDATE', 'TESTING:APPROVE',
                'REPORT:READ', 'REPORT:CREATE', 'REPORT:EXPORT',
                'USER:READ', 'USER:UPDATE'
            ]
        },
        {
            'name': 'Doctor',
            'description': 'Bác sĩ - Khám lâm sàng, kê đơn, chỉ định xét nghiệm',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ', 'PATIENT:UPDATE', 'PATIENT:SEARCH',
                'MEDICAL_RECORD:CREATE', 'MEDICAL_RECORD:READ', 'MEDICAL_RECORD:UPDATE',
                'APPOINTMENT:READ', 'APPOINTMENT:UPDATE',
                'PRESCRIPTION:CREATE', 'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE', 'PRESCRIPTION:APPROVE',
                'TESTING:CREATE', 'TESTING:READ', 'TESTING:UPDATE',
                'REPORT:READ'
            ]
        },
        {
            'name': 'Nurse',
            'description': 'Điều dưỡng - Chăm sóc bệnh nhân, hỗ trợ bác sĩ',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ', 'PATIENT:UPDATE',
                'MEDICAL_RECORD:READ', 'MEDICAL_RECORD:UPDATE',
                'APPOINTMENT:READ', 'APPOINTMENT:UPDATE',
                'TESTING:READ', 'TESTING:UPDATE',
                'PRESCRIPTION:READ'
            ]
        },
        {
            'name': 'Receptionist',
            'description': 'Lễ tân - Đăng ký khám, kiểm tra BHYT, đặt lịch',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:CREATE', 'PATIENT:READ', 'PATIENT:UPDATE', 'PATIENT:SEARCH',
                'APPOINTMENT:CREATE', 'APPOINTMENT:READ', 'APPOINTMENT:UPDATE', 'APPOINTMENT:DELETE',
                'BHYT:VERIFY', 'BHYT:READ',
                'PAYMENT:CREATE', 'PAYMENT:READ'
            ]
        },
        {
            'name': 'Pharmacist',
            'description': 'Dược sĩ - Soạn thuốc, cập nhật trạng thái đơn thuốc',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ',
                'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE', 'PRESCRIPTION:PREPARE', 
                'PRESCRIPTION:DISPENSE', 'PRESCRIPTION:UPDATE_STATUS',
                'BHYT:READ'
            ]
        },
        {
            'name': 'Technician',
            'description': 'Kỹ thuật viên - Thực hiện xét nghiệm, cập nhật kết quả',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ',
                'TESTING:READ', 'TESTING:UPDATE', 'TESTING:PERFORM',
                'REPORT:READ'
            ]
        },
        {
            'name': 'Cashier',
            'description': 'Thu ngân - Xử lý thanh toán, quyết toán BHYT',
            'role_type': 'DEPARTMENT',
            'permissions': [
                'PATIENT:READ',
                'PAYMENT:CREATE', 'PAYMENT:READ', 'PAYMENT:UPDATE', 'PAYMENT:APPROVE',
                'BHYT:READ', 'BHYT:SETTLEMENT'
            ]
        },
        {
            'name': 'Patient',
            'description': 'Bệnh nhân - Xem thông tin cá nhân, lịch khám',
            'role_type': 'EXTERNAL',
            'permissions': [
                'PATIENT:READ',  # Chỉ xem thông tin của mình
                'APPOINTMENT:READ',  # Chỉ xem lịch khám của mình
                'MEDICAL_RECORD:READ',  # Chỉ xem hồ sơ của mình
                'PRESCRIPTION:READ',  # Chỉ xem đơn thuốc của mình
                'TESTING:READ',  # Chỉ xem kết quả xét nghiệm của mình
                'PAYMENT:READ'  # Chỉ xem thanh toán của mình
            ]
        }
    ]
    
    created_roles = []
    for role_info in roles_data:
        role, created = Role.objects.get_or_create(
            name=role_info['name'],
            defaults={
                'description': role_info['description'],
                'role_type': role_info['role_type']
            }
        )
        
        # Gán permissions cho role thông qua RolePermission
        if role_info['permissions'] == ['*']:
            # Super Admin - tất cả permissions
            permissions = Permission.objects.all()
        else:
            # Các role khác - permissions cụ thể
            permissions = Permission.objects.filter(name__in=role_info['permissions'])
        
        # Xóa permissions cũ
        role.permissions.all().delete()
        
        # Tạo RolePermission mới
        from apps.users.models import RolePermission
        role_permissions = []
        for permission in permissions:
            role_permissions.append(RolePermission(role=role, permission=permission))
        
        RolePermission.objects.bulk_create(role_permissions)
        created_roles.append(role)
        
        if created:
            print(f"✅ Created role: {role.name} with {permissions.count()} permissions")
        else:
            print(f"ℹ️  Role already exists: {role.name} with {permissions.count()} permissions")
    
    print(f"\n📊 Total roles: {len(created_roles)}")
    return created_roles

def create_demo_users():
    """Tạo các user demo để test"""
    
    # Tạo superuser nếu chưa có
    if not User.objects.filter(is_superuser=True).exists():
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@hospital.com',
            password='admin123',
            first_name='Super',
            last_name='Admin'
        )
        print(f"✅ Created superuser: {superuser.username}")
    
    # Tạo các user demo khác
    demo_users = [
        {
            'username': 'doctor1',
            'email': 'doctor1@hospital.com',
            'password': 'doctor123',
            'first_name': 'Nguyễn Văn',
            'last_name': 'Bác Sĩ',
            'role_name': 'Doctor'
        },
        {
            'username': 'nurse1',
            'email': 'nurse1@hospital.com',
            'password': 'nurse123',
            'first_name': 'Trần Thị',
            'last_name': 'Điều Dưỡng',
            'role_name': 'Nurse'
        },
        {
            'username': 'reception1',
            'email': 'reception1@hospital.com',
            'password': 'reception123',
            'first_name': 'Lê Văn',
            'last_name': 'Lễ Tân',
            'role_name': 'Receptionist'
        },
        {
            'username': 'pharmacist1',
            'email': 'pharmacist1@hospital.com',
            'password': 'pharmacist123',
            'first_name': 'Phạm Thị',
            'last_name': 'Dược Sĩ',
            'role_name': 'Pharmacist'
        }
    ]
    
    for user_info in demo_users:
        user, created = User.objects.get_or_create(
            username=user_info['username'],
            defaults={
                'email': user_info['email'],
                'first_name': user_info['first_name'],
                'last_name': user_info['last_name'],
                'is_staff': True
            }
        )
        
        # Đảm bảo user có is_staff=True để có thể login
        if not user.is_staff:
            user.is_staff = True
            user.save()
        
        if created:
            user.set_password(user_info['password'])
            user.save()
            print(f"✅ Created user: {user.username}")
        
        # Gán role cho user
        try:
            role = Role.objects.get(name=user_info['role_name'])
            user_role, created = UserRole.objects.get_or_create(
                user=user,
                role=role
            )
            if created:
                print(f"✅ Assigned role {role.name} to user {user.username}")
        except Role.DoesNotExist:
            print(f"⚠️  Role {user_info['role_name']} not found for user {user.username}")

def main():
    """Main function để setup toàn bộ permission system"""
    print("🏥 Setting up Hospital Management System Permissions...")
    print("=" * 60)
    
    try:
        # 1. Tạo permissions
        print("\n1️⃣ Creating permissions...")
        permissions = create_permissions()
        
        # 2. Tạo roles
        print("\n2️⃣ Creating roles...")
        roles = create_roles()
        
        # 3. Tạo demo users
        print("\n3️⃣ Creating demo users...")
        create_demo_users()
        
        print("\n" + "=" * 60)
        print("🎉 Permission system setup completed successfully!")
        print("\n📋 Summary:")
        print(f"   • Permissions: {Permission.objects.count()}")
        print(f"   • Roles: {Role.objects.count()}")
        print(f"   • Users: {User.objects.count()}")
        
        print("\n🔑 Demo accounts:")
        print("   • Super Admin: admin / admin123")
        print("   • Doctor: doctor1 / doctor123")
        print("   • Nurse: nurse1 / nurse123")
        print("   • Receptionist: reception1 / reception123")
        print("   • Pharmacist: pharmacist1 / pharmacist123")
        
        print("\n💡 Next steps:")
        print("   1. Test login với các tài khoản demo")
        print("   2. Test API endpoints với từng role")
        print("   3. Customize permissions theo yêu cầu cụ thể")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
