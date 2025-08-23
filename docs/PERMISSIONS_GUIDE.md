# 🏥 Hướng dẫn Hệ thống Phân quyền - Hospital Management System

## 📋 Tổng quan

Hệ thống phân quyền được thiết kế dựa trên **nghiệp vụ thực tế** của bệnh viện, tuân theo các quy trình:
- **Tiếp đón & Đăng ký** → **Khám lâm sàng** → **Xét nghiệm** → **Lãnh thuốc** → **Thanh toán BHYT**

## 🔐 Cấu trúc Permissions

### **Format: `RESOURCE:ACTION`**
- **RESOURCE**: Đối tượng cần quản lý (PATIENT, MEDICAL_RECORD, APPOINTMENT, etc.)
- **ACTION**: Hành động được phép thực hiện (CREATE, READ, UPDATE, DELETE, etc.)

### **Các Resources chính:**
1. **PATIENT** - Quản lý bệnh nhân
2. **MEDICAL_RECORD** - Hồ sơ y tế
3. **APPOINTMENT** - Lịch khám
4. **PRESCRIPTION** - Đơn thuốc
5. **TESTING** - Xét nghiệm (CLS)
6. **PAYMENT** - Thanh toán
7. **BHYT** - Bảo hiểm y tế
8. **USER** - Quản lý người dùng
9. **ROLE** - Quản lý vai trò
10. **REPORT** - Báo cáo
11. **NOTIFICATION** - Thông báo
12. **SYSTEM** - Hệ thống

## 👥 Các Roles và Quyền

### **1. Super Admin** 🌟
- **Quyền**: Tất cả permissions
- **Chức năng**: Quản trị toàn bộ hệ thống

### **2. Hospital Admin** 🏥
- **Quyền**: Hầu hết permissions (trừ SYSTEM:BACKUP, SYSTEM:RESTORE)
- **Chức năng**: Quản lý toàn bộ bệnh viện

### **3. Department Head** 📋
- **Quyền**: Quản lý khoa/phòng ban
- **Chức năng**: Duyệt hồ sơ, phân bổ bác sĩ, xem báo cáo

### **4. Doctor** 👨‍⚕️
- **Quyền**: 
  - `PATIENT:READ, UPDATE, SEARCH`
  - `MEDICAL_RECORD:CREATE, READ, UPDATE`
  - `PRESCRIPTION:CREATE, READ, UPDATE, APPROVE`
  - `TESTING:CREATE, READ, UPDATE`
  - `APPOINTMENT:READ, UPDATE`
- **Chức năng**: Khám lâm sàng, kê đơn, chỉ định xét nghiệm

### **5. Nurse** 👩‍⚕️
- **Quyền**:
  - `PATIENT:READ, UPDATE`
  - `MEDICAL_RECORD:READ, UPDATE`
  - `APPOINTMENT:READ, UPDATE`
  - `TESTING:READ, UPDATE`
- **Chức năng**: Chăm sóc bệnh nhân, hỗ trợ bác sĩ

### **6. Receptionist** 🎫
- **Quyền**:
  - `PATIENT:CREATE, READ, UPDATE, SEARCH`
  - `APPOINTMENT:CREATE, READ, UPDATE, DELETE`
  - `BHYT:VERIFY, READ`
  - `PAYMENT:CREATE, READ`
- **Chức năng**: Đăng ký khám, kiểm tra BHYT, đặt lịch

### **7. Pharmacist** 💊
- **Quyền**:
  - `PATIENT:READ`
  - `PRESCRIPTION:READ, UPDATE, PREPARE, DISPENSE, UPDATE_STATUS`
  - `BHYT:READ`
- **Chức năng**: Soạn thuốc, cập nhật trạng thái đơn thuốc

### **8. Technician** 🔬
- **Quyền**:
  - `PATIENT:READ`
  - `TESTING:READ, UPDATE, PERFORM`
  - `REPORT:READ`
- **Chức năng**: Thực hiện xét nghiệm, cập nhật kết quả

### **9. Cashier** 💰
- **Quyền**:
  - `PATIENT:READ`
  - `PAYMENT:CREATE, READ, UPDATE, APPROVE`
  - `BHYT:READ, SETTLEMENT`
- **Chức năng**: Xử lý thanh toán, quyết toán BHYT

### **10. Patient** 👤
- **Quyền**: Chỉ xem thông tin của mình
- **Chức năng**: Xem hồ sơ, lịch khám, đơn thuốc cá nhân

## 🚀 Cách sử dụng

### **1. Setup Permissions**
```bash
# Chạy script setup permissions
python scripts/setup_permissions.py
```

### **2. Kiểm tra Permissions**
```bash
# Kiểm tra toàn bộ hệ thống
python scripts/check_permissions.py

# Kiểm tra permissions của user cụ thể
python scripts/check_permissions.py doctor1
```

### **3. Test với các tài khoản demo**
```bash
# Super Admin
username: admin, password: admin123

# Doctor
username: doctor1, password: doctor123

# Nurse
username: nurse1, password: nurse123

# Receptionist
username: reception1, password: reception123

# Pharmacist
username: pharmacist1, password: pharmacist123
```

## 🔒 Kiểm tra Permissions trong Code

### **Trong Views:**
```python
from shared.permissions.base_permissions import HasPermission

class PatientViewSet(viewsets.ModelViewSet):
    permission_classes = [HasPermission]
    
    def get_permissions(self):
        if self.action == 'list':
            permission = 'PATIENT:READ'
        elif self.action == 'create':
            permission = 'PATIENT:CREATE'
        elif self.action == 'update':
            permission = 'PATIENT:UPDATE'
        elif self.action == 'destroy':
            permission = 'PATIENT:DELETE'
        else:
            permission = 'PATIENT:READ'
        
        return [HasPermission(permission)]
```

### **Trong Templates:**
```html
{% if perms.PATIENT.CREATE %}
    <button class="btn btn-primary">Thêm bệnh nhân</button>
{% endif %}

{% if perms.PATIENT.READ %}
    <div class="patient-list">
        <!-- Hiển thị danh sách bệnh nhân -->
    </div>
{% endif %}
```

## 📊 Mapping Nghiệp vụ - Permissions

### **Quy trình Tiếp đón:**
1. **Lấy số thứ tự** → `APPOINTMENT:CREATE`
2. **Kiểm tra hồ sơ** → `PATIENT:READ, SEARCH`
3. **Kiểm tra BHYT** → `BHYT:VERIFY, READ`
4. **Đăng ký lịch khám** → `APPOINTMENT:CREATE, UPDATE`

### **Quy trình Khám lâm sàng:**
1. **Nhận phiếu** → `APPOINTMENT:READ`
2. **Tra cứu hồ sơ** → `PATIENT:READ, MEDICAL_RECORD:READ`
3. **Khám bệnh** → `MEDICAL_RECORD:UPDATE`
4. **Kê đơn** → `PRESCRIPTION:CREATE, APPROVE`
5. **Chỉ định xét nghiệm** → `TESTING:CREATE`

### **Quy trình Xét nghiệm:**
1. **Thực hiện xét nghiệm** → `TESTING:PERFORM, UPDATE`
2. **Cập nhật kết quả** → `TESTING:UPDATE`
3. **Duyệt kết quả** → `TESTING:APPROVE`

### **Quy trình Lãnh thuốc:**
1. **Soạn thuốc** → `PRESCRIPTION:PREPARE`
2. **Cấp phát thuốc** → `PRESCRIPTION:DISPENSE`
3. **Cập nhật trạng thái** → `PRESCRIPTION:UPDATE_STATUS`
4. **Quyết toán BHYT** → `BHYT:SETTLEMENT`

## ⚠️ Lưu ý quan trọng

### **1. Security:**
- Mỗi API endpoint phải có permission check
- User chỉ có thể truy cập dữ liệu theo quyền được cấp
- Audit log cho tất cả thao tác quan trọng

### **2. Performance:**
- Cache permissions để tránh query database mỗi lần check
- Sử dụng `select_related` và `prefetch_related` cho queries

### **3. Maintenance:**
- Regular review permissions
- Update permissions khi có thay đổi nghiệp vụ
- Backup permission data

## 🔧 Troubleshooting

### **Lỗi 403 Forbidden:**
- Kiểm tra user có được gán role không
- Kiểm tra role có permission cần thiết không
- Kiểm tra `HasPermission` class có hoạt động đúng không

### **Permissions không hoạt động:**
- Chạy `python scripts/check_permissions.py` để kiểm tra
- Kiểm tra database có permissions và roles không
- Kiểm tra `UserRole` relationships

## 📞 Hỗ trợ

Nếu gặp vấn đề với hệ thống permissions:
1. Chạy script check permissions
2. Kiểm tra logs Django
3. Verify database data
4. Contact development team

---

**Hệ thống permissions được thiết kế để đảm bảo an toàn và tuân thủ nghiệp vụ y tế Việt Nam! 🏥✨**
