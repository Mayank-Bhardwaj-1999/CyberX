#!/usr/bin/env python3
"""
Quick SSL Mode Fix using Global API Key
"""

import requests
import json

# Your CloudFlare credentials
ZONE_ID = "7386179fad0d3712e5fbb97dc4868782"
ACCOUNT_ID = "611478465d4e849c595ce1c53bce2cb0"

def get_auth_headers():
    """Get auth headers - you'll need to add your email and global API key"""
    # You can either:
    # 1. Set environment variables: CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY
    # 2. Or replace these with your actual values
    
    import os
    email = os.getenv('CLOUDFLARE_EMAIL')
    api_key = os.getenv('CLOUDFLARE_API_KEY')
    
    if not email or not api_key:
        print("⚠️  Please set CloudFlare credentials:")
        email = input("Enter your CloudFlare email: ").strip()
        api_key = input("Enter your CloudFlare Global API Key: ").strip()
    
    return {
        'X-Auth-Email': email,
        'X-Auth-Key': api_key,
        'Content-Type': 'application/json'
    }

def get_current_ssl_mode():
    """Check current SSL mode"""
    try:
        headers = get_auth_headers()
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/ssl"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                mode = data['result']['value']
                print(f"✅ Current SSL mode: {mode}")
                return mode, headers
            else:
                print(f"❌ API Error: {data['errors']}")
                return None, None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return None, None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None, None

def set_ssl_mode(mode, headers):
    """Set SSL mode"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/settings/ssl"
        data = {"value": mode}
        
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print(f"✅ SSL mode changed to: {mode}")
                return True
            else:
                print(f"❌ Failed: {result['errors']}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🛡️  Quick SSL Mode Fix for cyberx.icu")
    print("=" * 45)
    
    # Check current mode
    current_mode, headers = get_current_ssl_mode()
    
    if not headers:
        print("❌ Failed to authenticate with CloudFlare")
        return
    
    print(f"\n📋 Current SSL mode: {current_mode}")
    print("\n🔍 SSL Mode Options:")
    print("- 'flexible': CloudFlare ↔ Visitor (HTTPS), CloudFlare ↔ Server (HTTP)")
    print("- 'full': CloudFlare ↔ Visitor (HTTPS), CloudFlare ↔ Server (HTTPS, any cert)")
    print("- 'strict': CloudFlare ↔ Visitor (HTTPS), CloudFlare ↔ Server (HTTPS, valid cert)")
    
    print(f"\n🚨 Issue: Your browser shows 'Dangerous' because:")
    print(f"   - CloudFlare is presenting its own certificate to visitors")
    print(f"   - Your Let's Encrypt cert is only used for CloudFlare ↔ Server")
    print(f"   - Browser expects to see Let's Encrypt but gets CloudFlare cert")
    
    print(f"\n💡 Solutions:")
    print("1. Keep current setup (SSL works, ignore browser warning)")
    print("2. Switch to 'flexible' mode (less secure but no warnings)")
    print("3. Use CloudFlare origin certificate on server")
    
    choice = input("\nChoose solution (1-3) or 'q' to quit: ").strip()
    
    if choice == "1":
        print("✅ Current setup is actually secure!")
        print("   - Traffic to visitors is encrypted (CloudFlare cert)")
        print("   - Traffic to server is encrypted (Let's Encrypt cert)")
        print("   - Browser warning is cosmetic issue")
        print("\n🔄 To remove warning, purge cache and wait for propagation:")
        purge_cache(headers)
        
    elif choice == "2":
        print("\n⚠️  Switching to 'flexible' mode...")
        print("   - Less secure: CloudFlare ↔ Server will be HTTP")
        print("   - But removes browser warnings")
        
        confirm = input("Confirm switch to flexible? (y/N): ").strip().lower()
        if confirm == 'y':
            if set_ssl_mode("flexible", headers):
                print("✅ Changed to flexible mode")
                print("⏳ Wait 5-10 minutes for propagation")
                purge_cache(headers)
        
    elif choice == "3":
        print("\n📋 To use CloudFlare origin certificate:")
        print("1. Go to CloudFlare dashboard > SSL/TLS > Origin Server")
        print("2. Create Origin Certificate")
        print("3. Download and install on your server")
        print("4. Update nginx to use CloudFlare cert")
        print("5. Set SSL mode to 'Full (strict)'")
        
    else:
        print("👋 Exiting...")

def purge_cache(headers):
    """Purge all cache"""
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/purge_cache"
        data = {"purge_everything": True}
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ Cache purged successfully")
            else:
                print(f"❌ Cache purge failed: {result['errors']}")
        else:
            print(f"❌ Cache purge HTTP error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Cache purge exception: {e}")

if __name__ == "__main__":
    main()
