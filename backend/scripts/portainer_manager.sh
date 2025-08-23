#!/bin/bash

# CyberX Portainer Management Script
# Usage: ./portainer_manager.sh [start|stop|restart|logs|status]

CONTAINER_NAME="cybersec-portainer"
COMPOSE_FILE="/root/CyberX_backend/docker/docker-compose.monitoring.yml"

case $1 in
    "start")
        echo "🚀 Starting Portainer..."
        cd /root/CyberX_backend/docker
        docker-compose -f docker-compose.monitoring.yml up -d portainer
        echo "✅ Portainer started!"
        echo "🌐 Access at: https://cyberx.icu/portainer/"
        ;;
    
    "stop")
        echo "🛑 Stopping Portainer..."
        docker stop $CONTAINER_NAME
        echo "✅ Portainer stopped!"
        ;;
    
    "restart")
        echo "🔄 Restarting Portainer..."
        docker restart $CONTAINER_NAME
        echo "✅ Portainer restarted!"
        echo "🌐 Access at: https://cyberx.icu/portainer/"
        ;;
    
    "logs")
        echo "📋 Portainer logs (press Ctrl+C to exit):"
        docker logs -f $CONTAINER_NAME
        ;;
    
    "status")
        echo "📊 Portainer Status:"
        docker ps | grep portainer
        echo ""
        echo "🌐 Access URLs:"
        echo "  - Primary: https://cyberx.icu/portainer/"
        echo "  - Direct HTTPS: https://cyberx.icu:9443"
        echo "  - Direct HTTP: http://cyberx.icu:9000"
        ;;
    
    "update")
        echo "⬇️ Updating Portainer to latest version..."
        docker stop $CONTAINER_NAME
        docker rm $CONTAINER_NAME
        docker pull portainer/portainer-ce:latest
        cd /root/CyberX_backend/docker
        docker-compose -f docker-compose.monitoring.yml up -d portainer
        echo "✅ Portainer updated and restarted!"
        ;;
    
    "backup")
        echo "💾 Creating Portainer data backup..."
        BACKUP_DIR="/root/CyberX_backend/backups/portainer_$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        docker run --rm -v docker_portainer_data:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/portainer_data.tar.gz -C /data .
        echo "✅ Backup created at: $BACKUP_DIR/portainer_data.tar.gz"
        ;;
    
    *)
        echo "🐳 CyberX Portainer Management"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Start Portainer container"
        echo "  stop      - Stop Portainer container" 
        echo "  restart   - Restart Portainer container"
        echo "  logs      - View live logs"
        echo "  status    - Show current status and URLs"
        echo "  update    - Update to latest Portainer version"
        echo "  backup    - Backup Portainer data"
        echo ""
        echo "🌐 Current Access: https://cyberx.icu/portainer/"
        ;;
esac
