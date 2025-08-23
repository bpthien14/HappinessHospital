# Hospital Management System - Modular Monolith Setup Guide

## 🚀 Quick Start Guide for Modular Monolith (Cross-Platform)

### Prerequisites Setup 

#### 🍎 MacOS Setup

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python 3.11
brew install python@3.11

# 3. Install PostgreSQL (optional - can use SQLite for development)
brew install postgresql@15
brew services start postgresql@15

# 4. Install Redis
brew install redis
brew services start redis

# 5. Install Git (if not installed)
brew install git

# 6. Verify installations
python3.11 --version
psql --version
redis-server --version
```

#### 🪟 Windows Setup

```powershell
# 1. Install Python 3.11 from Microsoft Store or python.org
# Tải từ: https://www.python.org/downloads/windows/

# 2. Install Git
# Tải từ: https://git-scm.com/download/win

# 3. Install PostgreSQL (optional)
# Tải từ: https://www.postgresql.org/download/windows/

# 4. Install Redis (Windows Subsystem for Linux hoặc Redis on Windows)
# WSL: wsl --install
# Hoặc dùng Memurai: https://www.memurai.com/

# 5. Verify installations
python --version
git --version
psql --version  # nếu cài PostgreSQL
```

#### 🐧 Linux (Ubuntu/Debian) Setup

```bash
# 1. Update package lists
sudo apt update

# 2. Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# 3. Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib

# 4. Install Redis
sudo apt install redis-server

# 5. Install Git
sudo apt install git

# 6. Verify installations
python3.11 --version
psql --version
redis-server --version
```

## 📁 Project Structure Setup (Cross-Platform)

### 🍎 MacOS/Linux Setup

```bash
# Create main project directory
mkdir hospital-management-system
cd hospital-management-system

# Initialize git repository
git init
echo "# Hospital Management System" > README.md

# Create project structure
mkdir -p apps/{users,patients,appointments,prescriptions,payments,testing,notifications,reports}
mkdir -p config
mkdir -p shared/{utils,middlewares,permissions,exceptions}
mkdir -p static/{css,js,img}
mkdir -p templates/{base,auth,patients,appointments,prescriptions}
mkdir -p media/{uploads,reports}
mkdir -p docs scripts tests requirements

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Create requirements files
touch requirements/base.txt requirements/development.txt requirements/production.txt
```

### 🪟 Windows Setup (PowerShell)

```powershell
# Create main project directory
New-Item -ItemType Directory -Name "hospital-management-system"
Set-Location "hospital-management-system"

# Initialize git repository
git init
echo "# Hospital Management System" > README.md

# Create project structure
$directories = @(
    "apps/users", "apps/patients", "apps/appointments", "apps/prescriptions",
    "apps/payments", "apps/testing", "apps/notifications", "apps/reports",
    "config", "shared/utils", "shared/middlewares", "shared/permissions", 
    "shared/exceptions", "static/css", "static/js", "static/img",
    "templates/base", "templates/auth", "templates/patients", 
    "templates/appointments", "templates/prescriptions",
    "media/uploads", "media/reports", "docs", "scripts", "tests", "requirements"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Force -Path $dir
}

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Create requirements files
New-Item -ItemType File -Path "requirements/base.txt"
New-Item -ItemType File -Path "requirements/development.txt"
New-Item -ItemType File -Path "requirements/production.txt"
```

## 📋 Project Structure Overview

```
hospital-management-system/
├── README.md
├── manage.py
├── requirements/
│   ├── base.txt           # Core dependencies
│   ├── development.txt    # Dev-only dependencies
│   └── production.txt     # Production dependencies
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py       # Common settings
│   │   ├── development.py # Dev settings
│   │   └── production.py  # Prod settings
│   ├── urls.py           # Main URL configuration
│   ├── wsgi.py
│   └── asgi.py
├── apps/                 # All Django apps (modules)
│   ├── users/           # User management & authentication
│   ├── patients/        # Patient management
│   ├── appointments/    # Appointment scheduling
│   ├── prescriptions/   # Prescription management
│   ├── payments/        # Payment & BHYT integration
│   ├── testing/         # Lab tests & imaging
│   ├── notifications/   # SMS/Email notifications
│   └── reports/         # Analytics & reporting
├── shared/              # Shared utilities across modules
│   ├── utils/
│   ├── middlewares/
│   ├── permissions/
│   └── exceptions/
├── static/              # Static files (CSS, JS, Images)
├── templates/           # HTML templates
├── media/               # Uploaded files
├── tests/               # Test files
├── scripts/             # Management scripts
├── docs/                # Documentation
└── .env.example         # Environment variables template
```

## 🔧 Dependencies Setup

### requirements/base.txt
```txt
# Core Django
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.1
django-filter==23.3
django-extensions==3.2.3

# Database
psycopg2-binary==2.9.7
redis==5.0.1
django-redis==5.4.0

# Authentication & Security
djangorestframework-simplejwt==5.3.0
django-cryptography==1.1
bcrypt==4.0.1

# File handling
Pillow==10.0.1
python-decouple==3.8

# API Documentation
drf-yasg==1.21.7

# Background tasks
celery==5.3.4
kombu==5.3.3

# Utilities
python-dateutil==2.8.2
phonenumbers==8.13.24
requests==2.31.0

# Validation
django-phonenumber-field==7.1.0
django-crispy-forms==2.1
crispy-bootstrap5==0.7
```

### requirements/development.txt
```txt
-r base.txt

# Development tools
django-debug-toolbar==4.2.0
ipython==8.16.1
jupyter==1.0.0

# Testing
pytest==7.4.2
pytest-django==4.5.2
pytest-cov==4.1.0
factory-boy==3.3.0
faker==19.12.0

# Code quality
black==23.9.1
flake8==6.1.0
isort==5.12.0
mypy==1.6.1

# Database tools
django-seed==0.3.1
```

### requirements/production.txt
```txt
-r base.txt

# Production server
gunicorn==21.2.0
whitenoise==6.6.0

# Monitoring
sentry-sdk[django]==1.38.0

# Performance
django-cachalot==2.6.1
```

## ⚙️ Configuration Setup

### config/settings/base.py
```python
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='your-secret-key-here')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_yasg',
    'phonenumber_field',
    'crispy_forms',
    'crispy_bootstrap5',
]

LOCAL_APPS = [
    'apps.users',
    'apps.patients',
    'apps.appointments',
    'apps.prescriptions',
    'apps.payments',
    'apps.testing',
    'apps.notifications',
    'apps.reports',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'shared.middlewares.audit_middleware.AuditMiddleware',
    'shared.middlewares.rate_limit_middleware.RateLimitMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='hospital_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Redis Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Ho_Chi_Minh'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}

# JWT Configuration
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Encryption Key for sensitive data
ENCRYPTION_KEY = config('ENCRYPTION_KEY', default='your-encryption-key-here')

# Email Configuration (for notifications)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# SMS Configuration (for Vietnam)
SMS_API_KEY = config('SMS_API_KEY', default='')
SMS_API_URL = config('SMS_API_URL', default='')

# BHYT Integration
BHYT_API_URL = config('BHYT_API_URL', default='')
BHYT_API_KEY = config('BHYT_API_KEY', default='')
```

### config/settings/development.py
```python
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Add debug toolbar for development
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    # Debug Toolbar settings
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]

# Database for development - can use SQLite for quick setup
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hospital_dev_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable HTTPS requirements in development
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None

# Development-specific logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
```

### config/settings/production.py
```python
from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    config('DOMAIN_NAME', default='localhost'),
    config('SERVER_IP', default='127.0.0.1'),
]

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files settings for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Production database with connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 60

# Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### .env.example
```bash
# Django Configuration
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=hospital_dev_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Security
ENCRYPTION_KEY=your-fernet-encryption-key-here

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# SMS Configuration (Vietnam)
SMS_API_KEY=your-sms-api-key
SMS_API_URL=https://api.sms-provider.com

# BHYT Integration
BHYT_API_URL=https://bhyt-api.gov.vn
BHYT_API_KEY=your-bhyt-api-key

# Production Settings
DOMAIN_NAME=yourdomain.com
SERVER_IP=your-server-ip
SENTRY_DSN=your-sentry-dsn
```

## 🗄️ Database Setup

```bash
# Create PostgreSQL database
createdb hospital_dev_db

# Or using psql
psql postgres
CREATE DATABASE hospital_dev_db;
CREATE USER hospital_user WITH PASSWORD 'hospital_pass';
GRANT ALL PRIVILEGES ON DATABASE hospital_dev_db TO hospital_user;
\q
```

## 📦 Installation Script

### Cross-Platform Setup Scripts

#### 🚀 Quick Start (Recommended)
```bash
# Run từ project root directory
python scripts/quick_start.py
```

#### 🔧 Manual Setup (Cross-Platform)
```bash
# Run cross-platform setup script
python scripts/setup_cross_platform.py
```

#### 🍎 macOS/Linux Setup Script
```bash
#!/bin/bash

echo "🏥 Setting up Hospital Management System..."

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements/development.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "📋 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configurations"
fi

# Create logs directory
mkdir -p logs

# Run initial migrations
echo "🗄️ Setting up database..."
python manage.py migrate

# Create superuser (optional)
echo "👤 Creating superuser..."
python manage.py createsuperuser

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Setup completed! Run 'python manage.py runserver' to start development server"
```

#### 🪟 Windows Setup Script (PowerShell)
```powershell
Write-Host "🏥 Setting up Hospital Management System..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements/development.txt

# Copy environment file
if (-not (Test-Path ".env")) {
    Write-Host "📋 Creating environment file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️ Please update .env file with your configurations" -ForegroundColor Yellow
}

# Create logs directory
New-Item -ItemType Directory -Force -Path "logs"

# Run initial migrations
Write-Host "🗄️ Setting up database..." -ForegroundColor Yellow
python manage.py migrate

# Create superuser (optional)
Write-Host "👤 Creating superuser..." -ForegroundColor Yellow
python manage.py createsuperuser

# Collect static files
Write-Host "📁 Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput

Write-Host "✅ Setup completed! Run 'python manage.py runserver' to start development server" -ForegroundColor Green
```

### Cross-Platform Start Scripts

#### 🐍 Python Start Script (Recommended - Cross-Platform)
```python
# start_dev.py - Generated by setup script
python start_dev.py
```

#### 🍎 macOS/Linux Start Script
```bash
#!/bin/bash

echo "🚀 Starting Hospital Management System in development mode..."

# Activate virtual environment
source venv/bin/activate

# Start Redis server (if installed)
if command -v redis-server &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis
    else
        sudo systemctl start redis-server
    fi
fi

# Start PostgreSQL (if installed and configured)
if command -v psql &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql@15
    else
        sudo systemctl start postgresql
    fi
fi

# Run Django development server
python manage.py runserver 0.0.0.0:8000
```

#### 🪟 Windows Start Script (Batch)
```batch
@echo off
echo 🚀 Starting Hospital Management System in development mode...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start Redis server (if installed)
net start Redis > nul 2>&1

REM Run Django development server
python manage.py runserver 0.0.0.0:8000
pause
```

## 🛠️ Initial Django Setup Commands

```bash
# Navigate to project directory
cd hospital-management-system

# Create virtual environment and activate it
python3.11 -m venv venv
source venv/bin/activate

# Install Django and create project
pip install Django==4.2.7
django-admin startproject config .

# Install all dependencies
pip install -r requirements/development.txt

# Create all Django apps
python manage.py startapp users apps/users
python manage.py startapp patients apps/patients
python manage.py startapp appointments apps/appointments
python manage.py startapp prescriptions apps/prescriptions
python manage.py startapp payments apps/payments
python manage.py startapp testing apps/testing
python manage.py startapp notifications apps/notifications
python manage.py startapp reports apps/reports

# Create shared utilities
mkdir -p shared/{utils,middlewares,permissions,exceptions}
touch shared/__init__.py
touch shared/utils/__init__.py
touch shared/middlewares/__init__.py
touch shared/permissions/__init__.py
touch shared/exceptions/__init__.py

# Make setup script executable
chmod +x scripts/setup.sh
chmod +x scripts/start_dev.sh

# Run setup
./scripts/setup.sh
```

## 🔧 Cursor Editor Configuration

### .vscode/settings.json (for Cursor)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.sortImports.args": ["--profile", "black"],
    "[python]": {
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "files.associations": {
        "*.html": "html"
    },
    "emmet.includeLanguages": {
        "django-html": "html"
    },
    "django.templatesDir": ["templates"],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/migrations/*.py": false,
        "**/migrations/__pycache__": true
    }
}
```

### .vscode/launch.json
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Django",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "runserver",
                "0.0.0.0:8000"
            ],
            "django": true,
            "justMyCode": true,
            "env": {
                "DJANGO_SETTINGS_MODULE": "config.settings.development"
            }
        },
        {
            "name": "Django Shell",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "shell"
            ],
            "django": true,
            "justMyCode": true
        }
    ]
}
```

## 🧪 Testing Setup

### pytest.ini
```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
python_classes = Test* *Tests
python_functions = test_*
addopts = 
    --tb=short
    --strict-markers
    --strict-config
    --cov=apps
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
testpaths = tests
```

## 📚 Quick Start Commands (Cross-Platform)

### 🚀 Super Quick Start
```bash
# 1. Clone and setup (one command)
git clone <your-repo>
cd hospital-management-system
python scripts/quick_start.py
```

### 🔧 Manual Commands

#### Setup và Installation
```bash
# Windows
python scripts/setup_cross_platform.py

# macOS/Linux  
python3 scripts/setup_cross_platform.py
```

#### Development Server
```bash
# Cross-platform (recommended)
python start_dev.py

# Platform-specific
# Windows: start_dev.bat
# macOS/Linux: ./start_dev.sh
```

#### Django Management Commands
```bash
# Activate virtual environment first
# Windows: venv\Scripts\activate.bat
# macOS/Linux: source venv/bin/activate

# Create migrations
python manage.py makemigrations

# Apply migrations  
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
pytest

# Django shell
python manage.py shell
```

#### Access Points
- **Website**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/docs/
- **API Root**: http://localhost:8000/api/v1/

## 🎯 Next Steps After Setup

1. **Initialize git repository** và commit initial setup
2. **Configure database** và test connections
3. **Implement User model** trong apps/users/
4. **Create basic authentication** endpoints
5. **Implement Patient model** trong apps/patients/
6. **Add basic CRUD operations** cho Patient
7. **Test với Postman/Insomnia** hoặc DRF browsable API

Bạn ready để bắt đầu implement chưa? Tôi có thể guide bạn từng bước tiếp theo! 🚀