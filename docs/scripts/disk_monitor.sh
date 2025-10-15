#!/bin/bash

# =============================================================================
# Fiko Backend - Disk Space Monitor & Auto-Cleanup
# =============================================================================
# This script monitors disk space and automatically triggers cleanup when needed
# Can be run as a cron job for automated monitoring
# =============================================================================

set -e

# Configuration
ALERT_THRESHOLD=85  # Alert when disk usage exceeds this percentage
CLEANUP_THRESHOLD=90  # Auto-cleanup when disk usage exceeds this percentage
MIN_FREE_SPACE_GB=2  # Minimum free space required in GB
LOG_FILE="/var/log/disk_monitor.log"
CLEANUP_SCRIPT="/home/ubuntu/fiko-backend/disk_cleanup.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    log "WARNING: $1"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR: $1"
}

# Function to send alert (can be extended to send email, Slack, etc.)
send_alert() {
    local message="$1"
    local level="$2"
    
    print_error "ALERT [$level]: $message"
    
    # Here you can add integrations for:
    # - Email notifications
    # - Slack webhooks
    # - Discord webhooks
    # - SMS alerts
    # - Push notifications
    
    # Example webhook (uncomment and configure):
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"🚨 Fiko Server Alert [$level]: $message\"}" \
    #   "$SLACK_WEBHOOK_URL" 2>/dev/null || true
}

# Function to get disk usage percentage
get_disk_usage_percent() {
    df / | awk 'NR==2 {print $5}' | sed 's/%//'
}

# Function to get available space in GB
get_available_gb() {
    df / | awk 'NR==2 {print int($4/1024/1024)}'
}

# Function to get total space in GB
get_total_gb() {
    df / | awk 'NR==2 {print int($2/1024/1024)}'
}

# Function to check Docker space usage
check_docker_space() {
    if command -v docker &> /dev/null; then
        local docker_space=$(docker system df --format "table {{.Type}}\t{{.Size}}" 2>/dev/null | tail -n +2 | awk '{print $2}' | grep -o '[0-9.]*' | awk '{sum += $1} END {print sum}' 2>/dev/null || echo "0")
        echo "${docker_space:-0}"
    else
        echo "0"
    fi
}

# Function to analyze disk usage
analyze_disk_usage() {
    print_status "Analyzing disk usage..."
    
    local usage_percent=$(get_disk_usage_percent)
    local available_gb=$(get_available_gb)
    local total_gb=$(get_total_gb)
    local docker_gb=$(check_docker_space)
    
    echo ""
    echo "📊 Disk Usage Report"
    echo "==================="
    echo "Total Space: ${total_gb}GB"
    echo "Available Space: ${available_gb}GB"
    echo "Usage: ${usage_percent}%"
    echo "Docker Space: ${docker_gb}GB"
    echo ""
    
    # Log the metrics
    log "METRICS: Total=${total_gb}GB, Available=${available_gb}GB, Usage=${usage_percent}%, Docker=${docker_gb}GB"
    
    # Check thresholds
    if [ "$usage_percent" -ge "$CLEANUP_THRESHOLD" ]; then
        print_error "CRITICAL: Disk usage is ${usage_percent}% (>= ${CLEANUP_THRESHOLD}%)"
        return 2  # Critical
    elif [ "$usage_percent" -ge "$ALERT_THRESHOLD" ]; then
        print_warning "WARNING: Disk usage is ${usage_percent}% (>= ${ALERT_THRESHOLD}%)"
        return 1  # Warning
    else
        print_success "OK: Disk usage is ${usage_percent}% (< ${ALERT_THRESHOLD}%)"
        return 0  # OK
    fi
}

# Function to perform emergency cleanup
emergency_cleanup() {
    print_warning "Performing emergency cleanup..."
    
    if [ -f "$CLEANUP_SCRIPT" ]; then
        print_status "Running automated cleanup script..."
        bash "$CLEANUP_SCRIPT" --force
    else
        print_warning "Cleanup script not found at $CLEANUP_SCRIPT. Performing basic cleanup..."
        
        # Basic Docker cleanup
        docker system prune -af --volumes 2>/dev/null || true
        docker builder prune -af 2>/dev/null || true
        
        # Basic system cleanup
        sudo apt-get clean 2>/dev/null || true
        sudo journalctl --vacuum-time=1d 2>/dev/null || true
        sudo rm -rf /tmp/* 2>/dev/null || true
    fi
}

# Function to show largest directories
show_large_directories() {
    print_status "Top 10 largest directories:"
    sudo du -h / 2>/dev/null | sort -hr | head -10 | while read size dir; do
        echo "  $size - $dir"
    done
}

# Function to check specific application directories
check_app_directories() {
    print_status "Checking application-specific directories..."
    
    local app_dir="/home/ubuntu/fiko-backend"
    if [ -d "$app_dir" ]; then
        local app_size=$(du -sh "$app_dir" 2>/dev/null | cut -f1)
        echo "Application directory size: $app_size"
        log "Application directory ($app_dir) size: $app_size"
    fi
    
    # Check Docker directory
    if [ -d "/var/lib/docker" ]; then
        local docker_size=$(sudo du -sh /var/lib/docker 2>/dev/null | cut -f1)
        echo "Docker directory size: $docker_size"
        log "Docker directory (/var/lib/docker) size: $docker_size"
    fi
    
    # Check logs directory
    if [ -d "/var/log" ]; then
        local logs_size=$(sudo du -sh /var/log 2>/dev/null | cut -f1)
        echo "Logs directory size: $logs_size"
        log "Logs directory (/var/log) size: $logs_size"
    fi
}

# Main monitoring function
main() {
    echo "======================================"
    echo "🔍 Fiko Backend Disk Monitor"
    echo "======================================"
    echo ""
    
    # Create log file if it doesn't exist
    sudo touch "$LOG_FILE" 2>/dev/null || true
    sudo chmod 644 "$LOG_FILE" 2>/dev/null || true
    
    log "Starting disk monitoring check"
    
    # Analyze current disk usage
    analyze_disk_usage
    local status=$?
    
    case $status in
        0)
            print_success "Disk space is healthy"
            ;;
        1)
            print_warning "Disk space is approaching critical levels"
            send_alert "Disk usage is ${usage_percent}% on Fiko server" "WARNING"
            show_large_directories
            ;;
        2)
            print_error "Disk space is critically low!"
            send_alert "CRITICAL: Disk usage is ${usage_percent}% on Fiko server - Auto-cleanup triggered" "CRITICAL"
            emergency_cleanup
            
            # Check again after cleanup
            echo ""
            print_status "Checking disk space after cleanup..."
            analyze_disk_usage
            local post_cleanup_status=$?
            
            if [ $post_cleanup_status -eq 2 ]; then
                send_alert "URGENT: Cleanup completed but disk is still critically full - manual intervention required" "URGENT"
                show_large_directories
            else
                print_success "Cleanup successful - disk space recovered"
            fi
            ;;
    esac
    
    # Show additional information
    echo ""
    check_app_directories
    
    # Show recent log entries if verbose
    if [ "$1" = "--verbose" ] || [ "$1" = "-v" ]; then
        echo ""
        print_status "Recent monitoring logs (last 10 entries):"
        tail -n 10 "$LOG_FILE" 2>/dev/null || echo "No log entries found"
    fi
    
    log "Disk monitoring check completed"
}

# Function to setup automated monitoring
setup_monitoring() {
    print_status "Setting up automated disk monitoring..."
    
    # Create cron job for monitoring (every 30 minutes)
    local cron_job="*/30 * * * * /home/ubuntu/fiko-backend/disk_monitor.sh >/dev/null 2>&1"
    
    # Check if cron job already exists
    if ! crontab -l 2>/dev/null | grep -q "disk_monitor.sh"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        print_success "Automated monitoring setup complete - runs every 30 minutes"
    else
        print_warning "Automated monitoring already configured"
    fi
    
    # Create logrotate config for the monitor log
    local logrotate_config="/etc/logrotate.d/disk_monitor"
    if [ ! -f "$logrotate_config" ]; then
        sudo tee "$logrotate_config" > /dev/null << EOF
$LOG_FILE {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
        print_success "Log rotation configured for monitoring logs"
    fi
}

# Command line argument handling
case "${1:-}" in
    --setup)
        setup_monitoring
        ;;
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --setup     Setup automated monitoring (cron job)"
        echo "  --verbose   Show verbose output including recent logs"
        echo "  --help      Show this help message"
        echo ""
        echo "Thresholds:"
        echo "  Alert threshold: ${ALERT_THRESHOLD}%"
        echo "  Cleanup threshold: ${CLEANUP_THRESHOLD}%"
        echo "  Minimum free space: ${MIN_FREE_SPACE_GB}GB"
        ;;
    *)
        main "$@"
        ;;
esac
