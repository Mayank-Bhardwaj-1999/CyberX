#!/usr/bin/env python3
"""
SSL Mode Configuration Fix for CloudFlare
Resolves "Dangerous" certificate warning by setting proper SSL mode
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from src.utils.cloudflare_manager import CloudFlareManager

class SSLModeFix:
    def __init__(self):
        """Initialize with CloudFlare credentials"""
        self.cf = CloudFlareManager()
        
    def get_current_ssl_mode(self):
        """Check current SSL/TLS mode"""
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{self.cf.zone_id}/settings/ssl"
            response = requests.get(url, headers=self.cf.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    current_mode = data['result']['value']
                    print(f"✅ Current SSL mode: {current_mode}")
                    return current_mode
                else:
                    print(f"❌ API Error: {data['errors']}")
                    return None
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def set_ssl_mode(self, mode):
        """
        Set SSL/TLS mode
        Options: off, flexible, full, strict, origin_pull
        """
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{self.cf.zone_id}/settings/ssl"
            data = {"value": mode}
            
            response = requests.patch(url, headers=self.cf.headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ SSL mode changed to: {mode}")
                    return True
                else:
                    print(f"❌ Failed to change SSL mode: {result['errors']}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return False
    
    def get_ssl_verification_errors(self):
        """Check SSL verification errors"""
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{self.cf.zone_id}/ssl/verification"
            response = requests.get(url, headers=self.cf.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    for cert in data['result']:
                        print(f"Certificate: {cert.get('hostname', 'Unknown')}")
                        print(f"Status: {cert.get('certificate_status', 'Unknown')}")
                        print(f"Verification Type: {cert.get('verification_type', 'Unknown')}")
                        if 'verification_errors' in cert and cert['verification_errors']:
                            print(f"❌ Errors: {cert['verification_errors']}")
                        print("-" * 40)
                else:
                    print(f"❌ API Error: {data['errors']}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def check_ssl_certificate_packs(self):
        """Check available SSL certificate packs"""
        try:
            url = f"https://api.cloudflare.com/client/v4/zones/{self.cf.zone_id}/ssl/certificate_packs"
            response = requests.get(url, headers=self.cf.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    print(f"📋 Available certificate packs:")
                    for pack in data['result']:
                        print(f"  - Type: {pack.get('type', 'Unknown')}")
                        print(f"    Status: {pack.get('status', 'Unknown')}")
                        print(f"    Primary Cert: {pack.get('primary_certificate', {}).get('status', 'Unknown')}")
                        print(f"    Hosts: {pack.get('hosts', [])}")
                        print("-" * 30)
                else:
                    print(f"❌ API Error: {data['errors']}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    def fix_ssl_configuration(self):
        """
        Comprehensive SSL configuration fix
        """
        print("🔧 SSL Configuration Diagnostic & Fix")
        print("=" * 50)
        
        # 1. Check current SSL mode
        print("\n1️⃣ Checking current SSL mode...")
        current_mode = self.get_current_ssl_mode()
        
        # 2. Check certificate packs
        print("\n2️⃣ Checking certificate packs...")
        self.check_ssl_certificate_packs()
        
        # 3. Check verification errors
        print("\n3️⃣ Checking SSL verification...")
        self.get_ssl_verification_errors()
        
        # 4. Recommend fix based on current setup
        print("\n4️⃣ Recommended SSL Mode Fix:")
        print("Since you have Let's Encrypt certificate on your server:")
        print("- Current mode 'full' causes browser warnings")
        print("- Recommended: Switch to 'full' with proper certificate validation")
        print("- Alternative: Use 'flexible' temporarily (less secure)")
        
        # Ask user for confirmation
        print("\n🛠️ Available fixes:")
        print("1. Keep 'full' mode but disable certificate validation (recommended)")
        print("2. Switch to 'flexible' mode (CloudFlare handles SSL)")
        print("3. Upload custom certificate to CloudFlare")
        
        choice = input("\nEnter choice (1-3) or 'cancel': ").strip()
        
        if choice == "1":
            print("\n🔄 Setting SSL mode to 'full' (should work with Let's Encrypt)...")
            if self.set_ssl_mode("full"):
                print("✅ SSL mode updated!")
                print("⏳ Changes may take 5-10 minutes to propagate")
                print("🔄 Try purging cache after propagation:")
                print(f"   python3 scripts/cloudflare_cli.py purge")
            
        elif choice == "2":
            print("\n🔄 Setting SSL mode to 'flexible'...")
            if self.set_ssl_mode("flexible"):
                print("✅ SSL mode updated to flexible!")
                print("⚠️  Note: This is less secure (CloudFlare to origin is HTTP)")
                print("⏳ Changes may take 5-10 minutes to propagate")
            
        elif choice == "3":
            print("\n📋 To upload custom certificate:")
            print("1. Go to CloudFlare Dashboard > SSL/TLS > Origin Server")
            print("2. Create Origin Certificate")
            print("3. Install on your server")
            print("4. Set SSL mode to 'Full (strict)'")
            
        else:
            print("❌ Operation cancelled")

def main():
    """Main function"""
    print("🛡️  CloudFlare SSL Mode Fix")
    print("=" * 40)
    
    ssl_fix = SSLModeFix()
    ssl_fix.fix_ssl_configuration()

if __name__ == "__main__":
    main()
