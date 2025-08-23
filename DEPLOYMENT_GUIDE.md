# 🛡️ CyberX Production Deployment Guide

## 🚀 Complete HTTPS Migration & Security Setup

### 📋 **Fixed Issues & Solutions**

#### 1. **HTTP to HTTPS Migration** ✅
- **Problem**: 401 Unauthorized errors after HTTPS migration for Play Store deployment
- **Root Cause**: NGINX routing configuration sending API requests to wrong services
- **Solution**: Proper NGINX routing with `/api/*` → FastAPI backend

#### 2. **NGINX Configuration** ✅
- **Problem**: Complex subdomain setup causing redirect loops
- **Solution**: Simple, robust proxy configuration
- **Config**: `/etc/nginx/sites-available/cyberx.icu`

#### 3. **Grafana Dashboard** ✅
- **Problem**: Sub-path routing and datasource connectivity issues
- **Solution**: Proper Docker network configuration with Prometheus connection

### 🏗️ **Final Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    NGINX Reverse Proxy                     │
│                  (SSL Termination)                         │
├─────────────────────────────────────────────────────────────┤
│  https://cyberx.icu/                                       │
│  ├── /                    → NGINX Default Page (Security)   │
│  ├── /api/*               → FastAPI Backend :8090          │
│  ├── /grafana/*           → Grafana Dashboard :3000        │
│  └── /portainer/*         → Portainer :9443                │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                   Docker Infrastructure                     │
├─────────────────────────────────────────────────────────────┤
│  🔄 HAProxy Load Balancer                                   │
│  ├── FastAPI Instance 1 :8081                              │
│  ├── FastAPI Instance 2 :8082                              │
│  └── FastAPI Instance 3 :8083                              │
│                                                             │
│  📊 Monitoring Stack                                        │
│  ├── Prometheus :9091                                       │
│  ├── Grafana :3000                                          │
│  ├── cAdvisor :8081                                         │
│  └── Node Exporter :9100                                    │
│                                                             │
│  🗄️ Data Layer                                              │
│  ├── PostgreSQL :5432                                       │
│  ├── Redis :6379                                            │
│  └── Portainer :9443                                        │
└─────────────────────────────────────────────────────────────┘
```

### 🔧 **Production Configuration Files**

#### NGINX Production Config (`nginx-production.conf`)
```nginx
# Mobile App API Routes → FastAPI Backend
location /api/ {
    proxy_pass http://localhost:8090;
    # CORS for mobile app
    add_header Access-Control-Allow-Origin "*" always;
}

# Grafana Dashboard (Secured Path)
location /grafana/ {
    proxy_pass http://localhost:3000/grafana/;
    # WebSocket support for real-time monitoring
}

# Default NGINX page (Security)
location / {
    root /var/www/html;
    index index.nginx-debian.html;
}
```

#### Docker Compose Monitoring Stack
```yaml
services:
  grafana:
    image: grafana/grafana:latest
    container_name: cybersec-grafana
    environment:
      - GF_SECURITY_ADMIN_USER=venom
      - GF_SECURITY_ADMIN_PASSWORD=Youcanneverseeme@125270
      - GF_SERVER_ROOT_URL=https://cyberx.icu/grafana
      - GF_SERVER_SERVE_FROM_SUB_PATH=true
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - docker_cybersec-network
```

### 📱 **Mobile App Configuration**

#### app.json (HTTPS Only)
```json
{
  "expo": {
    "plugins": [
      [
        "expo-build-properties",
        {
          "android": {
            "usesCleartextTraffic": false
          }
        }
      ]
    ]
  }
}
```

#### API Service Configuration
```typescript
// services/googleNewsService.ts
const API_BASE_URL = 'https://cyberx.icu/api';

// Removed API key authentication (not needed)
// Clean HTTP requests to backend
```

### 🛡️ **Security Features**

1. **SSL/TLS Encryption** - Let's Encrypt certificates
2. **HSTS Headers** - Force HTTPS connections
3. **Hidden Admin Interfaces** - Grafana at `/grafana/`, Portainer at `/portainer/`
4. **CORS Configuration** - Proper mobile app access
5. **Rate Limiting** - Protection against abuse
6. **Professional Public Face** - Default NGINX page

### 🔗 **Access URLs**

- **Public**: `https://cyberx.icu/` (NGINX default page)
- **Mobile APIs**: `https://cyberx.icu/api/*`
- **Monitoring**: `https://cyberx.icu/grafana/` (admin only)
- **Container Mgmt**: `https://cyberx.icu/portainer/` (admin only)

### 📊 **Monitoring Dashboard**

**Grafana Login:**
- Username: `venom`
- Password: `Youcanneverseeme@125270`
- Dashboard: "🛡️ Cybersecurity Backend & Docker Monitoring"
- Features: 37 real-time monitoring panels

### ✅ **Verification Commands**

```bash
# Test mobile app APIs
curl -s https://cyberx.icu/api/health | jq '.status'

# Test Google News search
curl -X POST "https://cyberx.icu/api/google-news/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "cybersecurity", "limit": 5}'

# Check SSL certificate
curl -I https://cyberx.icu/

# Monitor services
docker ps | grep -E "(grafana|prometheus|fastapi)"
```

### 🚨 **Troubleshooting**

#### Common Issues:
1. **404 on /grafana/**: Check container network and proxy_pass URL
2. **CORS errors**: Verify NGINX CORS headers
3. **Redirect loops**: Ensure proper GF_SERVER_ROOT_URL configuration
4. **Dashboard not loading**: Verify volume mounts and provisioning

#### Quick Fixes:
```bash
# Restart NGINX
sudo systemctl reload nginx

# Restart Grafana
docker restart cybersec-grafana

# Check logs
docker logs cybersec-grafana
sudo tail -f /var/log/nginx/error.log
```

### 📈 **Performance Optimizations**

1. **HAProxy Load Balancing** - 3 FastAPI instances
2. **Redis Caching** - Fast data retrieval
3. **NGINX Compression** - Reduced bandwidth
4. **Docker Networks** - Isolated container communication
5. **Real-time Monitoring** - Prometheus metrics

---

## 🎯 **Play Store Ready**

✅ **HTTPS Only** - `usesCleartextTraffic: false`  
✅ **Secure APIs** - All endpoints encrypted  
✅ **SSL Certificates** - Let's Encrypt validated  
✅ **CORS Configured** - Mobile app compatibility  
✅ **Production Monitoring** - Real-time dashboards  

**Your CyberX app is now production-ready for Play Store deployment!** 🚀
