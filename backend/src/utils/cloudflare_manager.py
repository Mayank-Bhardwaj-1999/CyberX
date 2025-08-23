#!/usr/bin/env python3
"""
CloudFlare Cache Management Module for CyberX
============================================

Automates CloudFlare cache management for cyberx.icu domain
- Purge cache when deploying updates
- Manage cache levels
- Monitor cache performance
- Security rule management

Author: CyberX Security Team
Domain: cyberx.icu
Zone ID: 7386179fad0d3712e5fbb97dc4868782
Account ID: 611478465d4e849c595ce1c53bce2cb0
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudFlareManager:
    """CloudFlare API Manager for CyberX Domain"""
    
    def __init__(self, api_token: str = None):
        """
        Initialize CloudFlare manager
        
        Args:
            api_token: CloudFlare API token (if not provided, will look for environment variable)
        """
        self.api_token = api_token or self._get_api_token()
        self.zone_id = "7386179fad0d3712e5fbb97dc4868782"
        self.account_id = "611478465d4e849c595ce1c53bce2cb0"
        self.domain = "cyberx.icu"
        self.base_url = "https://api.cloudflare.com/client/v4"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"CloudFlare Manager initialized for domain: {self.domain}")
    
    def _get_api_token(self) -> str:
        """Get API token from environment or config file"""
        import os
        
        # Try environment variable first
        token = os.getenv('CLOUDFLARE_API_TOKEN')
        if token:
            return token
            
        # Try config file
        config_file = Path('/root/CyberX_backend/config/cloudflare.conf')
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith('API_TOKEN='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                logger.error(f"Error reading config file: {e}")
        
        raise ValueError("CloudFlare API token not found. Set CLOUDFLARE_API_TOKEN environment variable or provide token directly.")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make CloudFlare API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=self.headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CloudFlare API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    def get_zone_info(self) -> Dict:
        """Get zone information"""
        logger.info(f"Getting zone info for {self.domain}")
        endpoint = f"/zones/{self.zone_id}"
        return self._make_request('GET', endpoint)
    
    def get_cache_level(self) -> Dict:
        """Get current cache level setting"""
        logger.info("Getting cache level setting")
        endpoint = f"/zones/{self.zone_id}/settings/cache_level"
        return self._make_request('GET', endpoint)
    
    def set_cache_level(self, level: str) -> Dict:
        """
        Set cache level
        
        Args:
            level: Cache level ('aggressive', 'basic', 'simplified')
        """
        valid_levels = ['aggressive', 'basic', 'simplified']
        if level not in valid_levels:
            raise ValueError(f"Invalid cache level. Must be one of: {valid_levels}")
        
        logger.info(f"Setting cache level to: {level}")
        endpoint = f"/zones/{self.zone_id}/settings/cache_level"
        data = {"value": level}
        return self._make_request('PATCH', endpoint, data)
    
    def purge_cache(self, files: List[str] = None, tags: List[str] = None, hosts: List[str] = None) -> Dict:
        """
        Purge CloudFlare cache
        
        Args:
            files: Specific files to purge
            tags: Cache tags to purge
            hosts: Hostnames to purge
        """
        logger.info("Purging CloudFlare cache")
        endpoint = f"/zones/{self.zone_id}/purge_cache"
        
        data = {}
        if files:
            data["files"] = files
        elif tags:
            data["tags"] = tags
        elif hosts:
            data["hosts"] = hosts
        else:
            # Purge everything
            data["purge_everything"] = True
        
        return self._make_request('POST', endpoint, data)
    
    def get_cache_analytics(self, since: str = None) -> Dict:
        """Get cache analytics"""
        logger.info("Getting cache analytics")
        endpoint = f"/zones/{self.zone_id}/analytics/dashboard"
        
        if since:
            endpoint += f"?since={since}"
        
        return self._make_request('GET', endpoint)
    
    def get_security_level(self) -> Dict:
        """Get security level setting"""
        logger.info("Getting security level")
        endpoint = f"/zones/{self.zone_id}/settings/security_level"
        return self._make_request('GET', endpoint)
    
    def set_security_level(self, level: str) -> Dict:
        """
        Set security level
        
        Args:
            level: Security level ('off', 'essentially_off', 'low', 'medium', 'high', 'under_attack')
        """
        valid_levels = ['off', 'essentially_off', 'low', 'medium', 'high', 'under_attack']
        if level not in valid_levels:
            raise ValueError(f"Invalid security level. Must be one of: {valid_levels}")
        
        logger.info(f"Setting security level to: {level}")
        endpoint = f"/zones/{self.zone_id}/settings/security_level"
        data = {"value": level}
        return self._make_request('PATCH', endpoint, data)
    
    def get_ssl_mode(self) -> Dict:
        """Get SSL mode setting"""
        logger.info("Getting SSL mode")
        endpoint = f"/zones/{self.zone_id}/settings/ssl"
        return self._make_request('GET', endpoint)
    
    def get_development_mode(self) -> Dict:
        """Get development mode status"""
        logger.info("Getting development mode status")
        endpoint = f"/zones/{self.zone_id}/settings/development_mode"
        return self._make_request('GET', endpoint)
    
    def set_development_mode(self, enabled: bool) -> Dict:
        """
        Enable/disable development mode (bypasses cache)
        
        Args:
            enabled: True to enable development mode
        """
        logger.info(f"Setting development mode: {enabled}")
        endpoint = f"/zones/{self.zone_id}/settings/development_mode"
        data = {"value": "on" if enabled else "off"}
        return self._make_request('PATCH', endpoint, data)
    
    def create_page_rule(self, targets: List[Dict], actions: List[Dict], priority: int = 1) -> Dict:
        """
        Create page rule
        
        Args:
            targets: List of target patterns
            actions: List of actions to apply
            priority: Rule priority
        """
        logger.info("Creating page rule")
        endpoint = f"/zones/{self.zone_id}/pagerules"
        data = {
            "targets": targets,
            "actions": actions,
            "priority": priority,
            "status": "active"
        }
        return self._make_request('POST', endpoint, data)
    
    def get_dns_records(self, record_type: str = None) -> Dict:
        """Get DNS records"""
        logger.info(f"Getting DNS records (type: {record_type or 'all'})")
        endpoint = f"/zones/{self.zone_id}/dns_records"
        
        if record_type:
            endpoint += f"?type={record_type}"
        
        return self._make_request('GET', endpoint)
    
    def deployment_cache_setup(self) -> Dict:
        """Optimize cache settings for deployment"""
        logger.info("Setting up deployment-optimized cache configuration")
        
        results = {}
        
        try:
            # Set aggressive caching for static assets
            results['cache_level'] = self.set_cache_level('aggressive')
            
            # Enable development mode temporarily for immediate updates
            results['dev_mode'] = self.set_development_mode(True)
            
            # Wait a moment for settings to propagate
            time.sleep(2)
            
            # Purge everything to ensure fresh content
            results['purge'] = self.purge_cache()
            
            # Wait for purge to complete
            time.sleep(5)
            
            # Disable development mode
            results['dev_mode_off'] = self.set_development_mode(False)
            
            logger.info("Deployment cache setup completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Deployment cache setup failed: {e}")
            raise
    
    def get_comprehensive_status(self) -> Dict:
        """Get comprehensive domain status"""
        logger.info("Getting comprehensive domain status")
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'domain': self.domain,
            'zone_id': self.zone_id
        }
        
        try:
            status['zone_info'] = self.get_zone_info()
            status['cache_level'] = self.get_cache_level()
            status['security_level'] = self.get_security_level()
            status['ssl_mode'] = self.get_ssl_mode()
            status['development_mode'] = self.get_development_mode()
            status['dns_records'] = self.get_dns_records('A')
            
            logger.info("Comprehensive status retrieved successfully")
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            status['error'] = str(e)
        
        return status

def main():
    """Example usage and testing"""
    try:
        # Initialize manager (you'll need to provide API token)
        print("CloudFlare Cache Manager for CyberX")
        print("==================================")
        print()
        
        print("To use this module, you need to provide your CloudFlare API token.")
        print("You can either:")
        print("1. Set environment variable: export CLOUDFLARE_API_TOKEN='your_token'")
        print("2. Create config file: /root/CyberX_backend/config/cloudflare.conf")
        print("3. Pass token directly when initializing CloudFlareManager")
        print()
        
        # Example usage (uncomment when you have API token):
        # cf = CloudFlareManager(api_token="your_api_token_here")
        # status = cf.get_comprehensive_status()
        # print(json.dumps(status, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
