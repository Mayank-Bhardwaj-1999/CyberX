#!/usr/bin/env python3
"""
CloudFlare Cache CLI for CyberX
==============================

Command-line interface for managing CloudFlare cache and settings.

Usage:
    python cloudflare_cli.py --help
    python cloudflare_cli.py status
    python cloudflare_cli.py purge
    python cloudflare_cli.py cache-level aggressive
    python cloudflare_cli.py dev-mode on
    python cloudflare_cli.py deploy-setup
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.cloudflare_manager import CloudFlareManager

def setup_api_token():
    """Setup API token if not configured"""
    token = os.getenv('CLOUDFLARE_API_TOKEN')
    if not token:
        print("❌ CloudFlare API token not found!")
        print()
        print("Please set your API token using one of these methods:")
        print()
        print("1. Environment variable:")
        print("   export CLOUDFLARE_API_TOKEN='your_token_here'")
        print()
        print("2. Config file:")
        print("   echo 'API_TOKEN=your_token_here' > /root/CyberX_backend/config/cloudflare.conf")
        print()
        print("3. Provide token when prompted:")
        token = input("Enter your CloudFlare API token: ").strip()
        
        if token:
            # Save to config file
            config_dir = Path('/root/CyberX_backend/config')
            config_dir.mkdir(exist_ok=True)
            config_file = config_dir / 'cloudflare.conf'
            
            with open(config_file, 'w') as f:
                f.write(f"API_TOKEN={token}\n")
            
            print(f"✅ Token saved to {config_file}")
            os.environ['CLOUDFLARE_API_TOKEN'] = token
            return token
        else:
            sys.exit(1)
    
    return token

def print_json(data, title=None):
    """Print formatted JSON"""
    if title:
        print(f"\n🔍 {title}")
        print("=" * (len(title) + 4))
    
    print(json.dumps(data, indent=2))

def main():
    parser = argparse.ArgumentParser(description="CloudFlare Cache Management CLI for CyberX")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get comprehensive domain status')
    
    # Purge command
    purge_parser = subparsers.add_parser('purge', help='Purge cache')
    purge_parser.add_argument('--files', nargs='+', help='Specific files to purge')
    purge_parser.add_argument('--all', action='store_true', help='Purge everything (default)')
    
    # Cache level command
    cache_parser = subparsers.add_parser('cache-level', help='Get or set cache level')
    cache_parser.add_argument('level', nargs='?', choices=['aggressive', 'basic', 'simplified'],
                             help='Cache level to set (omit to get current level)')
    
    # Security level command
    security_parser = subparsers.add_parser('security-level', help='Get or set security level')
    security_parser.add_argument('level', nargs='?', 
                                choices=['off', 'essentially_off', 'low', 'medium', 'high', 'under_attack'],
                                help='Security level to set (omit to get current level)')
    
    # Development mode command
    dev_parser = subparsers.add_parser('dev-mode', help='Get or set development mode')
    dev_parser.add_argument('mode', nargs='?', choices=['on', 'off'], 
                           help='Development mode (omit to get current status)')
    
    # Deployment setup command
    deploy_parser = subparsers.add_parser('deploy-setup', help='Setup cache for deployment')
    
    # DNS records command
    dns_parser = subparsers.add_parser('dns', help='Get DNS records')
    dns_parser.add_argument('--type', choices=['A', 'AAAA', 'CNAME', 'MX', 'TXT'], 
                           help='DNS record type to filter')
    
    # Zone info command
    zone_parser = subparsers.add_parser('zone', help='Get zone information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Setup API token
        token = setup_api_token()
        
        # Initialize CloudFlare manager
        cf = CloudFlareManager(api_token=token)
        
        print(f"🌐 CloudFlare Manager for {cf.domain}")
        print(f"🆔 Zone ID: {cf.zone_id}")
        print()
        
        # Execute commands
        if args.command == 'status':
            status = cf.get_comprehensive_status()
            print_json(status, "Comprehensive Domain Status")
            
        elif args.command == 'purge':
            if args.files:
                result = cf.purge_cache(files=args.files)
                print(f"✅ Purged specific files: {args.files}")
            else:
                result = cf.purge_cache()
                print("✅ Purged all cache")
            print_json(result, "Purge Result")
            
        elif args.command == 'cache-level':
            if args.level:
                result = cf.set_cache_level(args.level)
                print(f"✅ Set cache level to: {args.level}")
                print_json(result, "Cache Level Update")
            else:
                result = cf.get_cache_level()
                current_level = result.get('result', {}).get('value', 'unknown')
                print(f"📊 Current cache level: {current_level}")
                print_json(result, "Cache Level Status")
                
        elif args.command == 'security-level':
            if args.level:
                result = cf.set_security_level(args.level)
                print(f"🛡️ Set security level to: {args.level}")
                print_json(result, "Security Level Update")
            else:
                result = cf.get_security_level()
                current_level = result.get('result', {}).get('value', 'unknown')
                print(f"🛡️ Current security level: {current_level}")
                print_json(result, "Security Level Status")
                
        elif args.command == 'dev-mode':
            if args.mode:
                enabled = args.mode == 'on'
                result = cf.set_development_mode(enabled)
                print(f"🔧 Development mode: {args.mode}")
                print_json(result, "Development Mode Update")
            else:
                result = cf.get_development_mode()
                current_mode = result.get('result', {}).get('value', 'unknown')
                print(f"🔧 Current development mode: {current_mode}")
                print_json(result, "Development Mode Status")
                
        elif args.command == 'deploy-setup':
            print("🚀 Setting up deployment cache configuration...")
            result = cf.deployment_cache_setup()
            print("✅ Deployment setup completed!")
            print_json(result, "Deployment Setup Results")
            
        elif args.command == 'dns':
            result = cf.get_dns_records(record_type=args.type)
            records = result.get('result', [])
            print(f"📋 Found {len(records)} DNS records")
            if args.type:
                print(f"📋 Filtered by type: {args.type}")
            print_json(result, "DNS Records")
            
        elif args.command == 'zone':
            result = cf.get_zone_info()
            zone_status = result.get('result', {}).get('status', 'unknown')
            print(f"🌐 Zone status: {zone_status}")
            print_json(result, "Zone Information")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
