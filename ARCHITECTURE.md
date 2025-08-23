# 🏗️ CyberX Architecture Documentation

## 📋 **System Overview**

CyberX is a production-ready cybersecurity news application with enterprise-grade infrastructure, featuring real-time monitoring, secure communications, and scalable architecture.

## 🔄 **Complete Data Flow**

```
📱 Mobile App (React Native/Expo)
    ↓ HTTPS/443 (Secure)
🌐 NGINX Reverse Proxy (SSL Termination)
    ↓ Load Distribution
🔄 HAProxy Load Balancer (3 Instances)
    ↓ API Requests
🐍 FastAPI Backend Services
    ↓ Data Operations
🗄️ PostgreSQL + Redis + File Storage
    ↓ Metrics Collection
📊 Prometheus + Grafana Monitoring
```

## 🛡️ **Security Architecture**

### **Network Security:**
- **SSL/TLS Encryption** - Let's Encrypt certificates
- **HSTS Headers** - Force HTTPS connections
- **CORS Protection** - Secure cross-origin requests
- **Rate Limiting** - DDoS protection
- **Hidden Admin Interfaces** - Security through obscurity

### **Application Security:**
- **HTTPS Only** - `usesCleartextTraffic: false`
- **API Authentication** - Secure endpoint access
- **Input Validation** - SQL injection prevention
- **Error Handling** - No sensitive data exposure

## 🐳 **Container Architecture**

### **Production Stack:**
```yaml
cybersec-network:
  ├── cybersecurity-fastapi-1 (:8081)
  ├── cybersecurity-fastapi-2 (:8082)  
  ├── cybersecurity-fastapi-3 (:8083)
  ├── cybersec-haproxy (:8090)
  ├── cybersec-grafana (:3000)
  ├── cybersec-prometheus (:9091)
  ├── cybersec-cadvisor (:8081)
  ├── cybersec-node-exporter (:9100)
  ├── cybersec-postgres (:5432)
  ├── cybersec-redis (:6379)
  └── cybersec-portainer (:9443)
```

### **Resource Allocation:**
- **CPU**: Load balanced across 3 FastAPI instances
- **Memory**: Redis caching for performance
- **Storage**: Persistent volumes for data
- **Network**: Isolated Docker networks

## 📊 **Monitoring Infrastructure**

### **Metrics Collection:**
- **Prometheus** - Time-series metrics database
- **Node Exporter** - System metrics (CPU, memory, disk)
- **cAdvisor** - Docker container metrics
- **Custom Exporters** - Application-specific metrics

### **Visualization:**
- **Grafana Dashboard** - Real-time monitoring
- **37 Monitoring Panels** - Comprehensive coverage
- **5-second Refresh** - Live updates
- **Custom Alerts** - Proactive issue detection

### **Key Performance Indicators:**
```
🔌 API Health Status
📰 Article Processing Rate  
🐳 Container Performance
🖥️ System Resources
🌐 Traffic Patterns
🚨 Error Rates
⚡ Response Times
💾 Storage Usage
```

## 🔌 **API Architecture**

### **Endpoint Structure:**
```
https://cyberx.icu/api/
├── /health                 → Service status
├── /news                   → Latest articles
├── /news/sources           → Available sources
├── /news/search            → Article search
├── /google-news/search     → Google News API
├── /google-news/personal-feed → Personalized content
├── /stats                  → Usage statistics
└── /config                 → App configuration
```

### **Response Format:**
```json
{
  "status": "success",
  "data": [...],
  "timestamp": "2025-08-23T...",
  "total": 150,
  "page": 1,
  "limit": 25
}
```

## 📱 **Mobile App Architecture**

### **Component Structure:**
```
app/
├── (tabs)/
│   ├── index.tsx           → News Feed
│   ├── search.tsx          → Search Interface  
│   └── threat-alerts.tsx   → Security Alerts
├── article/
│   └── [id].tsx           → Article Detail
├── components/
│   ├── NewsCard.tsx       → Article Display
│   ├── SearchBar.tsx      → Search Input
│   └── ThemeToggle.tsx    → Dark/Light Mode
├── services/
│   ├── api.ts             → API Client
│   ├── storage.ts         → Local Storage
│   └── notifications.ts   → Push Notifications
└── types/
    └── news.ts            → TypeScript Definitions
```

### **State Management:**
- **Context API** - Global state management
- **AsyncStorage** - Local data persistence
- **Real-time Updates** - Live news feed
- **Offline Support** - Cached content access

## 🔄 **Data Processing Pipeline**

### **News Collection:**
```
1. 🕷️ Web Scraping → Multiple news sources
2. 📝 Content Extraction → Clean article text  
3. 🤖 AI Summarization → Generate summaries
4. 🏷️ Categorization → Topic classification
5. 💾 Database Storage → PostgreSQL persistence
6. ⚡ Cache Updates → Redis optimization
7. 📱 API Delivery → Mobile app consumption
```

### **Real-time Processing:**
- **Scheduled Tasks** - Automated news collection
- **Queue Management** - Efficient task processing  
- **Error Handling** - Robust failure recovery
- **Performance Optimization** - Caching strategies

## 🌐 **Network Architecture**

### **NGINX Configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name cyberx.icu;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/cyberx.icu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cyberx.icu/privkey.pem;
    
    # Mobile App APIs
    location /api/ {
        proxy_pass http://localhost:8090;
        add_header Access-Control-Allow-Origin "*" always;
    }
    
    # Monitoring Dashboard  
    location /grafana/ {
        proxy_pass http://localhost:3000/grafana/;
    }
    
    # Default Security Page
    location / {
        root /var/www/html;
        index index.nginx-debian.html;
    }
}
```

### **Load Balancing:**
```
HAProxy Configuration:
├── Frontend: :8090
├── Backend Pool:
│   ├── fastapi-1:8081 (weight 1)
│   ├── fastapi-2:8082 (weight 1)  
│   └── fastapi-3:8083 (weight 1)
├── Health Checks: /health endpoint
└── Failover: Automatic instance switching
```

## 📊 **Performance Specifications**

### **Scalability Metrics:**
- **Concurrent Users**: 1000+ simultaneous  
- **API Throughput**: 500+ requests/second
- **Response Time**: <200ms average
- **Uptime**: 99.9% availability target
- **Data Processing**: 10K+ articles/day

### **Resource Requirements:**
- **CPU**: 4 cores minimum
- **RAM**: 8GB minimum  
- **Storage**: 100GB SSD
- **Bandwidth**: 1Gbps connection
- **SSL Certificates**: Auto-renewal enabled

## 🚀 **Deployment Architecture**

### **Production Environment:**
```
🌍 Internet Traffic
    ↓
🔒 Cloudflare/CDN (Optional)
    ↓ 
🌐 NGINX Reverse Proxy
    ↓
🔄 HAProxy Load Balancer
    ↓
🐳 Docker Swarm/Compose
    ↓
🖥️ VPS/Cloud Infrastructure
```

### **CI/CD Pipeline:**
1. **Code Commit** → GitHub repository
2. **Automated Testing** → Unit/Integration tests
3. **Build Process** → Docker image creation
4. **Deployment** → Production environment
5. **Health Checks** → Service validation
6. **Monitoring** → Real-time alerting

## 🔧 **Maintenance & Operations**

### **Regular Maintenance:**
- **SSL Certificate Renewal** - Automated via Certbot
- **Database Backups** - Daily PostgreSQL dumps
- **Log Rotation** - Automated cleanup  
- **Security Updates** - Regular Docker image updates
- **Performance Monitoring** - Grafana dashboards

### **Troubleshooting:**
```bash
# Service Health
docker ps --format "table {{.Names}}\t{{.Status}}"

# API Testing  
curl https://cyberx.icu/api/health

# Log Analysis
docker logs cybersec-grafana
sudo tail -f /var/log/nginx/access.log

# Performance Metrics
https://cyberx.icu/grafana/
```

---

## 🎯 **Architecture Benefits**

✅ **Scalability** - Load balanced, containerized services  
✅ **Reliability** - High availability with failover  
✅ **Security** - Multi-layer protection  
✅ **Monitoring** - Comprehensive observability  
✅ **Performance** - Optimized for speed  
✅ **Maintainability** - Clear separation of concerns  

**CyberX represents a production-grade architecture suitable for enterprise deployment and user growth!** 🚀
