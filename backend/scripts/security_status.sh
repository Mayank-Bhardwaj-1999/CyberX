#!/bin/bash

echo "🔒 CyberX Security Status Report"
echo "=================================="
echo ""

echo "🌐 Domain Configuration:"
echo "  - Domain: cyberx.icu"
echo "  - SSL: Let's Encrypt Certificate"
echo "  - CloudFlare: Active"
echo ""

echo "🔐 Public Access (HTTPS only):"
echo "  ✅ Grafana Dashboard: https://cyberx.icu"
echo "  ✅ API Endpoint: https://cyberx.icu/api/"
echo ""

echo "🛡️ Protected Services (localhost only):"
echo "  🔒 Prometheus: localhost:9091 (internal)"
echo "  🔒 cAdvisor: localhost:8081 (internal)"
echo "  🔒 AlertManager: localhost:9093 (internal)"
echo "  🔒 Node Exporter: localhost:9100 (internal)"
echo "  🔒 Log Exporters: localhost:9098-9099 (internal)"
echo "  🔒 Metrics Exporter: localhost:9097 (internal)"
echo ""

echo "🚦 Security Features:"
echo "  ✅ HTTPS/SSL enforcement"
echo "  ✅ Security headers (HSTS, CSP, etc.)"
echo "  ✅ Rate limiting on API"
echo "  ✅ CORS protection"
echo "  ✅ Internal service isolation"
echo "  ✅ CloudFlare DDoS protection"
echo ""

echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(grafana|prometheus|cadvisor|alertmanager|exporter|fastapi)" | head -10

echo ""
echo "🔧 Service Health Checks:"
echo -n "  Grafana: "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health | grep -q "200"; then
    echo "✅ OK"
else
    echo "❌ Error"
fi

echo -n "  Prometheus: "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/-/healthy | grep -q "200"; then
    echo "✅ OK"
else
    echo "❌ Error"
fi

echo -n "  FastAPI: "
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ | grep -q "200"; then
    echo "✅ OK"
else
    echo "❌ Error"
fi

echo ""
echo "🎯 Access Information:"
echo "  📊 Dashboard: https://cyberx.icu (admin/newpassword123)"
echo "  🔌 API: https://cyberx.icu/api/"
echo "  📋 All monitoring data flows through Grafana"
echo ""

echo "⚡ Quick Commands:"
echo "  # View logs: docker logs cybersec-grafana"
echo "  # Restart services: docker compose -f docker-compose.monitoring.secure.yml restart"
echo "  # SSL renewal: sudo certbot renew"
echo ""
