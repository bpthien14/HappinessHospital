#!/usr/bin/env python
"""
Setup script for Hospital Auth Service
Creates initial permissions, roles, and demo users
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from roles.models import Permission, Role, RolePermission, UserRole


def create_permissions():
    """Create initial permissions"""
    print("🔐 Creating permissions...")
    
    permissions_data = [
        # User Management
        ('USER', 'CREATE', 'Create new users'),
        ('USER', 'READ', 'View user information'),
        ('USER', 'UPDATE', 'Update user information'),
        ('USER', 'DELETE', 'Delete users'),
        
        # Patient Management
        ('PATIENT', 'CREATE', 'Create new patients'),
        ('PATIENT', 'READ', 'View patient information'),
        ('PATIENT', 'UPDATE', 'Update patient information'),
        ('PATIENT', 'DELETE', 'Delete patients'),
        
        # Appointment Management
        ('APPOINTMENT', 'CREATE', 'Create new appointments'),
        ('APPOINTMENT', 'READ', 'View appointment information'),
        ('APPOINTMENT', 'UPDATE', 'Update appointment information'),
        ('APPOINTMENT', 'DELETE', 'Delete appointments'),
        
        # Prescription Management
        ('PRESCRIPTION', 'CREATE', 'Create new prescriptions'),
        ('PRESCRIPTION', 'READ', 'View prescription information'),
        ('PRESCRIPTION', 'UPDATE', 'Update prescription information'),
        ('PRESCRIPTION', 'DELETE', 'Delete prescriptions'),
        
        # Payment Management
        ('PAYMENT', 'CREATE', 'Create new payments'),
        ('PAYMENT', 'READ', 'View payment information'),
        ('PAYMENT', 'UPDATE', 'Update payment information'),
        ('PAYMENT', 'APPROVE', 'Approve payments'),
        
        # Reporting
        ('REPORT', 'READ', 'View reports'),
        ('REPORT', 'EXPORT', 'Export reports'),
        
        # System Administration
        ('SYSTEM', 'READ', 'View system information'),
        ('SYSTEM', 'UPDATE', 'Update system settings'),
    ]
    
    created_permissions = []
    for resource, action, description in permissions_data:
        permission, created = Permission.objects.get_or_create(
            resource=resource,
            action=action,
            defaults={'description': description}
        )
        if created:
            print(f"  ✅ Created permission: {resource}:{action}")
        else:
            print(f"  ℹ️  Permission already exists: {resource}:{action}")
        created_permissions.append(permission)
    
    return created_permissions


def create_roles():
    """Create initial roles"""
    print("👥 Creating roles...")
    
    roles_data = [
        ('ADMIN', 'Administrator', 'Full system access'),
        ('DOCTOR', 'Doctor', 'Medical staff with patient management access'),
        ('NURSE', 'Nurse', 'Nursing staff with patient care access'),
        ('RECEPTIONIST', 'Receptionist', 'Front desk staff with appointment access'),
        ('PHARMACIST', 'Pharmacist', 'Pharmacy staff with prescription access'),
        ('ACCOUNTANT', 'Accountant', 'Financial staff with payment access'),
        ('PATIENT', 'Patient', 'Patient access to own information'),
    ]
    
    created_roles = {}
    for name, display_name, description in roles_data:
        role, created = Role.objects.get_or_create(
            name=name,
            defaults={
                'display_name': display_name,
                'description': description
            }
        )
        if created:
            print(f"  ✅ Created role: {display_name}")
        else:
            print(f"  ℹ️  Role already exists: {display_name}")
        created_roles[name] = role
    
    return created_roles


def assign_permissions_to_roles(permissions, roles):
    """Assign permissions to roles"""
    print("🔗 Assigning permissions to roles...")
    
    # Admin gets all permissions
    admin_role = roles['ADMIN']
    for permission in permissions:
        RolePermission.objects.get_or_create(
            role=admin_role,
            permission=permission
        )
    print(f"  ✅ Admin role has {len(permissions)} permissions")
    
    # Doctor permissions
    doctor_permissions = [
        ('PATIENT', 'READ'), ('PATIENT', 'UPDATE'),
        ('APPOINTMENT', 'CREATE'), ('APPOINTMENT', 'READ'), ('APPOINTMENT', 'UPDATE'),
        ('PRESCRIPTION', 'CREATE'), ('PRESCRIPTION', 'READ'), ('PRESCRIPTION', 'UPDATE'),
        ('REPORT', 'READ'), ('REPORT', 'EXPORT'),
    ]
    doctor_role = roles['DOCTOR']
    for resource, action in doctor_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=doctor_role, permission=permission)
    print(f"  ✅ Doctor role has {len(doctor_permissions)} permissions")
    
    # Nurse permissions
    nurse_permissions = [
        ('PATIENT', 'READ'), ('PATIENT', 'UPDATE'),
        ('APPOINTMENT', 'READ'), ('APPOINTMENT', 'UPDATE'),
        ('PRESCRIPTION', 'READ'),
    ]
    nurse_role = roles['NURSE']
    for resource, action in nurse_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=nurse_role, permission=permission)
    print(f"  ✅ Nurse role has {len(nurse_permissions)} permissions")
    
    # Receptionist permissions
    receptionist_permissions = [
        ('PATIENT', 'CREATE'), ('PATIENT', 'READ'), ('PATIENT', 'UPDATE'),
        ('APPOINTMENT', 'CREATE'), ('APPOINTMENT', 'READ'), ('APPOINTMENT', 'UPDATE'),
    ]
    receptionist_role = roles['RECEPTIONIST']
    for resource, action in receptionist_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=receptionist_role, permission=permission)
    print(f"  ✅ Receptionist role has {len(receptionist_permissions)} permissions")
    
    # Pharmacist permissions
    pharmacist_permissions = [
        ('PRESCRIPTION', 'READ'), ('PRESCRIPTION', 'UPDATE'),
        ('PATIENT', 'READ'),
    ]
    pharmacist_role = roles['PHARMACIST']
    for resource, action in pharmacist_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=pharmacist_role, permission=permission)
    print(f"  ✅ Pharmacist role has {len(pharmacist_permissions)} permissions")
    
    # Accountant permissions
    accountant_permissions = [
        ('PAYMENT', 'READ'), ('PAYMENT', 'UPDATE'), ('PAYMENT', 'APPROVE'),
        ('REPORT', 'READ'), ('REPORT', 'EXPORT'),
    ]
    accountant_role = roles['ACCOUNTANT']
    for resource, action in accountant_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=accountant_role, permission=permission)
    print(f"  ✅ Accountant role has {len(accountant_permissions)} permissions")
    
    # Patient permissions
    patient_permissions = [
        ('PATIENT', 'READ'),  # Can only read own information
        ('APPOINTMENT', 'READ'),  # Can only read own appointments
        ('PRESCRIPTION', 'READ'),  # Can only read own prescriptions
    ]
    patient_role = roles['PATIENT']
    for resource, action in patient_permissions:
        permission = Permission.objects.get(resource=resource, action=action)
        RolePermission.objects.get_or_create(role=patient_role, permission=permission)
    print(f"  ✅ Patient role has {len(patient_permissions)} permissions")


def create_demo_users(roles):
    """Create demo users"""
    print("👤 Creating demo users...")
    
    # Create admin user if not exists
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@hospital.com',
            'first_name': 'System',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("  ✅ Created admin user: admin/admin123")
    else:
        print("  ℹ️  Admin user already exists")
    
    # Create doctor user
    doctor_user, created = User.objects.get_or_create(
        username='doctor1',
        defaults={
            'email': 'doctor1@hospital.com',
            'first_name': 'Nguyễn',
            'last_name': 'Văn A',
            'is_staff': True,
        }
    )
    if created:
        doctor_user.set_password('doctor123')
        doctor_user.save()
        print("  ✅ Created doctor user: doctor1/doctor123")
    else:
        print("  ℹ️  Doctor user already exists")
    
    # Create nurse user
    nurse_user, created = User.objects.get_or_create(
        username='nurse1',
        defaults={
            'email': 'nurse1@hospital.com',
            'first_name': 'Trần',
            'last_name': 'Thị B',
            'is_staff': True,
        }
    )
    if created:
        nurse_user.set_password('nurse123')
        nurse_user.save()
        print("  ✅ Created nurse user: nurse1/nurse123")
    else:
        print("  ℹ️  Nurse user already exists")
    
    # Create receptionist user
    receptionist_user, created = User.objects.get_or_create(
        username='reception1',
        defaults={
            'email': 'reception1@hospital.com',
            'first_name': 'Lê',
            'last_name': 'Văn C',
            'is_staff': True,
        }
    )
    if created:
        receptionist_user.set_password('reception123')
        receptionist_user.save()
        print("  ✅ Created receptionist user: reception1/reception123")
    else:
        print("  ℹ️  Receptionist user already exists")
    
    return {
        'admin': admin_user,
        'doctor': doctor_user,
        'nurse': nurse_user,
        'receptionist': receptionist_user,
    }


def assign_roles_to_users(users, roles):
    """Assign roles to users"""
    print("🔗 Assigning roles to users...")
    
    # Assign admin role to admin user
    UserRole.objects.get_or_create(
        user=users['admin'],
        role=roles['ADMIN']
    )
    print("  ✅ Admin user has ADMIN role")
    
    # Assign doctor role to doctor user
    UserRole.objects.get_or_create(
        user=users['doctor'],
        role=roles['DOCTOR']
    )
    print("  ✅ Doctor user has DOCTOR role")
    
    # Assign nurse role to nurse user
    UserRole.objects.get_or_create(
        user=users['nurse'],
        role=roles['NURSE']
    )
    print("  ✅ Nurse user has NURSE role")
    
    # Assign receptionist role to receptionist user
    UserRole.objects.get_or_create(
        user=users['receptionist'],
        role=roles['RECEPTIONIST']
    )
    print("  ✅ Receptionist user has RECEPTIONIST role")


def main():
    """Main setup function"""
    print("🏥 Hospital Auth Service Setup")
    print("=" * 50)
    
    try:
        # Create permissions
        permissions = create_permissions()
        print()
        
        # Create roles
        roles = create_roles()
        print()
        
        # Assign permissions to roles
        assign_permissions_to_roles(permissions, roles)
        print()
        
        # Create demo users
        users = create_demo_users(roles)
        print()
        
        # Assign roles to users
        assign_roles_to_users(users, roles)
        print()
        
        print("🎉 Setup completed successfully!")
        print("\n📋 Demo Users:")
        print("  - admin/admin123 (Administrator)")
        print("  - doctor1/doctor123 (Doctor)")
        print("  - nurse1/nurse123 (Nurse)")
        print("  - reception1/reception123 (Receptionist)")
        print("\n🔐 You can now test the authentication endpoints!")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
