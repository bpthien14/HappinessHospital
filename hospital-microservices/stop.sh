#!/bin/bash

# Hospital Microservices Stop Script
echo "🏥 Hospital Microservices - Shutting down..."

# Stop all services
echo "🛑 Stopping all services..."
docker compose down

echo "✅ All services stopped successfully!"

# Optional: Remove volumes (uncomment if needed)
# echo "🗑️  Removing volumes..."
# docker compose down -v
# echo "✅ Volumes removed!"

echo ""
echo "📋 To start services again, run: ./start.sh"
echo "📋 To view logs: docker compose logs -f"
echo "📋 To check status: docker compose ps"
