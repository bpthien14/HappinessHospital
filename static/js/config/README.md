# 🏥 Hospital Services Configuration

Hệ thống quản lý cấu hình services tập trung cho Hospital Management System.

## 📋 Tổng quan

File `services.js` giúp quản lý tất cả các service URLs và endpoints ở một nơi, giúp dễ dàng chuyển đổi giữa Monolith và Microservices architecture.

## 🔧 Cấu hình Services

### Các Services và Ports

| Service | Port | Description |
|---------|------|-------------|
| **Nginx** | 80, 443 | API Gateway & Load Balancer |
| **RabbitMQ** | 5672, 15672 | Message Queue |
| **Auth Service** | 8001 | Xác thực và JWT |
| **Patients Service** | 8002 | Quản lý bệnh nhân |
| **Appointments Service** | 8003 | Quản lý lịch hẹn |
| **Prescriptions Service** | 8004 | Quản lý đơn thuốc |
| **Payments Service** | 8005 | Xử lý thanh toán |
| **Notifications Service** | 8006 | Gửi thông báo |
| **Main App** | 8000 | Django Monolith (hiện tại) |

## 🚀 Cách sử dụng

### 1. Cách đơn giản nhất - ServiceHelper

```javascript
// Thay vì hardcode
const response = await axios.get('/api/appointments/');

// Dùng ServiceHelper
const url = ServiceHelper.getAppointmentsURL();
const response = await axios.get(url);
```

### 2. Các helper functions có sẵn

```javascript
// Auth
ServiceHelper.getAuthLoginURL()
ServiceHelper.getAuthLogoutURL()
ServiceHelper.getAuthRefreshURL()

// Patients
ServiceHelper.getPatientsURL()
ServiceHelper.getPatientDetailURL(id)
ServiceHelper.getPatientsStatsURL()

// Appointments
ServiceHelper.getAppointmentsURL()
ServiceHelper.getAppointmentDetailURL(id)
ServiceHelper.getDepartmentsURL()
ServiceHelper.getDoctorsURL()

// Prescriptions
ServiceHelper.getPrescriptionsURL()
ServiceHelper.getPrescriptionDetailURL(id)
ServiceHelper.getDrugsURL()

// Payments
ServiceHelper.getPaymentsURL()
ServiceHelper.getPaymentDetailURL(id)
```

### 3. Cách linh hoạt - getEndpointURL

```javascript
// Lấy endpoint với parameters
const url = getEndpointURL('APPOINTMENTS_SERVICE', 'DETAIL', {id: 123});
// Kết quả: http://localhost:8003/api/appointments/123/

// Custom endpoint
const baseURL = getServiceURL('PRESCRIPTIONS_SERVICE');
const customURL = `${baseURL}/api/drugs/categories/`;
```

## 🔄 Chuyển đổi Environment

### Development (Monolith)
```javascript
const CURRENT_ENV = 'DEVELOPMENT';
// Tất cả services sẽ dùng localhost:8000
```

### Production (Microservices)
```javascript
const CURRENT_ENV = 'PRODUCTION';
// Services sẽ dùng các port riêng biệt
```

## 📝 Ví dụ thực tế

### Trước khi có Services Config
```javascript
async function loadAppointments() {
    const response = await axios.get('/api/appointments/');
    const doctorResponse = await axios.get('/api/doctors/');
    const departmentResponse = await axios.get('/api/departments/');
    // ... hardcode URLs khắp nơi
}
```

### Sau khi có Services Config
```javascript
async function loadAppointments() {
    const appointmentsURL = ServiceHelper.getAppointmentsURL();
    const doctorsURL = ServiceHelper.getDoctorsURL();
    const departmentsURL = ServiceHelper.getDepartmentsURL();
    
    const response = await axios.get(appointmentsURL);
    const doctorResponse = await axios.get(doctorsURL);
    const departmentResponse = await axios.get(departmentsURL);
}
```

## 🛠 Thay đổi cấu hình

### Đổi port của service
```javascript
// Trong services.js
PRESCRIPTIONS_SERVICE: {
    HOST: 'localhost',
    PORT: 9004,  // Thay đổi từ 8004 sang 9004
    BASE_URL: 'http://localhost:9004'
}
```

### Đổi sang external host
```javascript
PAYMENTS_SERVICE: {
    HOST: 'payments.hospital.com',
    PORT: 443,
    BASE_URL: 'https://payments.hospital.com'
}
```

### Thêm service mới
```javascript
REPORTS_SERVICE: {
    HOST: 'localhost',
    PORT: 8007,
    BASE_URL: 'http://localhost:8007',
    ENDPOINTS: {
        LIST: '/api/reports/',
        GENERATE: '/api/reports/generate/',
        DOWNLOAD: '/api/reports/{id}/download/'
    }
}
```

## 🎯 Lợi ích

1. **Tập trung quản lý**: Tất cả URLs ở một nơi
2. **Dễ bảo trì**: Đổi port chỉ cần sửa một chỗ
3. **Linh hoạt**: Chuyển đổi giữa monolith và microservices dễ dàng
4. **Debug friendly**: Dễ trace URLs trong console
5. **Environment specific**: Config khác nhau cho dev/prod

## 📚 Files liên quan

- `static/js/config/services.js` - Cấu hình chính
- `static/js/config/services-examples.js` - Ví dụ sử dụng
- `templates/base/base.html` - Load script

## 🔍 Debug

Mở console và gõ:
```javascript
console.log('Current config:', getCurrentServiceConfig());
console.log('Appointments URL:', ServiceHelper.getAppointmentsURL());
console.log('All services:', SERVICES);
```
