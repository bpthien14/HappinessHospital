import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import Permission, Role, User, UserRole

def check_permissions():
    """Kiểm tra permissions hiện tại"""
    print("🔍 Checking current permissions...")
    print("=" * 50)
    
    permissions = Permission.objects.all().order_by('resource', 'action')
    
    if not permissions.exists():
        print("❌ No permissions found in the system!")
        return
    
    current_resource = None
    for permission in permissions:
        if permission.resource != current_resource:
            current_resource = permission.resource
            print(f"\n📁 {current_resource}:")
        print(f"   • {permission.name}: {permission.description}")
    
    print(f"\n📊 Total permissions: {permissions.count()}")

def check_roles():
    """Kiểm tra roles hiện tại"""
    print("\n👥 Checking current roles...")
    print("=" * 50)
    
    roles = Role.objects.all().order_by('role_type', 'name')
    
    if not roles.exists():
        print("❌ No roles found in the system!")
        return
    
    current_type = None
    for role in roles:
        if role.role_type != current_type:
            current_type = role.role_type
            print(f"\n🏷️  {current_type}:")
        
        permission_count = role.permissions.count()
        print(f"   • {role.name}: {permission_count} permissions")
        print(f"     Description: {role.description}")
        
        # Hiển thị permissions của role
        if permission_count > 0:
            # Lấy permissions thông qua RolePermission
            role_permissions = role.permissions.all()
            permissions = [rp.permission for rp in role_permissions]
            permissions.sort(key=lambda x: (x.resource, x.action))
            
            for perm in permissions[:5]:  # Chỉ hiển thị 5 permissions đầu
                print(f"       - {perm.name}")
            if permission_count > 5:
                print(f"       ... and {permission_count - 5} more")
    
    print(f"\n📊 Total roles: {roles.count()}")

def check_users():
    """Kiểm tra users hiện tại"""
    print("\n👤 Checking current users...")
    print("=" * 50)
    
    users = User.objects.all().order_by('username')
    
    if not users.exists():
        print("❌ No users found in the system!")
        return
    
    for user in users:
        print(f"👤 {user.username} ({user.email})")
        print(f"   Name: {user.first_name} {user.last_name}")
        print(f"   Staff: {user.is_staff}, Superuser: {user.is_superuser}")
        
        # Kiểm tra roles của user
        user_roles = UserRole.objects.filter(user=user)
        if user_roles.exists():
            print(f"   Roles:")
            for user_role in user_roles:
                role = user_role.role
                permission_count = role.permissions.count()
                print(f"     • {role.name} ({permission_count} permissions)")
        else:
            print(f"   Roles: None assigned")
        print()
    
    print(f"📊 Total users: {users.count()}")

def check_user_permissions(username):
    """Kiểm tra permissions của một user cụ thể"""
    try:
        user = User.objects.get(username=username)
        print(f"\n🔐 Checking permissions for user: {username}")
        print("=" * 50)
        
        print(f"User: {user.first_name} {user.last_name} ({user.email})")
        print(f"Staff: {user.is_staff}, Superuser: {user.is_superuser}")
        
        if user.is_superuser:
            print("🌟 Superuser - Has all permissions!")
            return
        
        # Lấy permissions từ roles
        user_roles = UserRole.objects.filter(user=user)
        if not user_roles.exists():
            print("⚠️  No roles assigned - No permissions!")
            return
        
        all_permissions = set()
        print(f"\nRoles:")
        for user_role in user_roles:
            role = user_role.role
            permissions = role.permissions.all()
            all_permissions.update(permissions)
            
            print(f"  📋 {role.name}:")
            for perm in permissions:
                print(f"    • {perm.name}: {perm.description}")
        
        print(f"\n📊 Total unique permissions: {len(all_permissions)}")
        
        # Nhóm permissions theo resource
        permissions_by_resource = {}
        for perm in all_permissions:
            if perm.resource not in permissions_by_resource:
                permissions_by_resource[perm.resource] = []
            permissions_by_resource[perm.resource].append(perm)
        
        print(f"\n📁 Permissions by resource:")
        for resource, perms in permissions_by_resource.items():
            print(f"  {resource}:")
            for perm in perms:
                print(f"    • {perm.action}: {perm.description}")
                
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found!")

def main():
    """Main function"""
    print("🏥 Hospital Management System - Permission Checker")
    print("=" * 60)
    
    try:
        # 1. Kiểm tra permissions
        check_permissions()
        
        # 2. Kiểm tra roles
        check_roles()
        
        # 3. Kiểm tra users
        check_users()
        
        # 4. Kiểm tra permissions của user cụ thể (nếu có)
        if len(sys.argv) > 1:
            username = sys.argv[1]
            check_user_permissions(username)
        
        print("\n" + "=" * 60)
        print("✅ Permission check completed!")
        
    except Exception as e:
        print(f"\n❌ Error during check: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
