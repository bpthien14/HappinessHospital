#!/bin/bash

# Hospital Microservices Health Check Script
echo "🏥 Hospital Microservices - Health Check"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check health
check_health() {
    local service_name=$1
    local url=$2
    local description=$3
    
    echo -n "🔍 Checking $service_name ($description)... "
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

# Check if services are running
echo "📊 Checking if services are running..."
if ! docker compose ps | grep -q "Up"; then
    echo -e "${RED}❌ No services are running. Start services first with: ./start.sh${NC}"
    exit 1
fi

echo "✅ Services are running. Proceeding with health checks..."
echo ""

# Health check results
healthy_count=0
total_count=0

# Gateway health check
echo "🌐 Gateway Health Check:"
if check_health "Gateway" "http://localhost/health" "Port 80"; then
    ((healthy_count++))
fi
((total_count++))
echo ""

# Service health checks
echo "🔧 Service Health Checks:"
services=(
    "Auth Service:http://localhost:8001/health:Port 8001"
    "Patients Service:http://localhost:8002/health:Port 8002"
    "Appointments Service:http://localhost:8003/health:Port 8003"
    "Prescriptions Service:http://localhost:8004/health:Port 8004"
    "Payments Service:http://localhost:8005/health:Port 8005"
    "Notifications Service:http://localhost:8006/health:Port 8006"
)

for service in "${services[@]}"; do
    IFS=':' read -r name url description <<< "$service"
    if check_health "$name" "$url" "$description"; then
        ((healthy_count++))
    fi
    ((total_count++))
done

echo ""
echo "📊 Health Check Summary:"
echo "=========================="
echo -e "Total Services: ${YELLOW}$total_count${NC}"
echo -e "Healthy: ${GREEN}$healthy_count${NC}"
echo -e "Unhealthy: ${RED}$((total_count - healthy_count))${NC}"

if [ $healthy_count -eq $total_count ]; then
    echo -e "${GREEN}🎉 All services are healthy!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some services are unhealthy. Check logs with: docker compose logs -f${NC}"
    exit 1
fi
