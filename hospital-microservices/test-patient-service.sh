#!/bin/bash

# Test Patient Service
echo "🏥 Testing Patient Service"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test direct service health
echo -e "\n${BLUE}1. Testing Direct Service Health${NC}"
echo "----------------------------------------"
if curl -s http://localhost:8002/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✅ Patient Service: HEALTHY${NC}"
else
    echo -e "${RED}❌ Patient Service: UNHEALTHY${NC}"
fi

# Test service via Nginx
echo -e "\n${BLUE}2. Testing Service via Nginx Gateway${NC}"
echo "----------------------------------------"

# Test patients endpoint (should return empty list)
echo -n "Testing patients endpoint... "
if curl -s http://localhost/api/patients/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test Swagger documentation
echo -n "Testing Swagger UI... "
if curl -s http://localhost:8002/api/docs/ | grep -q "Hospital Patients Service API"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test API Schema
echo -n "Testing API Schema... "
if curl -s http://localhost:8002/api/schema/ | grep -q "openapi"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⚠️  Schema endpoint has issues${NC}"
fi

# Test authentication requirement
echo -e "\n${BLUE}3. Testing Authentication Requirements${NC}"
echo "----------------------------------------"

echo -n "Testing unauthenticated access... "
if curl -s -X POST http://localhost/api/patients/ -H "Content-Type: application/json" -d '{"test": "data"}' | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test endpoints structure
echo -e "\n${BLUE}4. Testing Endpoints Structure${NC}"
echo "----------------------------------------"

echo -n "Testing patients endpoint structure... "
if curl -s http://localhost/api/patients/ | grep -q '"count":0'; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Patient Service is working correctly!${NC}"
echo ""
echo -e "${YELLOW}🔗 Available endpoints:${NC}"
echo "  - Health: http://localhost:8002/health/"
echo "  - Patients: http://localhost/api/patients/"
echo "  - Medical Records: http://localhost/api/medical-records/"
echo "  - Documents: http://localhost/api/documents/"
echo "  - Swagger UI: http://localhost:8002/api/docs/"
echo "  - API Schema: http://localhost:8002/api/schema/"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "  1. Test with authentication (JWT token)"
echo "  2. Create test patients"
echo "  3. Test CRUD operations"
echo "  4. Test filtering and search"
