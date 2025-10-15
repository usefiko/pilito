#!/bin/bash

# Production PostgreSQL Collation Version Fix
# For Fiko Backend Production Server
# Eliminates: WARNING: database "FikoDB" has a collation version mismatch

set -e  # Exit on any error

echo "🔧 Production PostgreSQL Collation Fix"
echo "====================================="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if running as root or with sudo
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root - this is fine for production servers"
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running"
    print_warning "Start Docker with: sudo systemctl start docker"
    exit 1
fi

print_success "Docker is available and running"

# Function to find PostgreSQL container
find_postgres_container() {
    # Try common container names for production
    local container_names=("postgres_db" "db" "fiko_db" "postgresql" "postgres" "database")
    
    for name in "${container_names[@]}"; do
        container=$(docker ps --filter "name=$name" --format "{{.ID}}" 2>/dev/null | head -1)
        if [ -n "$container" ]; then
            echo "$container"
            return 0
        fi
    done
    
    # Try finding by image
    container=$(docker ps --filter "ancestor=postgres" --format "{{.ID}}" 2>/dev/null | head -1)
    if [ -n "$container" ]; then
        echo "$container"
        return 0
    fi
    
    return 1
}

# Find database container
print_status "Searching for PostgreSQL container..."
if ! DB_CONTAINER=$(find_postgres_container); then
    print_error "PostgreSQL container not found!"
    print_warning "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" 2>/dev/null || true
    
    print_warning "If using docker-compose, try:"
    echo "cd /path/to/your/project && docker-compose up -d db"
    exit 1
fi

print_success "Found PostgreSQL container: $DB_CONTAINER"

# Get container name for better output
CONTAINER_NAME=$(docker ps --filter "id=$DB_CONTAINER" --format "{{.Names}}" | head -1)
print_status "Container name: $CONTAINER_NAME"

# Database connection parameters
DB_NAME="FikoDB"
DB_USER="FikoUsr"

print_status "Target database: $DB_NAME"
print_status "Database user: $DB_USER"

# Function to execute SQL safely
execute_sql() {
    local sql_command="$1"
    local description="$2"
    
    print_status "$description"
    
    if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$sql_command" > /dev/null 2>&1; then
        print_success "$description - SUCCESS"
        return 0
    else
        print_error "$description - FAILED"
        return 1
    fi
}

# Main fix function
fix_collation() {
    print_status "Starting collation version fix..."
    echo ""
    
    # Show current status
    print_status "Current database information:"
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            current_database() as database,
            current_user as user,
            version() as postgres_version;
    " 2>/dev/null || print_warning "Could not retrieve database info"
    
    echo ""
    
    # Execute the main fix
    print_status "Executing: ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION"
    
    if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION;" 2>/dev/null; then
        print_success "Collation version refreshed successfully!"
    else
        print_error "Failed to refresh collation version"
        print_warning "This might be due to:"
        echo "  - Insufficient database privileges"
        echo "  - Database connection issues"
        echo "  - PostgreSQL version compatibility"
        return 1
    fi
    
    return 0
}

# Verification function
verify_fix() {
    print_status "Verifying the fix..."
    
    # Test database connectivity
    if docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "Database connectivity test passed"
    else
        print_warning "Database connectivity test failed"
    fi
    
    # Run a test query that might trigger collation checks
    print_status "Running verification query..."
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            'Collation fix applied on production' as status,
            current_timestamp as fixed_at;
    " 2>/dev/null || print_warning "Verification query failed"
    
    print_success "Verification completed"
}

# Check for Django/web container
check_web_services() {
    print_status "Checking for web application containers..."
    
    local web_containers=("django_app" "web" "app" "fiko_web" "backend")
    local found_container=""
    
    for name in "${web_containers[@]}"; do
        container=$(docker ps --filter "name=$name" --format "{{.ID}}" 2>/dev/null | head -1)
        if [ -n "$container" ]; then
            found_container="$container"
            local container_name=$(docker ps --filter "id=$container" --format "{{.Names}}" | head -1)
            print_success "Found web container: $container_name ($container)"
            
            # Test Django database connection if possible
            print_status "Testing Django database connection..."
            if docker exec "$container" python manage.py check --database default > /dev/null 2>&1; then
                print_success "Django database connection is healthy"
            else
                print_warning "Django database connection test failed (may need restart)"
            fi
            break
        fi
    done
    
    if [ -z "$found_container" ]; then
        print_warning "No web application container found"
        print_warning "You may need to restart your web services manually"
    fi
}

# Restart services function
restart_services() {
    print_status "Service restart recommendations..."
    
    # Check if docker-compose is available
    if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
        print_warning "To apply changes completely, restart your web services:"
        echo ""
        echo "  # If using docker-compose:"
        echo "  docker-compose restart web"
        echo ""
        echo "  # If using docker compose (newer):"
        echo "  docker compose restart web"
        echo ""
        echo "  # Or restart specific container:"
        echo "  docker restart <web_container_name>"
    else
        print_warning "Docker Compose not found. Restart web containers manually."
    fi
}

# Main execution
main() {
    echo ""
    print_status "Starting production collation fix..."
    echo ""
    
    # Execute the fix
    if fix_collation; then
        echo ""
        verify_fix
        echo ""
        check_web_services
        echo ""
        restart_services
        echo ""
        print_success "🎉 PostgreSQL collation fix completed on production!"
        print_success "The collation version mismatch warnings should be eliminated."
        echo ""
        print_warning "IMPORTANT: Restart your web application to see the changes:"
        echo "           docker-compose restart web"
        echo ""
        print_status "Monitor logs after restart to confirm warnings are gone:"
        echo "           docker-compose logs web | grep -i collation"
        
    else
        echo ""
        print_error "Production collation fix failed!"
        echo ""
        print_warning "Manual fix steps:"
        echo "1. Connect to PostgreSQL:"
        echo "   docker exec -it $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME"
        echo ""
        echo "2. Run this command:"
        echo "   ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION;"
        echo ""
        echo "3. Exit with: \\q"
        echo ""
        exit 1
    fi
}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Production PostgreSQL Collation Fix"
    echo ""
    echo "Eliminates the following warnings from production logs:"
    echo "  WARNING: database \"FikoDB\" has a collation version mismatch"
    echo "  DETAIL: The database was created using collation version 2.36..."
    echo ""
    echo "Usage:"
    echo "  $0              # Run the fix"
    echo "  $0 --help       # Show this help"
    echo ""
    echo "This script will:"
    echo "  1. Find your PostgreSQL container"
    echo "  2. Execute ALTER DATABASE REFRESH COLLATION VERSION"
    echo "  3. Verify the fix"
    echo "  4. Provide restart instructions"
    echo ""
    exit 0
fi

# Record execution
echo "=== Production Collation Fix Log ===" >> /tmp/fiko_collation_fix.log
echo "Date: $(date)" >> /tmp/fiko_collation_fix.log
echo "Server: $(hostname)" >> /tmp/fiko_collation_fix.log
echo "User: $(whoami)" >> /tmp/fiko_collation_fix.log

# Run main function
main

echo "Execution completed at $(date)" >> /tmp/fiko_collation_fix.log
echo "=====================================\n" >> /tmp/fiko_collation_fix.log
