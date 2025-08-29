# Hospital Management System - Microservices Architecture

Hệ thống quản lý bệnh viện được thiết kế theo kiến trúc microservices với database-per-service pattern.

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx         │    │   RabbitMQ      │
│   (React/Vue)   │    │   API Gateway   │    │   Event Bus     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Auth Service  │    │   Patients      │    │   Appointments  │
│   (JWT, RBAC)  │    │   Service       │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prescriptions │    │   Payments      │    │   Notifications │
│   Service       │    │   Service       │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Các Services

| Service | Port | Database | Mô tả |
|---------|------|----------|-------|
| **Auth Service** | 8001 | `hospital_auth` | Xác thực, phân quyền, JWT |
| **Patients Service** | 8002 | `hospital_patients` | Quản lý bệnh nhân |
| **Appointments Service** | 8003 | `hospital_appointments` | Đặt lịch hẹn, lịch trình |
| **Prescriptions Service** | 8004 | `hospital_prescriptions` | Kê đơn, thuốc, cấp phát |
| **Payments Service** | 8005 | `hospital_payments` | Thanh toán, VNPAY |
| **Notifications Service** | 8006 | - | Thông báo, SMS, Email |

**📊 Database**: Sử dụng PostgreSQL local (không phải Docker containers)

## 🐳 Khởi động hệ thống

### 1. Cài đặt Docker và PostgreSQL

```bash
# Kiểm tra Docker
docker --version
docker compose version

# Kiểm tra PostgreSQL
brew services list | grep postgresql
psql --version
```

### 2. Tạo file .env

```bash
# Sử dụng script tự động
./create-env.sh

# Hoặc copy thủ công
cp env.example .env

# Chỉnh sửa các biến môi trường cần thiết
nano .env
```

### 3. Kiểm tra PostgreSQL

```bash
# Test kết nối databases
./test-db.sh
```

### 4. Khởi động toàn bộ hệ thống

```bash
# Build và khởi động
docker compose up -d --build

# Xem logs
docker compose logs -f

# Kiểm tra trạng thái
docker compose ps
```

### 5. Kiểm tra health

```bash
# Gateway health
curl http://localhost/health

# Service health
curl http://localhost:8001/health  # Auth
curl http://localhost:8002/health  # Patients
curl http://localhost:8003/health  # Appointments
curl http://localhost:8004/health  # Prescriptions
curl http://localhost:8005/health  # Payments
curl http://localhost:8006/health  # Notifications
```

## 🔧 Quản lý hệ thống

### Scripts tiện ích

```bash
# Tạo file .env
./create-env.sh

# Test database connections
./test-db.sh

# Khởi động hệ thống
./start.sh

# Dừng hệ thống
./stop.sh

# Kiểm tra health
./health-check.sh
```

**Lưu ý**: Đảm bảo scripts có quyền thực thi: `chmod +x *.sh`

### Khởi động lại service cụ thể

```bash
# Khởi động lại auth service
docker compose restart auth-service

# Khởi động lại database
docker compose restart auth-db
```

### Xem logs service cụ thể

```bash
# Xem logs auth service
docker compose logs -f auth-service

# Xem logs database
docker compose logs -f auth-db
```

### Dừng hệ thống

```bash
# Dừng tất cả services
docker compose down

# Dừng và xóa volumes (cẩn thận!)
docker compose down -v
```

## 📊 Monitoring

### RabbitMQ Management

```bash
# Truy cập RabbitMQ Management UI
open http://localhost:15672
# Username: guest, Password: guest
```

### Database connections

```bash
# Kết nối database auth
docker compose exec auth-db psql -U postgres -d hospital_auth

# Kết nối database patients
docker compose exec patients-db psql -U postgres -d hospital_patients
```

## 🚨 Troubleshooting

### Service không khởi động

```bash
# Kiểm tra logs
docker compose logs service-name

# Kiểm tra health check
docker compose ps

# Restart service
docker compose restart service-name
```

### Database connection issues

```bash
# Kiểm tra database status
docker compose exec db-name pg_isready -U postgres

# Restart database
docker compose restart db-name
```

### Port conflicts

```bash
# Kiểm tra ports đang sử dụng
lsof -i :8001
lsof -i :8002
# ...

# Thay đổi ports trong docker-compose.yml nếu cần
```

## 📁 Cấu trúc thư mục

```
hospital-microservices/
├── docker-compose.yml          # Cấu hình Docker Compose
├── env.example                # Biến môi trường mẫu
├── nginx/                     # Nginx API Gateway
│   └── nginx.conf
├── auth-service/              # Auth Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── patients-service/           # Patients Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── appointments-service/        # Appointments Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── prescriptions-service/       # Prescriptions Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── payments-service/            # Payments Service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
└── notifications-service/       # Notifications Service
    ├── Dockerfile
    ├── requirements.txt
    └── manage.py
```

## 🔐 Bảo mật

- **JWT Authentication**: Tất cả API calls cần Bearer token
- **Rate Limiting**: Nginx gateway giới hạn 10r/s cho API, 5r/s cho auth/payments
- **Internal Network**: Services chỉ giao tiếp qua Docker network nội bộ
- **Health Checks**: Tất cả services có health check endpoint

## 📝 Ghi chú

- **Bước 1**: ✅ Hạ tầng microservices (hiện tại)
- **Bước 2**: 🔄 Tách code business logic
- **Bước 3**: ⏳ Testing và monitoring

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Tạo Pull Request

## 📞 Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Docker logs
2. Health check endpoints
3. Network connectivity
4. Environment variables
