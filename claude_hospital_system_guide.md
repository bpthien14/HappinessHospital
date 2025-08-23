# Claude.md - Hướng dẫn Hỗ trợ Thiết kế Hệ thống Quản lý Bệnh viện

## 🎯 Mục tiêu Hỗ trợ

Claude sẽ hỗ trợ bạn thiết kế và xây dựng **Hệ thống Quản lý Bệnh viện ABC** theo kiến trúc Microservices với đầy đủ các chức năng quản lý bệnh nhân, lịch khám, đơn thuốc, thanh toán BHYT và thông báo.

## 📋 Thông tin Dự án Đã Phân tích

### Actors (Tác nhân)
- **Bệnh nhân**: Đăng ký khám, xem thông tin cá nhân, lãnh thuốc
- **Bác sĩ**: Khám lâm sàng, chỉ định xét nghiệm, kê đơn thuốc
- **Nhân viên tiếp đón**: Đăng ký khám bệnh, kiểm tra thẻ BHYT
- **Dược sĩ**: Soạn thuốc, cập nhật trạng thái đơn thuốc
- **Kỹ thuật viên**: Thực hiện xét nghiệm, cập nhật kết quả
- **Quản trị viên**: Quản lý hệ thống, xem báo cáo
- **Hệ thống BHXH**: Xác thực thẻ BHYT (external system)

### Use Cases Chính
1. **Đăng ký khám bệnh** (include: Kiểm tra thẻ BHYT)
2. **Khám lâm sàng** (include: Quản lý hồ sơ bệnh nhân)
3. **Chỉ định xét nghiệm** (extend: Khám lâm sàng)
4. **Thực hiện xét nghiệm** (extend: Chỉ định xét nghiệm)
5. **Tạo đơn thuốc**
6. **Lãnh thuốc**
7. **Quản lý hồ sơ bệnh nhân**

### Luồng Nghiệp vụ Chính (Từ Flowcharts)
1. **Tiếp đón & Đăng ký**: Lấy số → Kiểm tra hồ sơ → Kiểm tra BHYT → Đăng ký lịch khám
2. **Khám lâm sàng**: Nhận phiếu → Tra cứu hồ sơ → Khám bệnh → Quyết định CLS/Kê đơn
3. **Xét nghiệm**: Đến phòng XN → Nộp phiếu → Thực hiện → Cập nhật kết quả → Trả kết quả
4. **Lãnh thuốc**: Nhập đơn → Ký duyệt → Đến nhà thuốc → Soạn thuốc → Ký nhận → Cập nhật BHYT

## 🏗️ Kiến trúc Microservices Đề xuất

### Core Services
1. **Patient Service** - Quản lý thông tin bệnh nhân, hồ sơ bệnh án
2. **Appointment Service** - Quản lý lịch khám, phân bổ bác sĩ
3. **Prescription Service** - Quản lý đơn thuốc, trạng thái cấp phát
4. **Payment Service** - Xử lý thanh toán, tính toán BHYT/dịch vụ
5. **Notification Service** - Gửi thông báo SMS/Email
6. **Testing Service** - Quản lý xét nghiệm CLS, kết quả
7. **Report Service** - Báo cáo, thống kê

### Support Services
- **User Management Service** - Xác thực, phân quyền
- **BHYT Integration Service** - Kết nối với hệ thống BHXH
- **API Gateway** - Điểm vào duy nhất, routing, security
- **Configuration Service** - Quản lý cấu hình tập trung

### Infrastructure Services
- **Message Broker** (RabbitMQ) - Giao tiếp bất đồng bộ
- **Service Discovery** - Tự động phát hiện services
- **Monitoring & Logging** - Giám sát hiệu năng, log tập trung

## 🛠️ Stack Công nghệ Đề xuất

### Frontend (Website)
- **Backend**: PHP/Python với framework (Laravel/Django)
- **Architecture**: MVC pattern
- **Database**: MySQL/PostgreSQL cho dữ liệu quan hệ

### Microservices
- **API Framework**: Java Spring Boot / Node.js / .NET Core
- **Database**: 
  - MySQL/PostgreSQL: Patient, Appointment, Prescription
  - MongoDB: Logs, Notifications, Reports
- **Message Queue**: RabbitMQ
- **API Communication**: REST API (synchronous)
- **Cache**: Redis
- **Container**: Docker + Kubernetes

## 📊 Yêu cầu Phi chức năng

### Performance
- Xử lý tối thiểu 100 requests/second
- API response time < 1 second
- 99.9% uptime

### Security
- JWT authentication & role-based authorization
- Mã hóa dữ liệu nhạy cảm (AES-256)
- HTTPS cho tất cả communications
- Input validation & SQL injection protection

### Scalability
- Horizontal scaling cho từng service
- Independent deployment
- Circuit breaker pattern
- Auto-scaling based on load

## 🎯 Hỗ trợ Claude Có thể Cung cấp

### 1. Thiết kế Kiến trúc
- ✅ **Detailed Architecture Diagram**: Vẽ sơ đồ chi tiết các services và mối quan hệ
- ✅ **Database Schema Design**: Thiết kế schema cho từng service
- ✅ **API Design**: Định nghĩa REST APIs, request/response models
- ✅ **Message Flow Design**: Thiết kế async messaging với RabbitMQ

### 2. Kế hoạch Implementation
- ✅ **Project Roadmap**: Lịch trình phát triển theo phases
- ✅ **Sprint Planning**: Chia nhỏ features theo sprint 2-3 tuần
- ✅ **Priority Matrix**: Xác định thứ tự ưu tiên features
- ✅ **Risk Assessment**: Đánh giá rủi ro và mitigation plans

### 3. Code & Documentation
- ✅ **Boilerplate Code**: Tạo template cho services
- ✅ **Configuration Files**: Docker, Kubernetes, RabbitMQ configs
- ✅ **API Documentation**: OpenAPI/Swagger specifications
- ✅ **Deployment Scripts**: CI/CD pipeline scripts

### 4. Testing Strategy
- ✅ **Unit Test Templates**: Test cases cho business logic
- ✅ **Integration Test Scenarios**: Test inter-service communication
- ✅ **Load Testing Plans**: Performance testing strategies
- ✅ **Security Testing**: Vulnerability assessment checklist

### 5. Monitoring & Operations
- ✅ **Logging Strategy**: Structured logging cho microservices
- ✅ **Monitoring Setup**: Metrics, alerts, dashboards
- ✅ **Troubleshooting Guides**: Common issues và solutions
- ✅ **Backup & Recovery Plans**: Data protection strategies

## 📝 Cách Tương tác Hiệu quả với Claude

### Khi cần Thiết kế
```
"Claude, hãy thiết kế API cho Patient Service với các endpoints CRUD và search functionality"
```

### Khi cần Code
```
"Claude, tạo Spring Boot controller cho Appointment Service với validation và error handling"
```

### Khi cần Planning
```
"Claude, lập kế hoạch 3 tháng để implement core services theo thứ tự ưu tiên"
```

### Khi cần Troubleshooting
```
"Claude, đề xuất cách handle khi Payment Service bị down mà vẫn cho phép bệnh nhân khám"
```

## 🔄 Workflow Hỗ trợ

1. **Requirements Analysis** → Phân tích chi tiết requirements
2. **Architecture Design** → Thiết kế tổng thể và chi tiết
3. **Planning & Prioritization** → Lập kế hoạch implementation
4. **Implementation Support** → Hỗ trợ coding, testing
5. **Deployment & Operations** → Hỗ trợ deploy và vận hành

## 📞 Sẵn sàng Hỗ trợ

Claude đã sẵn sàng hỗ trợ bạn ở bất kỳ giai đoạn nào của dự án. Hãy cho tôi biết bạn muốn bắt đầu từ đâu:

- 🏗️ **Thiết kế chi tiết kiến trúc microservices?**
- 📋 **Lập kế hoạch implementation roadmap?**
- 💻 **Bắt đầu code một service cụ thể?**
- 📊 **Thiết kế database schemas?**
- 🔄 **Cấu hình message queues và APIs?**

**Chỉ cần nói: "Claude, tôi muốn [mục tiêu cụ thể]" và tôi sẽ hỗ trợ bạn ngay!**