#!/usr/bin/env python3
"""
🔗 URL Tracking Manager
Manages tracking of scraped and summarized article URLs to prevent duplicate processing.
Reduces backend processing power by skipping already processed articles.

Author: AI Assistant
Date: August 6, 2025
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Set, List, Dict

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
                               .replace("⚠️", "[WARNING]"))
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            print(*safe_args, **kwargs)
    
    EMOJIS = {'success': '[OK]', 'error': '[ERROR]', 'warning': '[WARNING]'}
import hashlib
from urllib.parse import urlparse

class URLTracker:
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
        
        # URL tracking files
        self.scraped_urls_file = self.data_dir / "url_scraped.txt"
        self.summarized_urls_file = self.data_dir / "url_final_summarized.txt"

        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize files if they don't exist
        self._initialize_files()
        
    def _initialize_files(self):
        """Initialize URL tracking files if they don't exist"""
        if not self.scraped_urls_file.exists():
            with open(self.scraped_urls_file, 'w', encoding='utf-8') as f:
                f.write(f"# Scraped URLs Tracking File\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n")
                f.write(f"# Format: URL|SCRAPED_DATE|DOMAIN\n")
                f.write(f"# This file tracks all scraped article URLs to prevent duplicate processing\n\n")
            safe_print(f"✅ Created scraped URLs tracking file: {self.scraped_urls_file}")
            
        if not self.summarized_urls_file.exists():
            with open(self.summarized_urls_file, 'w', encoding='utf-8') as f:
                f.write(f"# Summarized URLs Tracking File\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n")
                f.write(f"# Format: URL|SUMMARIZED_DATE|DOMAIN|SUMMARY_STATUS\n")
                f.write(f"# This file tracks all successfully summarized article URLs\n\n")
            safe_print(f"✅ Created summarized URLs tracking file: {self.summarized_urls_file}")
    
    def _load_urls_from_file(self, file_path: Path) -> Set[str]:
        """Load URLs from tracking file"""
        urls = set()
        
        if not file_path.exists():
            return urls
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        # Extract URL from format: URL|DATE|DOMAIN or URL|DATE|DOMAIN|STATUS
                        parts = line.split('|')
                        if len(parts) >= 1:
                            urls.add(parts[0].strip())
        except Exception as e:
            safe_print(f"⚠️ Warning: Could not load URLs from {file_path}: {e}")
            
        return urls
    
    def get_scraped_urls(self) -> Set[str]:
        """Get all previously scraped URLs"""
        return self._load_urls_from_file(self.scraped_urls_file)
    
    def get_summarized_urls(self) -> Set[str]:
        """Get all previously summarized URLs"""
        return self._load_urls_from_file(self.summarized_urls_file)
    
    def is_url_scraped(self, url: str) -> bool:
        """Check if URL has been previously scraped"""
        scraped_urls = self.get_scraped_urls()
        return url in scraped_urls
    
    def is_url_summarized(self, url: str) -> bool:
        """Check if URL has been previously summarized"""
        summarized_urls = self.get_summarized_urls()
        return url in summarized_urls
    
    def add_scraped_url(self, url: str, domain: str = None) -> bool:
        """Add a URL to the scraped URLs list"""
        try:
            # Extract domain if not provided
            if not domain:
                domain = urlparse(url).netloc
            
            # Check if URL already exists
            if self.is_url_scraped(url):
                return True  # Already exists, no need to add
            
            # Add to file
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"{url}|{current_date}|{domain}\n"
            
            with open(self.scraped_urls_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return True
            
        except Exception as e:
            safe_print(f"❌ Error adding scraped URL {url}: {e}")
            return False
    
    def add_summarized_url(self, url: str, domain: str = None, status: str = "success") -> bool:
        """Add a URL to the summarized URLs list"""
        try:
            # Extract domain if not provided
            if not domain:
                domain = urlparse(url).netloc
            
            # Check if URL already exists
            if self.is_url_summarized(url):
                return True  # Already exists, no need to add
            
            # Add to file
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = f"{url}|{current_date}|{domain}|{status}\n"
            
            with open(self.summarized_urls_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            return True
            
        except Exception as e:
            safe_print(f"❌ Error adding summarized URL {url}: {e}")
            return False
    
    def filter_new_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter out articles that have already been scraped"""
        if not articles:
            return []
        
        scraped_urls = self.get_scraped_urls()
        new_articles = []
        
        for article in articles:
            article_url = article.get('url', '')
            if article_url and article_url not in scraped_urls:
                new_articles.append(article)
            else:
                safe_print(f"⏩ Skipping already scraped: {article_url}")
        
        return new_articles
    
    def filter_unsummarized_articles(self, articles: List[Dict]) -> List[Dict]:
        """Filter out articles that have already been summarized"""
        if not articles:
            return []
        
        summarized_urls = self.get_summarized_urls()
        unsummarized_articles = []
        
        for article in articles:
            article_url = article.get('url', '')
            if article_url and article_url not in summarized_urls:
                unsummarized_articles.append(article)
            else:
                safe_print(f"⏩ Skipping already summarized: {article_url}")
        
        return unsummarized_articles
    
    def bulk_add_scraped_urls(self, articles: List[Dict]) -> int:
        """Add multiple scraped URLs at once"""
        added_count = 0
        
        for article in articles:
            url = article.get('url', '')
            domain = article.get('domain', '')
            
            if url and self.add_scraped_url(url, domain):
                added_count += 1
        
        return added_count
    
    def bulk_add_summarized_urls(self, articles: List[Dict], status: str = "success") -> int:
        """Add multiple summarized URLs at once"""
        added_count = 0
        
        for article in articles:
            url = article.get('url', '')
            domain = article.get('domain', '')
            
            if url and self.add_summarized_url(url, domain, status):
                added_count += 1
        
        return added_count
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tracked URLs"""
        scraped_urls = self.get_scraped_urls()
        summarized_urls = self.get_summarized_urls()
        
        return {
            'total_scraped': len(scraped_urls),
            'total_summarized': len(summarized_urls),
            'pending_summarization': len(scraped_urls - summarized_urls)
        }
    
    def display_stats(self):
        """Display URL tracking statistics"""
        stats = self.get_stats()
        
        safe_print(f"\n📊 URL TRACKING STATISTICS")
        safe_print("="*40)
        safe_print(f"📥 Total Scraped URLs: {stats['total_scraped']}")
        safe_print(f"🤖 Total Summarized URLs: {stats['total_summarized']}")
        safe_print(f"⏳ Pending Summarization: {stats['pending_summarization']}")
        
        if stats['total_scraped'] > 0:
            completion_rate = (stats['total_summarized'] / stats['total_scraped']) * 100
            safe_print(f"📈 Completion Rate: {completion_rate:.1f}%")


def main():
    """Main function for standalone execution"""
    tracker = URLTracker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'stats':
            tracker.display_stats()
        else:
            print("Usage: python url_tracker.py [stats]")
    else:
        tracker.display_stats()


if __name__ == "__main__":
    main()
