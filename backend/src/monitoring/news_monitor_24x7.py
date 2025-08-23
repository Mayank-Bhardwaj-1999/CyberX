#!/usr/bin/env python3
"""
24/7 Cybersecurity News Monitor
Continuously monitors cybersecurity websites for new articles and appends them to JSON file.
Perfect for backend 24/7 operations with real-time status display.

Author: AI Assistant
Date: August 4, 2025
"""

import asyncio
import json
import sys
import time
import signal
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set
from pathlib import Path
from urllib.parse import urlparse
import hashlib
from tabulate import tabulate
from colorama import init, Fore, Back, Style

# Windows console safe print (avoid UnicodeEncodeError with emojis)
import platform
_WINDOWS = platform.system().lower().startswith('win')
_UNSAFE_CHARS = ['✅','❌','⚠️','🔗','🗄️','🔍','📁','📄','🔄','🆕','🖥️','📊','📝','🌐','🔔','⚡']
def safe_print(*args, **kwargs):
    if _WINDOWS:
        new_args = []
        for a in args:
            if isinstance(a, str):
                for ch in _UNSAFE_CHARS:
                    a = a.replace(ch, '')
            new_args.append(a)
        print(*new_args, **kwargs)
    else:
        print(*args, **kwargs)

# Add parent directories to path to import the scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scrapers'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from crawl4ai_scraper import EnhancedCyberSecurityNewsScraper

# Try to import backup manager and URL tracker from utils directory
try:
    # Add the utils directory to Python path
    utils_dir = os.path.join(os.path.dirname(__file__), '..', 'utils')
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    
    # Import Unicode helper for Windows compatibility
    try:
        from unicode_helper import safe_print, EMOJIS
        UNICODE_HELPER_AVAILABLE = True
    except ImportError:
        # Fallback if unicode_helper is not available
        def safe_print(*args, **kwargs):
            try:
                print(*args, **kwargs)
            except UnicodeEncodeError:
                # Simple fallback - replace common Unicode chars
                safe_args = []
                for arg in args:
                    if isinstance(arg, str):
                        safe_arg = (arg.replace("✅", "[OK]")
                                      .replace("❌", "[ERROR]")
                                      .replace("⚠️", "[WARNING]")
                                      .replace("🚀", "[START]")
                                      .replace("📰", "[NEWS]")
                                      .replace("🔄", "[CYCLE]"))
                        safe_args.append(safe_arg)
                    else:
                        safe_args.append(arg)
                print(*safe_args, **kwargs)
        
        EMOJIS = {
            'success': '[OK]',
            'error': '[ERROR]', 
            'warning': '[WARNING]',
            'rocket': '[START]',
            'news': '[NEWS]',
            'cycle': '[CYCLE]'
        }
        UNICODE_HELPER_AVAILABLE = False
    
    from backup_manager import BackupManager
    from url_tracker import URLTracker
    BACKUP_AVAILABLE = True
    URL_TRACKER_AVAILABLE = True
    safe_print(f"{EMOJIS['success']} Successfully imported backup manager and URL tracker")
except ImportError as e:
    # Define safe_print fallback if not defined yet
    if 'safe_print' not in locals():
        def safe_print(*args, **kwargs):
            try:
                print(*args, **kwargs)
            except UnicodeEncodeError:
                safe_args = []
                for arg in args:
                    if isinstance(arg, str):
                        safe_arg = (arg.replace("✅", "[OK]")
                                      .replace("❌", "[ERROR]")
                                      .replace("⚠️", "[WARNING]")
                                      .replace("🚀", "[START]")
                                      .replace("📰", "[NEWS]")
                                      .replace("🔄", "[CYCLE]"))
                        safe_args.append(safe_arg)
                    else:
                        safe_args.append(arg)
                print(*safe_args, **kwargs)
        
        EMOJIS = {
            'success': '[OK]',
            'error': '[ERROR]', 
            'warning': '[WARNING]',
            'rocket': '[START]',
            'news': '[NEWS]',
            'cycle': '[CYCLE]'
        }
    
    safe_print(f"{EMOJIS['warning']} Warning: Utils not available in monitor - {e}")
    BACKUP_AVAILABLE = False
    URL_TRACKER_AVAILABLE = False

# Initialize colorama for Windows color support
init(autoreset=True)

class NewsMonitor24x7:
    def __init__(self):
        self.scraper = EnhancedCyberSecurityNewsScraper()
        self.known_articles: Set[str] = set()  # Track article URLs we've seen
        self.monitoring = True
        self.stats = {
            'total_checks': 0,
            'new_articles_found': 0,
            'last_check': None,
            'start_time': datetime.now(),
            'errors': 0,
            'sites_status': {}
        }
        
        # Initialize backup manager
        if BACKUP_AVAILABLE:
            try:
                self.backup_manager = BackupManager()
                print(f"{Fore.GREEN}🗄️ Backup manager initialized")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Warning: Could not initialize backup manager: {e}")
                self.backup_manager = None
        else:
            self.backup_manager = None
        
        # Initialize URL tracker
        if URL_TRACKER_AVAILABLE:
            try:
                self.url_tracker = URLTracker()
                print(f"{Fore.GREEN}🔗 URL tracker initialized")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Warning: Could not initialize URL tracker: {e}")
                self.url_tracker = None
        else:
            self.url_tracker = None
        
        # 🚀 Enhanced Data Storage System
        self.live_output_file = 'data/cybersecurity_news_live.json'  # Temporary storage for new articles
        self.log_file = 'logs/monitor_log.txt'
        self.current_date = datetime.now().strftime("%Y%m%d")
        self.daily_archive_file = None  # Will be set dynamically
        
        # Initialize storage system
        self.setup_data_storage()
        
        # Load existing articles to avoid duplicates
        self.load_existing_articles()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n{Fore.YELLOW}🛑 Shutdown signal received. Stopping monitor...")
        self.monitoring = False
        sys.exit(0)
    
    def setup_data_storage(self):
        """🚀 Setup enhanced data storage system - Fixed daily file logic"""
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Set daily archive filename - ONE FILE PER DAY (no timestamp!)
        date_only = datetime.now().strftime("%Y%m%d")
        self.daily_archive_file = f'data/News_today_{date_only}.json'
        # Informational output (Windows-safe)
        safe_print(f"{Fore.CYAN}📁 Data Storage Setup:")
        safe_print(f"   Live File: {self.live_output_file}")
        safe_print(f"   Daily Archive: {self.daily_archive_file}")
        safe_print(f"   Fixed: One daily file per day (no multiple timestamped files)")
    
    def get_or_create_daily_archive(self):
        """Get today's daily archive file, create if needed - Enhanced with automatic backup"""
        current_date = datetime.now().strftime("%Y%m%d")
        
        # Check if date changed (new day)
        if current_date != self.current_date:
            print(f"{Fore.YELLOW}📅 NEW DAY DETECTED! Date changed from {self.current_date} to {current_date}")
            
            # Run automatic backup of previous day's data BEFORE creating new files
            if self.backup_manager:
                try:
                    print(f"{Fore.CYAN}🗄️ Running automatic backup for previous day's data...")
                    backup_stats = self.backup_manager.run_daily_backup()
                    
                    if backup_stats['total_errors'] == 0:
                        print(f"{Fore.GREEN}✅ Automatic backup completed successfully!")
                        print(f"{Fore.GREEN}📁 {backup_stats['total_backed_up']} files moved to backup folder")
                    else:
                        print(f"{Fore.YELLOW}⚠️ Automatic backup completed with {backup_stats['total_errors']} errors")
                        
                except Exception as e:
                    print(f"{Fore.RED}❌ Error during automatic backup: {e}")
                    print(f"{Fore.YELLOW}🔄 Continuing with new day setup...")
            else:
                print(f"{Fore.YELLOW}⚠️ Backup manager not available - skipping automatic backup")
            
            # Update current date and create new archive file
            self.current_date = current_date
            # Create NEW daily file for the NEW date (no timestamp!)
            self.daily_archive_file = f'data/News_today_{current_date}.json'
            print(f"{Fore.YELLOW}📅 New day detected! Created new archive: {self.daily_archive_file}")
        
        # Create daily archive if it doesn't exist
        if not os.path.exists(self.daily_archive_file):
            # Create file with proper format that matches existing daily files
            initial_archive = {
                'scraping_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_sites': 0,
                    'successful_sites': 0,
                    'failed_sites': 0,
                    'total_articles': 0,
                    'robust_timeout_enabled': True,
                    'interrupted': False
                },
                'results': {}
            }
            
            with open(self.daily_archive_file, 'w', encoding='utf-8') as f:
                json.dump(initial_archive, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.GREEN}✅ Created daily archive with proper format: {self.daily_archive_file}")
        
        return self.daily_archive_file
    
    def load_existing_articles(self):
        """🚀 Enhanced: Load existing articles from all sources to avoid duplicates"""
        try:
            # Load from live file
            if os.path.exists(self.live_output_file):
                with open(self.live_output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if data has proper structure
                if data and 'results' in data:
                    # Extract URLs from live data
                    for site_data in data.get('results', {}).values():
                        if isinstance(site_data, dict):
                            for article in site_data.get('articles', []):
                                if article.get('url'):
                                    self.known_articles.add(article['url'])
                else:
                    # File exists but has wrong structure, recreate it
                    print(f"{Fore.YELLOW}⚠️ Live file has incorrect structure, recreating...")
                    self.create_initial_live_file()
            
            # Load from today's daily archive
            daily_archive = self.get_or_create_daily_archive()
            if os.path.exists(daily_archive):
                with open(daily_archive, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract URLs from daily archive
                if data and 'results' in data:
                    for site_data in data.get('results', {}).values():
                        if isinstance(site_data, dict):
                            for article in site_data.get('articles', []):
                                if article.get('url'):
                                    self.known_articles.add(article['url'])
            
            # 🚀 ENHANCED: Load from URL tracker database for comprehensive duplicate prevention
            url_tracker_count = 0
            if self.url_tracker:
                scraped_urls = self.url_tracker.get_scraped_urls()
                self.known_articles.update(scraped_urls)
                url_tracker_count = len(scraped_urls)
                safe_print(f"{Fore.CYAN}🔗 Loaded {url_tracker_count} URLs from tracking database")
            
            safe_print(f"{Fore.GREEN}📚 Loaded {len(self.known_articles)} total existing articles from all sources")
            safe_print(f"    └─ Memory: {len(self.known_articles) - url_tracker_count} URLs")
            safe_print(f"    └─ Database: {url_tracker_count} URLs")
            
            # Create initial live file if it doesn't exist
            if not os.path.exists(self.live_output_file):
                self.create_initial_live_file()
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading existing articles: {e}")
            print(f"{Fore.YELLOW}🔧 Recreating live file structure...")
            self.known_articles = set()
            # Try to recreate the live file
            try:
                self.create_initial_live_file()
            except Exception as create_error:
                print(f"{Fore.RED}❌ Error creating live file: {create_error}")
    
    def create_initial_live_file(self):
        """Create initial live JSON file structure"""
        initial_data = {
            'monitoring_info': {
                'started_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_articles': 0,
                'monitor_version': '2.0',  # Updated version
                'status': 'active',
                'purpose': 'Temporary storage for new articles only'
            },
            'results': {}
        }
        
        with open(self.live_output_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        print(f"{Fore.GREEN}✅ Created initial live file: {self.live_output_file}")
    
    def create_initial_file(self):
        """DEPRECATED: Use create_initial_live_file instead"""
        pass
    
    def log_activity(self, message: str):
        """Log activity to file and console"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Console output
        print(log_entry)
        
        # File logging
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception as e:
            print(f"{Fore.RED}⚠️ Logging error: {e}")
    
    def generate_article_hash(self, article: Dict) -> str:
        """Generate unique hash for article to detect duplicates"""
        content = f"{article.get('title', '')}{article.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def check_for_new_articles(self) -> Dict:
        """🚀 Enhanced: Check all websites for new articles with advanced duplicate prevention"""
        safe_print(f"\n{Fore.CYAN}🔍 Checking for new articles... {datetime.now().strftime('%H:%M:%S')}")

        new_articles = {}
        total_new = 0

        try:
            # 🚀 CRITICAL FIX: Run the scraper with save_to_file=True to ensure data transfer
            # This ensures that articles are ALWAYS transferred from live to daily file
            print(f"{Fore.YELLOW}🔄 Running scraper with data transfer enabled...")
            results = await self.scraper.run_enhanced_scraper(save_to_file=True)

            if not results or 'results' not in results:
                print(f"{Fore.RED}❌ No results from scraper or invalid results structure")
                return {'error': 'No results from scraper'}

            # 🎯 CRITICAL SUCCESS: Scraper has completed data transfer
            total_articles_scraped = results.get('scraping_info', {}).get('total_articles', 0)
            print(f"{Fore.GREEN}✅ Scraper completed data transfer!")
            print(f"{Fore.GREEN}   Total articles in daily file: {total_articles_scraped}")
            
            # For monitoring mode, we now need to detect which articles are truly NEW
            # since the scraper has already saved everything to the daily file
            for site_url, site_data in results['results'].items():
                if not site_data.get('articles'):
                    continue

                site_new_articles = []
                for article in site_data['articles']:
                    article_url = article.get('url', '')
                    if not article_url:
                        continue

                    # Enhanced duplicate check: Local memory + URL tracker database
                    is_duplicate = (
                        article_url in self.known_articles or  # Local memory check
                        (self.url_tracker and self.url_tracker.is_url_scraped(article_url))  # Database check
                    )

                    if not is_duplicate:
                        # New article found!
                        site_new_articles.append(article)
                        self.known_articles.add(article_url)  # Add to local memory
                        total_new += 1
                    else:
                        # Skip duplicate with detailed logging
                        source_type = "local cache" if article_url in self.known_articles else "URL tracker"
                        print(f"⏩ Skipping duplicate from {source_type}: {article_url}")

                if site_new_articles:
                    new_articles[site_url] = {
                        'website_name': site_data.get('website_name', ''),
                        'articles': site_new_articles,
                        'new_count': len(site_new_articles)
                    }

            self.stats['new_articles_found'] += total_new

            if total_new > 0:
                safe_print(f"{Fore.GREEN}🆕 Found {total_new} truly new articles (duplicates filtered out)")
                safe_print(f"{Fore.GREEN}📂 Articles are already saved in daily file by scraper")
                safe_print(f"{Fore.GREEN}🤖 AI Summarizer will have content to process!")
            else:
                safe_print(f"{Fore.YELLOW}⚪ No new articles found (all were duplicates)")
                if total_articles_scraped > 0:
                    safe_print(f"{Fore.CYAN}📊 Scraper processed {total_articles_scraped} articles (no new ones)")

            return new_articles

        except Exception as e:
            self.stats['errors'] += 1
            error_msg = f"Error checking for new articles: {str(e)}"
            self.log_activity(f"{Fore.RED}❌ {error_msg}")
            print(f"{Fore.RED}❌ CRITICAL ERROR in monitoring: {error_msg}")
            return {'error': error_msg}
    
    def append_new_articles(self, new_articles: Dict):
        """🚀 SIMPLIFIED: Data transfer is now handled by scraper - just update live file for AI"""
        if not new_articles or 'error' in new_articles:
            return
        
        try:
            # 🚀 CRITICAL FIX: Since scraper now handles data transfer to daily file,
            # we only need to update the live file for AI processing
            
            total_new = sum(len(site_data.get('articles', [])) for site_data in new_articles.values())
            
            if total_new > 0:
                # 1. Track scraped URLs to prevent future duplicate processing
                if self.url_tracker:
                    all_articles = []
                    for site_data in new_articles.values():
                        all_articles.extend(site_data.get('articles', []))
                    
                    tracked_count = self.url_tracker.bulk_add_scraped_urls(all_articles)
                    print(f"{Fore.CYAN}🔗 Tracked {tracked_count} new URLs in scraped database")
                
                # 2. Update live file with ONLY the new articles for AI processing
                print(f"{Fore.YELLOW}� Updating live file with new articles for AI processing...")
                self.flush_and_update_live_file(new_articles)
                
                print(f"{Fore.GREEN}✅ Monitor flow complete:")
                print(f"{Fore.GREEN}   ├─ Scraper: Saved {total_new} articles to daily file")
                print(f"{Fore.GREEN}   ├─ Monitor: Updated live file for AI processing") 
                print(f"{Fore.GREEN}   └─ Ready: AI Summarizer can now process content!")
            else:
                print(f"{Fore.YELLOW}⚪ No new articles to process this cycle")
            
        except Exception as e:
            self.stats['errors'] += 1
            error_msg = f"Error in monitor article processing: {str(e)}"
            self.log_activity(f"{Fore.RED}❌ {error_msg}")
            print(f"{Fore.RED}❌ {error_msg}")
    
    def flush_and_update_live_file(self, new_articles: Dict):
        """🚀 LIVE MODE IMPLEMENTATION: Flush previous content and store ONLY new articles"""
        try:
            # Create a completely fresh live file with ONLY the new articles
            live_data = {
                'monitoring_info': {
                    'last_updated': datetime.now().isoformat(),
                    'status': 'live_mode_active',
                    'total_articles': 0,
                    'mode': 'live_flush',
                    'note': 'Live file flushed - contains only latest new articles'
                },
                'results': {}
            }
            
            # Add only the NEW articles (previous content is flushed)
            total_new_articles = 0
            for site_url, site_new_data in new_articles.items():
                live_data['results'][site_url] = {
                    'website_url': site_url,
                    'website_name': site_new_data.get('website_name', site_url),
                    'scraped_at': datetime.now().isoformat(),
                    'articles': site_new_data['articles'],
                    'total_articles': len(site_new_data['articles']),
                    'status': 'new_in_live_mode'
                }
                total_new_articles += len(site_new_data['articles'])
            
            live_data['monitoring_info']['total_articles'] = total_new_articles
            
            # 🚀 FLUSH: Completely replace live file content (no appending)
            with open(self.live_output_file, 'w', encoding='utf-8') as f:
                json.dump(live_data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.CYAN}🔄 Live file flushed! Now contains {total_new_articles} new articles only")
            print(f"{Fore.GREEN}📁 Previous articles archived in daily file, live file refreshed")
            
        except Exception as e:
            raise Exception(f"Live file flush error: {str(e)}")
    
    def update_live_file_for_ai(self, new_articles: Dict):
        """DEPRECATED: Use flush_and_update_live_file for live mode implementation"""
        # Redirect to new live mode implementation
        self.flush_and_update_live_file(new_articles)
    
    def clear_live_file_after_ai_processing(self):
        """Clear the live file after AI summarization is complete"""
        try:
            # Create empty live file structure
            empty_live_data = {
                'monitoring_info': {
                    'last_updated': datetime.now().isoformat(),
                    'status': 'ai_processing_complete',
                    'total_articles': 0,
                    'note': 'Live file cleared - ready for next articles'
                },
                'results': {}
            }
            
            with open(self.live_output_file, 'w', encoding='utf-8') as f:
                json.dump(empty_live_data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.GREEN}🧹 Live file cleared after AI processing")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not clear live file: {e}")
    
    def save_to_live_file(self, new_articles: Dict):
        """Save new articles to live file (temporary storage)"""
        try:
            # Load existing live data
            if os.path.exists(self.live_output_file):
                with open(self.live_output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check if data has proper structure, if not recreate it
                if not data or 'monitoring_info' not in data or 'results' not in data:
                    self.create_initial_live_file()
                    with open(self.live_output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            else:
                self.create_initial_live_file()
                with open(self.live_output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Update monitoring info
            data['monitoring_info']['last_updated'] = datetime.now().isoformat()
            data['monitoring_info']['status'] = 'active'
            
            # Add new articles to live data
            for site_url, site_new_data in new_articles.items():
                if site_url not in data['results']:
                    data['results'][site_url] = {
                        'website_url': site_url,
                        'website_name': site_new_data['website_name'],
                        'first_seen': datetime.now().isoformat(),
                        'articles': []
                    }
                
                # Add new articles
                data['results'][site_url]['articles'].extend(site_new_data['articles'])
                data['results'][site_url]['last_updated'] = datetime.now().isoformat()
                data['results'][site_url]['total_articles'] = len(data['results'][site_url]['articles'])
            
            # Update total count
            total_articles = sum(len(site_data.get('articles', [])) for site_data in data['results'].values())
            data['monitoring_info']['total_articles'] = total_articles
            
            # Save to live file
            with open(self.live_output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.CYAN}💾 Saved to live file: {self.live_output_file}")
            
        except Exception as e:
            raise Exception(f"Live file save error: {str(e)}")
    
    def append_to_daily_archive(self, new_articles: Dict):
        """Append new articles to daily archive (permanent storage) - Fixed format"""
        try:
            daily_archive = self.get_or_create_daily_archive()
            
            # Load existing archive data
            with open(daily_archive, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
            
            # Handle both archive_info and scraping_info formats for compatibility
            if 'scraping_info' in archive_data:
                # Use scraping_info format (matches actual daily files)
                archive_data['scraping_info']['timestamp'] = datetime.now().isoformat()
                info_key = 'scraping_info'
            else:
                # Use archive_info format (legacy)
                if 'archive_info' not in archive_data:
                    archive_data['archive_info'] = {
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'created_at': datetime.now().isoformat(),
                        'total_articles': 0,
                        'total_sites': 0
                    }
                archive_data['archive_info']['last_updated'] = datetime.now().isoformat()
                info_key = 'archive_info'
            
            # Append new articles to archive
            for site_url, site_new_data in new_articles.items():
                if site_url not in archive_data['results']:
                    # Create new site entry with proper structure
                    archive_data['results'][site_url] = {
                        'website_url': site_url,
                        'website_name': site_new_data['website_name'],
                        'scraped_at': datetime.now().isoformat(),
                        'articles_found': 0,
                        'articles': []
                    }
                
                # Append new articles (keeping all historical data)
                existing_articles = archive_data['results'][site_url].get('articles', [])
                new_article_list = site_new_data.get('articles', [])
                
                # Add new articles to existing ones
                existing_articles.extend(new_article_list)
                archive_data['results'][site_url]['articles'] = existing_articles
                archive_data['results'][site_url]['articles_found'] = len(existing_articles)
                archive_data['results'][site_url]['scraped_at'] = datetime.now().isoformat()
            
            # Update archive totals
            total_articles = sum(len(site_data.get('articles', [])) for site_data in archive_data['results'].values())
            successful_sites = len([site for site in archive_data['results'].values() if site.get('articles')])
            
            # Update the appropriate info section
            if info_key == 'scraping_info':
                archive_data['scraping_info']['total_articles'] = total_articles
                archive_data['scraping_info']['successful_sites'] = successful_sites
                archive_data['scraping_info']['total_sites'] = len(archive_data['results'])
            else:
                archive_data['archive_info']['total_articles'] = total_articles
                archive_data['archive_info']['total_sites'] = successful_sites
            
            # Save to daily archive
            with open(daily_archive, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.GREEN}✅ Appended {sum(len(site['articles']) for site in new_articles.values())} new articles to daily archive: {daily_archive}")
            
        except Exception as e:
            raise Exception(f"Daily archive append error: {str(e)}")
    
    def clear_live_file(self):
        """Clear live file after successful archive (keep only structure)"""
        try:
            # Reset live file to initial state
            initial_data = {
                'monitoring_info': {
                    'started_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'total_articles': 0,
                    'monitor_version': '2.0',
                    'status': 'active',
                    'purpose': 'Temporary storage for new articles only'
                },
                'results': {}
            }
            
            with open(self.live_output_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
            
            print(f"{Fore.YELLOW}🧹 Cleared live file (ready for next articles)")
            
        except Exception as e:
            print(f"{Fore.RED}⚠️ Warning: Could not clear live file: {str(e)}")
    
    def display_status_table(self, new_articles: Dict):
        """🚀 Enhanced: Display status with dual-file system information"""
        print(f"\n{Style.BRIGHT}{Back.BLUE} 📊 CYBERSECURITY NEWS MONITOR - STATUS REPORT {Style.RESET_ALL}")
        
        # Monitor Stats Table
        uptime = datetime.now() - self.stats['start_time']
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        monitor_stats = [
            ["🕐 Uptime", uptime_str],
            ["🔄 Total Checks", self.stats['total_checks']],
            ["📰 New Articles Found", self.stats['new_articles_found']],
            ["❌ Errors", self.stats['errors']],
            ["⏰ Last Check", self.stats['last_check'] or 'Never'],
            ["📁 Live File", self.live_output_file],
            ["📅 Daily Archive", self.daily_archive_file or 'Not set']
        ]
        
        print(f"\n{Fore.CYAN}🖥️  MONITOR STATISTICS:")
        print(tabulate(monitor_stats, headers=["Metric", "Value"], tablefmt="grid"))
        
        # New Articles Table
        if new_articles and 'error' not in new_articles:
            if new_articles:
                print(f"\n{Fore.GREEN}🆕 NEW ARTICLES FOUND:")
                new_articles_table = []
                
                for site_url, site_data in new_articles.items():
                    site_name = site_data['website_name']
                    new_count = site_data['new_count']
                    
                    for i, article in enumerate(site_data['articles'][:3], 1):  # Show first 3 articles
                        title = article.get('title', 'No title')[:60] + "..." if len(article.get('title', '')) > 60 else article.get('title', 'No title')
                        new_articles_table.append([
                            site_name if i == 1 else "",
                            f"📝 {title}",
                            article.get('word_count', 0),
                            "🖼️ Yes" if article.get('main_image') else "❌ No"
                        ])
                    
                    if len(site_data['articles']) > 3:
                        new_articles_table.append([
                            "",
                            f"... and {len(site_data['articles']) - 3} more articles",
                            "",
                            ""
                        ])
                
                headers = ["Website", "Article Title", "Words", "Image"]
                print(tabulate(new_articles_table, headers=headers, tablefmt="grid"))
                
                # Show storage information
                print(f"\n{Fore.MAGENTA}💾 STORAGE INFO:")
                print(f"   � Appended to daily archive: {self.daily_archive_file}")
                print(f"   🤖 Live file prepared for AI: {self.live_output_file}")
                print(f"   🔄 Workflow: Monitor → Daily Archive → AI Ready")
                print(f"   📝 Note: Run AI summarizer to process new articles")
            else:
                print(f"\n{Fore.YELLOW}📭 No new articles found in this check.")
        elif 'error' in new_articles:
            print(f"\n{Fore.RED}❌ ERROR: {new_articles['error']}")
        
        # Sites Status Table
        print(f"\n{Fore.MAGENTA}🌐 WEBSITES STATUS:")
        sites_table = []
        urls = self.scraper.load_urls_from_file('config/url_fetch.txt')
        
        for url in urls:
            domain = urlparse(url).netloc
            status = "🟢 Active" if url in new_articles else "🟡 No New"
            if 'error' in new_articles:
                status = "🔴 Error"
            
            sites_table.append([domain, status, url])
        
        print(tabulate(sites_table, headers=["Domain", "Status", "URL"], tablefmt="grid"))
        
        print(f"\n{Style.BRIGHT}⏰ Next check in 30 minutes... Press Ctrl+C to stop{Style.RESET_ALL}")
    
    async def monitor_cycle(self):
        """Single monitoring cycle"""
        self.stats['total_checks'] += 1
        self.stats['last_check'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check for new articles
        new_articles = await self.check_for_new_articles()
        
        # Append to file if new articles found
        if new_articles and 'error' not in new_articles and new_articles:
            self.append_new_articles(new_articles)
            self.log_activity(f"{Fore.GREEN}✅ Found and added {sum(site['new_count'] for site in new_articles.values())} new articles")
        
        # Display status
        self.display_status_table(new_articles)
        
        return new_articles
    
    async def start_monitoring(self):
        """🚀 Start enhanced 24/7 monitoring with dual-file system"""
        print(f"{Style.BRIGHT}{Fore.GREEN}🚀 Starting 24/7 Cybersecurity News Monitor...")
        print(f"{Fore.CYAN}📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}� Live File: {self.live_output_file}")
        print(f"{Fore.CYAN}📅 Daily Archive: {self.daily_archive_file}")
        print(f"{Fore.CYAN}📋 Log File: {self.log_file}")
        print(f"{Fore.YELLOW}⏰ Check interval: Every 30 minutes")
        print(f"{Fore.MAGENTA}💡 New articles are saved to live file then archived to daily file")
        print(f"{Style.BRIGHT}Press Ctrl+C to stop monitoring{Style.RESET_ALL}\n")
        
        # Initial check
        await self.monitor_cycle()
        
        # Schedule monitoring every 30 minutes
        while self.monitoring:
            try:
                # Wait 30 minutes
                await asyncio.sleep(30 * 60)  # 30 minutes
                
                if self.monitoring:
                    await self.monitor_cycle()
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}🛑 Monitor stopped by user")
                break
            except Exception as e:
                self.stats['errors'] += 1
                error_msg = f"Monitor error: {str(e)}"
                self.log_activity(f"{Fore.RED}❌ {error_msg}")
                print(f"{Fore.RED}❌ {error_msg}")
                
                # Wait 5 minutes before retrying after error
                await asyncio.sleep(5 * 60)

def main():
    """Main entry point"""
    import sys
    
    # Check for single-cycle mode
    single_cycle = "--single-cycle" in sys.argv
    
    try:
        monitor = NewsMonitor24x7()
        
        if single_cycle:
            # Run single monitoring cycle for batch integration
            print(f"{Fore.CYAN}🔄 Running single monitoring cycle...")
            asyncio.run(monitor.monitor_cycle())
            print(f"{Fore.GREEN}✅ Single cycle completed")
        else:
            # Run continuous monitoring
            asyncio.run(monitor.start_monitoring())
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}🚫 Monitor interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
