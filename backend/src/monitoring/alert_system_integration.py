#!/usr/bin/env python3
"""
Alert System Integration Script
This script integrates the f            if response.status_code == 200:
                safe_print(f"✅ Notification sent to API successfully")
                return True
            else:
                safe_print(f"⚠️ API notification failed with status {response.status_code}")
                return False
            
        except requests.RequestException as e:
            safe_print(f"⚠️ Failed to send notification to API: {e}")
            return False
        except Exception as e:
            safe_print(f"⚠️ Error in notification sending: {e}")
            return Falseith the AI summarizer to create a complete 
real-time alert system for new cybersecurity articles.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add utils directory to path for unicode helper
utils_path = Path(__file__).parent.parent / "utils"
sys.path.append(str(utils_path))

try:
    from unicode_helper import safe_print, EMOJIS
except ImportError:
    # Fallback if unicode_helper is not available
    def safe_print(*args, **kwargs):
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            # Convert emojis to ASCII
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_arg = (arg.replace("🚀", "[START]").replace("📁", "[FOLDER]")
                               .replace("🌐", "[WEB]").replace("✅", "[OK]")
                               .replace("❌", "[ERROR]").replace("⚠️", "[WARNING]")
                               .replace("📰", "[NEWS]").replace("🔔", "[ALERT]"))
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            print(*safe_args, **kwargs)
    
    EMOJIS = {'rocket': '[START]', 'news': '[NEWS]', 'alert': '[ALERT]', 'success': '[OK]', 'error': '[ERROR]'}

import asyncio
import sys
import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'monitoring'))

try:
    from src.monitoring.file_watcher import NewsFileWatcher, start_file_watcher
    WATCHER_AVAILABLE = True
except ImportError as e:
    safe_print(f"⚠️ Warning: File watcher not available: {e}")
    WATCHER_AVAILABLE = False

class AlertSystemIntegrator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.api_url = "http://localhost:8080"
        
        safe_print(f"{EMOJIS['rocket']} Alert System Integrator initialized")
        safe_print(f"📁 Data directory: {self.data_dir}")
        safe_print(f"🌐 API endpoint: {self.api_url}")
    
    def send_notification_to_api(self, alert_data):
        """Send notification to the API endpoint for frontend consumption"""
        try:
            # Prepare notification data for API
            notification_payload = {
                "type": alert_data.get("type", "new_articles_alert"),
                "count": alert_data.get("count", 0),
                "timestamp": alert_data.get("timestamp", datetime.now().isoformat()),
                "title": f"🔔 {alert_data.get('count', 0)} New Articles",
                "body": f"New cybersecurity articles from {len(alert_data.get('summary', {}).get('sources', []))} sources",
                "message": f"Found {alert_data.get('count', 0)} new cybersecurity articles",
                "priority": "high" if alert_data.get('count', 0) > 5 else "normal"
            }
            
            # Send to API notification endpoint
            response = requests.post(
                f"{self.api_url}/api/notify",
                json=notification_payload,
                timeout=5,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                safe_print(f"✅ Notification sent to API successfully")
                return True
            else:
                safe_print(f"⚠️ API notification failed with status {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            safe_print(f"⚠️ Failed to send notification to API: {e}")
            return False
        except Exception as e:
            safe_print(f"⚠️ Error in notification sending: {e}")
            return False
    
    def enhanced_alert_callback(self, alert_data):
        """Enhanced callback that integrates with the API system"""
        safe_print(f"\n🔔 Enhanced Alert Callback Triggered!")
        
        # Send notification to API for real-time frontend updates
        api_success = self.send_notification_to_api(alert_data)
        
        # Create enhanced alert summary
        count = alert_data.get('count', 0)
        sources = alert_data.get('summary', {}).get('sources', [])
        keywords = alert_data.get('summary', {}).get('keywords', [])
        
        safe_print("📊 Alert Summary:")
        safe_print(f"   • New Articles: {count}")
        safe_print(f"   • Sources: {', '.join(sources[:3])}{'...' if len(sources) > 3 else ''}")
        safe_print(f"   • Keywords: {', '.join(keywords[:3])}")
        safe_print(f"   • API Notification: {'✅ Success' if api_success else '❌ Failed'}")
        
        # Ensure alerts directory exists
        alerts_dir = self.data_dir / "alerts"
        alerts_dir.mkdir(exist_ok=True)
        
        # Log alert for debugging
        try:
            alert_log_file = alerts_dir / "integration_alerts.log"
            with open(alert_log_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - Alert: {count} articles, API: {api_success}\n")
        except Exception as e:
            safe_print(f"⚠️ Failed to log alert: {e}")
    
    def test_system(self):
        """Test the alert system with a sample alert"""
        safe_print(f"\n🧪 Testing Alert System...")
        
        sample_alert = {
            "type": "test_alert",
            "timestamp": datetime.now().isoformat(),
            "count": 3,
            "articles": [
                {"title": "Test Cybersecurity Alert 1", "source": "Test Source 1"},
                {"title": "Test Cybersecurity Alert 2", "source": "Test Source 2"},
                {"title": "Test Cybersecurity Alert 3", "source": "Test Source 1"},
            ],
            "summary": {
                "total_new": 3,
                "sources": ["Test Source 1", "Test Source 2"],
                "keywords": ["test", "cybersecurity", "alert"]
            }
        }
        
        safe_print("📤 Sending test alert...")
        self.enhanced_alert_callback(sample_alert)
        safe_print("✅ Test completed!")
    
    def start_monitoring(self):
        """Start the integrated monitoring system"""
        print("\n🚀 Starting Integrated Alert Monitoring System...")
        
        if not WATCHER_AVAILABLE:
            safe_print("❌ File watcher not available - cannot start monitoring")
            return
        
        try:
            # Test API connection
            try:
                response = requests.get(f"{self.api_url}/api/health", timeout=5)
                if response.status_code == 200:
                    safe_print("✅ API connection successful")
                else:
                    safe_print(f"⚠️ API health check failed: {response.status_code}")
            except:
                safe_print("⚠️ API not available - alerts will be logged only")
            
            # Start file watcher with enhanced callback
            print("👀 Starting file watcher with API integration...")
            start_file_watcher(self.enhanced_alert_callback)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            safe_print(f"❌ Error starting monitoring: {e}")

def main():
    """Main function to run the alert system"""
    try:
        print("🛡️ Cybersecurity Alert System - Integration Module")
    except UnicodeEncodeError:
        print("[SECURITY] Cybersecurity Alert System - Integration Module")
    print("="*60)
    
    integrator = AlertSystemIntegrator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        integrator.test_system()
    else:
        integrator.start_monitoring()

if __name__ == "__main__":
    main()
