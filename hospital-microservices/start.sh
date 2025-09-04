#!/bin/bash

# Hospital Microservices Startup Script
echo "🏥 Hospital Microservices - Starting up..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ .env file created. Please review and update the values if needed."
    else
        echo "⚠️  .env.example not found. Creating basic .env file..."
        cat > .env << EOF
# Hospital Microservices Environment Variables
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
VNPAY_TMN_CODE=VGGT78DX
VNPAY_HASH_SECRET=20UY4ZYMA23D4J41X6M92ANRV5YPSGU
DEBUG=True
EOF
        echo "✅ Basic .env file created."
    fi
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker compose down

# Build and start services
echo "🔨 Building and starting services..."
docker compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker compose ps

# Health checks
echo "🏥 Running health checks..."

# Gateway health
echo "🔍 Checking gateway health..."
if curl -s http://localhost/health/ > /dev/null; then
    echo "✅ Gateway is healthy"
else
    echo "❌ Gateway health check failed"
fi

# Service health checks
services=("auth" "patients" "appointments" "prescriptions" "payments" "notifications")
ports=(8001 8002 8003 8004 8005 8006)

for i in "${!services[@]}"; do
    service=${services[$i]}
    port=${ports[$i]}
    echo "🔍 Checking $service service health..."
    if curl -s http://localhost:$port/health/ > /dev/null; then
        echo "✅ $service service is healthy"
    else
        echo "❌ $service service health check failed"
    fi
done

echo ""
echo "🎉 Hospital Microservices started successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker compose logs -f"
echo "  Stop services: docker compose down"
echo "  Restart specific service: docker compose restart <service-name>"
echo "  View status: docker compose ps"
echo ""
echo "🌐 Access points:"
echo "  Gateway: http://localhost"
echo "  Auth Service: http://localhost:8001"
echo "  Patients Service: http://localhost:8002"
echo "  Appointments Service: http://localhost:8003"
echo "  Prescriptions Service: http://localhost:8004"
echo "  Payments Service: http://localhost:8005"
echo "  Notifications Service: http://localhost:8006"
echo "  RabbitMQ Management: http://localhost:15672 (guest/guest)"
echo ""
echo "🔍 Health check: curl http://localhost/health"
