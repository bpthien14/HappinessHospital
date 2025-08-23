#!/usr/bin/env python3
"""
Quick Start Script for Hospital Management System
Automatically detects environment and runs appropriate setup
"""
import os
import sys
import platform
from pathlib import Path


def main():
    print("🏥 Hospital Management System - Quick Start")
    print("=" * 50)

    # Detect platform
    system = platform.system()
    print(f"📱 Platform: {system} {platform.release()}")

    # Check if we're in the project directory
    current_dir = Path.cwd()
    setup_script = current_dir / "scripts" / "setup_cross_platform.py"

    if not setup_script.exists():
        print("❌ Please run this script from the project root directory")
        print("💡 Make sure you're in the hospital-management-system folder")
        sys.exit(1)

    # Show platform-specific instructions
    print("\n🔧 Prerequisites Check:")

    if system == "Windows":
        print("🪟 Windows detected")
        print("Required:")
        print("  - Python 3.8+ (python.org or Microsoft Store)")
        print("  - Git (git-scm.com)")
        print("Optional:")
        print("  - PostgreSQL (postgresql.org)")
        print("  - Redis (WSL or Memurai)")

    elif system == "Darwin":  # macOS
        print("🍎 macOS detected")
        print("Required:")
        print("  - Homebrew (brew.sh)")
        print("  - Python 3.8+ (brew install python@3.11)")
        print("  - Git (brew install git)")
        print("Optional:")
        print("  - PostgreSQL (brew install postgresql@15)")
        print("  - Redis (brew install redis)")

    elif system == "Linux":
        print("🐧 Linux detected")
        print("Required:")
        print("  - Python 3.8+ (apt install python3.11)")
        print("  - Git (apt install git)")
        print("Optional:")
        print("  - PostgreSQL (apt install postgresql)")
        print("  - Redis (apt install redis-server)")

    print("\n" + "=" * 50)

    # Ask user if they want to proceed
    response = (
        input("📋 Have you installed the required prerequisites? (y/N): ")
        .strip()
        .lower()
    )

    if response not in ["y", "yes"]:
        print("🔗 Install prerequisites first, then run this script again.")
        print("\n📚 Full setup guide available in:")
        print("   hospital_modular_monolith_setup.md")
        sys.exit(0)

    print("\n🚀 Starting automated setup...")
    print("This will:")
    print("  ✓ Detect Python version")
    print("  ✓ Create virtual environment")
    print("  ✓ Install dependencies")
    print("  ✓ Setup Django project")
    print("  ✓ Create configuration files")

    response = input("\n Continue? (Y/n): ").strip().lower()
    if response in ["n", "no"]:
        print("👋 Setup cancelled")
        sys.exit(0)

    # Run the main setup script
    print("\n" + "=" * 50)
    try:
        if system == "Windows":
            os.system(f'python "{setup_script}"')
        else:
            os.system(f'python3 "{setup_script}"')
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
