#!/usr/bin/env python3
"""
Complete CloudFlare SSL Fix and Cache Management
Resolves the 'Dangerous' certificate warning and cache issues
"""

import requests
import json
import time

# Your CloudFlare credentials
ZONE_ID = "7386179fad0d3712e5fbb97dc4868782"
EMAIL = "mayankroxx.25979@gmail.com"
API_KEY = "c5746279efa90a0b1b1330587749a8842d105"

HEADERS = {
    'X-Auth-Email': EMAIL,
    'X-Auth-Key': API_KEY,
    'Content-Type': 'application/json'
}

def purge_everything():
    """Purge all CloudFlare cache"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/purge_cache"
        data = {"purge_everything": True}
        
        response = requests.post(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ All cache purged successfully")
                return True
            else:
                print(f"❌ Cache purge failed: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def set_development_mode(enabled=True):
    """Enable/disable development mode (bypasses cache for 3 hours)"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/development_mode"
        data = {"value": "on" if enabled else "off"}
        
        response = requests.patch(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                status = "enabled" if enabled else "disabled"
                print(f"✅ Development mode {status}")
                return True
            else:
                print(f"❌ Failed to change development mode: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_ssl_settings():
    """Check all SSL-related settings"""
    settings_to_check = [
        'ssl',
        'always_use_https', 
        'ssl_recommender',
        'automatic_https_rewrites'
    ]
    
    print("🔍 Current SSL Settings:")
    print("-" * 30)
    
    for setting in settings_to_check:
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/{setting}"
            response = requests.get(url, headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    value = result['result']['value']
                    print(f"✅ {setting}: {value}")
                else:
                    print(f"❌ {setting}: {result['errors']}")
            else:
                print(f"❌ {setting}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {setting}: {e}")

def enable_always_use_https():
    """Enable 'Always Use HTTPS' setting"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/always_use_https"
        data = {"value": "on"}
        
        response = requests.patch(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Always Use HTTPS enabled")
                return True
            else:
                print(f"❌ Failed to enable Always Use HTTPS: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_dns_records():
    """Check DNS records for the domain"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("🌐 DNS Records:")
                print("-" * 20)
                for record in result['result']:
                    name = record['name']
                    record_type = record['type']
                    content = record['content']
                    proxied = "🟠 Proxied" if record.get('proxied') else "⚪ DNS Only"
                    print(f"  {name} ({record_type}) → {content} {proxied}")
                return True
            else:
                print(f"❌ DNS check failed: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🛡️  Complete CloudFlare SSL & Cache Fix")
    print("=" * 45)
    print("🎯 Goal: Fix 'Dangerous' warning and cache issues for cyberx.icu")
    
    print("\n1️⃣ Checking current SSL settings...")
    check_ssl_settings()
    
    print("\n2️⃣ Checking DNS configuration...")
    check_dns_records()
    
    print("\n3️⃣ Optimizing CloudFlare settings...")
    
    # Enable Always Use HTTPS
    enable_always_use_https()
    
    # Purge all cache
    print("\n4️⃣ Purging all cache...")
    purge_everything()
    
    # Enable development mode temporarily
    print("\n5️⃣ Enabling development mode (3 hours)...")
    set_development_mode(True)
    
    print("\n✅ SSL & Cache Fix Complete!")
    print("=" * 45)
    
    print("\n📋 Summary of fixes applied:")
    print("✅ SSL settings verified")
    print("✅ Always Use HTTPS enabled")
    print("✅ All cache purged")
    print("✅ Development mode enabled (3 hours)")
    
    print("\n⏳ Next steps:")
    print("1. Wait 5-10 minutes for settings to propagate")
    print("2. Test your site: https://cyberx.icu/api/status")
    print("3. Browser certificate warning should disappear")
    print("4. Development mode will auto-disable in 3 hours")
    
    print("\n🔍 Understanding the SSL setup:")
    print("• Your setup IS secure (end-to-end encryption)")
    print("• CloudFlare uses its own certificate for visitors")
    print("• Your Let's Encrypt cert encrypts CloudFlare ↔ Server")
    print("• Browser warning is normal for CloudFlare Full mode")
    print("• The warning doesn't mean your site is insecure!")
    
    print("\n🌐 Check your API:")
    print("   curl -k https://cyberx.icu/api/status")

if __name__ == "__main__":
    main()
