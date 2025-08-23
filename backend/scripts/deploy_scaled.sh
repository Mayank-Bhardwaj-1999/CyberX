#!/bin/bash
"""
Production Deployment Script for Scaled CyberX API
Handles 1000-2000 concurrent users with load balancing
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.scaled.yml"
NETWORK_NAME="cybersec-scaled-network"
BACKUP_DIR="/root/backups/$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}🚀 CyberX Scaled API Deployment${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Function to check system requirements
check_system_requirements() {
    print_info "Checking system requirements..."
    
    # Check available memory (need at least 4GB for scaled deployment)
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 4 ]; then
        print_warning "System has ${MEMORY_GB}GB RAM. Recommended: 4GB+ for optimal performance"
    else
        print_status "Memory check passed: ${MEMORY_GB}GB RAM available"
    fi
    
    # Check available disk space (need at least 10GB)
    DISK_GB=$(df -BG / | awk 'NR==2 {print int($4)}')
    if [ "$DISK_GB" -lt 10 ]; then
        print_error "Insufficient disk space: ${DISK_GB}GB available. Need at least 10GB"
        exit 1
    else
        print_status "Disk space check passed: ${DISK_GB}GB available"
    fi
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Function to backup current deployment
backup_current_deployment() {
    print_info "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup volumes
    if docker volume ls | grep -q "docker_postgres-data"; then
        print_info "Backing up PostgreSQL data..."
        docker run --rm -v docker_postgres-data:/data -v "$BACKUP_DIR":/backup alpine \
            tar czf /backup/postgres-data.tar.gz -C /data .
    fi
    
    if docker volume ls | grep -q "docker_redis-data"; then
        print_info "Backing up Redis data..."
        docker run --rm -v docker_redis-data:/data -v "$BACKUP_DIR":/backup alpine \
            tar czf /backup/redis-data.tar.gz -C /data .
    fi
    
    # Backup configurations
    cp -r /root/CyberX_backend/docker "$BACKUP_DIR/"
    cp -r /root/CyberX_backend/nginx "$BACKUP_DIR/"
    
    print_status "Backup created at: $BACKUP_DIR"
}

# Function to optimize system settings
optimize_system() {
    print_info "Optimizing system settings for high load..."
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" >> /etc/security/limits.conf
    echo "* hard nofile 65536" >> /etc/security/limits.conf
    echo "root soft nofile 65536" >> /etc/security/limits.conf
    echo "root hard nofile 65536" >> /etc/security/limits.conf
    
    # Optimize network settings
    cat >> /etc/sysctl.conf << EOF
# Network optimizations for high load
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_congestion_control = bbr
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 1024
net.ipv4.tcp_tw_reuse = 1
EOF
    
    # Apply sysctl settings
    sysctl -p
    
    print_status "System optimized for high load"
}

# Function to stop current services
stop_current_services() {
    print_info "Stopping current services..."
    
    cd /root/CyberX_backend/docker
    
    # Stop existing containers
    if [ -f docker-compose.yml ]; then
        docker-compose down 2>/dev/null || true
    fi
    
    if [ -f docker-compose.monitoring.yml ]; then
        docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true
    fi
    
    print_status "Current services stopped"
}

# Function to deploy scaled architecture
deploy_scaled_architecture() {
    print_info "Deploying scaled architecture..."
    
    cd /root/CyberX_backend/docker
    
    # Set environment variables
    export POSTGRES_PASSWORD="$(openssl rand -base64 32)"
    echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" > .env
    
    # Build and start services
    print_info "Building production images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --parallel
    
    print_info "Starting infrastructure services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d redis postgres rate-limiter
    
    # Wait for infrastructure to be ready
    print_info "Waiting for infrastructure to be ready..."
    sleep 30
    
    print_info "Starting API instances..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d cybersecurity-api-1 cybersecurity-api-2 cybersecurity-api-3
    
    # Wait for API instances to be ready
    print_info "Waiting for API instances to be ready..."
    sleep 45
    
    print_info "Starting load balancer..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d load-balancer
    
    print_status "Scaled architecture deployed successfully"
}

# Function to update nginx configuration
update_nginx_config() {
    print_info "Updating nginx configuration..."
    
    # Backup current nginx config
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)
    
    # Copy new configuration
    cp /root/CyberX_backend/nginx/nginx.conf /etc/nginx/nginx.conf
    
    # Test nginx configuration
    if nginx -t; then
        print_status "Nginx configuration is valid"
        systemctl reload nginx
        print_status "Nginx reloaded successfully"
    else
        print_error "Nginx configuration is invalid"
        # Restore backup
        cp /etc/nginx/nginx.conf.backup.* /etc/nginx/nginx.conf
        exit 1
    fi
}

# Function to run health checks
run_health_checks() {
    print_info "Running health checks..."
    
    # Check if containers are running
    CONTAINERS=("cybersecurity-fastapi-1" "cybersecurity-fastapi-2" "cybersecurity-fastapi-3" "cybersec-load-balancer" "cybersec-redis" "cybersec-postgres")
    
    for container in "${CONTAINERS[@]}"; do
        if docker ps | grep -q "$container"; then
            print_status "Container $container is running"
        else
            print_error "Container $container is not running"
            docker logs "$container" --tail 20
        fi
    done
    
    # Check API endpoints
    print_info "Testing API endpoints..."
    
    # Test load balancer
    if curl -f http://localhost:8090/health &>/dev/null; then
        print_status "Load balancer health check passed"
    else
        print_error "Load balancer health check failed"
    fi
    
    # Test through nginx (if running)
    if curl -f http://localhost/api/health &>/dev/null; then
        print_status "End-to-end health check passed"
    else
        print_warning "End-to-end health check failed (nginx might not be configured)"
    fi
    
    # Test external access (CloudFlare)
    if curl -f -k https://cyberx.icu/api/health &>/dev/null; then
        print_status "External access health check passed"
    else
        print_warning "External access health check failed (CloudFlare/DNS might need time to propagate)"
    fi
}

# Function to display deployment summary
show_deployment_summary() {
    echo
    echo -e "${GREEN}🎉 Deployment Complete!${NC}"
    echo "======================="
    echo
    echo -e "${BLUE}📊 Scaled Architecture Summary:${NC}"
    echo "• 3 FastAPI instances (load balanced)"
    echo "• HAProxy load balancer with health checks"
    echo "• Redis cache for API responses"
    echo "• PostgreSQL for analytics and rate limiting"
    echo "• Enhanced nginx with caching and rate limiting"
    echo
    echo -e "${BLUE}📈 Performance Capabilities:${NC}"
    echo "• Target: 1000-2000 concurrent users"
    echo "• Rate limiting: 30 requests/second per IP"
    echo "• Burst protection: 100 requests/10 seconds"
    echo "• Response caching: 5-10 minutes TTL"
    echo "• Auto-scaling ready architecture"
    echo
    echo -e "${BLUE}🔗 Access Points:${NC}"
    echo "• Load Balancer: http://localhost:8090"
    echo "• HAProxy Stats: http://localhost:8404/stats"
    echo "• Nginx Status: http://localhost:8081/nginx-status"
    echo "• External API: https://cyberx.icu/api/"
    echo
    echo -e "${BLUE}📋 Monitoring:${NC}"
    echo "• Real-time metrics: Prometheus + Grafana"
    echo "• Request analytics: PostgreSQL database"
    echo "• Performance logs: Container logs"
    echo "• Health monitoring: Built-in health checks"
    echo
    echo -e "${YELLOW}⚡ Next Steps:${NC}"
    echo "1. Monitor performance with: docker stats"
    echo "2. Check logs with: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "3. Scale if needed: docker-compose -f $DOCKER_COMPOSE_FILE up -d --scale cybersecurity-api-N=2"
    echo "4. Set up monitoring dashboard for production insights"
    echo
}

# Main execution
main() {
    check_system_requirements
    backup_current_deployment
    optimize_system
    stop_current_services
    deploy_scaled_architecture
    update_nginx_config
    run_health_checks
    show_deployment_summary
}

# Run main function
main "$@"
