#!/usr/bin/env python3
"""
CyberX Deployment with CloudFlare Cache Management
================================================

Automated deployment script that:
1. Updates application
2. Manages CloudFlare cache
3. Ensures zero-downtime deployment
4. Validates deployment success

Usage:
    python deploy_with_cache.py --help
    python deploy_with_cache.py --purge-cache
    python deploy_with_cache.py --dev-mode
    python deploy_with_cache.py --full-deploy
"""

import argparse
import time
import subprocess
import sys
from pathlib import Path
import logging

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.cloudflare_manager import CloudFlareManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CyberXDeployment:
    """CyberX Deployment Manager with CloudFlare Integration"""
    
    def __init__(self, api_token: str = None):
        """Initialize deployment manager"""
        self.cf_manager = CloudFlareManager(api_token=api_token)
        self.project_root = Path('/root/CyberX_backend')
        
    def check_services_health(self) -> bool:
        """Check if all services are healthy"""
        logger.info("🔍 Checking service health...")
        
        services_to_check = [
            ('Grafana', 'http://localhost:3000/api/health'),
            ('Prometheus', 'http://localhost:9091/-/healthy'),
            ('FastAPI', 'http://localhost:8080/health'),
        ]
        
        all_healthy = True
        
        for service_name, url in services_to_check:
            try:
                import requests
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name}: Healthy")
                else:
                    logger.warning(f"⚠️ {service_name}: Unhealthy (status: {response.status_code})")
                    all_healthy = False
            except Exception as e:
                logger.error(f"❌ {service_name}: Failed to check - {e}")
                all_healthy = False
        
        return all_healthy
    
    def restart_containers(self, service: str = None) -> bool:
        """Restart Docker containers"""
        logger.info(f"🔄 Restarting containers {f'({service})' if service else ''}")
        
        try:
            docker_dir = self.project_root / 'docker'
            
            if service:
                # Restart specific service
                cmd = f"docker compose -f docker-compose.monitoring.secure.yml restart {service}"
                subprocess.run(cmd, shell=True, cwd=docker_dir, check=True)
            else:
                # Restart all monitoring services
                cmd = "docker compose -f docker-compose.monitoring.secure.yml restart"
                subprocess.run(cmd, shell=True, cwd=docker_dir, check=True)
                
                # Restart FastAPI
                cmd = "docker compose restart cybersecurity-api"
                subprocess.run(cmd, shell=True, cwd=docker_dir, check=True)
            
            logger.info("✅ Container restart completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Container restart failed: {e}")
            return False
    
    def enable_development_mode(self) -> bool:
        """Enable CloudFlare development mode for immediate updates"""
        logger.info("🔧 Enabling CloudFlare development mode...")
        
        try:
            result = self.cf_manager.set_development_mode(True)
            if result.get('success', False):
                logger.info("✅ Development mode enabled")
                return True
            else:
                logger.error("❌ Failed to enable development mode")
                return False
        except Exception as e:
            logger.error(f"❌ Error enabling development mode: {e}")
            return False
    
    def disable_development_mode(self) -> bool:
        """Disable CloudFlare development mode"""
        logger.info("🔧 Disabling CloudFlare development mode...")
        
        try:
            result = self.cf_manager.set_development_mode(False)
            if result.get('success', False):
                logger.info("✅ Development mode disabled")
                return True
            else:
                logger.error("❌ Failed to disable development mode")
                return False
        except Exception as e:
            logger.error(f"❌ Error disabling development mode: {e}")
            return False
    
    def purge_cache(self) -> bool:
        """Purge CloudFlare cache"""
        logger.info("🧹 Purging CloudFlare cache...")
        
        try:
            result = self.cf_manager.purge_cache()
            if result.get('success', False):
                logger.info("✅ Cache purged successfully")
                return True
            else:
                logger.error("❌ Failed to purge cache")
                return False
        except Exception as e:
            logger.error(f"❌ Error purging cache: {e}")
            return False
    
    def optimize_cache_settings(self) -> bool:
        """Optimize cache settings for production"""
        logger.info("⚡ Optimizing cache settings...")
        
        try:
            # Set aggressive caching
            cache_result = self.cf_manager.set_cache_level('aggressive')
            if not cache_result.get('success', False):
                logger.warning("⚠️ Failed to set cache level")
                return False
            
            logger.info("✅ Cache settings optimized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error optimizing cache settings: {e}")
            return False
    
    def validate_domain_access(self) -> bool:
        """Validate domain is accessible"""
        logger.info("🌐 Validating domain access...")
        
        try:
            import requests
            
            # Test HTTPS access
            response = requests.get('https://cyberx.icu', timeout=30, allow_redirects=True)
            if response.status_code in [200, 302]:
                logger.info("✅ Domain is accessible via HTTPS")
                
                # Test API endpoint
                api_response = requests.get('https://cyberx.icu/api/', timeout=30)
                if api_response.status_code == 200:
                    logger.info("✅ API endpoint is accessible")
                    return True
                else:
                    logger.warning(f"⚠️ API endpoint returned status: {api_response.status_code}")
                    return False
            else:
                logger.error(f"❌ Domain returned status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Domain validation failed: {e}")
            return False
    
    def quick_deploy(self) -> bool:
        """Quick deployment with cache purge"""
        logger.info("🚀 Starting quick deployment...")
        
        steps = [
            ("Enable development mode", self.enable_development_mode),
            ("Purge cache", self.purge_cache),
            ("Wait for propagation", lambda: time.sleep(10)),
            ("Check service health", self.check_services_health),
            ("Disable development mode", self.disable_development_mode),
            ("Validate domain access", self.validate_domain_access),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Step: {step_name}")
            if callable(step_func):
                if step_func == (lambda: time.sleep(10)):
                    step_func()
                    continue
                    
                if not step_func():
                    logger.error(f"❌ Quick deployment failed at: {step_name}")
                    return False
            else:
                logger.info(f"ℹ️ Manual step: {step_name}")
        
        logger.info("✅ Quick deployment completed successfully!")
        return True
    
    def full_deploy(self) -> bool:
        """Full deployment with container restart and cache management"""
        logger.info("🚀 Starting full deployment...")
        
        steps = [
            ("Enable development mode", self.enable_development_mode),
            ("Restart containers", self.restart_containers),
            ("Wait for services to start", lambda: time.sleep(30)),
            ("Check service health", self.check_services_health),
            ("Purge cache", self.purge_cache),
            ("Optimize cache settings", self.optimize_cache_settings),
            ("Wait for propagation", lambda: time.sleep(15)),
            ("Disable development mode", self.disable_development_mode),
            ("Final validation", self.validate_domain_access),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Step: {step_name}")
            if callable(step_func):
                if step_func in [lambda: time.sleep(30), lambda: time.sleep(15)]:
                    if step_func == (lambda: time.sleep(30)):
                        time.sleep(30)
                    else:
                        time.sleep(15)
                    continue
                    
                if not step_func():
                    logger.error(f"❌ Full deployment failed at: {step_name}")
                    return False
            else:
                logger.info(f"ℹ️ Manual step: {step_name}")
        
        logger.info("✅ Full deployment completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description="CyberX Deployment with CloudFlare Cache Management")
    
    parser.add_argument('--purge-cache', action='store_true', help='Purge CloudFlare cache only')
    parser.add_argument('--dev-mode', choices=['on', 'off'], help='Enable/disable development mode')
    parser.add_argument('--quick-deploy', action='store_true', help='Quick deployment (cache management only)')
    parser.add_argument('--full-deploy', action='store_true', help='Full deployment (restart + cache management)')
    parser.add_argument('--validate', action='store_true', help='Validate domain access only')
    parser.add_argument('--api-token', help='CloudFlare API token')
    
    args = parser.parse_args()
    
    if not any([args.purge_cache, args.dev_mode, args.quick_deploy, args.full_deploy, args.validate]):
        parser.print_help()
        return
    
    try:
        deployer = CyberXDeployment(api_token=args.api_token)
        
        print("🔧 CyberX Deployment Manager")
        print("============================")
        print()
        
        success = True
        
        if args.purge_cache:
            success = deployer.purge_cache()
            
        elif args.dev_mode:
            if args.dev_mode == 'on':
                success = deployer.enable_development_mode()
            else:
                success = deployer.disable_development_mode()
                
        elif args.quick_deploy:
            success = deployer.quick_deploy()
            
        elif args.full_deploy:
            success = deployer.full_deploy()
            
        elif args.validate:
            success = deployer.validate_domain_access()
        
        if success:
            print("\n🎉 Operation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Operation failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Deployment error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
