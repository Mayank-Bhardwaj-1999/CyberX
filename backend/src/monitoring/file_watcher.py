#!/usr/bin/env python3
"""
Real-time File Watcher for summarized_news_hf.json
Monitors changes to the summarized news file and triggers alerts when new articles are added.
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

try:
    from src.utils.backup_manager import BackupManager
    BACKUP_AVAILABLE = True
except ImportError:
    print("⚠️ Warning: Backup manager not available")
    BACKUP_AVAILABLE = False


class NewsFileWatcher(FileSystemEventHandler):
    def __init__(self, callback_function=None):
        super().__init__()
        self.callback_function = callback_function
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.alerts_dir = self.data_dir / "alerts"
        self.summarized_file = self.data_dir / "summarized_news_hf.json"
        self.alert_state_file = self.alerts_dir / "alert_state.json"
        
        # Ensure alerts directory exists
        self.alerts_dir.mkdir(exist_ok=True)
        
        # Track file state
        self.last_known_articles: Set[str] = set()
        self.last_file_hash = ""
        self.last_check_time = datetime.now()
        
        # Statistics
        self.stats = {
            'total_alerts_sent': 0,
            'last_alert_time': None,
            'articles_processed': 0,
            'file_changes_detected': 0
        }
        
        # Initialize
        self.load_initial_state()
        print(f"📁 Watching file: {self.summarized_file}")
        print(f"💾 Alert state file: {self.alert_state_file}")
    
    def load_initial_state(self):
        """Load the initial state of articles and file hash"""
        try:
            if self.summarized_file.exists():
                with open(self.summarized_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Track article URLs to detect new ones
                for article in data:
                    if 'url' in article:
                        self.last_known_articles.add(article['url'])
                
                # Calculate file hash
                self.last_file_hash = self.calculate_file_hash()
                
                print(f"✅ Loaded {len(self.last_known_articles)} existing articles")
            else:
                print("📄 Summarized file doesn't exist yet - waiting for creation")
                
            # Load alert state if exists
            if self.alert_state_file.exists():
                with open(self.alert_state_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
                    print(f"📊 Loaded alert state: {self.stats['total_alerts_sent']} total alerts sent")
                    
        except Exception as e:
            print(f"⚠️ Error loading initial state: {e}")
    
    def calculate_file_hash(self) -> str:
        """Calculate SHA256 hash of the file"""
        try:
            if not self.summarized_file.exists():
                return ""
            
            with open(self.summarized_file, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            print(f"⚠️ Error calculating file hash: {e}")
            return ""
    
    def save_alert_state(self):
        """Save current alert state to file"""
        try:
            with open(self.alert_state_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️ Error saving alert state: {e}")
    
    def detect_new_articles(self) -> List[Dict]:
        """Detect new articles added to the file"""
        try:
            if not self.summarized_file.exists():
                return []
            
            with open(self.summarized_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
            
            new_articles = []
            current_urls = set()
            
            for article in current_data:
                if 'url' in article:
                    current_urls.add(article['url'])
                    if article['url'] not in self.last_known_articles:
                        new_articles.append(article)
            
            # Update known articles
            self.last_known_articles = current_urls
            
            return new_articles
            
        except Exception as e:
            print(f"⚠️ Error detecting new articles: {e}")
            return []
    
    def create_alert_notification(self, new_articles: List[Dict]) -> Dict:
        """Create alert notification data for new articles"""
        alert_data = {
            'type': 'new_articles_alert',
            'timestamp': datetime.now().isoformat(),
            'count': len(new_articles),
            'articles': [],
            'summary': {
                'total_new': len(new_articles),
                'sources': set(),
                'keywords': []
            }
        }
        
        # Process each new article
        for article in new_articles:
            article_info = {
                'title': article.get('title', 'Unknown Title'),
                'source': article.get('source', {}).get('name', 'Unknown Source'),
                'url': article.get('url', ''),
                'published_at': article.get('publishedAt', ''),
                'summary': article.get('summary', article.get('description', ''))[:200] + '...'
            }
            
            alert_data['articles'].append(article_info)
            alert_data['summary']['sources'].add(article_info['source'])
            
            # Extract keywords from title for alert categorization
            title_lower = article.get('title', '').lower()
            cyber_keywords = ['vulnerability', 'attack', 'malware', 'ransomware', 'breach', 
                            'security', 'hacker', 'threat', 'exploit', 'phishing', 'scam']
            for keyword in cyber_keywords:
                if keyword in title_lower:
                    alert_data['summary']['keywords'].append(keyword)
        
        # Convert sets to lists for JSON serialization
        alert_data['summary']['sources'] = list(alert_data['summary']['sources'])
        
        return alert_data
    
    def send_alert(self, alert_data: Dict):
        """Send alert notification (can be extended to integrate with frontend)"""
        count = alert_data['count']
        sources = alert_data['summary']['sources']
        
        print("\n" + "="*60)
        print("🚨 NEW CYBERSECURITY ARTICLES ALERT 🚨")
        print("="*60)
        print(f"📊 Count: {count} new articles")
        print(f"📰 Sources: {', '.join(sources[:3])}{'...' if len(sources) > 3 else ''}")
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        print("-"*60)
        
        for i, article in enumerate(alert_data['articles'][:5], 1):  # Show first 5
            print(f"{i}. {article['title'][:80]}...")
            print(f"   Source: {article['source']}")
        
        if count > 5:
            print(f"   ... and {count - 5} more articles")
        
        print("="*60)
        
        # Update statistics
        self.stats['total_alerts_sent'] += 1
        self.stats['last_alert_time'] = datetime.now().isoformat()
        self.stats['articles_processed'] += count
        self.save_alert_state()
        
        # Save alert to alerts log file
        self.save_alert_to_log(alert_data)
        
        # Call custom callback if provided
        if self.callback_function:
            try:
                self.callback_function(alert_data)
            except Exception as e:
                print(f"⚠️ Error in callback function: {e}")
    
    def save_alert_to_log(self, alert_data: Dict):
        """Save alert data to alerts log file"""
        try:
            alerts_log_file = self.alerts_dir / "alerts_log.json"
            
            # Load existing alerts
            alerts = []
            if alerts_log_file.exists():
                with open(alerts_log_file, 'r', encoding='utf-8') as f:
                    alerts = json.load(f)
            
            # Add new alert
            alerts.append(alert_data)
            
            # Keep only last 100 alerts
            if len(alerts) > 100:
                alerts = alerts[-100:]
            
            # Save back to file
            with open(alerts_log_file, 'w', encoding='utf-8') as f:
                json.dump(alerts, f, indent=2, default=str, ensure_ascii=False)
                
            print(f"💾 Alert saved to log file")
            
        except Exception as e:
            print(f"⚠️ Error saving alert to log: {e}")
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        if event.src_path == str(self.summarized_file):
            print(f"\n📄 File change detected: {event.src_path}")
            self.process_file_change()
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        if event.src_path == str(self.summarized_file):
            print(f"\n📄 File created: {event.src_path}")
            time.sleep(1)  # Wait for file to be fully written
            self.process_file_change()
    
    def process_file_change(self):
        """Process detected file changes"""
        try:
            # Calculate new file hash
            new_hash = self.calculate_file_hash()
            
            # Skip if hash hasn't changed (duplicate event)
            if new_hash == self.last_file_hash:
                return
            
            print(f"🔄 Processing file change...")
            self.stats['file_changes_detected'] += 1
            
            # Wait a moment for file to be fully written
            time.sleep(2)
            
            # Detect new articles
            new_articles = self.detect_new_articles()
            
            if new_articles:
                print(f"🆕 Found {len(new_articles)} new articles!")
                
                # Create and send alert
                alert_data = self.create_alert_notification(new_articles)
                self.send_alert(alert_data)
            else:
                print("📰 File updated but no new articles detected")
            
            # Update hash
            self.last_file_hash = new_hash
            self.last_check_time = datetime.now()
            
        except Exception as e:
            print(f"⚠️ Error processing file change: {e}")


def start_file_watcher(callback_function=None):
    """Start the file watcher service"""
    print("🚀 Starting News File Watcher Service...")
    
    watcher = NewsFileWatcher(callback_function)
    observer = Observer()
    
    # Watch the data directory
    watch_path = str(watcher.data_dir)
    observer.schedule(watcher, watch_path, recursive=False)
    
    print(f"👀 Watching directory: {watch_path}")
    print(f"🎯 Target file: {watcher.summarized_file.name}")
    print("✅ File watcher started - waiting for changes...")
    print("Press Ctrl+C to stop\n")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("✅ File watcher stopped")


if __name__ == "__main__":
    start_file_watcher()
