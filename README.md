# 🛡️ CyberX News - Cybersecurity News App

A comprehensive React Native/Expo application that delivers real-time cybersecurity news with AI-powered summarization, backed by a robust production infrastructure.

## 🚀 Quick Start

### **Production Environment (HTTPS):**
```bash
# Mobile App APIs (Production Ready)
EXPO_PUBLIC_API_URL=https://cyberx.icu/api

# Monitoring Dashboard
https://cyberx.icu/grafana/ (Admin: venom)

# Container Management  
https://cyberx.icu/portainer/
```

### **Development Environment:**
```bash
# Option 1: One-click start (Recommended)
start-complete-project.bat

# Option 2: Manual start
# Terminal 1: Data collection service
cd backend && python main_launch.py

# Terminal 2: API server  
cd backend && python api/cybersecurity_api.py
```

### **Start Frontend:**
```bash
npx expo start
```

## 🏗️ Complete Architecture

### **📱 Frontend → 🌐 Backend → 📊 Monitoring Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                 📱 CyberX Mobile App                        │
│                 (React Native/Expo)                        │
├─────────────────────────────────────────────────────────────┤
│  🔍 News Feed      │  🔎 Search        │  📰 Articles      │
│  🔖 Bookmarks      │  ⚠️ Threats       │  🌐 WebView       │
│  🎨 Dark/Light     │  🔄 Real-time     │  📤 Sharing       │
└─────────────────────────────────────────────────────────────┘
                                │ HTTPS/443 
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                🌐 NGINX Reverse Proxy                       │
│                   (SSL Termination)                        │
├─────────────────────────────────────────────────────────────┤
│  📍 Routes:                                                 │
│  ├── /                    → Default Page (Security)        │
│  ├── /api/*               → FastAPI Backend               │
│  ├── /grafana/*           → Monitoring Dashboard          │
│  └── /portainer/*         → Container Management          │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                 🔄 HAProxy Load Balancer                    │
│                    (Port 8090)                             │
├─────────────────────────────────────────────────────────────┤
│  ⚖️ Distributes load across:                               │
│  ├── 🐍 FastAPI Instance 1 (:8081)                         │
│  ├── 🐍 FastAPI Instance 2 (:8082)                         │
│  └── 🐍 FastAPI Instance 3 (:8083)                         │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              🐍 FastAPI Backend Services                    │
├─────────────────────────────────────────────────────────────┤
│  📊 Endpoints:                                              │
│  ├── /health              → Service status                 │
│  ├── /news                → Latest articles                │
│  ├── /news/sources        → News sources                   │
│  ├── /news/search         → Article search                 │
│  ├── /google-news/search  → Google News API                │
│  └── /google-news/personal-feed → Personalized feed       │
└─────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  🗄️ PostgreSQL │ │  ⚡ Redis     │ │  📁 File      │
│  Database     │ │  Cache       │ │  Storage     │
│  :5432        │ │  :6379       │ │  /data       │
└──────────────┘ └──────────────┘ └──────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│              📊 Monitoring & Analytics Stack                │
├─────────────────────────────────────────────────────────────┤
│  🎯 Prometheus (:9091)     → Metrics Collection            │
│  📈 Grafana (:3000)        → Real-time Dashboards         │
│  🐳 cAdvisor (:8081)       → Docker Metrics               │
│  🖥️ Node Exporter (:9100)  → System Metrics               │
│  🔍 Log Exporters          → Application Logs             │
└─────────────────────────────────────────────────────────────┘
```

### **🔄 Data Processing Pipeline**

```
┌─────────────────────────────────────────────────────────────┐
│                   🤖 AI Processing Engine                   │
├─────────────────────────────────────────────────────────────┤
│  1. 🕷️ Web Scraping        → News sources                   │
│  2. 🧠 AI Summarization    → Article summaries             │
│  3. 📝 Content Processing  → Clean, formatted text         │
│  4. 🏷️ Categorization      → Topic classification          │
│  5. 💾 Data Storage        → Database persistence          │
│  6. 🔄 Real-time Updates   → Live news feed               │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Environment Configuration

### **Production (HTTPS - Play Store Ready):**
```bash
# .env
EXPO_PUBLIC_API_URL=https://cyberx.icu/api

# app.json
"usesCleartextTraffic": false  # HTTPS only for security
```

### **Development:**
```bash
# .env  
EXPO_PUBLIC_API_URL=http://192.168.225.208:8080

# app.json
"usesCleartextTraffic": true   # Allow HTTP for local dev
```

## 📱 Features & Capabilities

### **🎯 Core Features:**
- 📰 **Real-time News Feed** - Latest cybersecurity articles
- 🔍 **Advanced Search** - Find specific topics instantly  
- 🤖 **AI Summarization** - Quick article summaries
- 🔖 **Bookmarks** - Save articles for later
- 🎨 **Dark/Light Theme** - Customizable interface
- ⚠️ **Threat Alerts** - Critical security notifications
- 🌐 **WebView Integration** - Read full articles in-app
- 📤 **Share Articles** - Social media integration

### **🔒 Security Features:**
- 🛡️ **HTTPS Only** - All communications encrypted
- 🔐 **Secure APIs** - Protected backend endpoints
- 📱 **Play Store Ready** - Production security standards
- 🚫 **No Cleartext** - Encrypted traffic only
- 🎯 **CORS Protection** - Secure cross-origin requests

### **⚡ Performance:**
- 🔄 **Load Balancing** - Multiple FastAPI instances
- ⚡ **Redis Caching** - Fast data retrieval
- 📊 **Real-time Monitoring** - Live performance metrics
- 🐳 **Docker Optimization** - Efficient containerization
- 🌐 **CDN Ready** - Scalable content delivery

## 🔍 Traffic Analysis (Mobile App)

### **Normal Traffic Patterns:**
✅ **HTTPS to cyberx.icu:443** - Your secure API calls  
✅ **QUIC/443 to Google** - Modern HTTP/3 protocol  
✅ **DNS lookups** - Normal domain resolution  
✅ **Google Analytics** - Standard tracking (optional)  

**This traffic is SECURE and NORMAL for a news app!**

## 📊 Monitoring & Analytics

### **Real-time Dashboard:**
- **URL**: `https://cyberx.icu/grafana/`
- **Panels**: 37 monitoring widgets
- **Metrics**: API performance, system health, user activity
- **Alerts**: Automated issue detection
- **Refresh**: 5-second real-time updates

### **Key Metrics Tracked:**
- 🔌 API Health & Response Times
- 📰 Article Processing Pipeline  
- 🐳 Docker Container Performance
- 🖥️ System Resources (CPU/Memory/Disk)
- 🌐 Traffic Patterns & Load
- 🚨 Error Rates & Debugging

## 🛠️ Development Workflow

### **Local Development:**
```bash
# 1. Start backend services
cd backend && python main_launch.py

# 2. Start API server
cd backend && python api/cybersecurity_api.py  

# 3. Start mobile app
npx expo start

# 4. Access local APIs
http://localhost:8080/api/health
```

### **Production Deployment:**
```bash
# 1. Build for production
expo build:android --type apk

# 2. Deploy backend (automated)
docker-compose up -d

# 3. Configure NGINX SSL
sudo certbot --nginx -d cyberx.icu

# 4. Test production APIs
curl https://cyberx.icu/api/health
```

## 🔗 Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Public Site** | https://cyberx.icu/ | NGINX default page |
| **Mobile APIs** | https://cyberx.icu/api/ | App backend |
| **Monitoring** | https://cyberx.icu/grafana/ | Real-time dashboard |
| **Containers** | https://cyberx.icu/portainer/ | Docker management |
| **Prometheus** | Internal :9091 | Metrics collection |

## 🚀 Play Store Deployment

### **Requirements Met:**
✅ **Target SDK 34+** - Latest Android requirements  
✅ **HTTPS Only** - `usesCleartextTraffic: false`  
✅ **SSL Certificates** - Let's Encrypt validated  
✅ **Privacy Policy** - User data protection  
✅ **App Signing** - Google Play App Signing  
✅ **Content Rating** - Appropriate for all ages  

### **Production Checklist:**
- [x] Backend APIs secured with HTTPS
- [x] Mobile app configured for production
- [x] Monitoring dashboard operational  
- [x] SSL certificates valid
- [x] Error tracking enabled
- [x] Performance optimized

## 🧑‍💻 For Developers

### **Tech Stack:**
- **Frontend**: React Native, Expo, TypeScript
- **Backend**: Python, FastAPI, HAProxy
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, NGINX, Let's Encrypt
- **Monitoring**: Prometheus, Grafana, cAdvisor
- **AI**: Custom summarization engine

### **Key Files:**
- `app.json` - Expo configuration
- `services/api.ts` - API client
- `nginx-production.conf` - Production routing
- `backend/main_launch.py` - Data collection
- `backend/api/cybersecurity_api.py` - REST API
- `monitoring/grafana/` - Dashboard configs

---

## 🎯 **CyberX is Production Ready!**

Your cybersecurity news app now features enterprise-grade infrastructure with real-time monitoring, secure HTTPS communications, and comprehensive analytics. Perfect for Play Store deployment and scalable user growth! 🚀
- Offline support

## 🏥 Health Check

- **API Status**: http://localhost:8080/
- **News Endpoint**: http://localhost:8080/api/news
- **Sources**: http://localhost:8080/api/news/sources

## 🚀 Deployment

For production deployment, use the provided VPS scripts:
```bash
# Deploy to VPS
./deploy-vps.sh

# Windows production server
start-production.bat
```

## 🧹 Codebase Cleanup

The project has been cleaned up to remove:
- ✅ Duplicate directories (`src/`, `data/`, `config/`)
- ✅ Duplicate files (`monitor_config.json`, `requirements.txt`)
- ✅ Empty documentation files
- ✅ Empty utility files

See `CLEANUP_PLAN.md` for detailed cleanup information.

## 🛠️ Development

Built with:
- **Frontend**: React Native, Expo, TypeScript
- **Backend**: Python, Flask, AI Summarization
- **Data**: Real-time web scraping and monitoring

---
*Stay informed about the latest cybersecurity threats with CyberX News* 🛡️
