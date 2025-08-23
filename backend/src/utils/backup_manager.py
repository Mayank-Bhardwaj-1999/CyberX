#!/usr/bin/env python3
"""
🗄️ Cybersecurity News Backup Manager
Automatically manages backup of old scraped and summarized data files.
Keeps main data directory clean while preserving historical data with proper date structure.

Author: AI Assistant
Date: August 6, 2025
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add utils directory to path for unicode helper
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
                    safe_arg = (arg.replace("✅", "[OK]").replace("❌", "[ERROR]")
                               .replace("⚠️", "[WARNING]").replace("🔄", "[CYCLE]"))
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            print(*safe_args, **kwargs)
    
    EMOJIS = {'success': '[OK]', 'error': '[ERROR]', 'warning': '[WARNING]', 'cycle': '[CYCLE]'}
from typing import List, Dict, Optional
import glob

class BackupManager:
    def __init__(self):
        # Find the project root by looking for key files that should be in the root
        current_path = Path(__file__).parent.absolute()
        
        # Traverse up the directory tree to find the project root
        while current_path.parent != current_path:  # Stop at filesystem root
            # Check if this directory contains project root indicators
            if (current_path / "main_launch.py").exists() or (current_path / "requirements.txt").exists():
                self.project_root = current_path
                break
            current_path = current_path.parent
        else:
            # Fallback to the old method if we can't find the root
            self.project_root = Path(__file__).parent.parent.parent
        
        self.data_dir = self.project_root / "data"
        self.backup_dir = self.data_dir / "backup"
        self.current_date = datetime.now().strftime("%Y%m%d")
        
        # Ensure both data and backup directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # File patterns to manage
        self.patterns = {
            'news_files': 'News_today_*.json',
            'summarized_files': 'summarized_news_hf*.json',
            'live_files': 'cybersecurity_news_live.json'
        }
        
    def get_file_date_from_name(self, filename: str) -> Optional[str]:
        """Extract date from filename in format YYYYMMDD"""
        # For News_today_YYYYMMDD.json
        if filename.startswith('News_today_') and filename.endswith('.json'):
            date_part = filename.replace('News_today_', '').replace('.json', '')
            if len(date_part) == 8 and date_part.isdigit():
                return date_part
        
        # For summarized_news_hf_YYYYMMDD.json
        if filename.startswith('summarized_news_hf_') and filename.endswith('.json'):
            date_part = filename.replace('summarized_news_hf_', '').replace('.json', '')
            if len(date_part) == 8 and date_part.isdigit():
                return date_part
        
        return None
    
    def get_file_modification_date(self, file_path: Path) -> str:
        """Get file modification date in YYYYMMDD format"""
        timestamp = file_path.stat().st_mtime
        return datetime.fromtimestamp(timestamp).strftime("%Y%m%d")
    
    def should_backup_file(self, file_path: Path) -> bool:
        """Determine if a file should be backed up (not today's file)"""
        filename = file_path.name
        
        # Extract date from filename
        file_date = self.get_file_date_from_name(filename)
        
        if file_date:
            # If we can extract date from filename, compare with current date
            return file_date != self.current_date
        else:
            # For files without date in name, check modification date
            mod_date = self.get_file_modification_date(file_path)
            return mod_date != self.current_date
    
    def backup_file_with_date(self, source_path: Path, target_name: str) -> bool:
        """Backup a file to backup directory with proper naming"""
        try:
            target_path = self.backup_dir / target_name
            
            # If target already exists, check if source is newer
            if target_path.exists():
                source_time = source_path.stat().st_mtime
                target_time = target_path.stat().st_mtime
                
                if source_time <= target_time:
                    safe_print(f"⏩ Skipping {source_path.name} - backup is up to date")
                    return True
            
            # Copy file to backup
            shutil.copy2(source_path, target_path)
            safe_print(f"✅ Backed up: {source_path.name} → {target_name}")
            return True
            
        except Exception as e:
            safe_print(f"❌ Error backing up {source_path.name}: {e}")
            return False
    
    def backup_news_files(self) -> Dict[str, int]:
        """Backup old News_today_*.json files"""
        stats = {'backed_up': 0, 'skipped': 0, 'errors': 0}
        
        print("\n📰 Backing up news files...")
        
        # Find all News_today_*.json files in data directory
        pattern = self.data_dir / self.patterns['news_files']
        news_files = list(self.data_dir.glob(self.patterns['news_files']))
        
        for file_path in news_files:
            if self.should_backup_file(file_path):
                # File should be backed up
                if self.backup_file_with_date(file_path, file_path.name):
                    # Remove original after successful backup
                    try:
                        file_path.unlink()
                        safe_print(f"🗑️  Removed original: {file_path.name}")
                        stats['backed_up'] += 1
                    except Exception as e:
                        safe_print(f"⚠️ Warning: Could not remove {file_path.name}: {e}")
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
            else:
                print(f"📅 Keeping current file: {file_path.name}")
                stats['skipped'] += 1
        
        return stats
    
    def backup_summarized_files(self) -> Dict[str, int]:
        """Backup old summarized files with proper naming"""
        stats = {'backed_up': 0, 'skipped': 0, 'errors': 0}
        
        print("\n🤖 Backing up summarized files...")
        
        # Find summarized_news_hf.json (without date)
        main_summarized = self.data_dir / "summarized_news_hf.json"
        
        if main_summarized.exists():
            if self.should_backup_file(main_summarized):
                # Get the date this file represents
                file_date = self.get_file_modification_date(main_summarized)
                # Check if it's from yesterday
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                
                if file_date == yesterday or file_date != self.current_date:
                    # Create backup name with date
                    backup_name = f"summarized_news_hf_{file_date}.json"
                    
                    if self.backup_file_with_date(main_summarized, backup_name):
                        try:
                            main_summarized.unlink()
                            safe_print(f"🗑️  Removed original: {main_summarized.name}")
                            stats['backed_up'] += 1
                        except Exception as e:
                            safe_print(f"⚠️ Warning: Could not remove {main_summarized.name}: {e}")
                            stats['errors'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    stats['skipped'] += 1
            else:
                print(f"📅 Keeping current summarized file: {main_summarized.name}")
                stats['skipped'] += 1
        
        # Also backup any existing dated summarized files
        dated_files = list(self.data_dir.glob("summarized_news_hf_*.json"))
        for file_path in dated_files:
            if self.should_backup_file(file_path):
                if self.backup_file_with_date(file_path, file_path.name):
                    try:
                        file_path.unlink()
                        safe_print(f"🗑️  Removed original: {file_path.name}")
                        stats['backed_up'] += 1
                    except Exception as e:
                        safe_print(f"⚠️ Warning: Could not remove {file_path.name}: {e}")
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
            else:
                stats['skipped'] += 1
        
        return stats
    
    def cleanup_live_file(self) -> bool:
        """Clean up old live file if it exists and is stale"""
        live_file = self.data_dir / "cybersecurity_news_live.json"
        
        if live_file.exists():
            if self.should_backup_file(live_file):
                print(f"\n🔄 Cleaning up stale live file: {live_file.name}")
                try:
                    # Just remove it, don't backup (it's temporary data)
                    live_file.unlink()
                    safe_print(f"🗑️  Removed stale live file")
                    return True
                except Exception as e:
                    safe_print(f"❌ Error removing live file: {e}")
                    return False
            else:
                print(f"📅 Live file is current, keeping it")
        
        return True
    
    def backup_previous_summarized_file(self) -> bool:
        """Backup the current summarized_news_hf.json before creating a new one"""
        main_summarized = self.data_dir / "summarized_news_hf.json"
        
        if not main_summarized.exists():
            print("ℹ️ No existing summarized file to backup")
            return True
            
        try:
            # Get the date this file should represent (modification date)
            file_date = self.get_file_modification_date(main_summarized)
            
            # Only backup if it's not today's file
            if file_date != self.current_date:
                backup_name = f"summarized_news_hf_{file_date}.json"
                
                if self.backup_file_with_date(main_summarized, backup_name):
                    safe_print(f"✅ Previous summarized file backed up as: {backup_name}")
                    return True
                else:
                    safe_print(f"❌ Failed to backup previous summarized file")
                    return False
            else:
                print(f"📅 Current summarized file is from today, no backup needed")
                return True
                
        except Exception as e:
            safe_print(f"❌ Error backing up previous summarized file: {e}")
            return False
    
    def smart_backup_on_new_content(self, content_type: str = "news") -> bool:
        """Smart backup that only backs up old files when new content is being created"""
        print(f"\n🧠 Smart backup triggered for new {content_type} content...")
        
        if content_type == "news":
            # Backup any old news files (not today's)
            return self.backup_news_files()['errors'] == 0
            
        elif content_type == "summarized":
            # Backup the current summarized file before new one is created
            return self.backup_previous_summarized_file()
            
        return False
    
    def run_daily_backup(self) -> Dict[str, any]:
        """Run complete daily backup process"""
        print(f"\n🗄️ CYBERSECURITY NEWS BACKUP MANAGER")
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print(f"📁 Data Directory: {self.data_dir}")
        print(f"🗄️ Backup Directory: {self.backup_dir}")
        print("="*60)
        
        total_stats = {
            'news_files': {'backed_up': 0, 'skipped': 0, 'errors': 0},
            'summarized_files': {'backed_up': 0, 'skipped': 0, 'errors': 0},
            'live_cleanup': False,
            'total_backed_up': 0,
            'total_errors': 0
        }
        
        # Backup news files
        total_stats['news_files'] = self.backup_news_files()
        
        # Backup summarized files
        total_stats['summarized_files'] = self.backup_summarized_files()
        
        # Cleanup live file
        total_stats['live_cleanup'] = self.cleanup_live_file()
        
        # Calculate totals
        total_stats['total_backed_up'] = (
            total_stats['news_files']['backed_up'] + 
            total_stats['summarized_files']['backed_up']
        )
        
        total_stats['total_errors'] = (
            total_stats['news_files']['errors'] + 
            total_stats['summarized_files']['errors']
        )
        
        # Summary
        print(f"\n📊 BACKUP SUMMARY")
        print("="*30)
        print(f"📰 News files backed up: {total_stats['news_files']['backed_up']}")
        safe_print(f"🤖 Summarized files backed up: {total_stats['summarized_files']['backed_up']}")
        safe_print(f"📊 Total files backed up: {total_stats['total_backed_up']}")
        safe_print(f"❌ Total errors: {total_stats['total_errors']}")
        print(f"🔄 Live file cleanup: {'✅' if total_stats['live_cleanup'] else '❌'}")
        
        if total_stats['total_errors'] == 0:
            print(f"\n✅ Backup completed successfully!")
        else:
            print(f"\n⚠️ Backup completed with {total_stats['total_errors']} errors")
        
        return total_stats
    
    def list_backup_files(self):
        """List all files in backup directory"""
        print(f"\n📋 BACKUP DIRECTORY CONTENTS")
        safe_print(f"📁 Location: {self.backup_dir}")
        print("="*50)
        
        if not self.backup_dir.exists():
            safe_print("❌ Backup directory does not exist")
            return
        
        backup_files = list(self.backup_dir.glob("*.json"))
        
        if not backup_files:
            print("📭 No backup files found")
            return
        
        # Group files by type
        news_files = [f for f in backup_files if f.name.startswith('News_today_')]
        summarized_files = [f for f in backup_files if f.name.startswith('summarized_news_hf_')]
        other_files = [f for f in backup_files if f not in news_files and f not in summarized_files]
        
        if news_files:
            print(f"\n📰 News Files ({len(news_files)}):")
            for file in sorted(news_files):
                file_size = file.stat().st_size / 1024  # KB
                mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"   {file.name} ({file_size:.1f} KB, modified: {mod_time})")
        
        if summarized_files:
            print(f"\n🤖 Summarized Files ({len(summarized_files)}):")
            for file in sorted(summarized_files):
                file_size = file.stat().st_size / 1024  # KB
                mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"   {file.name} ({file_size:.1f} KB, modified: {mod_time})")
        
        if other_files:
            print(f"\n📄 Other Files ({len(other_files)}):")
            for file in sorted(other_files):
                file_size = file.stat().st_size / 1024  # KB
                mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"   {file.name} ({file_size:.1f} KB, modified: {mod_time})")
        
        total_size = sum(f.stat().st_size for f in backup_files) / (1024 * 1024)  # MB
        print(f"\n📊 Total: {len(backup_files)} files, {total_size:.1f} MB")


def main():
    """Main entry point for standalone execution"""
    backup_manager = BackupManager()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            backup_manager.list_backup_files()
        elif sys.argv[1] == 'backup':
            backup_manager.run_daily_backup()
        else:
            print("Usage: python backup_manager.py [backup|list]")
    else:
        # Default: run backup
        backup_manager.run_daily_backup()


if __name__ == "__main__":
    main()
