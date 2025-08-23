#!/usr/bin/env python3
"""
CloudFlare Origin Certificate Setup Guide
This creates the most secure setup with no browser warnings
"""

import requests
import json
import base64
from datetime import datetime, timedelta

# Your CloudFlare credentials
ZONE_ID = "7386179fad0d3712e5fbb97dc4868782"
EMAIL = "mayankroxx.25979@gmail.com"
API_KEY = "c5746279efa90a0b1b1330587749a8842d105"

HEADERS = {
    'X-Auth-Email': EMAIL,
    'X-Auth-Key': API_KEY,
    'Content-Type': 'application/json'
}

def create_origin_certificate():
    """Create CloudFlare origin certificate"""
    try:
        url = f"https://api.cloudflare.com/client/v4/certificates"
        
        # Certificate request data
        data = {
            "hostnames": ["cyberx.icu"],
            "requested_validity": 365,  # 1 year
            "request_type": "origin-rsa"
        }
        
        response = requests.post(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                cert_data = result['result']
                
                print("✅ Origin certificate created successfully!")
                print(f"Certificate ID: {cert_data['id']}")
                print(f"Expires: {cert_data['expires_on']}")
                
                # Save certificate and private key
                cert_content = cert_data['certificate']
                private_key = cert_data['private_key']
                
                print("\n📄 Saving certificate files...")
                
                # Save certificate
                with open('/tmp/cloudflare_origin.crt', 'w') as f:
                    f.write(cert_content)
                print("✅ Certificate saved: /tmp/cloudflare_origin.crt")
                
                # Save private key
                with open('/tmp/cloudflare_origin.key', 'w') as f:
                    f.write(private_key)
                print("✅ Private key saved: /tmp/cloudflare_origin.key")
                
                return True, cert_data['id']
            else:
                print(f"❌ Failed to create certificate: {result['errors']}")
                return False, None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return False, None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None

def update_nginx_config():
    """Generate updated nginx configuration"""
    
    nginx_config = """
# CloudFlare Origin Certificate Configuration for cyberx.icu
server {
    listen 80;
    server_name cyberx.icu;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cyberx.icu;
    
    # CloudFlare Origin Certificate
    ssl_certificate /etc/ssl/certs/cloudflare_origin.crt;
    ssl_certificate_key /etc/ssl/private/cloudflare_origin.key;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # API proxy
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization" always;
        
        # Handle preflight
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Root location
    location / {
        root /var/www/cyberx.icu;
        index index.html;
        try_files $uri $uri/ =404;
    }
}
"""
    
    return nginx_config

def set_ssl_mode_strict():
    """Set CloudFlare SSL mode to Full (strict)"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/ssl"
        data = {"value": "strict"}
        
        response = requests.patch(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ SSL mode set to 'Full (strict)'")
                return True
            else:
                print(f"❌ Failed to set SSL mode: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🛡️  CloudFlare Origin Certificate Setup")
    print("=" * 45)
    print("This will create the most secure SSL setup with no browser warnings")
    
    print("\n1️⃣ Creating CloudFlare origin certificate...")
    success, cert_id = create_origin_certificate()
    
    if success:
        print(f"\n2️⃣ Generating nginx configuration...")
        nginx_config = update_nginx_config()
        
        # Save nginx config
        with open('/tmp/cyberx.icu.conf', 'w') as f:
            f.write(nginx_config)
        print("✅ Nginx config saved: /tmp/cyberx.icu.conf")
        
        print(f"\n3️⃣ Installation steps:")
        print("Run these commands to install the certificates:")
        print(f"sudo cp /tmp/cloudflare_origin.crt /etc/ssl/certs/")
        print(f"sudo cp /tmp/cloudflare_origin.key /etc/ssl/private/")
        print(f"sudo chmod 644 /etc/ssl/certs/cloudflare_origin.crt")
        print(f"sudo chmod 600 /etc/ssl/private/cloudflare_origin.key")
        print(f"sudo cp /tmp/cyberx.icu.conf /etc/nginx/sites-available/")
        print(f"sudo ln -sf /etc/nginx/sites-available/cyberx.icu.conf /etc/nginx/sites-enabled/")
        print(f"sudo nginx -t && sudo systemctl reload nginx")
        
        print(f"\n4️⃣ Setting CloudFlare SSL mode to 'Full (strict)'...")
        if set_ssl_mode_strict():
            print("✅ SSL mode updated!")
        
        print(f"\n✅ Setup complete! Benefits:")
        print("- No more browser 'Dangerous' warnings")
        print("- Maximum security (Full strict mode)")
        print("- CloudFlare validates your certificate")
        print("- Certificate valid for 1 year")
        
    else:
        print("❌ Failed to create origin certificate")

if __name__ == "__main__":
    main()
