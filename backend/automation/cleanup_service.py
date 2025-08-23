#!/usr/bin/env python3
"""
🧹 Cleanup Service
Handles automatic file cleanup and maintenance
"""

import os
import sys
import time
import json
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('CleanupService')

class CleanupService:
    """Automatic cleanup and maintenance service"""
    
    def __init__(self):
        self.data_dir = Path('/app/data')
        self.logs_dir = Path('/app/logs')
        self.cleanup_interval = int(os.getenv('CLEANUP_INTERVAL', 86400))  # Daily
        self.keep_days = int(os.getenv('KEEP_DAYS', 30))
        self.running = False
        
    def cleanup_old_files(self):
        """Remove old files based on retention policy"""
        logger.info("🧹 Starting cleanup process...")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.keep_days)
            removed_count = 0
            
            # Clean backup files
            backup_dir = self.data_dir / 'backup'
            if backup_dir.exists():
                for backup_file in backup_dir.glob('*.json'):
                    if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                        backup_file.unlink()
                        removed_count += 1
                        logger.info(f"🗑️ Removed old backup: {backup_file.name}")
            
            # Clean old daily files
            for daily_file in self.data_dir.glob('News_today_*.json'):
                if datetime.fromtimestamp(daily_file.stat().st_mtime) < cutoff_date:
                    daily_file.unlink()
                    removed_count += 1
                    logger.info(f"🗑️ Removed old daily file: {daily_file.name}")
            
            # Clean old log files (keep last 7 days)
            log_cutoff = datetime.now() - timedelta(days=7)
            for log_file in self.logs_dir.glob('*.log*'):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < log_cutoff:
                    log_file.unlink()
                    removed_count += 1
                    logger.info(f"🗑️ Removed old log: {log_file.name}")
            
            logger.info(f"✅ Cleanup completed: {removed_count} files removed")
            
            # Save cleanup report
            cleanup_report = {
                'timestamp': datetime.now().isoformat(),
                'files_removed': removed_count,
                'cutoff_date': cutoff_date.isoformat(),
                'keep_days': self.keep_days
            }
            
            report_file = self.logs_dir / 'cleanup_report.json'
            with open(report_file, 'w') as f:
                json.dump(cleanup_report, f, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
    
    def disk_usage_check(self):
        """Check disk usage and log warnings"""
        try:
            disk_usage = os.statvfs(self.data_dir)
            free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
            total_space_gb = (disk_usage.f_frsize * disk_usage.f_blocks) / (1024**3)
            used_percentage = ((total_space_gb - free_space_gb) / total_space_gb) * 100
            
            logger.info(f"💾 Disk usage: {used_percentage:.1f}% used, {free_space_gb:.2f} GB free")
            
            if free_space_gb < 1:
                logger.warning(f"⚠️ LOW DISK SPACE: Only {free_space_gb:.2f} GB remaining!")
            elif used_percentage > 90:
                logger.warning(f"⚠️ High disk usage: {used_percentage:.1f}% used")
            
            # Save disk usage report
            usage_report = {
                'timestamp': datetime.now().isoformat(),
                'free_space_gb': free_space_gb,
                'total_space_gb': total_space_gb,
                'used_percentage': used_percentage
            }
            
            usage_file = self.logs_dir / 'disk_usage.json'
            with open(usage_file, 'w') as f:
                json.dump(usage_report, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Disk usage check failed: {e}")
    
    def update_heartbeat(self):
        """Update heartbeat for health monitoring"""
        heartbeat_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'running',
            'last_cleanup': self.get_last_cleanup_time(),
            'keep_days': self.keep_days
        }
        
        heartbeat_file = self.logs_dir / 'cleanup_heartbeat.json'
        with open(heartbeat_file, 'w') as f:
            json.dump(heartbeat_data, f, indent=2)
    
    def get_last_cleanup_time(self):
        """Get timestamp of last cleanup"""
        try:
            report_file = self.logs_dir / 'cleanup_report.json'
            if report_file.exists():
                with open(report_file) as f:
                    data = json.load(f)
                    return data.get('timestamp')
        except:
            pass
        return None
    
    def setup_schedules(self):
        """Setup cleanup schedules"""
        logger.info("📅 Setting up cleanup schedules...")
        
        # Daily cleanup at 3 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_files)
        
        # Disk usage check every 6 hours
        schedule.every(6).hours.do(self.disk_usage_check)
        
        # Heartbeat every 5 minutes
        schedule.every(5).minutes.do(self.update_heartbeat)
        
        logger.info("✅ Cleanup schedules configured")
    
    def run(self):
        """Main cleanup service loop"""
        logger.info("🧹 Starting Cleanup Service")
        
        self.setup_schedules()
        
        # Initial checks
        self.disk_usage_check()
        self.update_heartbeat()
        
        self.running = True
        logger.info("✅ Cleanup service is now running")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(300)  # Check every 5 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}")
                time.sleep(60)
        
        logger.info("🏁 Cleanup service stopped")

if __name__ == "__main__":
    service = CleanupService()
    service.run()
