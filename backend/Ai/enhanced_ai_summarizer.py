#!/usr/bin/env python3
"""
Enhanced AI News Summarizer - Single Comprehensive Script
Integrates with 24/7 Cybersecurity News Monitor
Automatically processes daily archives and creates AI summaries
"""

import json
import requests  # (HF legacy, now optional)
import time
import os
import sys
import io
from datetime import datetime
import glob

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Try to import Unicode helper for Windows compatibility
try:
    utils_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src", "utils")
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    from unicode_helper import safe_print, EMOJIS
    UNICODE_HELPER_AVAILABLE = True
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
                               .replace("⚠️", "[WARNING]").replace("🤖", "[AI]")
                               .replace("📊", "[DATA]").replace("🚀", "[START]"))
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            print(*safe_args, **kwargs)
    
    EMOJIS = {'success': '[OK]', 'error': '[ERROR]', 'warning': '[WARNING]', 'ai': '[AI]', 'data': '[DATA]', 'rocket': '[START]'}
    UNICODE_HELPER_AVAILABLE = False

# Try to import backup manager and URL tracker
try:
    from backup_manager import BackupManager
    from url_tracker import URLTracker
    BACKUP_AVAILABLE = True
    URL_TRACKER_AVAILABLE = True
    safe_print("✅ Successfully imported backup manager and URL tracker")
except ImportError as e:
    safe_print(f"⚠️ Warning: Utils not available in AI summarizer - {e}")
    BACKUP_AVAILABLE = False
    URL_TRACKER_AVAILABLE = False

# Fallback: redefine print to handle Unicode errors
original_print = print
def print(*args, **kwargs):
    try:
        original_print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert problematic characters
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_arg = (str(arg)
                    .replace('📄', '[DOC]')
                    .replace('✅', '[OK]')
                    .replace('⚠️', '[WARN]')
                    .replace('💾', '[SAVE]')
                    .replace('⏩', '[SKIP]')
                    .replace('🚀', '[ROCKET]')
                    .replace('🔄', '[REFRESH]')
                    .replace('📰', '[NEWS]')
                    .replace('🎯', '[TARGET]')
                    .replace('📊', '[CHART]')
                    .replace('🔧', '[TOOL]')
                    .replace('🔍', '[SEARCH]')
                    .replace('⏰', '[CLOCK]')
                    .replace('🌐', '[GLOBE]')
                    .replace('📈', '[GRAPH]')
                    .replace('📋', '[CLIPBOARD]')
                    .replace('🧪', '[TEST]')
                    .replace('📁', '[FOLDER]')
                    .replace('📅', '[CALENDAR]')
                )
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        original_print(*safe_args, **kwargs)

# Load environment from .env if available (optional)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# API Configuration (token loaded from environment for security)
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"  # legacy
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Gemini configuration (new primary path when USE_GEMINI=1 or GEMINI_API_KEY set)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
USE_GEMINI = os.getenv("USE_GEMINI", "1" if GEMINI_API_KEY else "0") == "1"

# Rate limiting for Gemini (RPM-30, TPM-1,000,000, RPD-200)
GEMINI_RATE_LIMIT = {
    "requests_per_minute": 30,
    "min_delay_between_requests": 2.1  # 60/30 = 2s + buffer
}

_gemini_model_instance = None
_gemini_request_times = []

def get_gemini_model():
    global _gemini_model_instance
    if not USE_GEMINI or not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai  # type: ignore
        if _gemini_model_instance is None:
            os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_model_instance = genai.GenerativeModel(GEMINI_MODEL)
        return _gemini_model_instance
    except Exception as e:
        safe_print(f"⚠️ Gemini init failed: {e}")
        return None

def enforce_gemini_rate_limit():
    """Enforce Gemini rate limits: 30 RPM with graceful delays"""
    global _gemini_request_times
    current_time = time.time()
    
    # Clean old requests (older than 1 minute)
    _gemini_request_times = [t for t in _gemini_request_times if current_time - t < 60]
    
    # Check if we're at the rate limit
    if len(_gemini_request_times) >= GEMINI_RATE_LIMIT["requests_per_minute"]:
        oldest_request = min(_gemini_request_times)
        wait_time = 60 - (current_time - oldest_request) + 1  # +1 buffer
        if wait_time > 0:
            safe_print(f"🚦 Gemini rate limit: waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    # Minimum delay between requests
    if _gemini_request_times:
        last_request = max(_gemini_request_times)
        time_since_last = current_time - last_request
        if time_since_last < GEMINI_RATE_LIMIT["min_delay_between_requests"]:
            delay = GEMINI_RATE_LIMIT["min_delay_between_requests"] - time_since_last
            safe_print(f"⏱️ Gemini pacing: waiting {delay:.1f}s...")
            time.sleep(delay)
    
    # Record this request
    _gemini_request_times.append(time.time())

CONFIG = {
    "max_retries": 2,
    "base_delay": 1,
    "max_delay": 5,
    "timeout": 10,
    "batch_size": 3,
    "fallback_summary_length": 3,
    "rate_limit_delay": 0.5,
    "model_loading_wait": 10
}

# Enhanced fallback summaries for when API fails
FALLBACK_SUMMARIES = [
    "This article discusses important cybersecurity developments and their implications for digital security.",
    "The article covers recent cybersecurity threats and provides analysis of current security trends.",
    "This piece examines cybersecurity challenges and potential solutions in the current digital landscape.",
    "The article addresses significant cybersecurity issues and their impact on organizations and individuals.",
    "This content explores cybersecurity developments and their relevance to current security practices."
]

class EnhancedAISummarizer:
    """Single comprehensive AI summarizer for cybersecurity news"""
    
    def __init__(self):
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_request_time = 0
        
        # Setup paths - Find project root by looking for key files
        current_path = os.path.abspath(__file__)
        while True:
            parent_dir = os.path.dirname(current_path)
            if parent_dir == current_path:  # Reached filesystem root
                # Fallback to old method
                self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
                break
            
            # Check if this directory contains project root indicators
            if (os.path.exists(os.path.join(parent_dir, "main_launch.py")) or 
                os.path.exists(os.path.join(parent_dir, "requirements.txt"))):
                self.data_dir = os.path.join(parent_dir, "data")
                break
            current_path = parent_dir
        
        self.output_file = os.path.join(self.data_dir, "summarized_news_hf.json")
        
        safe_print("🚀 Enhanced AI News Summarizer Initialized")
        safe_print(f"📁 Data Directory: {self.data_dir}")
        safe_print(f"💾 Output File: {self.output_file}")
        
        # Initialize backup manager
        if BACKUP_AVAILABLE:
            try:
                self.backup_manager = BackupManager()
                safe_print("🗄️ Backup manager initialized")
            except Exception as e:
                safe_print(f"⚠️ Warning: Could not initialize backup manager: {e}")
                self.backup_manager = None
        else:
            self.backup_manager = None
        
        # Initialize URL tracker
        if URL_TRACKER_AVAILABLE:
            try:
                self.url_tracker = URLTracker()
                safe_print("🔗 URL tracker initialized for summarization tracking")
            except Exception as e:
                safe_print(f"⚠️ Warning: Could not initialize URL tracker: {e}")
                self.url_tracker = None
        else:
            self.url_tracker = None
        
    def enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < CONFIG["rate_limit_delay"]:
            sleep_time = CONFIG["rate_limit_delay"] - time_since_last
            safe_print(f"⏰ Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    def get_fallback_summary(self, content):
        """Generate intelligent fallback summary from content"""
        try:
            content = content.strip()
            sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]
            
            if not sentences:
                return FALLBACK_SUMMARIES[hash(content) % len(FALLBACK_SUMMARIES)]
            
            # Enhanced fallback logic - prioritize cybersecurity terms
            cyber_keywords = [
                'vulnerability', 'attack', 'malware', 'ransomware', 'breach', 
                'security', 'hacker', 'threat', 'exploit', 'phishing',
                'cybersecurity', 'zero-day', 'data', 'encryption', 'firewall'
            ]
            
            # Score sentences based on cybersecurity relevance
            scored_sentences = []
            for sentence in sentences:
                score = 0
                sentence_lower = sentence.lower()
                for keyword in cyber_keywords:
                    if keyword in sentence_lower:
                        score += 1
                scored_sentences.append((sentence, score))
            
            # Sort by relevance score (highest first)
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            
            # Take top 2-3 most relevant sentences
            top_sentences = [s[0] for s in scored_sentences[:3]]
            
            # If no cyber-relevant sentences, use first few sentences
            if not any(s[1] > 0 for s in scored_sentences):
                top_sentences = sentences[:CONFIG["fallback_summary_length"]]
            
            summary = '. '.join(top_sentences)
            
            if not summary.endswith('.'):
                summary += '.'
                
            if len(summary) > 400:
                summary = summary[:397] + "..."
                
            return summary
            
        except:
            return FALLBACK_SUMMARIES[hash(content) % len(FALLBACK_SUMMARIES)]

    def get_latest_daily_file(self):
        """Get today's daily file - uses single daily file without timestamp"""
        today = datetime.now().strftime("%Y%m%d")
        
        # Use the fixed naming convention: News_today_YYYYMMDD.json (no timestamp!)
        today_file = os.path.join(self.data_dir, f"News_today_{today}.json")
        
        if os.path.exists(today_file):
            safe_print(f"✅ Found today's daily file: News_today_{today}.json")
            return today_file
        
        # If today's file doesn't exist, find the most recent one
        pattern = os.path.join(self.data_dir, "News_today_*.json")
        files = glob.glob(pattern)
        
        if files:
            # Filter out old timestamped files and prefer date-only files
            date_only_files = [f for f in files if len(os.path.basename(f).replace("News_today_", "").replace(".json", "")) == 8]
            
            if date_only_files:
                date_only_files.sort(reverse=True)
                safe_print(f"✅ Using most recent daily file: {os.path.basename(date_only_files[0])}")
                return date_only_files[0]
            else:
                files.sort(key=os.path.getmtime, reverse=True)
                safe_print(f"⚠️ Using timestamped file: {os.path.basename(files[0])}")
                return files[0]
        
        safe_print(f"❌ No daily archive files found. Expected: News_today_{today}.json")
        return None
    
    def get_live_file(self):
        """Get the live file for processing new articles"""
        live_file = os.path.join(self.data_dir, "cybersecurity_news_live.json")
        if os.path.exists(live_file):
            safe_print(f"🔄 Found live file with new articles: cybersecurity_news_live.json")
            return live_file
        return None
    
    def clear_live_file_after_processing(self):
        """Clear the live file after processing - signals monitor that AI is done"""
        live_file = os.path.join(self.data_dir, "cybersecurity_news_live.json")
        try:
            if os.path.exists(live_file):
                # Create empty structure
                empty_data = {
                    'monitoring_info': {
                        'last_updated': datetime.now().isoformat(),
                        'status': 'ai_processing_complete',
                        'total_articles': 0,
                        'note': 'Live file cleared - ready for next articles'
                    },
                    'results': {}
                }
                
                with open(live_file, 'w', encoding='utf-8') as f:
                    json.dump(empty_data, f, indent=2, ensure_ascii=False)
                
                safe_print(f"🧹 Live file cleared after AI processing")
        except Exception as e:
            safe_print(f"⚠️ Warning: Could not clear live file: {e}")

    def load_articles_from_daily_file(self, file_path):
        """Load articles from the daily archive format"""
        if not os.path.exists(file_path):
            safe_print(f"❌ Daily file {file_path} not found")
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            all_articles = []
            
            if "results" in data:
                for website_url, website_data in data["results"].items():
                    if "articles" in website_data:
                        for article in website_data["articles"]:
                            if (article.get("status") == "success" and 
                                article.get("content") and 
                                len(article.get("content", "").strip()) > 100):
                                
                                if "source" not in article:
                                    article["source"] = {
                                        "name": website_data.get("website_name", website_url),
                                        "url": website_url
                                    }
                                
                                all_articles.append(article)
            
            safe_print(f"📰 Loaded {len(all_articles)} valid articles from {os.path.basename(file_path)}")
            return all_articles
            
        except Exception as e:
            safe_print(f"❌ Error loading daily file {file_path}: {e}")
            return []

    def load_existing_summaries(self):
        """Load existing summaries to avoid duplicates"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                safe_print("⚠️ Corrupted summary file, starting fresh")
                return []
        return []

    def get_article_id(self, article):
        """Get unique identifier for article"""
        return article.get("url") or article.get("title")

    def is_article_recent(self, article, hours=24):
        """Check if article is recent"""
        try:
            if "scraped_at" in article:
                scraped_time = datetime.fromisoformat(article["scraped_at"].replace('Z', '+00:00'))
                time_diff = datetime.now() - scraped_time.replace(tzinfo=None)
                return time_diff.total_seconds() < (hours * 3600)
            return True
        except:
            return True

    def prioritize_articles(self, articles):
        """Prioritize articles by recency and importance"""
        return sorted(articles, key=lambda x: (
            not self.is_article_recent(x, 6),
            x.get("scraped_at", ""),
        ))

    def process_articles_smartly(self, articles, max_per_session=15):
        """Process articles with smart limits"""
        if not articles:
            return []
        
        prioritized = self.prioritize_articles(articles)
        to_process = prioritized[:max_per_session]
        
        if len(prioritized) > max_per_session:
            safe_print(f"🎯 Processing {max_per_session} of {len(prioritized)} articles (prioritizing recent)")
        
        return to_process

    def summarize_content(self, content, max_retries=None):
        """Summarize using Gemini with your exact working pattern and rate limiting."""
        if not content or len(content.strip()) < 50:
            return self.get_fallback_summary(content)

        # Primary: Gemini using your exact working pattern
        if USE_GEMINI and GEMINI_API_KEY:
            model = get_gemini_model()
            if model:
                try:
                    # Enforce rate limiting before request
                    enforce_gemini_rate_limit()
                    
                    # Your exact prompt format
                    prompt = f"""
Summarize the following article like a professional cybersecurity journalist.  
Requirements:
1. Use a compelling headline-style opening to hook the reader.  
2. Maintain a logical flow: urgency → explain the vulnerability → provide technical context → real-world impact → recommended action.  
3. Preserve all important details such as CVE numbers, patch dates, exploit methods, and threat actor involvement, but avoid overloading with unnecessary technical jargon.  
4. Vary sentence structure and use natural connector phrases like "According to researchers…", "In a concerning twist…", "Experts warn that…", etc. to make the text flow smoothly.  
5. Add narrative glue so the summary reads like a short news story rather than a fact list.  
6. Format as exactly **two short paragraphs** for scannability, with a natural break after the context is set in the first paragraph.  
7. Keep the summary concise and focused, avoiding unnecessary details.

Content:
{content}
"""
                    
                    safe_print("🤖 Sending request to Gemini...")
                    start_time = time.time()
                    response = model.generate_content(prompt)
                    end_time = time.time()
                    
                    if response and hasattr(response, 'text') and response.text:
                        summary = response.text.strip()
                        if len(summary.split()) >= 20:  # Minimum word count check
                            self.success_count += 1
                            safe_print(f"✅ Gemini summarized in {end_time - start_time:.1f}s")
                            return summary
                        else:
                            safe_print("⚠️ Gemini summary too short – using fallback")
                    else:
                        safe_print("⚠️ Gemini returned empty response")
                        
                except Exception as e:
                    safe_print(f"⚠️ Gemini error: {e} – falling back")
            else:
                safe_print("⚠️ Gemini model unavailable – falling back")

        # Legacy Hugging Face path (commented out but preserved for future reactivation)
        # if HF_API_TOKEN:
        #     max_retries = max_retries or CONFIG["max_retries"]
        #     self.request_count += 1
        #     for attempt in range(max_retries):
        #         try:
        #             self.enforce_rate_limit()
        #             truncated_content = content[:1000] if len(content) > 1000 else content
        #             payload = {"inputs": truncated_content, "parameters": {"max_length": 150, "min_length": 50, "do_sample": False, "early_stopping": True}}
        #             headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        #             result = requests.post(HF_API_URL, headers=headers, json=payload, timeout=CONFIG["timeout"])
        #             if result.status_code == 200:
        #                 response = result.json()
        #                 if isinstance(response, list) and response and response[0].get("summary_text"):
        #                     summary = response[0]["summary_text"].strip()
        #                     if summary:
        #                         self.success_count += 1
        #                         return summary
        #             elif result.status_code == 503:
        #                 time.sleep(CONFIG['model_loading_wait']); continue
        #             elif result.status_code == 429:
        #                 retry_after = int(result.headers.get('Retry-After', CONFIG["base_delay"] * (2 ** attempt)))
        #                 time.sleep(retry_after); continue
        #         except Exception as e:
        #             pass
        #         if attempt < max_retries - 1:
        #             time.sleep(min(CONFIG["base_delay"] * (2 ** attempt), CONFIG["max_delay"]))
        #     safe_print("⚠️ HF API failed – using fallback")

        # Final fallback
        self.failure_count += 1
        return self.get_fallback_summary(content)

    def run_summarization(self, auto_mode=False):
        """Main summarization function - Enhanced to handle both daily and live files"""
        if auto_mode:
            safe_print("🤖 Running in AUTO mode (called from monitor)")
        else:
            safe_print("🚀 Starting AI News Summarization...")
        
        # 🗄️ CRITICAL: Backup previous day's summarized file before starting
        if self.backup_manager:
            try:
                safe_print("🗄️ Checking for previous summarized file backup...")
                backup_success = self.backup_manager.backup_previous_summarized_file()
                if backup_success:
                    safe_print("✅ Previous summarized file backup completed")
                else:
                    safe_print("⚠️ Previous file backup had issues (continuing anyway)")
            except Exception as e:
                safe_print(f"⚠️ Backup check error: {e} (continuing anyway)")
        
        all_articles = []
        files_processed = []
        
        # 🚀 CRITICAL FIX: Better data source validation and error reporting
        safe_print("🔍 Checking for data sources...")
        
        # First, check for live file with new articles
        live_file = self.get_live_file()
        if live_file:
            try:
                live_articles = self.load_articles_from_daily_file(live_file)
                if live_articles:
                    all_articles.extend(live_articles)
                    files_processed.append("live file")
                    safe_print(f"🔄 ✅ Loaded {len(live_articles)} articles from live file")
                else:
                    safe_print(f"🔄 ⚠️ Live file exists but contains no valid articles")
            except Exception as e:
                safe_print(f"🔄 ❌ Error loading live file: {e}")
        else:
            safe_print(f"🔄 📭 No live file found - checking daily file only")
        
        # Then check daily file for additional articles
        daily_file = self.get_latest_daily_file()
        if daily_file:
            try:
                daily_articles = self.load_articles_from_daily_file(daily_file)
                if daily_articles:
                    # Remove duplicates between live and daily files
                    existing_urls = {article.get('url') for article in all_articles}
                    new_daily_articles = [a for a in daily_articles if a.get('url') not in existing_urls]
                    
                    all_articles.extend(new_daily_articles)
                    files_processed.append(f"daily file ({len(new_daily_articles)} new)")
                    safe_print(f"📅 ✅ Loaded {len(new_daily_articles)} additional articles from daily file")
                    safe_print(f"📅 Daily file: {os.path.basename(daily_file)}")
                else:
                    safe_print(f"📅 ❌ Daily file exists but contains no valid articles")
                    safe_print(f"📅 File: {os.path.basename(daily_file)}")
                    safe_print(f"🔍 This suggests the data transfer from scraper to daily file failed!")
            except Exception as e:
                safe_print(f"📅 ❌ Error loading daily file: {e}")
                safe_print(f"📅 File: {daily_file}")
        else:
            safe_print(f"📅 ❌ No daily file found!")
            today = datetime.now().strftime("%Y%m%d")
            expected_file = f"News_today_{today}.json"
            safe_print(f"� Expected file: {expected_file}")
            safe_print(f"🔍 This indicates the scraper did not create or transfer data to the daily file!")
        
        if not all_articles:
            safe_print("\n❌ CRITICAL ERROR: No valid articles found to summarize")
            safe_print("🔍 DIAGNOSIS:")
            safe_print("   ├─ No articles in live file")
            safe_print("   ├─ No articles in daily file") 
            safe_print("   └─ This indicates data transfer from scraper failed!")
            safe_print("\n💡 SOLUTION:")
            safe_print("   1. Check if scraper is creating 'cybersecurity_news_live.json'")
            safe_print("   2. Verify scraper transfers data to 'News_today_YYYYMMDD.json'")
            safe_print("   3. Ensure monitoring system calls scraper with proper parameters")
            if not auto_mode:
                safe_print("   4. Try running scraper manually first: python src/scrapers/crawl4ai_scraper.py")
            return False
        
        safe_print(f"📊 ✅ SUCCESS: Found {len(all_articles)} total articles from {', '.join(files_processed)}")
        
        # Load existing summaries
        existing_summaries = self.load_existing_summaries()
        summarized_ids = {self.get_article_id(a) for a in existing_summaries}

        # Filter unsummarized articles using multiple methods
        unsummarized = [a for a in all_articles if self.get_article_id(a) not in summarized_ids]
        
        # 🔗 Additional filtering using URL tracker to prevent duplicate processing
        if self.url_tracker:
            url_filtered = self.url_tracker.filter_unsummarized_articles(unsummarized)
            if len(url_filtered) < len(unsummarized):
                filtered_count = len(unsummarized) - len(url_filtered)
                safe_print(f"🔗 URL tracker filtered {filtered_count} already processed articles")
                unsummarized = url_filtered
        
        # 🔒 Additional deduplication by URL within current batch
        seen_urls = set()
        deduplicated_unsummarized = []
        for article in unsummarized:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated_unsummarized.append(article)
            elif url:
                safe_print(f"⏩ Skipping duplicate URL in current batch: {url}")
        
        unsummarized = deduplicated_unsummarized
        
        safe_print(f"🔄 Articles needing summarization: {len(unsummarized)}")
        
        if not unsummarized:
            safe_print("✅ All articles are already summarized!")
            if not auto_mode:
                safe_print(f"📊 Total summarized articles in database: {len(existing_summaries)}")
            return True

        # Process articles
        articles_to_process = self.process_articles_smartly(unsummarized, max_per_session=20 if not auto_mode else 10)
        safe_print(f"🎯 Processing {len(articles_to_process)} articles this session")

        new_summaries = []
        successful_count = 0
        failed_count = 0
        
        for idx, article in enumerate(articles_to_process):
            # Progress indicator
            progress = ((idx + 1) / len(articles_to_process)) * 100
            safe_print(f"\n[{progress:.1f}%] Processing article {idx+1}/{len(articles_to_process)}")
            safe_print(f"📄 {article.get('title', 'No title')[:80]}...")
            
            content = article.get("content", "")
            if len(content.strip()) < 100:
                safe_print("⏩ Skipping: Content too short")
                continue
            
            start_time = time.time()
            summary = self.summarize_content(content)
            end_time = time.time()

            if summary:
                summarized_article = {
                    "source": article.get("source", {"name": "Unknown", "url": ""}),
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "urlToImage": article.get("main_image", article.get("urlToImage", "")),
                    "publishedAt": article.get("publishedAt", article.get("scraped_at", "")),
                    "content": content,
                    "scraped_at": article.get("scraped_at", ""),
                    "summary": summary
                }
                
                new_summaries.append(summarized_article)
                successful_count += 1
                
                # 🔗 Track summarized URL
                if self.url_tracker and article.get("url"):
                    self.url_tracker.add_summarized_url(article["url"], status="success")
                    
                safe_print(f"✅ Summarized in {end_time - start_time:.1f}s")
            else:
                failed_count += 1
                
                # 🔗 Track failed summarization attempt
                if self.url_tracker and article.get("url"):
                    self.url_tracker.add_summarized_url(article["url"], status="failed")
                    
                safe_print("❌ Failed to summarize")

            # Smart rate limiting
            time.sleep(1.5 if summary else 3)

        # Save results
        safe_print(f"\n📊 SESSION SUMMARY:")
        safe_print(f"   ✅ Successfully summarized: {successful_count}")
        safe_print(f"   ❌ Failed to summarize: {failed_count}")
        safe_print(f"   📈 Success rate: {(successful_count/(successful_count+failed_count)*100) if (successful_count+failed_count) > 0 else 0:.1f}%")

        if new_summaries:
            # Backup previous summarized file before creating new one
            if self.backup_manager:
                try:
                    safe_print(f"🗄️ Backing up previous summarized file...")
                    self.backup_manager.smart_backup_on_new_content("summarized")
                except Exception as e:
                    safe_print(f"⚠️ Warning: Backup failed but continuing: {e}")
            
            all_summaries = new_summaries + existing_summaries
            
            # 🔒 Final deduplication pass before saving to prevent any duplicates in output
            seen_urls = set()
            deduplicated_summaries = []
            
            for summary in all_summaries:
                url = summary.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    deduplicated_summaries.append(summary)
                elif url:
                    safe_print(f"🔒 Removing duplicate summary for: {url}")
            
            safe_print(f"\n💾 Saving {len(deduplicated_summaries)} total summaries (added {len(new_summaries)} new, removed {len(all_summaries) - len(deduplicated_summaries)} duplicates)...")
            
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(deduplicated_summaries, f, indent=2, ensure_ascii=False)
            
            safe_print(f"✅ Output saved to {self.output_file}")
            safe_print(f"📈 Added {len(new_summaries)} new summaries.")
            safe_print(f"🎯 Total articles in database: {len(all_summaries)}")
            
            # Clear live file after successful processing
            self.clear_live_file_after_processing()
            
            remaining = len(unsummarized) - len(articles_to_process)
            if remaining > 0:
                safe_print(f"📋 {remaining} articles remaining for next session")
                
            return True
        else:
            safe_print("⚠️ No new articles were successfully summarized this session.")
            # Still clear live file even if no summaries were created
            self.clear_live_file_after_processing()
            return False

    def auto_check_and_summarize(self):
        """Auto-run summarization if there are new articles"""
        try:
            # 🗄️ CRITICAL: Backup previous day's summarized file before starting
            if self.backup_manager:
                try:
                    safe_print("🗄️ Auto-mode: Checking for previous summarized file backup...")
                    backup_success = self.backup_manager.backup_previous_summarized_file()
                    if backup_success:
                        safe_print("✅ Previous summarized file backup completed")
                except Exception as e:
                    safe_print(f"⚠️ Auto-mode backup check error: {e} (continuing anyway)")
            
            daily_file = self.get_latest_daily_file()
            if not daily_file:
                return False
                
            all_articles = self.load_articles_from_daily_file(daily_file)
            if not all_articles:
                return False
                
            existing_summaries = self.load_existing_summaries()
            summarized_ids = {self.get_article_id(a) for a in existing_summaries}
            unsummarized = [a for a in all_articles if self.get_article_id(a) not in summarized_ids]
            
            if len(unsummarized) > 0:
                safe_print(f"🔍 Auto-detected {len(unsummarized)} new articles needing summarization")
                return self.run_summarization(auto_mode=True)
            else:
                safe_print("✅ No new articles to summarize")
                return False
                
        except Exception as e:
            safe_print(f"❌ Error in auto-summarization check: {e}")
            return False

def main():
    """Main entry point"""
    summarizer = EnhancedAISummarizer()
    
    # Check command line arguments
    auto_mode = len(sys.argv) > 1 and sys.argv[1] == "--auto"
    
    if auto_mode:
        # Called automatically from monitoring system
        return summarizer.auto_check_and_summarize()
    else:
        # Manual run
        return summarizer.run_summarization(auto_mode=False)

if __name__ == "__main__":
    main()
