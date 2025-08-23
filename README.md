# 🏥 Hospital Management System

Hệ thống quản lý bệnh viện hiện đại được xây dựng bằng Django REST Framework với kiến trúc Modular Monolith.

## 🚀 Quick Start

### Cài đặt nhanh (Recommended)
```bash
git clone <your-repo>
cd hospital-management-system
python scripts/quick_start.py
```

### Chạy development server
```bash
python start_dev.py
```

Truy cập: http://localhost:8000

## 📋 Yêu cầu hệ thống

### 🪟 Windows
- Python 3.8+ từ [python.org](https://python.org) hoặc Microsoft Store
- Git từ [git-scm.com](https://git-scm.com)

### 🍎 macOS  
- Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- Python: `brew install python@3.11`
- Git: `brew install git`

### 🐧 Linux (Ubuntu/Debian)
- Python: `sudo apt install python3.11 python3.11-venv`
- Git: `sudo apt install git`

## 📁 Cấu trúc project

```
hospital-management-system/
├── apps/                    # Django applications (modules)
│   ├── users/              # Quản lý người dùng
│   ├── patients/           # Quản lý bệnh nhân  
│   ├── appointments/       # Đặt lịch khám
│   ├── prescriptions/      # Đơn thuốc
│   ├── payments/           # Thanh toán & BHYT
│   ├── testing/            # Xét nghiệm & chẩn đoán hình ảnh
│   ├── notifications/      # SMS/Email thông báo
│   └── reports/           # Báo cáo & phân tích
├── config/                 # Django settings
├── shared/                 # Utilities dùng chung
├── scripts/                # Setup scripts
└── requirements/           # Dependencies
```

## 🔧 Lệnh thường dùng

```bash
# Setup môi trường
python scripts/setup_cross_platform.py

# Chạy server
python start_dev.py

# Django commands (sau khi activate venv)
python manage.py migrate
python manage.py createsuperuser  
python manage.py makemigrations

# Test
pytest
```

## 📚 Documentation

- **Setup chi tiết**: `hospital_modular_monolith_setup.md`
- **API Documentation**: 
  - **Swagger UI**: http://localhost:8000/api/docs/
  - **ReDoc**: http://localhost:8000/redoc/
  - **OpenAPI Schema**: http://localhost:8000/api/schema/
- **Admin Panel**: http://localhost:8000/admin/

## 🛠️ Tech Stack

- **Backend**: Django 4.2+ với REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)  
- **Cache**: Redis
- **Task Queue**: Celery
- **API Docs**: Swagger/OpenAPI
- **Testing**: Pytest
- **Code Quality**: Black, flake8, isort

## 🎯 Features

- ✅ Quản lý bệnh nhân và hồ sơ y tế
- ✅ Đặt lịch khám và quản lý lịch trình
- ✅ Kê đơn thuốc điện tử  
- ✅ Tích hợp thanh toán và BHYT
- ✅ Quản lý xét nghiệm và chẩn đoán hình ảnh
- ✅ Hệ thống thông báo SMS/Email
- ✅ Báo cáo và phân tích dữ liệu
- ✅ RESTful API với documentation
- ✅ Cross-platform support (Windows/macOS/Linux)

## 👥 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`  
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

Nếu gặp vấn đề:
1. Kiểm tra `hospital_modular_monolith_setup.md` cho hướng dẫn chi tiết
2. Chạy `python scripts/quick_start.py` để setup tự động
3. Tạo issue trên GitHub với thông tin lỗi cụ thể

---

Made with ❤️ for Vietnamese Healthcare System
