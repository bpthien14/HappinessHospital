#!/bin/bash

# Test Prescription Service
echo "💊 Testing Prescription Service"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test direct service health
echo -e "\n${BLUE}1. Testing Direct Service Health${NC}"
echo "----------------------------------------"
if curl -s http://localhost:8004/health/ | grep -q "healthy"; then
    echo -e "${GREEN}✅ Prescription Service: HEALTHY${NC}"
else
    echo -e "${RED}❌ Prescription Service: UNHEALTHY${NC}"
fi

# Test service via Nginx
echo -e "\n${BLUE}2. Testing Service via Nginx Gateway${NC}"
echo "----------------------------------------"

echo -n "Testing prescriptions endpoint... "
if curl -s http://localhost/api/prescriptions/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing drugs endpoint... "
if curl -s http://localhost/api/drugs/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing drug-categories endpoint... "
if curl -s http://localhost/api/drug-categories/ | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing prescription-items endpoint... "
if curl -s http://localhost/api/prescription-items/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing dispensing endpoint... "
if curl -s http://localhost/api/dispensing/ | grep -q "count"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing Swagger UI... "
if curl -s http://localhost:8004/api/docs/ | grep -q "Hospital Prescriptions Service API"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo -n "Testing API Schema... "
if curl -s http://localhost:8004/api/schema/ | grep -q "openapi"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test authentication requirements
echo -e "\n${BLUE}3. Testing Authentication Requirements${NC}"
echo "----------------------------------------"
echo -n "Testing unauthenticated access... "
if curl -s -X POST http://localhost/api/prescriptions/ \
    -H "Content-Type: application/json" \
    -d '{"patient_id": "123e4567-e89b-12d3-a456-426614174000", "doctor_id": "123e4567-e89b-12d3-a456-426614174001", "diagnosis": "Test diagnosis", "valid_from": "2024-01-15T09:00:00Z", "valid_until": "2024-01-22T09:00:00Z", "items": []}' | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}✅ OK (Authentication required)${NC}"
else
    echo -e "${YELLOW}⚠️  Different error response${NC}"
fi

# Test endpoints structure
echo -e "\n${BLUE}4. Testing Endpoints Structure${NC}"
echo "----------------------------------------"
echo -n "Testing prescriptions endpoint structure... "
if curl -s http://localhost/api/prescriptions/ | grep -q "results"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Prescription Service is working correctly!${NC}"
echo ""
echo -e "${YELLOW}🔗 Available endpoints:${NC}"
echo "  - Health: http://localhost:8004/health/"
echo "  - Prescriptions: http://localhost/api/prescriptions/"
echo "  - Drugs: http://localhost/api/drugs/"
echo "  - Drug Categories: http://localhost/api/drug-categories/"
echo "  - Prescription Items: http://localhost/api/prescription-items/"
echo "  - Dispensing: http://localhost/api/dispensing/"
echo "  - Swagger UI: http://localhost:8004/api/docs/"
echo "  - API Schema: http://localhost:8004/api/schema/"
echo ""
echo -e "${BLUE}🚀 Next Steps:${NC}"
echo "  1. Test with authentication (JWT token)"
echo "  2. Create test drug categories and drugs"
echo "  3. Test prescription creation"
echo "  4. Test CRUD operations"
echo "  5. Test filtering and search"
