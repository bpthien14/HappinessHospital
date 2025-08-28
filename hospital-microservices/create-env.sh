#!/bin/bash

# Create .env file from env.example
echo "🏥 Hospital Microservices - Creating .env file..."

# Check if .env already exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operation cancelled."
        exit 1
    fi
fi

# Check if env.example exists
if [ ! -f env.example ]; then
    echo "❌ env.example file not found!"
    echo "Please make sure env.example exists in the current directory."
    exit 1
fi

# Copy env.example to .env
cp env.example .env

if [ $? -eq 0 ]; then
    echo "✅ .env file created successfully from env.example"
    echo ""
    echo "📝 Please review and update the following values in .env:"
    echo "  - JWT_SECRET_KEY (change to a secure random string)"
    echo "  - VNPAY_TMN_CODE (your VNPAY merchant code)"
    echo "  - VNPAY_HASH_SECRET (your VNPAY hash secret)"
    echo ""
    echo "🔧 You can edit .env with: nano .env"
    echo "🚀 Then start services with: ./start.sh"
else
    echo "❌ Failed to create .env file"
    exit 1
fi
