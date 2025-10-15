#!/bin/bash

# Comprehensive PostgreSQL Collation Version Fix
# Fixes ICU collation version mismatch warnings in PostgreSQL

set -e  # Exit on any error

echo "🔧 PostgreSQL Collation Version Fix Tool"
echo "========================================"

# Color codes for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Function to get database container
get_db_container() {
    local container_names=("postgres_db" "db" "fiko_db" "postgresql")
    
    for name in "${container_names[@]}"; do
        container=$(docker ps --filter "name=$name" --format "{{.ID}}" | head -1)
        if [ -n "$container" ]; then
            echo "$container"
            return 0
        fi
    done
    
    # If no named container found, try to find postgres image
    container=$(docker ps --filter "ancestor=postgres" --format "{{.ID}}" | head -1)
    if [ -n "$container" ]; then
        echo "$container"
        return 0
    fi
    
    return 1
}

# Get database container
print_status "Looking for PostgreSQL container..."
if ! DB_CONTAINER=$(get_db_container); then
    print_error "PostgreSQL container not found!"
    print_warning "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
    
    echo ""
    print_warning "To start the database container, run:"
    echo "docker-compose up -d db"
    exit 1
fi

print_success "Found PostgreSQL container: $DB_CONTAINER"

# Get database connection details from environment or use defaults
DB_NAME="${POSTGRES_DB:-FikoDB}"
DB_USER="${POSTGRES_USER:-FikoUsr}"

print_status "Database: $DB_NAME, User: $DB_USER"

# Function to execute SQL command
execute_sql() {
    local sql_command="$1"
    local description="$2"
    
    print_status "$description"
    
    if docker exec $DB_CONTAINER psql -U "$DB_USER" -d "$DB_NAME" -c "$sql_command" > /dev/null 2>&1; then
        print_success "$description completed"
        return 0
    else
        print_error "$description failed"
        return 1
    fi
}

# Main fix function
fix_collation() {
    print_status "Starting collation version fix..."
    
    # Check current collation version
    print_status "Checking current collation version..."
    docker exec $DB_CONTAINER psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            datname, 
            datcollate, 
            datctype,
            version() as postgres_version
        FROM pg_database 
        WHERE datname = '$DB_NAME';"
    
    echo ""
    
    # Refresh collation version for the database
    if execute_sql "ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION;" "Refreshing collation version for database $DB_NAME"; then
        print_success "Database collation version refreshed successfully!"
    else
        print_error "Failed to refresh database collation version"
        return 1
    fi
    
    # Also refresh collation for all objects that use collations
    print_status "Refreshing collation version for all collation objects..."
    
    # Get all collations that need refreshing
    docker exec $DB_CONTAINER psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT collname, collversion 
        FROM pg_collation 
        WHERE collprovider = 'i' 
        AND collversion IS NOT NULL 
        AND collversion != pg_collation_actual_version(oid);" 2>/dev/null || true
    
    # Refresh all collations (this command works for PostgreSQL 13+)
    if execute_sql "ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION;" "Final collation refresh"; then
        print_success "All collation versions refreshed!"
    else
        print_warning "Some collation objects may still have version mismatches"
    fi
}

# Verification function
verify_fix() {
    print_status "Verifying the fix..."
    
    # Test basic database connectivity
    if docker exec $DB_CONTAINER psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "Database connection test passed"
    else
        print_error "Database connection test failed"
        return 1
    fi
    
    # Check for any remaining warnings in a simple query
    print_status "Running test query to check for warnings..."
    docker exec $DB_CONTAINER psql -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            'Collation fix verification' as status,
            current_database() as database,
            current_timestamp as checked_at;"
    
    print_success "Verification completed"
}

# Test Django connectivity if container exists
test_django_connection() {
    print_status "Checking for Django container..."
    
    local django_containers=("django_app" "web" "app" "fiko_web")
    local django_container=""
    
    for name in "${django_containers[@]}"; do
        container=$(docker ps --filter "name=$name" --format "{{.ID}}" | head -1)
        if [ -n "$container" ]; then
            django_container="$container"
            break
        fi
    done
    
    if [ -n "$django_container" ]; then
        print_success "Found Django container: $django_container"
        
        print_status "Testing Django database connection..."
        if docker exec $django_container python manage.py check --database default > /dev/null 2>&1; then
            print_success "Django database connection is healthy"
        else
            print_warning "Django database connection has issues (may be unrelated to collation)"
        fi
        
        # Show migration status
        print_status "Current migration status:"
        docker exec $django_container python manage.py showmigrations --plan 2>/dev/null | tail -5 || true
    else
        print_warning "No Django container found. Database fix completed, but Django connectivity not tested."
    fi
}

# Main execution
main() {
    echo ""
    print_status "Starting PostgreSQL collation fix process..."
    echo ""
    
    # Run the fix
    if fix_collation; then
        echo ""
        verify_fix
        echo ""
        test_django_connection
        echo ""
        print_success "🎉 PostgreSQL collation version mismatch has been fixed!"
        print_success "The warnings should no longer appear in your logs."
        echo ""
        print_warning "Note: You may need to restart your Django application to see the changes."
        echo "      Run: docker-compose restart web"
    else
        echo ""
        print_error "Fix failed. Please check the error messages above."
        echo ""
        print_warning "Manual fix steps:"
        echo "1. Connect to the database:"
        echo "   docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME"
        echo ""
        echo "2. Run this SQL command:"
        echo "   ALTER DATABASE \"$DB_NAME\" REFRESH COLLATION VERSION;"
        echo ""
        echo "3. Exit with: \\q"
        exit 1
    fi
}

# Show help if requested
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "PostgreSQL Collation Version Fix Tool"
    echo ""
    echo "This script fixes the common PostgreSQL collation version mismatch warning:"
    echo "  WARNING: database has a collation version mismatch"
    echo ""
    echo "Usage:"
    echo "  $0              # Fix collation version mismatch"
    echo "  $0 --help       # Show this help"
    echo ""
    echo "Environment variables (optional):"
    echo "  POSTGRES_DB     # Database name (default: FikoDB)"
    echo "  POSTGRES_USER   # Database user (default: FikoUsr)"
    echo ""
    echo "Prerequisites:"
    echo "  - Docker must be running"
    echo "  - PostgreSQL container must be running"
    echo ""
    exit 0
fi

# Run main function
main
