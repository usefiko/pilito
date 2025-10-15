#!/bin/bash

# =============================================================================
# Fiko Backend - Comprehensive Disk Cleanup Script
# =============================================================================
# This script performs aggressive disk cleanup to free up space on the server
# Usage: ./disk_cleanup.sh [--force] [--dry-run]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=false
FORCE=false
MIN_FREE_SPACE_GB=2

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--force] [--dry-run]"
            echo "  --force    Skip confirmation prompts"
            echo "  --dry-run  Show what would be cleaned without actually doing it"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

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

# Function to get disk usage
get_disk_usage() {
    df -h / | awk 'NR==2 {print $3, $4, $5}' | read used avail percent
    echo "Used: $used, Available: $avail, Usage: $percent"
}

# Function to get available space in GB
get_available_gb() {
    df / | awk 'NR==2 {print int($4/1024/1024)}'
}

# Function to execute command or show what would be executed
execute_or_show() {
    local cmd="$1"
    local description="$2"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would execute: $description${NC}"
        echo "Command: $cmd"
    else
        print_status "$description"
        eval "$cmd" || true
    fi
}

# Main cleanup function
main() {
    echo "======================================"
    echo "🧹 Fiko Backend Disk Cleanup Tool"
    echo "======================================"
    echo ""
    
    # Show initial disk usage
    print_status "Initial disk usage:"
    get_disk_usage
    echo ""
    
    AVAILABLE_GB=$(get_available_gb)
    print_status "Available space: ${AVAILABLE_GB}GB"
    
    if [ "$AVAILABLE_GB" -gt $MIN_FREE_SPACE_GB ] && [ "$FORCE" = false ]; then
        print_warning "You have ${AVAILABLE_GB}GB available. Cleanup may not be necessary."
        echo "Use --force to proceed anyway."
        read -p "Continue with cleanup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleanup cancelled."
            exit 0
        fi
    fi
    
    echo ""
    print_status "Starting comprehensive cleanup..."
    echo ""
    
    # 1. Docker Cleanup
    print_status "🐳 Docker Cleanup"
    echo "==================="
    
    execute_or_show "docker stop \$(docker ps -aq) 2>/dev/null || true" "Stopping all containers"
    execute_or_show "docker container prune -f" "Removing stopped containers"
    execute_or_show "docker image prune -af" "Removing unused images"
    execute_or_show "docker volume prune -f" "Removing unused volumes"
    execute_or_show "docker network prune -f" "Removing unused networks"
    execute_or_show "docker builder prune -af" "Removing build cache"
    execute_or_show "docker system prune -af --volumes" "Complete Docker system cleanup"
    
    # 2. Docker Logs Cleanup
    print_status "📝 Docker Logs Cleanup"
    echo "======================="
    
    execute_or_show "sudo find /var/lib/docker/containers/ -name '*-json.log' -exec truncate -s 0 {} \;" "Truncating Docker container logs"
    
    # 3. System Logs Cleanup
    print_status "📋 System Logs Cleanup"
    echo "======================"
    
    execute_or_show "sudo journalctl --vacuum-time=1d" "Cleaning system journal (keep 1 day)"
    execute_or_show "sudo journalctl --vacuum-size=50M" "Limiting journal size to 50MB"
    execute_or_show "sudo find /var/log -name '*.log' -type f -mtime +1 -delete" "Removing old log files"
    execute_or_show "sudo find /var/log -name '*.log.*' -type f -delete" "Removing rotated log files"
    execute_or_show "sudo find /var/log -name '*.gz' -type f -delete" "Removing compressed log files"
    
    # 4. Temporary Files Cleanup
    print_status "🗑️  Temporary Files Cleanup"
    echo "============================"
    
    execute_or_show "sudo rm -rf /tmp/*" "Cleaning /tmp directory"
    execute_or_show "sudo rm -rf /var/tmp/*" "Cleaning /var/tmp directory"
    execute_or_show "sudo rm -rf /var/cache/apt/archives/*" "Cleaning APT cache archives"
    
    # 5. Package Manager Cleanup
    print_status "📦 Package Manager Cleanup"
    echo "==========================="
    
    execute_or_show "sudo apt-get clean" "Cleaning APT cache"
    execute_or_show "sudo apt-get autoremove -y --purge" "Removing unnecessary packages"
    execute_or_show "sudo apt-get autoclean" "Auto-cleaning APT cache"
    
    # 6. User Cache Cleanup
    print_status "👤 User Cache Cleanup"
    echo "===================="
    
    execute_or_show "sudo rm -rf /home/*/.cache/* 2>/dev/null" "Cleaning user caches"
    execute_or_show "sudo rm -rf /root/.cache/* 2>/dev/null" "Cleaning root cache"
    execute_or_show "sudo rm -rf /home/*/.thumbnails/* 2>/dev/null" "Cleaning thumbnails"
    
    # 7. Application-specific Cleanup
    print_status "🔧 Application Cleanup"
    echo "======================"
    
    if [ -d "/home/ubuntu/fiko-backend" ]; then
        execute_or_show "find /home/ubuntu/fiko-backend -name '*.pyc' -delete" "Removing Python bytecode files"
        execute_or_show "find /home/ubuntu/fiko-backend -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null" "Removing Python cache directories"
        execute_or_show "find /home/ubuntu/fiko-backend -name '*.log' -mtime +1 -delete" "Removing old application logs"
        execute_or_show "find /home/ubuntu/fiko-backend -name '.git/objects/pack/*.pack' -mtime +7 -delete 2>/dev/null" "Cleaning old Git pack files"
    fi
    
    # 8. Kernel Cleanup
    print_status "🔧 Kernel Cleanup"
    echo "================="
    
    execute_or_show "sudo apt-get autoremove --purge -y" "Removing old kernel versions"
    
    # 9. Additional Cleanup for specific directories that grow large
    print_status "🔍 Additional Cleanup"
    echo "===================="
    
    execute_or_show "sudo find /var/crash -type f -delete 2>/dev/null" "Removing crash dump files"
    execute_or_show "sudo find /var/spool -name '*' -mtime +7 -delete 2>/dev/null" "Cleaning old spool files"
    execute_or_show "sudo truncate -s 0 /var/log/wtmp" "Truncating wtmp log"
    execute_or_show "sudo truncate -s 0 /var/log/btmp" "Truncating btmp log"
    
    echo ""
    print_status "Final disk usage:"
    get_disk_usage
    
    FINAL_AVAILABLE_GB=$(get_available_gb)
    print_success "Final available space: ${FINAL_AVAILABLE_GB}GB"
    
    if [ "$FINAL_AVAILABLE_GB" -gt $MIN_FREE_SPACE_GB ]; then
        print_success "Cleanup completed successfully! You now have sufficient disk space."
    else
        print_warning "Cleanup completed but disk space is still low (${FINAL_AVAILABLE_GB}GB)."
        print_warning "Consider:"
        echo "  1. Expanding your server storage"
        echo "  2. Moving large files to external storage"
        echo "  3. Analyzing large directories: sudo du -h / 2>/dev/null | sort -hr | head -20"
    fi
    
    echo ""
    print_status "Top 10 largest directories after cleanup:"
    if [ "$DRY_RUN" = false ]; then
        sudo du -h / 2>/dev/null | sort -hr | head -10 || true
    else
        echo "[DRY RUN] Would show largest directories"
    fi
}

# Ensure script is run with appropriate permissions
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root. This is fine, but be careful!"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Docker cleanup will be skipped."
fi

# Run main function
main

echo ""
print_success "Disk cleanup script completed!"

# Show a summary of what could be automated
if [ "$DRY_RUN" = false ]; then
    echo ""
    print_status "💡 Pro tip: You can automate this cleanup by adding to crontab:"
    echo "sudo crontab -e"
    echo "# Add this line to run cleanup weekly:"
    echo "0 2 * * 0 /home/ubuntu/fiko-backend/disk_cleanup.sh --force >/tmp/cleanup.log 2>&1"
fi