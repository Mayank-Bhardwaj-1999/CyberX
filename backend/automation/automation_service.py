#!/usr/bin/env python3
"""
🤖 CYBERSECURITY NEWS AUTOMATION SERVICE
Complete automation that handles everything without manual intervention.

Features:
- 🔄 Automatic backup rotation
- 📰 Continuous news scraping 
- 🧠 AI summarization pipeline
- 📊 Health monitoring
- 🚨 Alert system
- 🧹 File cleanup
- 📡 API coordination

This service replaces all manual processes with full automation.
"""

import os
import sys
import time
import json
import schedule
import threading
import subprocess
import logging
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AutomationService')

class AutomationService:
    """Main automation service that coordinates all processes"""
    
    def __init__(self):
        self.base_dir = Path('/app')
        self.data_dir = self.base_dir / 'data'
        self.logs_dir = self.base_dir / 'logs'
        self.config_dir = self.base_dir / 'config'
        
        # Ensure directories exist
        for dir_path in [self.data_dir, self.logs_dir, self.config_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.running = False
        self.processes = {}
        self.last_heartbeat = datetime.now()
        
        # Configuration
        self.config = {
            'scraping_interval': int(os.getenv('SCRAPING_INTERVAL', 1800)),  # 30 min
            'ai_processing_interval': int(os.getenv('AI_PROCESSING_INTERVAL', 3600)),  # 1 hour
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', 300)),  # 5 min
            'backup_interval': int(os.getenv('BACKUP_INTERVAL', 86400)),  # Daily
            'api_endpoint': 'http://cyber-api:8080',
            'max_retries': 3,
            'retry_delay': 60
        }
        
        logger.info("🚀 Automation Service initialized")
        logger.info(f"📊 Configuration: {self.config}")

    def update_heartbeat(self):
        """Update heartbeat file for health monitoring"""
        heartbeat_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'uptime_seconds': (datetime.now() - self.last_heartbeat).total_seconds(),
            'processes': list(self.processes.keys()),
            'next_scraping': self.get_next_run_time('scraping'),
            'next_ai_processing': self.get_next_run_time('ai_processing'),
            'next_backup': self.get_next_run_time('backup')
        }
        
        heartbeat_file = self.data_dir / 'automation_heartbeat.json'
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat_data, f, indent=2)

    def get_next_run_time(self, job_type: str) -> Optional[str]:
        """Get next scheduled run time for a job type"""
        try:
            jobs = schedule.get_jobs()
            for job in jobs:
                if hasattr(job, 'job_func') and job_type in str(job.job_func):
                    return job.next_run.isoformat() if job.next_run else None
        except:
            pass
        return None

    def backup_old_files(self):
        """Automatic backup rotation - only when day changes"""
        logger.info("🗂️ Starting automatic backup process...")
        
        try:
            backup_dir = self.data_dir / 'backup'
            backup_dir.mkdir(exist_ok=True)
            
            # Get current date for backup naming
            current_date = datetime.now().strftime('%Y%m%d')
            
            # Check if we already backed up today
            backup_lock_file = backup_dir / f'backup_completed_{current_date}.lock'
            if backup_lock_file.exists():
                logger.info("📦 Backup already completed today, skipping...")
                return
            
            # Files to backup when transitioning to a new day
            files_to_check = [
                'cybersecurity_news_live.json',
                'summarized_news_hf.json'
            ]
            
            backup_count = 0
            
            # Only backup if we haven't backed up today and files exist from previous day
            for file_name in files_to_check:
                file_path = self.data_dir / file_name
                if file_path.exists():
                    # Check if file is from previous day
                    file_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y%m%d')
                    
                    # Create backup name with date only (no time)
                    backup_name = f"{file_path.stem}_{file_date}.json"
                    backup_path = backup_dir / backup_name
                    
                    # Only backup if:
                    # 1. File is from previous day OR
                    # 2. No backup exists for that date yet
                    if file_date != current_date and not backup_path.exists():
                        import shutil
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"📦 Backed up {file_name} → {backup_name}")
                        backup_count += 1
            
            if backup_count == 0:
                logger.info("📦 No files needed backup (already backed up or current day)")
            
            # Create lock file to prevent multiple backups today
            backup_lock_file.touch()
            
            # Clean old backups (keep last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            for backup_file in backup_dir.glob('*.json'):
                if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"🗑️ Removed old backup: {backup_file.name}")
            
            # Clean old lock files (older than 7 days)
            for lock_file in backup_dir.glob('backup_completed_*.lock'):
                if datetime.fromtimestamp(lock_file.stat().st_mtime) < (datetime.now() - timedelta(days=7)):
                    lock_file.unlink()
            
            logger.info("✅ Backup process completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Backup process failed: {e}")

    def run_scraping(self):
        """Execute the scraping process"""
        logger.info("🕷️ Starting automatic scraping process...")
        
        try:
            # Run the main scraping script
            cmd = [sys.executable, 'main_launch.py', '--mode', 'scrape', '--no-setup']
            process = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if process.returncode == 0:
                logger.info("✅ Scraping completed successfully")
                
                # Check if we got new articles
                live_file = self.data_dir / 'cybersecurity_news_live.json'
                if live_file.exists():
                    with open(live_file) as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'results' in data:
                            total_articles = sum(
                                len(site_data.get('articles', [])) 
                                for site_data in data['results'].values()
                            )
                            logger.info(f"📰 Scraped {total_articles} articles")
                            
                            # Trigger AI processing if we have new content
                            if total_articles > 0:
                                self.schedule_immediate_ai_processing()
                
            else:
                logger.error(f"❌ Scraping failed with exit code {process.returncode}")
                logger.error(f"Error output: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Scraping process timed out after 30 minutes")
        except Exception as e:
            logger.error(f"❌ Scraping process failed: {e}")

    def run_ai_processing(self):
        """Execute AI summarization"""
        logger.info("🧠 Starting AI processing...")
        
        try:
            # Check if we have data to process
            live_file = self.data_dir / 'cybersecurity_news_live.json'
            if not live_file.exists():
                logger.info("📝 No live data found, skipping AI processing")
                return
            
            # Run AI summarization
            ai_script = self.base_dir / 'Ai' / 'enhanced_ai_summarizer.py'
            if ai_script.exists():
                cmd = [sys.executable, str(ai_script)]
                process = subprocess.run(
                    cmd,
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minute timeout
                )
                
                if process.returncode == 0:
                    logger.info("✅ AI processing completed successfully")
                    
                    # Notify API about new summarized data
                    self.notify_api_update()
                    
                else:
                    logger.error(f"❌ AI processing failed: {process.stderr}")
            else:
                logger.warning("⚠️ AI summarizer script not found")
                
        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")

    def schedule_immediate_ai_processing(self):
        """Schedule AI processing to run immediately"""
        logger.info("⚡ Scheduling immediate AI processing due to new articles")
        schedule.every().second.do(self.run_ai_processing).tag('immediate_ai')
        
        # Remove the immediate job after it runs once
        def cleanup_immediate_job():
            schedule.clear('immediate_ai')
        
        schedule.every().second.do(cleanup_immediate_job).tag('cleanup')

    def notify_api_update(self):
        """Notify the API about data updates"""
        try:
            response = requests.post(
                f"{self.config['api_endpoint']}/api/notify",
                json={
                    "type": "data_update",
                    "count": 1,
                    "title": "Data Updated",
                    "message": "New summarized data available",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("📡 Successfully notified API about data update")
            else:
                logger.warning(f"⚠️ API notification failed: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"⚠️ Could not notify API: {e}")

    def health_check(self):
        """Perform system health checks"""
        logger.debug("🏥 Performing health check...")
        
        try:
            # Check API health
            api_healthy = False
            try:
                response = requests.get(f"{self.config['api_endpoint']}/health", timeout=5)
                api_healthy = response.status_code == 200
            except:
                pass
            
            # Check disk space
            disk_usage = os.statvfs(self.data_dir)
            free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
            
            # Check file ages
            critical_files = ['cybersecurity_news_live.json', 'summarized_news_hf.json']
            file_status = {}
            
            for file_name in critical_files:
                file_path = self.data_dir / file_name
                if file_path.exists():
                    age_hours = (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).total_seconds() / 3600
                    file_status[file_name] = {
                        'exists': True,
                        'age_hours': age_hours,
                        'size_mb': file_path.stat().st_size / (1024**2)
                    }
                else:
                    file_status[file_name] = {'exists': False}
            
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'api_healthy': api_healthy,
                'free_space_gb': free_space_gb,
                'file_status': file_status,
                'uptime_hours': (datetime.now() - self.last_heartbeat).total_seconds() / 3600
            }
            
            # Save health report
            health_file = self.data_dir / 'health_report.json'
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            # Log warnings if needed
            if not api_healthy:
                logger.warning("⚠️ API health check failed")
            
            if free_space_gb < 1:
                logger.warning(f"⚠️ Low disk space: {free_space_gb:.2f} GB remaining")
            
            for file_name, status in file_status.items():
                if status.get('exists') and status.get('age_hours', 0) > 24:
                    logger.warning(f"⚠️ {file_name} is over 24 hours old")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")

    def cleanup_old_data(self):
        """Clean up old log files and temporary data"""
        logger.info("🧹 Starting cleanup process...")
        
        try:
            # Clean old log files (keep last 7 days)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in self.logs_dir.glob('*.log*'):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    logger.info(f"🗑️ Removed old log: {log_file.name}")
            
            # Clean old daily files (keep last 30 days)
            for daily_file in self.data_dir.glob('News_today_*.json'):
                if datetime.fromtimestamp(daily_file.stat().st_mtime) < cutoff_date:
                    daily_file.unlink()
                    logger.info(f"🗑️ Removed old daily file: {daily_file.name}")
            
            logger.info("✅ Cleanup completed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

    def setup_schedules(self):
        """Setup all scheduled jobs"""
        logger.info("📅 Setting up automation schedules...")
        
        # Scraping schedule (every 30 minutes)
        schedule.every(self.config['scraping_interval']).seconds.do(self.run_scraping).tag('scraping')
        
        # AI processing schedule (every hour)
        schedule.every(self.config['ai_processing_interval']).seconds.do(self.run_ai_processing).tag('ai_processing')
        
        # Backup schedule (daily at 2 AM) - only once per day
        schedule.every().day.at("02:00").do(self.backup_old_files).tag('backup')
        
        # Health check schedule (every 5 minutes)
        schedule.every(self.config['health_check_interval']).seconds.do(self.health_check).tag('health')
        
        # Heartbeat update (every minute)
        schedule.every(60).seconds.do(self.update_heartbeat).tag('heartbeat')
        
        # Daily cleanup (at 3 AM)
        schedule.every().day.at("03:00").do(self.cleanup_old_data).tag('cleanup')
        
        logger.info("✅ All schedules configured")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False

    def run(self):
        """Main automation loop"""
        logger.info("🚀 Starting Cybersecurity News Automation Service")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Setup schedules
        self.setup_schedules()
        
        # Initial run
        logger.info("🔄 Performing initial setup...")
        self.backup_old_files()
        self.health_check()
        self.update_heartbeat()
        
        # Start initial scraping if no recent data exists
        live_file = self.data_dir / 'cybersecurity_news_live.json'
        if not live_file.exists():
            logger.info("📰 No existing data found, starting initial scraping...")
            self.run_scraping()
        
        self.running = True
        logger.info("✅ Automation service is now running")
        logger.info("📊 Monitoring and automation active - all processes will run automatically")
        
        # Main loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("🛑 Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        logger.info("🏁 Automation service stopped")

if __name__ == "__main__":
    service = AutomationService()
    service.run()
