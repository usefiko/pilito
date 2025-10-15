#!/bin/bash

# ==================================================================
# AWS Security Group Configuration for Monitoring Ports
# ==================================================================
# This script configures AWS Security Group to allow access to
# monitoring services (Grafana, Prometheus, etc.)
# ==================================================================

set -e

echo "🔧 Monitoring Ports Configuration Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTANCE_ID="${1:-}"
SECURITY_GROUP_ID="${2:-}"

# Port configurations
declare -A PORTS=(
    ["3001"]="Grafana Dashboard"
    ["9090"]="Prometheus UI"
    ["9121"]="Redis Exporter"
    ["9187"]="PostgreSQL Exporter"
    ["9808"]="Celery Worker Metrics"
)

# Function to display usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 [instance-id] [security-group-id]"
    echo ""
    echo -e "${BLUE}Arguments:${NC}"
    echo "  instance-id       (Optional) EC2 Instance ID"
    echo "  security-group-id (Optional) Security Group ID"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0                                    # Auto-detect from current instance"
    echo "  $0 i-1234567890abcdef0                # Using instance ID"
    echo "  $0 '' sg-1234567890abcdef0            # Using security group ID"
    echo ""
}

# Function to check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        echo ""
        echo "Please install AWS CLI first:"
        echo "  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo ""
        echo "Or install via pip:"
        echo "  pip install awscli"
        exit 1
    fi
    echo -e "${GREEN}✅ AWS CLI is installed${NC}"
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured${NC}"
        echo ""
        echo "Please configure AWS credentials:"
        echo "  aws configure"
        echo ""
        echo "Or set environment variables:"
        echo "  export AWS_ACCESS_KEY_ID=your_key"
        echo "  export AWS_SECRET_ACCESS_KEY=your_secret"
        echo "  export AWS_DEFAULT_REGION=us-east-2"
        exit 1
    fi
    echo -e "${GREEN}✅ AWS credentials are configured${NC}"
}

# Function to get instance metadata (when running on EC2)
get_instance_metadata() {
    local metadata_url="http://169.254.169.254/latest/meta-data"
    
    if curl -s --connect-timeout 2 "${metadata_url}/instance-id" &> /dev/null; then
        INSTANCE_ID=$(curl -s "${metadata_url}/instance-id")
        echo -e "${GREEN}✅ Detected Instance ID: ${INSTANCE_ID}${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Not running on EC2 or metadata service unavailable${NC}"
        return 1
    fi
}

# Function to get security group from instance
get_security_group() {
    local instance_id="$1"
    
    SECURITY_GROUP_ID=$(aws ec2 describe-instances \
        --instance-ids "${instance_id}" \
        --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
        --output text 2>/dev/null)
    
    if [ -z "$SECURITY_GROUP_ID" ] || [ "$SECURITY_GROUP_ID" == "None" ]; then
        echo -e "${RED}❌ Could not find security group for instance ${instance_id}${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Detected Security Group: ${SECURITY_GROUP_ID}${NC}"
    return 0
}

# Function to add security group rule
add_security_rule() {
    local port="$1"
    local description="$2"
    local cidr="${3:-0.0.0.0/0}"
    
    # Check if rule already exists
    local existing_rule=$(aws ec2 describe-security-groups \
        --group-ids "${SECURITY_GROUP_ID}" \
        --query "SecurityGroups[0].IpPermissions[?FromPort==\`${port}\` && ToPort==\`${port}\`]" \
        --output text 2>/dev/null)
    
    if [ -n "$existing_rule" ]; then
        echo -e "${YELLOW}⚠️  Port ${port} already open - skipping${NC}"
        return 0
    fi
    
    # Add the rule
    if aws ec2 authorize-security-group-ingress \
        --group-id "${SECURITY_GROUP_ID}" \
        --protocol tcp \
        --port "${port}" \
        --cidr "${cidr}" \
        --description "${description}" &> /dev/null; then
        echo -e "${GREEN}✅ Opened port ${port} - ${description}${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to open port ${port}${NC}"
        return 1
    fi
}

# Function to display manual instructions
show_manual_instructions() {
    echo ""
    echo -e "${YELLOW}=========================================="
    echo "   MANUAL AWS SECURITY GROUP SETUP"
    echo "==========================================${NC}"
    echo ""
    echo "1. Go to AWS Console → EC2 → Security Groups"
    echo "2. Find your EC2 instance's security group"
    echo "3. Click 'Edit inbound rules'"
    echo "4. Add these rules:"
    echo ""
    
    for port in "${!PORTS[@]}"; do
        echo "   • Type: Custom TCP"
        echo "     Port: ${port}"
        echo "     Source: 0.0.0.0/0 (or your IP for security)"
        echo "     Description: ${PORTS[$port]}"
        echo ""
    done
    
    echo -e "${YELLOW}⚠️  SECURITY WARNING:${NC}"
    echo "   For production, use your specific IP instead of 0.0.0.0/0"
    echo "   Example: 203.0.113.0/32 (your IP address)"
    echo ""
}

# Function to show SSH tunnel instructions
show_ssh_tunnel_instructions() {
    echo ""
    echo -e "${BLUE}=========================================="
    echo "   SECURE ALTERNATIVE: SSH TUNNELING"
    echo "==========================================${NC}"
    echo ""
    echo "Instead of opening ports, use SSH tunneling (more secure):"
    echo ""
    echo "ssh -L 3001:localhost:3001 \\"
    echo "    -L 9090:localhost:9090 \\"
    echo "    -L 9121:localhost:9121 \\"
    echo "    -L 9187:localhost:9187 \\"
    echo "    -L 9808:localhost:9808 \\"
    echo "    ubuntu@3.12.166.146"
    echo ""
    echo "Then access services locally:"
    echo "  • Grafana:      http://localhost:3001"
    echo "  • Prometheus:   http://localhost:9090"
    echo "  • Redis:        http://localhost:9121"
    echo "  • PostgreSQL:   http://localhost:9187"
    echo "  • Celery:       http://localhost:9808"
    echo ""
}

# Main execution
main() {
    echo ""
    
    # Show usage if requested
    if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        show_usage
        exit 0
    fi
    
    # Check prerequisites
    check_aws_cli
    check_aws_credentials
    
    echo ""
    
    # Determine instance and security group
    if [ -z "$INSTANCE_ID" ]; then
        echo "🔍 Attempting to detect instance information..."
        if ! get_instance_metadata; then
            echo -e "${YELLOW}⚠️  Could not auto-detect instance${NC}"
            echo ""
            echo "Please provide instance ID or security group ID:"
            show_usage
            show_manual_instructions
            show_ssh_tunnel_instructions
            exit 1
        fi
    fi
    
    if [ -z "$SECURITY_GROUP_ID" ] && [ -n "$INSTANCE_ID" ]; then
        echo "🔍 Getting security group from instance..."
        if ! get_security_group "$INSTANCE_ID"; then
            show_manual_instructions
            show_ssh_tunnel_instructions
            exit 1
        fi
    fi
    
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Instance ID:      ${INSTANCE_ID:-N/A}"
    echo "   Security Group:   ${SECURITY_GROUP_ID}"
    echo ""
    
    # Ask for confirmation
    echo -e "${YELLOW}⚠️  This will open ports to 0.0.0.0/0 (the entire internet)${NC}"
    echo -e "${YELLOW}⚠️  For production, consider using SSH tunneling instead${NC}"
    echo ""
    read -p "Do you want to proceed? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo ""
        echo "❌ Operation cancelled"
        show_ssh_tunnel_instructions
        exit 0
    fi
    
    # Add security rules
    echo ""
    echo "🔧 Adding security group rules..."
    echo ""
    
    for port in "${!PORTS[@]}"; do
        add_security_rule "$port" "${PORTS[$port]}"
    done
    
    echo ""
    echo -e "${GREEN}=========================================="
    echo "   ✅ SETUP COMPLETE"
    echo "==========================================${NC}"
    echo ""
    echo "You can now access:"
    for port in "${!PORTS[@]}"; do
        echo "  • ${PORTS[$port]}: http://3.12.166.146:${port}"
    done
    echo ""
    
    show_ssh_tunnel_instructions
}

# Run main function
main "$@"

