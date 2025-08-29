#!/bin/bash

# Test PostgreSQL Connection for Hospital Microservices
echo "🏥 Hospital Microservices - Testing PostgreSQL Connections"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database configuration
DB_USER="fe-phuocthien"
DB_HOST="localhost"
DB_PORT="5432"

# List of databases to test
databases=(
    "hospital_auth"
    "hospital_patients"
    "hospital_appointments"
    "hospital_prescriptions"
    "hospital_payments"
)

# Function to test database connection
test_database() {
    local db_name=$1
    
    echo -n "🔍 Testing connection to $db_name... "
    
    if psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$db_name" -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Check if PostgreSQL is running
echo "📊 Checking PostgreSQL service status..."
if brew services list | grep -q "postgresql@15.*started"; then
    echo -e "${GREEN}✅ PostgreSQL is running${NC}"
else
    echo -e "${RED}❌ PostgreSQL is not running${NC}"
    echo "Start PostgreSQL with: brew services start postgresql@15"
    exit 1
fi

echo ""

# Test each database
echo "🔧 Testing database connections..."
success_count=0
total_count=0

for db in "${databases[@]}"; do
    if test_database "$db"; then
        ((success_count++))
    fi
    ((total_count++))
done

echo ""
echo "📊 Database Connection Summary:"
echo "================================"
echo -e "Total Databases: ${YELLOW}$total_count${NC}"
echo -e "Connected: ${GREEN}$success_count${NC}"
echo -e "Failed: ${RED}$((total_count - success_count))${NC}"

if [ $success_count -eq $total_count ]; then
    echo -e "${GREEN}🎉 All databases are accessible!${NC}"
    echo ""
    echo "🚀 You can now start the microservices with: ./start.sh"
    exit 0
else
    echo -e "${RED}⚠️  Some databases are not accessible.${NC}"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Check if PostgreSQL is running: brew services list | grep postgresql"
    echo "2. Verify databases exist: psql -U fe-phuocthien -d postgres -c '\l' | grep hospital"
    echo "3. Check user permissions: psql -U fe-phuocthien -d postgres -c '\du'"
    exit 1
fi
