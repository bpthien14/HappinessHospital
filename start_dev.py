#!/usr/bin/env python3
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
        subprocess.run([str(venv_python), str(manage_py), "runserver", "127.0.0.1:8000"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")

if __name__ == "__main__":
    main()
