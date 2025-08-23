#!/usr/bin/env python3
"""
Cross-platform Hospital Management System Setup Script
Supports Windows, macOS, and Linux
"""
import os
import sys
import subprocess
import platform
import venv
from pathlib import Path


class CrossPlatformHospitalSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / "venv"

        # Platform-specific configurations
        self.configs = {
            "windows": {
                "python_cmd": "python",
                "pip_cmd": "pip",
                "venv_activate": "venv\\Scripts\\activate.bat",
                "venv_python": "venv\\Scripts\\python.exe",
                "shell": True,
                "path_sep": "\\",
            },
            "darwin": {  # MacOS
                "python_cmd": "python3.11",
                "pip_cmd": "pip3",
                "venv_activate": "venv/bin/activate",
                "venv_python": "venv/bin/python",
                "shell": True,
                "path_sep": "/",
            },
            "linux": {
                "python_cmd": "python3.11",
                "pip_cmd": "pip3",
                "venv_activate": "venv/bin/activate",
                "venv_python": "venv/bin/python",
                "shell": True,
                "path_sep": "/",
            },
        }

        self.config = self.configs.get(self.system, self.configs["linux"])

    def log(self, message, level="INFO"):
        """Cross-platform logging"""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "STEP": "🔧",
        }
        print(f"{symbols.get(level, 'ℹ️')} {message}")

    def run_command(self, command, cwd=None, shell=None):
        """Run command with cross-platform support"""
        if shell is None:
            shell = self.config["shell"]

        try:
            if isinstance(command, list):
                cmd = command
            else:
                cmd = command if shell else command.split()

            result = subprocess.run(
                cmd,
                shell=shell,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root,
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {command}", "ERROR")
            self.log(f"Error: {e.stderr}", "ERROR")
            return None
        except FileNotFoundError as e:
            self.log(f"Command not found: {command}", "ERROR")
            self.log(f"Error: {e}", "ERROR")
            return None

    def detect_python(self):
        """Detect available Python version"""
        self.log("Detecting Python installation...")

        python_commands = ["python3.11", "python3", "python"]
        if self.system == "windows":
            python_commands = ["python", "python3", "py"]

        for cmd in python_commands:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    shell=self.system == "windows",
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    self.log(f"Found: {version}")
                    # Check if it's Python 3.8+
                    if "Python 3." in version:
                        version_parts = version.split("Python ")[1].split(".")
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        if major == 3 and minor >= 8:
                            self.config["python_cmd"] = cmd
                            return True
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

        self.log("Python 3.8+ not found! Please install Python 3.8 or higher", "ERROR")
        self.show_python_install_instructions()
        return False

    def show_python_install_instructions(self):
        """Show platform-specific Python installation instructions"""
        instructions = {
            "windows": [
                "🪟 Windows Python Installation:",
                "1. Tải Python từ: https://www.python.org/downloads/windows/",
                "2. Hoặc cài từ Microsoft Store: 'python'",
                "3. Kiểm tra: python --version",
            ],
            "darwin": [
                "🍎 MacOS Python Installation:",
                '1. Cài Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"',
                "2. Cài Python: brew install python@3.11",
                "3. Kiểm tra: python3.11 --version",
            ],
            "linux": [
                "🐧 Linux Python Installation:",
                "Ubuntu/Debian: sudo apt install python3.11 python3.11-venv",
                "CentOS/RHEL: sudo yum install python3.11",
                "Kiểm tra: python3.11 --version",
            ],
        }

        for instruction in instructions.get(self.system, instructions["linux"]):
            self.log(instruction, "INFO")

    def create_virtual_environment(self):
        """Create virtual environment"""
        self.log("Creating virtual environment...")

        if self.venv_path.exists():
            self.log("Virtual environment already exists")
            return True

        try:
            # Use the detected Python command
            result = self.run_command(
                [self.config["python_cmd"], "-m", "venv", str(self.venv_path)]
            )
            if result is not None:
                self.log("Virtual environment created successfully", "SUCCESS")
                return True
            else:
                return False
        except Exception as e:
            self.log(f"Failed to create virtual environment: {e}", "ERROR")
            return False

    def get_venv_python(self):
        """Get virtual environment Python path"""
        if self.system == "windows":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"

    def get_venv_pip(self):
        """Get virtual environment pip path"""
        if self.system == "windows":
            return self.venv_path / "Scripts" / "pip.exe"
        else:
            return self.venv_path / "bin" / "pip"

    def install_dependencies(self):
        """Install Python dependencies"""
        self.log("Installing dependencies...")

        venv_pip = self.get_venv_pip()

        # Check for requirements files
        req_files = [
            self.project_root / "requirements" / "development.txt",
            self.project_root / "requirements" / "base.txt",
            self.project_root / "requirements.txt",
        ]

        requirements_file = None
        for req_file in req_files:
            if req_file.exists():
                requirements_file = req_file
                break

        if not requirements_file:
            self.log("No requirements file found. Creating basic one...", "WARNING")
            self.create_basic_requirements()
            requirements_file = self.project_root / "requirements" / "development.txt"

        command = [str(venv_pip), "install", "-r", str(requirements_file)]
        result = self.run_command(command)

        if result is not None:
            self.log("Dependencies installed successfully", "SUCCESS")
            return True
        else:
            self.log("Failed to install dependencies", "ERROR")
            return False

    def create_basic_requirements(self):
        """Create basic requirements.txt if none exists"""
        requirements_dir = self.project_root / "requirements"
        requirements_dir.mkdir(exist_ok=True)

        basic_requirements = """# Core Django
Django>=4.2.0,<5.0.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0

# Database
psycopg2-binary>=2.9.0
django-extensions>=3.2.0

# Development tools
python-dotenv>=1.0.0
django-debug-toolbar>=4.0.0

# Utilities
Pillow>=10.0.0
"""

        dev_requirements_file = requirements_dir / "development.txt"
        with open(dev_requirements_file, "w", encoding="utf-8") as f:
            f.write(basic_requirements)

        self.log("Created basic requirements/development.txt", "SUCCESS")

    def create_directories(self):
        """Create necessary project directories"""
        self.log("Creating project directories...")

        directories = [
            "logs",
            "media/uploads",
            "media/reports",
            "staticfiles",
            "templates/base",
            "static/css",
            "static/js",
            "static/img",
        ]

        try:
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.log(f"Created directory: {directory}")

            self.log("Directories created", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to create directories: {e}", "ERROR")
            return False

    def setup_environment_file(self):
        """Setup environment file"""
        self.log("Setting up environment file...")

        env_file = self.project_root / ".env"
        if env_file.exists():
            self.log("Environment file already exists")
            return True

        env_content = """# Django Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (SQLite for development)
DB_NAME=db.sqlite3
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# PostgreSQL Configuration (uncomment if using PostgreSQL)
# DB_NAME=hospital_dev_db
# DB_USER=postgres
# DB_PASSWORD=postgres
# DB_HOST=localhost
# DB_PORT=5432

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
"""

        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            self.log("Environment file created", "SUCCESS")
            self.log("⚠️ Please update .env file with your configurations", "WARNING")
            return True
        except Exception as e:
            self.log(f"Failed to create environment file: {e}", "ERROR")
            return False

    def setup_django_project(self):
        """Setup Django project if not exists"""
        self.log("Setting up Django project...")

        manage_py = self.project_root / "manage.py"
        if manage_py.exists():
            self.log("Django project already exists")
            return True

        venv_python = self.get_venv_python()

        # Create Django project
        command = [str(venv_python), "-m", "django", "startproject", "config", "."]
        result = self.run_command(command)

        if result is not None:
            self.log("Django project created", "SUCCESS")
            return True
        else:
            self.log("Failed to create Django project", "ERROR")
            return False

    def run_django_commands(self):
        """Run initial Django commands"""
        self.log("Running Django setup commands...")

        venv_python = self.get_venv_python()
        manage_py = self.project_root / "manage.py"

        if not manage_py.exists():
            self.log("manage.py not found, skipping Django commands", "WARNING")
            return True

        # Skip Django commands for now to avoid hanging
        self.log("Skipping Django commands to avoid configuration issues", "WARNING")
        self.log("You can run Django commands manually after setup:", "INFO")
        self.log("  python manage.py migrate", "INFO")
        self.log("  python manage.py collectstatic", "INFO")

        return True

    def create_startup_scripts(self):
        """Create platform-specific startup scripts"""
        self.log("Creating startup scripts...")

        # Unix shell script
        if self.system in ["darwin", "linux"]:
            script_content = """#!/bin/bash
echo "🚀 Starting Hospital Management System..."
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
"""
            script_path = self.project_root / "start_dev.sh"
            with open(script_path, "w") as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)

        # Windows batch script
        if self.system == "windows":
            script_content = """@echo off
echo 🚀 Starting Hospital Management System...
call venv\\Scripts\\activate.bat
python manage.py runserver 0.0.0.0:8000
pause
"""
            script_path = self.project_root / "start_dev.bat"
            with open(script_path, "w") as f:
                f.write(script_content)

        # Python script (cross-platform)
        python_script = """#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / ("Scripts" if os.name == 'nt' else "bin") / ("python.exe" if os.name == 'nt' else "python")
    manage_py = project_root / "manage.py"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run setup first.")
        sys.exit(1)
    
    if not manage_py.exists():
        print("❌ Django project not found. Please complete setup first.")
        sys.exit(1)
    
    print("🚀 Starting Hospital Management System...")
    print("📍 Server will be available at: http://localhost:8000")
    print("⏹️ Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run([str(venv_python), str(manage_py), "runserver", "0.0.0.0:8000"])
    except KeyboardInterrupt:
        print("\\n👋 Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
"""

        script_path = self.project_root / "start_dev.py"
        with open(script_path, "w") as f:
            f.write(python_script)

        self.log("Startup scripts created", "SUCCESS")
        return True

    def run_setup(self):
        """Main setup process"""
        self.log("🏥 Starting Hospital Management System Setup...", "STEP")
        self.log(f"Platform detected: {platform.system()} {platform.release()}", "INFO")

        steps = [
            ("Detecting Python", self.detect_python),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Setting up environment file", self.setup_environment_file),
            ("Setting up Django project", self.setup_django_project),
            ("Running Django commands", self.run_django_commands),
            ("Creating startup scripts", self.create_startup_scripts),
        ]

        for step_name, step_function in steps:
            self.log(f"Step: {step_name}", "STEP")
            if not step_function():
                self.log(f"Setup failed at: {step_name}", "ERROR")
                return False

        self.log("🎉 Setup completed successfully!", "SUCCESS")
        self.show_next_steps()
        return True

    def show_next_steps(self):
        """Show next steps after setup"""
        self.log("Next steps:", "INFO")
        self.log("1. Update .env file with your configurations", "INFO")

        if self.system == "windows":
            self.log("2. Run: python start_dev.py or start_dev.bat", "INFO")
        else:
            self.log("2. Run: python start_dev.py or ./start_dev.sh", "INFO")

        self.log("3. Open: http://localhost:8000", "INFO")
        self.log(
            "4. For admin access, create superuser: python manage.py createsuperuser",
            "INFO",
        )


if __name__ == "__main__":
    setup = CrossPlatformHospitalSetup()
    success = setup.run_setup()
    sys.exit(0 if success else 1)
