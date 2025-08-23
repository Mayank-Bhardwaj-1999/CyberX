#!/usr/bin/env python3
"""
🚀 ALL-IN-ONE AUTOMATION SERVICE
Complete cybersecurity news automation in a single process

Features:
- 📡 FastAPI server
- 🕷️ News scraping  
- 🧠 AI summarization
- 🔍 File monitoring
- 🧹 Cleanup tasks
- ❤️ Health monitoring
- 🚨 Alert system

Everything runs automatically with zero manual intervention!
"""

import os
import sys
import time
import json
import threading
import subprocess
import multiprocessing
from datetime import datetime
import logging
import signal
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/all_in_one.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AllInOneAutomation')

class AllInOneAutomation:
    """Complete automation system in one service"""
    
    def __init__(self):
        self.base_dir = Path('/app')
        self.running = False
        self.processes = {}
        self.threads = {}
        
    def start_fastapi_server(self):
        """Start FastAPI server in a separate process"""
        logger.info("📡 Starting FastAPI server...")
        
        try:
            # Start uvicorn server
            cmd = [
                sys.executable, '-m', 'uvicorn',
                'api.cybersecurity_fastapi:app',
                '--host', '0.0.0.0',
                '--port', '8080',
                '--workers', '2'
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['fastapi'] = process
            logger.info("✅ FastAPI server started")
            
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start FastAPI: {e}")
            return None
    
    def automation_worker(self):
        """Worker thread that handles all automation tasks"""
        logger.info("🤖 Starting automation worker...")
        
        import schedule
        
        # Setup automation schedules
        schedule.every(30).minutes.do(self.run_scraping)
        schedule.every(1).hours.do(self.run_ai_processing)
        schedule.every().day.at("02:00").do(self.backup_files)
        schedule.every().day.at("03:00").do(self.cleanup_files)
        schedule.every(5).minutes.do(self.health_check)
        
        # Initial run
        self.run_scraping()
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"❌ Automation worker error: {e}")
                time.sleep(60)
        
        logger.info("🏁 Automation worker stopped")
    
    def file_monitor_worker(self):
        """Worker thread for file monitoring"""
        logger.info("👁️ Starting file monitor...")
        
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class FileHandler(FileSystemEventHandler):
                def on_modified(self, event):
                    if not event.is_directory and event.src_path.endswith('.json'):
                        logger.info(f"📁 File modified: {Path(event.src_path).name}")
                        # Notify API about file changes
                        self.notify_file_change(event.src_path)
            
            observer = Observer()
            observer.schedule(FileHandler(), '/app/data', recursive=False)
            observer.start()
            
            while self.running:
                time.sleep(30)
            
            observer.stop()
            observer.join()
            
        except Exception as e:
            logger.error(f"❌ File monitor error: {e}")
    
    def notify_file_change(self, file_path):
        """Notify about file changes"""
        try:
            import requests
            
            file_name = Path(file_path).name
            response = requests.post(
                'http://localhost:8080/api/notify',
                json={
                    "type": "file_update",
                    "count": 1,
                    "title": f"File Updated: {file_name}",
                    "message": "Data file has been updated",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"📡 Notified API about {file_name}")
            
        except Exception as e:
            logger.debug(f"⚠️ Could not notify API: {e}")
    
    def run_scraping(self):
        """Execute scraping process"""
        logger.info("🕷️ Running scraping process...")
        
        try:
            cmd = [sys.executable, 'main_launch.py', '--mode', 'scrape-only', '--quiet']
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes
            )
            
            if result.returncode == 0:
                logger.info("✅ Scraping completed successfully")
                
                # Check for new articles and trigger AI processing
                live_file = self.base_dir / 'data' / 'cybersecurity_news_live.json'
                if live_file.exists():
                    with open(live_file) as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'results' in data:
                            total_articles = sum(
                                len(site_data.get('articles', [])) 
                                for site_data in data['results'].values()
                            )
                            if total_articles > 0:
                                logger.info(f"📰 Found {total_articles} new articles")
                                # Schedule immediate AI processing
                                threading.Timer(60, self.run_ai_processing).start()
            else:
                logger.warning(f"⚠️ Scraping had issues: {result.stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            logger.error("⏰ Scraping timed out")
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
    
    def run_ai_processing(self):
        """Execute AI summarization"""
        logger.info("🧠 Running AI processing...")
        
        try:
            ai_script = self.base_dir / 'Ai' / 'enhanced_ai_summarizer.py'
            if ai_script.exists():
                cmd = [sys.executable, str(ai_script)]
                result = subprocess.run(
                    cmd,
                    cwd=self.base_dir,
                    capture_output=True,
                    text=True,
                    timeout=1800
                )
                
                if result.returncode == 0:
                    logger.info("✅ AI processing completed")
                else:
                    logger.warning(f"⚠️ AI processing had issues: {result.stderr[:200]}")
            else:
                logger.warning("⚠️ AI script not found")
                
        except Exception as e:
            logger.error(f"❌ AI processing failed: {e}")
    
    def backup_files(self):
        """Backup important files"""
        logger.info("📦 Creating backups...")
        
        try:
            backup_dir = self.base_dir / 'data' / 'backup'
            backup_dir.mkdir(exist_ok=True)
            
            import shutil
            
            files_to_backup = [
                'cybersecurity_news_live.json',
                'summarized_news_hf.json'
            ]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            for file_name in files_to_backup:
                source = self.base_dir / 'data' / file_name
                if source.exists():
                    backup_name = f"{source.stem}_{timestamp}.json"
                    dest = backup_dir / backup_name
                    shutil.copy2(source, dest)
                    logger.info(f"📦 Backed up {file_name}")
            
            logger.info("✅ Backup completed")
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
    
    def cleanup_files(self):
        """Clean up old files"""
        logger.info("🧹 Cleaning up old files...")
        
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=30)
            removed_count = 0
            
            # Clean old backups
            backup_dir = self.base_dir / 'data' / 'backup'
            if backup_dir.exists():
                for backup_file in backup_dir.glob('*.json'):
                    if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
            
            # Clean old logs
            log_cutoff = datetime.now() - timedelta(days=7)
            logs_dir = self.base_dir / 'logs'
            for log_file in logs_dir.glob('*.log*'):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < log_cutoff:
                    log_file.unlink()
                    removed_count += 1
            
            logger.info(f"✅ Cleanup completed: {removed_count} files removed")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def health_check(self):
        """Perform health checks"""
        logger.debug("🏥 Health check...")
        
        try:
            health_data = {
                'timestamp': datetime.now().isoformat(),
                'processes': {
                    name: proc.poll() is None 
                    for name, proc in self.processes.items()
                },
                'threads': {
                    name: thread.is_alive() 
                    for name, thread in self.threads.items()
                }
            }
            
            # Check API health
            try:
                import requests
                response = requests.get('http://localhost:8080/health', timeout=5)
                health_data['api_healthy'] = response.status_code == 200
            except:
                health_data['api_healthy'] = False
            
            # Save health report
            health_file = self.base_dir / 'data' / 'health_report.json'
            with open(health_file, 'w') as f:
                json.dump(health_data, f, indent=2)
            
            # Log issues
            if not health_data['api_healthy']:
                logger.warning("⚠️ API health check failed")
            
            dead_processes = [name for name, alive in health_data['processes'].items() if not alive]
            if dead_processes:
                logger.warning(f"⚠️ Dead processes: {dead_processes}")
            
            dead_threads = [name for name, alive in health_data['threads'].items() if not alive]
            if dead_threads:
                logger.warning(f"⚠️ Dead threads: {dead_threads}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"🛑 Received signal {signum}, shutting down...")
        self.running = False
    
    def run(self):
        """Main automation loop"""
        logger.info("🚀 Starting All-in-One Cybersecurity Automation")
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.running = True
        
        # Start FastAPI server
        self.start_fastapi_server()
        
        # Start worker threads
        self.threads['automation'] = threading.Thread(target=self.automation_worker, daemon=True)
        self.threads['file_monitor'] = threading.Thread(target=self.file_monitor_worker, daemon=True)
        
        for name, thread in self.threads.items():
            thread.start()
            logger.info(f"✅ Started {name} thread")
        
        logger.info("🎯 ALL SYSTEMS OPERATIONAL")
        logger.info("📡 API: http://localhost:8080")
        logger.info("📚 Docs: http://localhost:8080/docs")
        logger.info("🔄 Automation: ACTIVE")
        logger.info("💡 Everything is now running automatically!")
        
        # Main loop - just keep alive and monitor
        try:
            while self.running:
                time.sleep(30)
                
                # Restart dead processes
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:  # Process died
                        logger.warning(f"⚠️ Process {name} died, restarting...")
                        if name == 'fastapi':
                            self.start_fastapi_server()
                
        except KeyboardInterrupt:
            logger.info("🛑 Received keyboard interrupt")
        
        # Cleanup
        logger.info("🧹 Shutting down all services...")
        
        for name, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=10)
                logger.info(f"✅ Stopped {name}")
            except:
                try:
                    process.kill()
                except:
                    pass
        
        logger.info("🏁 All-in-One Automation stopped")

if __name__ == "__main__":
    automation = AllInOneAutomation()
    automation.run()
