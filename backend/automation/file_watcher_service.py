#!/usr/bin/env python3
"""
👁️ File Watcher Service
Monitors data directory for changes and triggers API notifications
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/watcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('FileWatcher')

class NewsFileHandler(FileSystemEventHandler):
    """Handle file system events for news data files"""
    
    def __init__(self, api_endpoint: str):
        self.api_endpoint = api_endpoint
        self.last_notification = {}
        self.cooldown_seconds = 30  # Prevent spam notifications
        
    def should_notify(self, file_path: str) -> bool:
        """Check if we should send a notification for this file"""
        now = datetime.now()
        last_time = self.last_notification.get(file_path)
        
        if last_time is None:
            self.last_notification[file_path] = now
            return True
            
        if (now - last_time).total_seconds() > self.cooldown_seconds:
            self.last_notification[file_path] = now
            return True
            
        return False
        
    def notify_api(self, event_type: str, file_path: str):
        """Send notification to API"""
        try:
            if not self.should_notify(file_path):
                return
                
            file_name = Path(file_path).name
            
            # Determine notification details based on file
            if 'live' in file_name:
                title = "Live Data Updated"
                message = "New articles scraped and available"
            elif 'summarized' in file_name:
                title = "AI Processing Complete"
                message = "Articles have been summarized and processed"
            elif 'News_today' in file_name:
                title = "Daily Archive Updated"
                message = "Daily news archive has been updated"
            else:
                title = "Data File Updated"
                message = f"File {file_name} has been updated"
            
            notification_data = {
                "type": "file_update",
                "count": 1,
                "title": title,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "file_path": file_name,
                "event_type": event_type
            }
            
            response = requests.post(
                f"{self.api_endpoint}/api/notify",
                json=notification_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"📡 Notified API: {title}")
            else:
                logger.warning(f"⚠️ API notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to notify API: {e}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        file_name = Path(file_path).name
        
        # Only monitor specific files
        if file_name.endswith('.json') and any(pattern in file_name for pattern in [
            'cybersecurity_news_live',
            'summarized_news_hf',
            'News_today_'
        ]):
            logger.info(f"📁 File modified: {file_name}")
            self.notify_api('modified', file_path)
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        file_name = Path(file_path).name
        
        if file_name.endswith('.json'):
            logger.info(f"📄 File created: {file_name}")
            self.notify_api('created', file_path)

class FileWatcherService:
    """Main file watcher service"""
    
    def __init__(self):
        self.watch_directory = os.getenv('WATCH_DIRECTORY', '/app/data')
        self.api_endpoint = os.getenv('API_ENDPOINT', 'http://cyber-api:8080')
        self.observer = None
        self.running = False
        
    def update_heartbeat(self):
        """Update heartbeat for health monitoring"""
        heartbeat_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'watch_directory': self.watch_directory,
            'api_endpoint': self.api_endpoint
        }
        
        heartbeat_file = Path('/app/logs/watcher_heartbeat.json')
        heartbeat_file.parent.mkdir(exist_ok=True)
        
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat_data, f, indent=2)
    
    def run(self):
        """Start the file watcher service"""
        logger.info("👁️ Starting File Watcher Service")
        logger.info(f"📁 Watching directory: {self.watch_directory}")
        logger.info(f"📡 API endpoint: {self.api_endpoint}")
        
        # Create event handler
        event_handler = NewsFileHandler(self.api_endpoint)
        
        # Create observer
        self.observer = Observer()
        self.observer.schedule(event_handler, self.watch_directory, recursive=False)
        
        # Start watching
        self.observer.start()
        self.running = True
        
        logger.info("✅ File watcher is now active")
        
        try:
            while self.running:
                self.update_heartbeat()
                time.sleep(60)  # Update heartbeat every minute
                
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        finally:
            self.observer.stop()
            self.observer.join()
            logger.info("🏁 File watcher stopped")

if __name__ == "__main__":
    service = FileWatcherService()
    service.run()
