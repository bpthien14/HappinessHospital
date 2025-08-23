from django.core.management.base import BaseCommand
from apps.users.models import Role, Permission, RolePermission

class Command(BaseCommand):
    help = 'Create default roles and permissions for the hospital system'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating default permissions...')
        
        # Create permissions
        permissions_data = [
            ('USER:CREATE', 'USER', 'CREATE', 'Create user accounts'),
            ('USER:READ', 'USER', 'READ', 'View user information'),
            ('USER:UPDATE', 'USER', 'UPDATE', 'Update user information'),
            ('USER:DELETE', 'USER', 'DELETE', 'Delete user accounts'),
            
            ('PATIENT:CREATE', 'PATIENT', 'CREATE', 'Create patient records'),
            ('PATIENT:READ', 'PATIENT', 'READ', 'View patient information'),
            ('PATIENT:UPDATE', 'PATIENT', 'UPDATE', 'Update patient information'),
            ('PATIENT:DELETE', 'PATIENT', 'DELETE', 'Delete patient records'),
            
            ('APPOINTMENT:CREATE', 'APPOINTMENT', 'CREATE', 'Schedule appointments'),
            ('APPOINTMENT:READ', 'APPOINTMENT', 'READ', 'View appointments'),
            ('APPOINTMENT:UPDATE', 'APPOINTMENT', 'UPDATE', 'Modify appointments'),
            ('APPOINTMENT:CANCEL', 'APPOINTMENT', 'CANCEL', 'Cancel appointments'),
            
            ('PRESCRIPTION:CREATE', 'PRESCRIPTION', 'CREATE', 'Create prescriptions'),
            ('PRESCRIPTION:READ', 'PRESCRIPTION', 'READ', 'View prescriptions'),
            ('PRESCRIPTION:UPDATE', 'PRESCRIPTION', 'UPDATE', 'Update prescriptions'),
            ('PRESCRIPTION:APPROVE', 'PRESCRIPTION', 'APPROVE', 'Approve prescriptions'),
            
            ('PAYMENT:CREATE', 'PAYMENT', 'CREATE', 'Process payments'),
            ('PAYMENT:READ', 'PAYMENT', 'READ', 'View payment records'),
            ('PAYMENT:UPDATE', 'PAYMENT', 'UPDATE', 'Update payment status'),
            
            ('TESTING:CREATE', 'TESTING', 'CREATE', 'Order tests'),
            ('TESTING:READ', 'TESTING', 'READ', 'View test results'),
            ('TESTING:UPDATE', 'TESTING', 'UPDATE', 'Update test results'),
            
            ('REPORT:READ', 'REPORT', 'READ', 'View reports'),
            ('REPORT:CREATE', 'REPORT', 'CREATE', 'Generate reports'),
            
            ('SYSTEM:READ', 'SYSTEM', 'READ', 'View system settings'),
            ('SYSTEM:UPDATE', 'SYSTEM', 'UPDATE', 'Modify system settings'),
        ]
        
        for name, resource, action, description in permissions_data:
            permission, created = Permission.objects.get_or_create(
                name=name,
                defaults={
                    'resource': resource,
                    'action': action,
                    'description': description
                }
            )
            if created:
                self.stdout.write(f'Created permission: {name}')
        
        self.stdout.write('Creating default roles...')
        
        # Create roles
        roles_data = [
            ('ADMIN', 'SYSTEM', 'System administrator with all permissions'),
            ('DOCTOR', 'SYSTEM', 'Doctor with patient care permissions'),
            ('NURSE', 'SYSTEM', 'Nurse with patient care permissions'),
            ('RECEPTION', 'SYSTEM', 'Reception staff with patient registration'),
            ('PHARMACIST', 'SYSTEM', 'Pharmacist with prescription management'),
            ('TECHNICIAN', 'SYSTEM', 'Lab technician with testing permissions'),
            ('CASHIER', 'SYSTEM', 'Cashier with payment processing'),
            ('PATIENT', 'SYSTEM', 'Patient with limited self-service permissions'),
        ]
        
        for name, role_type, description in roles_data:
            role, created = Role.objects.get_or_create(
                name=name,
                defaults={
                    'role_type': role_type,
                    'description': description
                }
            )
            if created:
                self.stdout.write(f'Created role: {name}')
        
        self.stdout.write('Assigning permissions to roles...')
        
        # Assign permissions to roles
        role_permissions = {
            'ADMIN': [
                'USER:CREATE', 'USER:READ', 'USER:UPDATE', 'USER:DELETE',
                'PATIENT:CREATE', 'PATIENT:READ', 'PATIENT:UPDATE', 'PATIENT:DELETE',
                'APPOINTMENT:CREATE', 'APPOINTMENT:READ', 'APPOINTMENT:UPDATE', 'APPOINTMENT:CANCEL',
                'PRESCRIPTION:CREATE', 'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE', 'PRESCRIPTION:APPROVE',
                'PAYMENT:CREATE', 'PAYMENT:READ', 'PAYMENT:UPDATE',
                'TESTING:CREATE', 'TESTING:READ', 'TESTING:UPDATE',
                'REPORT:READ', 'REPORT:CREATE',
                'SYSTEM:READ', 'SYSTEM:UPDATE'
            ],
            'DOCTOR': [
                'PATIENT:READ', 'PATIENT:UPDATE',
                'APPOINTMENT:READ', 'APPOINTMENT:UPDATE',
                'PRESCRIPTION:CREATE', 'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE',
                'TESTING:CREATE', 'TESTING:READ', 'TESTING:UPDATE',
                'REPORT:READ'
            ],
            'NURSE': [
                'PATIENT:READ', 'PATIENT:UPDATE',
                'APPOINTMENT:READ', 'APPOINTMENT:UPDATE',
                'PRESCRIPTION:READ',
                'TESTING:READ'
            ],
            'RECEPTION': [
                'PATIENT:CREATE', 'PATIENT:READ', 'PATIENT:UPDATE',
                'APPOINTMENT:CREATE', 'APPOINTMENT:READ', 'APPOINTMENT:UPDATE', 'APPOINTMENT:CANCEL'
            ],
            'PHARMACIST': [
                'PRESCRIPTION:READ', 'PRESCRIPTION:UPDATE', 'PRESCRIPTION:APPROVE',
                'PATIENT:READ'
            ],
            'TECHNICIAN': [
                'TESTING:READ', 'TESTING:UPDATE',
                'PATIENT:READ'
            ],
            'CASHIER': [
                'PAYMENT:CREATE', 'PAYMENT:READ', 'PAYMENT:UPDATE',
                'PATIENT:READ'
            ],
            'PATIENT': [
                'PATIENT:READ',
                'APPOINTMENT:CREATE', 'APPOINTMENT:READ',
                'PRESCRIPTION:READ'
            ]
        }
        
        for role_name, permission_names in role_permissions.items():
            try:
                role = Role.objects.get(name=role_name)
                for permission_name in permission_names:
                    try:
                        permission = Permission.objects.get(name=permission_name)
                        role_permission, created = RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission
                        )
                        if created:
                            self.stdout.write(f'Assigned {permission_name} to {role_name}')
                    except Permission.DoesNotExist:
                        self.stdout.write(f'Permission {permission_name} not found')
            except Role.DoesNotExist:
                self.stdout.write(f'Role {role_name} not found')
        
        self.stdout.write(self.style.SUCCESS('Successfully created default roles and permissions'))
        