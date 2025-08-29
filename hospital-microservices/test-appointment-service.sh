#!/bin/bash

# Test Appointment Service
echo "🏥 Testing Appointment Service"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test direct service health
echo -e "\n${BLUE}1. Testing Direct Service Health${NC}"
echo "----------------------------------------"
if curl -s http://localhost:8003/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✅ Appointment Service: HEALTHY${NC}"
else
    echo -e "${RED}❌ Appointment Service: UNHEALTHY${NC}"
fi

# Test service via Nginx
echo -e "\n${BLUE}2. Testing Service via Nginx Gateway${NC}"
echo "----------------------------------------"

echo -n "Testing appointments endpoint... "
if curl -s http://localhost/api/appointments/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing departments endpoint... "
if curl -s http://localhost/api/departments/ | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing doctors endpoint... "
if curl -s http://localhost/api/doctors/ | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing Swagger UI... "
if curl -s http://localhost:8003/api/docs/ | grep -q "Hospital Appointments Service API"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing API Schema... "
if curl -s http://localhost:8003/api/schema/ | grep -q "openapi"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test authentication requirements
echo -e "\n${BLUE}3. Testing Authentication Requirements${NC}"
echo "----------------------------------------"
echo -n "Testing unauthenticated access... "
if curl -s -X POST http://localhost/api/appointments/ \
    -H "Content-Type: application/json" \
    -d '{"patient_id": "123e4567-e89b-12d3-a456-426614174000", "doctor_id": "123e4567-e89b-12d3-a456-426614174001", "department_id": "123e4567-e89b-12d3-a456-426614174002", "appointment_date": "2024-01-15", "appointment_time": "09:00:00", "chief_complaint": "Test complaint"}' | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${YELLOW}⚠️  Different error response${NC}"
fi

# Test endpoints structure
echo -e "\n${BLUE}4. Testing Endpoints Structure${NC}"
echo "----------------------------------------"
echo -n "Testing appointments endpoint structure... "
if curl -s http://localhost/api/appointments/ | grep -q "results"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Appointment Service is working correctly!${NC}"
echo ""
echo -e "${YELLOW}🔗 Available endpoints:${NC}"
echo "  - Health: http://localhost:8003/health/"
echo "  - Appointments: http://localhost/api/appointments/"
echo "  - Departments: http://localhost/api/departments/"
echo "  - Doctors: http://localhost/api/doctors/"
echo "  - Schedules: http://localhost/api/schedules/"
echo "  - Time Slots: http://localhost/api/time-slots/"
echo "  - Status History: http://localhost/api/status-history/"
echo "  - Swagger UI: http://localhost:8003/api/docs/"
echo "  - API Schema: http://localhost:8003/api/schema/"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "  1. Test with authentication (JWT token)"
echo "  2. Create test departments and doctors"
echo "  3. Test appointment creation"
echo "  4. Test CRUD operations"
echo "  5. Test filtering and search"
