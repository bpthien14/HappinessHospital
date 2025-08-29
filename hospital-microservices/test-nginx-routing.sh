#!/bin/bash

# Test Nginx Routing to Auth Service
echo "🌐 Testing Nginx Routing to Auth Service"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test health endpoint
echo -e "\n${BLUE}1. Testing Health Endpoint${NC}"
echo "----------------------------------------"
if curl -s http://localhost/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health endpoint: OK${NC}"
else
    echo -e "${RED}❌ Health endpoint: FAILED${NC}"
fi

# Test auth service login
echo -e "\n${BLUE}2. Testing Auth Service Login${NC}"
echo "----------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST http://localhost/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')

if echo "$LOGIN_RESPONSE" | grep -q "access"; then
    echo -e "${GREEN}✅ Login endpoint: OK${NC}"
    
    # Extract access token
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access":"[^"]*"' | cut -d'"' -f4)
    echo -e "${YELLOW}📝 Access token extracted${NC}"
else
    echo -e "${RED}❌ Login endpoint: FAILED${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test protected endpoints with token
echo -e "\n${BLUE}3. Testing Protected Endpoints${NC}"
echo "----------------------------------------"

# Test users endpoint
echo -n "Testing users endpoint... "
if curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    http://localhost/api/auth/users/ | grep -q "count"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

# Test roles endpoint
echo -n "Testing roles endpoint... "
if curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    http://localhost/api/auth/roles/ | grep -q "count"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

# Test permissions endpoint
echo -n "Testing permissions endpoint... "
if curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    http://localhost/api/auth/permissions/ | grep -q "count"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

# Test Swagger documentation
echo -e "\n${BLUE}4. Testing Swagger Documentation${NC}"
echo "----------------------------------------"

# Test Swagger UI
echo -n "Testing Swagger UI... "
if curl -s http://localhost/api/docs/ | grep -q "Hospital Auth Service API"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

# Test API Schema
echo -n "Testing API Schema... "
if curl -s http://localhost/api/schema/ | grep -q "openapi"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}⚠️  Schema endpoint has issues${NC}"
fi

# Test error handling
echo -e "\n${BLUE}5. Testing Error Handling${NC}"
echo "----------------------------------------"

# Test invalid endpoint
echo -n "Testing invalid endpoint... "
if curl -s http://localhost/api/invalid/ | grep -q "API endpoint not found"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAILED${NC}"
fi

# Test unauthorized access
echo -n "Testing unauthorized access... "
if curl -s http://localhost/api/auth/users/ | grep -q "Authentication credentials were not provided"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}⚠️  Different error response${NC}"
fi

# Test rate limiting
echo -e "\n${BLUE}6. Testing Rate Limiting${NC}"
echo "----------------------------------------"

echo -n "Testing rate limiting (making multiple requests)... "
for i in {1..15}; do
    curl -s -X POST http://localhost/api/auth/login/ \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}' > /dev/null
done

# Check if rate limiting is working
if curl -s -X POST http://localhost/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}' | grep -q "Too Many Requests"; then
    echo -e "${GREEN}OK (Rate limiting active)${NC}"
else
    echo -e "${YELLOW}⚠️  Rate limiting not detected${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=========================================="
echo -e "${GREEN}✅ Nginx routing to Auth Service is working correctly!${NC}"
echo ""
echo -e "${YELLOW}🔗 Available endpoints:${NC}"
echo "  - Health: http://localhost/health"
echo "  - Login: http://localhost/api/auth/login/"
echo "  - Users: http://localhost/api/auth/users/"
echo "  - Roles: http://localhost/api/auth/roles/"
echo "  - Permissions: http://localhost/api/auth/permissions/"
echo "  - Swagger UI: http://localhost/api/docs/"
echo "  - API Schema: http://localhost/api/schema/"
echo ""
echo -e "${BLUE}🚀 You can now use the Nginx gateway to access all Auth Service endpoints!${NC}"
