import asyncio
import json
import re
import os
import random
import signal
import sys
import os
import sys
import json
import time
import random
import asyncio
import signal
import re
from typing import List, Dict, Set
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Import unicode helper for safe printing
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'utils'))
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
                    safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                else:
                    safe_args.append(str(arg))
            print(*safe_args, **kwargs)
    
    EMOJIS = {
        'success': '[OK]',
        'error': '[ERROR]', 
        'warning': '[WARNING]'
    }
    UNICODE_HELPER_AVAILABLE = False

# Try to import URL tracker
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
    from url_tracker import URLTracker
    URL_TRACKER_AVAILABLE = True
except ImportError:
    URL_TRACKER_AVAILABLE = False
    safe_print("⚠️ Warning: URL tracker not available in scraper")

class EnhancedCyberSecurityNewsScraper:
    def __init__(self):
        self.scraped_urls: Set[str] = set()
        self.filtered_urls_count = 0  # Track smart filtering stats
        
        # Get the backend directory path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.backend_dir = os.path.join(current_dir, '..', '..')
        self.backend_dir = os.path.abspath(self.backend_dir)
        
        # Paths relative to backend directory
        self.config_dir = os.path.join(self.backend_dir, 'config')
        self.data_dir = os.path.join(self.backend_dir, 'data')
        
        print(f"🔧 Backend directory: {self.backend_dir}")
        print(f"🔧 Config directory: {self.config_dir}")
        print(f"🔧 Data directory: {self.data_dir}")
        
        # Initialize URL tracker if available
        if URL_TRACKER_AVAILABLE:
            try:
                self.url_tracker = URLTracker()
                safe_print("✅ URL tracker initialized in scraper")
            except Exception as e:
                safe_print(f"⚠️ Warning: Could not initialize URL tracker: {e}")
                self.url_tracker = None
        else:
            self.url_tracker = None
        
        # Enhanced user agents pool for better stealth
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0"
        ]
        
        # 🎯 Enhanced site-specific configurations with better stealth
        self.site_configs = {
            'darkreading.com': {
                'timeout': 90000, 'playwright_timeout': 120000, 'retries': 2, 
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'high',
                'delay_range': (3, 7), 'scroll_pause': 2
            },
            'krebsonsecurity.com': {
                'timeout': 75000, 'playwright_timeout': 90000, 'retries': 2,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'high',
                'delay_range': (2, 5), 'scroll_pause': 1.5
            },
            'bleepingcomputer.com': {
                'timeout': 90000, 'playwright_timeout': 120000, 'retries': 3,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'maximum',
                'delay_range': (4, 8), 'scroll_pause': 2.5
            },
            'securityweek.com': {
                'timeout': 60000, 'playwright_timeout': 75000, 'retries': 2,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (2, 4), 'scroll_pause': 1
            },
            'threatpost.com': {
                'timeout': 60000, 'playwright_timeout': 75000, 'retries': 2,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (2, 4), 'scroll_pause': 1
            },
            'scmagazine.com': {
                'timeout': 60000, 'playwright_timeout': 75000, 'retries': 1,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (2, 4), 'scroll_pause': 1
            },
            'thehackernews.com': {
                'timeout': 30000, 'playwright_timeout': 45000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'low',
                'delay_range': (0.5, 1.5), 'scroll_pause': 0.5
            },
            'cybersecuritynews.com': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'low',
                'delay_range': (1, 2), 'scroll_pause': 0.5
            },
            'infosecurity-magazine.com': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (1, 3), 'scroll_pause': 1
            },
            # 🌟 ADD MORE SITE CONFIGS FOR COMPREHENSIVE COVERAGE
            'csoonline.com': {
                'timeout': 60000, 'playwright_timeout': 75000, 'retries': 2,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (2, 4), 'scroll_pause': 1
            },
            'helpnetsecurity.com': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'low',
                'delay_range': (1, 3), 'scroll_pause': 1
            },
            'hackread.com': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (1, 3), 'scroll_pause': 1
            },
            'cyware.com': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (1, 3), 'scroll_pause': 1
            },
            'cybersecuritydive.com': {
                'timeout': 60000, 'playwright_timeout': 75000, 'retries': 1,
                'wait_until': 'networkidle', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (2, 4), 'scroll_pause': 1
            },
            'the420.in': {
                'timeout': 30000, 'playwright_timeout': 45000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'low',
                'delay_range': (0.5, 1.5), 'scroll_pause': 0.5
            },
            'default': {
                'timeout': 45000, 'playwright_timeout': 60000, 'retries': 1,
                'wait_until': 'domcontentloaded', 'wait_for': None, 'stealth_mode': 'medium',
                'delay_range': (1, 3), 'scroll_pause': 1
            }
        }
        
        # 🛡️ ENHANCED BrowserConfig with maximum stealth
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1920,  # Full HD for better stealth
            viewport_height=1080,
            verbose=False,
            use_persistent_context=True,
            user_data_dir=os.path.join(self.backend_dir, "enhanced_cybersec_crawler_profile"),
            user_agent_mode="random",
            ignore_https_errors=True,
            # Enhanced stealth arguments
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-extensions",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-default-apps",
                "--disable-sync",
                "--disable-background-networking",
                "--disable-component-extensions-with-background-pages",
                "--no-default-browser-check",
                "--no-pings",
                "--disable-client-side-phishing-detection",
                "--disable-hang-monitor",
                "--disable-prompt-on-repost",
                "--disable-domain-reliability",
                "--enable-features=NetworkService,NetworkServiceLogging",
                "--force-color-profile=srgb",
                "--disable-features=AudioServiceOutOfProcess",
                # Mimic real browser behavior
                "--enable-automation=false",
                "--disable-blink-features=AutomationControlled",
            ],
        )

    def get_domain_config(self, url: str) -> dict:
        """Get site-specific configuration for dynamic handling"""
        domain = urlparse(url).netloc.lower()
        
        for site_domain, config in self.site_configs.items():
            if site_domain in domain:
                return config
        return self.site_configs['default']

    async def setup_stealth_page(self, page, domain_config):
        """Enhanced stealth setup for the page"""
        try:
            # Set timeouts
            timeout = domain_config['playwright_timeout']
            page.set_default_navigation_timeout(timeout)
            page.set_default_timeout(timeout)
            
            # Set realistic viewport
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Enhanced headers that mimic real browsers
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": random.choice(self.user_agents)
            }
            
            await page.set_extra_http_headers(headers)
            
            # Inject stealth scripts to hide automation
            stealth_script = """
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Hide chrome object
                window.chrome = {
                    runtime: {},
                };
                
                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """
            
            await page.add_init_script(stealth_script)
            
            print(f"🛡️ Enhanced stealth setup completed for {domain_config.get('stealth_mode', 'medium')} mode")
            
        except Exception as e:
            safe_print(f"⚠️ Warning in stealth setup: {e}")
        
        return page

    async def on_page_context_created(self, page, context, **kwargs):
        """Enhanced page context setup"""
        try:
            # Get domain config for this page
            url = kwargs.get('url', '')
            domain_config = self.get_domain_config(url)
            
            # Apply stealth setup
            page = await self.setup_stealth_page(page, domain_config)
            
            print(f"🔧 Enhanced page context created")
        except Exception as e:
            safe_print(f"⚠️ Warning in page context creation: {e}")
        return page

    async def before_goto(self, page, context, url, config, **kwargs):
        """Enhanced before-navigation setup"""
        try:
            domain = urlparse(url).netloc.lower()
            domain_config = self.get_domain_config(url)
            
            # Apply domain-specific configuration
            timeout = domain_config['timeout']
            page.set_default_navigation_timeout(timeout)
            config.page_timeout = timeout
            config.wait_until = domain_config['wait_until']
            config.wait_for = domain_config['wait_for']
            
            # Enhanced delay for problematic sites
            if domain_config['stealth_mode'] in ['high', 'maximum']:
                delay = random.uniform(*domain_config['delay_range'])
                safe_print(f"🕒 Applying stealth delay: {delay:.1f}s for {domain}")
                await asyncio.sleep(delay)
            
            print(f"🚦 Applied enhanced config for {domain}: {domain_config['stealth_mode']} stealth mode")
            
        except Exception as e:
            safe_print(f"⚠️ Warning in before_goto hook: {e}")
        
        return page

    async def extract_article_links(self, url: str, html_content: str) -> List[Dict]:
        """Enhanced article link extraction with smart URL deduplication"""
        soup = BeautifulSoup(html_content, 'html.parser')
        base_url = f"https://{urlparse(url).netloc}"
        domain = urlparse(url).netloc
        articles = []
        
        print(f"  🔍 Extracting articles from {domain}...")
        
        # Smart URL filtering - check against already processed URLs
        processed_urls = set()
        if self.url_tracker:
            try:
                scraped_urls = self.url_tracker.get_scraped_urls()
                summarized_urls = self.url_tracker.get_summarized_urls()
                processed_urls = scraped_urls.union(summarized_urls)
                print(f"  🧠 Smart filtering: {len(processed_urls)} URLs already processed")
            except Exception as e:
                print(f"  ⚠️ Warning: Could not load processed URLs: {e}")
        
        # Enhanced site-specific extraction
        if 'bleepingcomputer.com' in domain:
            print("  🎯 Applying Bleeping Computer specific extraction...")
            
            # Updated selectors for Bleeping Computer based on 2025 analysis
            selectors = [
                # Primary news article links
                'a[href*="/news/"]',  # Main news articles
                'a[href*="bleepingcomputer.com/news/"]',  # Full URLs
                # Headlines and titles
                'h1 a[href*="/news/"]',
                'h2 a[href*="/news/"]', 
                'h3 a[href*="/news/"]',
                # Article containers
                'article a[href*="/news/"]',
                '.post a[href*="/news/"]',
                # Story containers (found 3 in analysis)
                '.story a[href*="/news/"]',
                # Generic content areas
                '.content a[href*="/news/"]',
                'main a[href*="/news/"]',
                '#content a[href*="/news/"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        
                        # Smart filtering: Skip if already processed
                        if href in processed_urls:
                            print(f"    ⏩ Skipping already processed: {title[:50]}...")
                            self.filtered_urls_count += 1
                            continue
                        
                        # Validate it's a proper Bleeping Computer news article
                        if ('/news/' in href and 
                            'bleepingcomputer.com' in href and
                            len(title) > 20 and len(title) < 200):
                            
                            articles.append({
                                'title': title,
                                'url': href,
                                'domain': domain,
                                'found_on': base_url
                            })
                        
                if articles:
                    break
            
            # If no articles found, try broader approach
            if not articles:
                print("  🔄 Trying broader selectors for Bleeping Computer...")
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    # Smart filtering: Skip if already processed
                    if href in processed_urls:
                        continue
                    
                    if (href and title and len(title) > 25 and len(title) < 150 and
                        '/news/' in href and 'bleepingcomputer.com' in href):
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                    if len(articles) >= 10:
                        break
        
        elif 'krebsonsecurity.com' in domain:
            print("  🎯 Applying Krebs on Security specific extraction...")
            
            # Updated selectors for Krebs on Security based on 2025 analysis
            selectors = [
                # Article links with krebs domain
                'a[href*="krebsonsecurity.com/2025/"]',
                'a[href*="krebsonsecurity.com/2024/"]',
                'a[href*="krebsonsecurity.com/"]',
                # Headlines
                'h1 a', 'h2 a', 'h3 a',
                # Entry titles and post titles
                'h2.entry-title a',
                '.post-title a',
                'article h2 a',
                'h3.entry-title a',
                '.entry-header h2 a',
                # Article containers
                'article a[href*="krebsonsecurity.com"]',
                '.post a[href*="krebsonsecurity.com"]',
                # Content areas
                '.content a[href*="krebsonsecurity.com"]',
                'main a[href*="krebsonsecurity.com"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        
                        # Smart filtering: Skip if already processed
                        if href in processed_urls:
                            print(f"    ⏩ Skipping already processed: {title[:50]}...")
                            continue
                        
                        # Validate it's a proper Krebs article
                        if ('krebsonsecurity.com' in href and
                            any(year in href for year in ['2024', '2025']) and
                            len(title) > 20 and len(title) < 200):
                            
                            articles.append({
                                'title': title,
                                'url': href,
                                'domain': domain,
                                'found_on': base_url
                            })
                        
                if articles:
                    break
            
            # Broader search if needed
            if not articles:
                print("  🔄 Trying broader selectors for Krebs on Security...")
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    # Smart filtering: Skip if already processed
                    if href in processed_urls:
                        continue
                    
                    if (href and title and len(title) > 25 and len(title) < 150 and
                        'krebsonsecurity.com' in href and
                        any(year in href for year in ['2024', '2025'])):
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                    if len(articles) >= 10:
                        break
        
        elif 'darkreading.com' in domain:
            print("  🎯 Applying Dark Reading specific extraction...")
            
            selectors = [
                '.headline a',
                'h2.headline a',
                'h3.headline a',
                '.story-headline a',
                '.article-title a',
                'article h2 a',
                '.content-item h2 a',
                '.teaser-headline a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                if articles:
                    break
        
        elif 'securityweek.com' in domain:
            print("  🎯 Applying Security Week specific extraction...")
            
            selectors = [
                '.field-content h2 a',
                '.views-field-title a',
                'h2.node-title a',
                '.article-title a',
                'article h2 a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                if articles:
                    break
        
        elif 'thehackernews.com' in domain:
            print("  🎯 Applying The Hacker News specific extraction...")
            
            # Updated selectors for The Hacker News - Working as of August 2025
            selectors = [
                # Primary article links - these are the main ones that work
                'a[href*="/2025/"]',  # 2025 articles (most current)
                'a[href*="/2024/"]',  # 2024 articles
                'a[href*="thehackernews.com/2025/"]',  # Full URLs with 2025
                'a[href*="thehackernews.com/2024/"]',  # Full URLs with 2024
                # Generic selectors that catch articles
                'h1 a[href*="thehackernews.com"]',
                'h2 a[href*="thehackernews.com"]',
                'h3 a[href*="thehackernews.com"]',
                # Links in article containers
                'article a[href*="/2025/"]',
                'article a[href*="/2024/"]',
                # Post containers
                '.post a[href*="/2025/"]',
                '.post a[href*="/2024/"]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        
                        # Validate it's a proper article URL
                        if ('thehackernews.com' in href and 
                            any(year in href for year in ['2024', '2025']) and
                            href.endswith('.html')):
                            
                            articles.append({
                                'title': title,
                                'url': href,
                                'domain': domain,
                                'found_on': base_url
                            })
                        
                if articles:
                    break
            
            # If no articles found, try even broader selectors
            if not articles:
                print("  🔄 Trying broader selectors for The Hacker News...")
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if (href and title and len(title) > 20 and len(title) < 150 and
                        'thehackernews.com' in href and 
                        any(year in href for year in ['2024', '2025']) and
                        href.endswith('.html')):
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                    if len(articles) >= 10:  # Limit for efficiency
                        break
        
        # 🌟 ADD MORE SITE-SPECIFIC EXTRACTORS FROM YOUR ORIGINAL CODE
        elif 'the420.in' in domain:
            print("  🎯 Applying The420.in specific extraction...")
            
            # Updated selectors for The420.in based on analysis
            selectors = [
                # Primary article links
                'a[href*="the420.in/"]',
                'h1 a', 'h2 a', 'h3 a',  # Headlines with links
                '.entry-title a',
                '.post-title a', 
                'article a',
                '.title a',
                '.headline a',
                # WordPress patterns
                '.wp-block-heading a',
                '.entry-header a',
                # Content areas
                '.content a[href*="the420.in/"]',
                'main a[href*="the420.in/"]',
                # Generic content links that point to articles
                'a[href*="/"][title]'  # Links with titles
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        
                        # Validate it's a proper article URL for the420.in
                        if ('the420.in' in href and 
                            not any(skip in href.lower() for skip in ['login', 'register', 'contact', 'about', 'privacy', 'terms']) and
                            len(title) > 20 and len(title) < 200):
                            
                            articles.append({
                                'title': title,
                                'url': href,
                                'domain': domain,
                                'found_on': base_url
                            })
                        
                if articles:
                    break
            
            # If no articles found with specific selectors, try broad search
            if not articles:
                print("  🔄 Trying broader selectors for The420.in...")
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if (href and title and len(title) > 25 and len(title) < 150 and
                        'the420.in' in href and
                        not any(skip in href.lower() for skip in ['wp-admin', 'wp-login', 'feed', 'rss', 'sitemap', 'robots.txt'])):
                        
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                    if len(articles) >= 15:  # Reasonable limit
                        break
        
        elif 'infosecurity-magazine.com' in domain:
            print("  🎯 Applying Infosecurity Magazine specific extraction...")
            
            selectors = [
                '.teaser__title a',
                '.article-teaser h2 a',
                'h2.teaser-title a',
                '.content-item h3 a',
                'article h2 a',
                '.headline a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                if articles:
                    break
        
        elif 'cybersecuritynews.com' in domain:
            print("  🎯 Applying Cybersecurity News specific extraction...")
            
            selectors = [
                '.entry-title a',
                'h2.entry-title a',
                '.post-title a',
                'article h2 a',
                '.wp-block-heading a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                if articles:
                    break
        
        elif 'scmagazine.com' in domain:
            print("  🎯 Applying SC Magazine specific extraction...")
            
            selectors = [
                '.field-content h2 a',
                '.article-title a',
                'h2.node-title a',
                '.views-field-title a',
                'article h2 a'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    title = element.get_text(strip=True)
                    if href and title and len(title) > 15:
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        articles.append({
                            'title': title,
                            'url': href,
                            'domain': domain,
                            'found_on': base_url
                        })
                        
                if articles:
                    break
        
        else:
            # 🌟 COMPREHENSIVE GENERAL EXTRACTION (Enhanced from your original code)
            print("  🎯 Applying comprehensive general extraction...")
            
            # Multiple extraction strategies for maximum coverage
            extraction_strategies = [
                # Strategy 1: Modern article patterns
                {
                    'name': 'Modern Article Patterns',
                    'selectors': [
                        'a[href*="/news/"]', 'a[href*="/article/"]', 'a[href*="/post/"]',
                        'a[href*="/story/"]', 'a[href*="/blog/"]',
                        'a[href*="/2024/"]', 'a[href*="/2025/"]',  # Year-based URLs
                        'article a[href*="/"]', '.article a[href*="/"]'
                    ]
                },
                # Strategy 2: WordPress and CMS patterns
                {
                    'name': 'CMS Patterns',
                    'selectors': [
                        '.entry-title a', '.post-title a', '.article-title a',
                        '.news-title a', '.story-title a', '.content-title a',
                        'h1.entry-title a', 'h2.entry-title a', 'h3.entry-title a',
                        '.wp-block-post-title a', '.wp-block-heading a'
                    ]
                },
                # Strategy 3: Headline patterns
                {
                    'name': 'Headline Patterns',
                    'selectors': [
                        'h1 a[href*="/"]', 'h2 a[href*="/"]', 'h3 a[href*="/"]',
                        '.headline a', '.title a', '.header a',
                        'h1 a[title]', 'h2 a[title]', 'h3 a[title]'  # Links with titles
                    ]
                },
                # Strategy 4: Content container patterns
                {
                    'name': 'Content Containers',
                    'selectors': [
                        'article h1 a', 'article h2 a', 'article h3 a',
                        'article .title a', 'article .headline a',
                        '.post-content a[href*="/"]', '.entry-content a[href*="/"]',
                        '.content a[href*="/"]', 'main a[href*="/"]'
                    ]
                },
                # Strategy 5: Modern web patterns
                {
                    'name': 'Modern Web Patterns',
                    'selectors': [
                        '[data-post-id] a', '[data-article-id] a',
                        '.card-title a', '.teaser-title a',
                        '.link-title a', '.story-headline a',
                        '.feed-item a', '.listing-item a'
                    ]
                },
                # Strategy 6: Broad link search with validation
                {
                    'name': 'Validated Link Search',
                    'selectors': [
                        'a[href][title]',  # Links with both href and title
                        'a[href*="/"][title]'  # Internal links with titles
                    ]
                }
            ]
            
            # Try each strategy until we find articles
            for strategy in extraction_strategies:
                if articles:  # Stop if we already found articles
                    break
                    
                print(f"    🔍 Trying {strategy['name']}...")
                
                for selector in strategy['selectors']:
                    elements = soup.select(selector)
                    strategy_articles = []
                    
                    for element in elements:
                        href = element.get('href')
                        title = element.get_text(strip=True)
                        
                        if href and title:
                            # Clean up the URL
                            if href.startswith('/'):
                                href = urljoin(base_url, href)
                            elif not href.startswith('http'):
                                continue  # Skip invalid URLs
                            
                            # Use enhanced validation method
                            if self.is_valid_article_link(href, title, domain):
                                strategy_articles.append({
                                    'title': title,
                                    'url': href,
                                    'domain': domain,
                                    'found_on': base_url,
                                    'extraction_method': strategy['name'],
                                    'selector_used': selector
                                })
                    
                    if strategy_articles:
                        articles.extend(strategy_articles)
                        print(f"    ✅ Found {len(strategy_articles)} articles using {strategy['name']}")
                        break  # Move to next strategy
                
                if articles:
                    break  # Stop trying strategies if we found articles
            
            # If still no articles, try very broad search
            if not articles:
                print("    🔄 Trying broad link extraction...")
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if href and title and len(title) > 20 and len(title) < 150:
                        # Clean up the URL
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        elif not href.startswith('http'):
                            continue
                        
                        # Smart filtering: Skip if already processed
                        if href in processed_urls:
                            continue
                        
                        # More restrictive filtering for broad search
                        if (self.is_cybersecurity_related(title, domain) and
                            not any(skip in href.lower() for skip in [
                                '#', 'javascript:', 'mailto:', 'tel:',
                                'facebook.com', 'twitter.com', 'linkedin.com',
                                'youtube.com', 'instagram.com', 'reddit.com'
                            ])):
                            articles.append({
                                'title': title,
                                'url': href,
                                'domain': domain,
                                'found_on': base_url,
                                'extraction_method': 'Broad Search'
                            })
                            
                            if len(articles) >= 15:  # Limit broad search results
                                break
        
        # Remove duplicates
        unique_articles = []
        seen_urls = set()
        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)
        
        # Smart filtering statistics
        if processed_urls:
            filtered_count = len(processed_urls)
            print(f"  🧠 Smart filtering: {filtered_count} URLs already processed, {len(unique_articles)} new articles found")
        else:
            print(f"  📊 Found {len(unique_articles)} unique articles")
            
        return unique_articles[:15]  # Limit per site
    
    def is_valid_article_link(self, href: str, title: str, domain: str) -> bool:
        """Enhanced validation for article links"""
        if not href or not title:
            return False
        
        # Title length validation
        if len(title) < 20 or len(title) > 250:
            return False
        
        # Skip patterns - links that are definitely not articles
        skip_patterns = [
            '#', 'javascript:', 'mailto:', 'tel:',
            '/about', '/contact', '/privacy', '/terms', '/policy',
            '/category/', '/tag/', '/author/', '/wp-admin', '/wp-login',
            '/login', '/register', '/signup', '/admin',
            'facebook.com', 'twitter.com', 'linkedin.com',
            'youtube.com', 'instagram.com', 'pinterest.com',
            '.pdf', '.doc', '.xls', '.zip', '.exe',
            '/feed', '/rss', '/sitemap', '/robots.txt'
        ]
        
        if any(pattern in href.lower() for pattern in skip_patterns):
            return False
        
        # Positive patterns - URLs that are likely articles
        article_patterns = [
            '/news/', '/article/', '/post/', '/story/', '/blog/',
            '/2024/', '/2025/',  # Recent articles
            domain.lower()  # Internal links to the same domain
        ]
        
        has_article_pattern = any(pattern in href.lower() for pattern in article_patterns)
        
        # Check if it's cybersecurity related or from a known cybersec domain
        is_cybersec_relevant = self.is_cybersecurity_related(title, domain)
        
        # Known cybersecurity domains get preference
        cybersec_domains = [
            'thehackernews.com', 'krebsonsecurity.com', 'bleepingcomputer.com',
            'threatpost.com', 'infosecurity-magazine.com', 'cybersecuritynews.com',
            'securityweek.com', 'darkreading.com', 'scmagazine.com', 'the420.in'
        ]
        
        is_cybersec_domain = any(cybersec_domain in domain for cybersec_domain in cybersec_domains)
        
        # For cybersecurity domains, be more lenient
        if is_cybersec_domain:
            return has_article_pattern or is_cybersec_relevant
        else:
            # For general domains, require both article pattern and cybersec relevance
            return has_article_pattern and is_cybersec_relevant

    def is_cybersecurity_related(self, title: str, domain: str = "") -> bool:
        """Enhanced cybersecurity relevance check with comprehensive keywords"""
        # Known cybersecurity domains - automatically pass
        cybersec_domains = [
            'thehackernews.com', 'krebsonsecurity.com', 'bleepingcomputer.com',
            'threatpost.com', 'infosecurity-magazine.com', 'cybersecuritynews.com',
            'securityweek.com', 'darkreading.com', 'scmagazine.com', 'csoonline.com',
            'helpnetsecurity.com', 'hackread.com', 'cyware.com', 'cybersecuritydive.com',
            'the420.in', 'securityaffairs.co', 'grahamcluley.com', 'risky.biz',
            'malwarebytes.com', 'trendmicro.com', 'kaspersky.com', 'symantec.com'
        ]
        
        if any(cybersec_domain in domain for cybersec_domain in cybersec_domains):
            return True
        
        # Comprehensive cybersecurity keywords
        cybersec_keywords = [
            # Core security terms
            'cyber', 'security', 'hack', 'breach', 'malware', 'ransomware', 
            'phishing', 'vulnerability', 'exploit', 'attack', 'threat',
            'data breach', 'trojan', 'backdoor', 'zero-day', 'privacy',
            'encryption', 'firewall', 'antivirus', 'scam', 'fraud',
            
            # Advanced threats
            'APT', 'botnet', 'CISO', 'SOC', 'incident response', 'forensics',
            'penetration testing', 'red team', 'blue team', 'threat hunting',
            'IOC', 'indicators of compromise', 'SIEM', 'XDR', 'EDR',
            
            # Malware types
            'spyware', 'adware', 'rootkit', 'keylogger', 'worm', 'virus',
            'cryptocurrency miner', 'stealer', 'loader', 'banking trojan',
            
            # Attack vectors
            'social engineering', 'business email compromise', 'BEC',
            'supply chain attack', 'watering hole', 'man-in-the-middle',
            'DNS hijacking', 'SQL injection', 'XSS', 'CSRF',
            
            # Security tools and concepts
            'NIST', 'ISO 27001', 'compliance', 'audit', 'governance',
            'risk management', 'security awareness', 'training',
            'password manager', 'multi-factor authentication', 'MFA',
            '2FA', 'biometric', 'certificate', 'PKI',
            
            # Incident types
            'data leak', 'insider threat', 'nation-state', 'cybercrime',
            'cyber espionage', 'hacktivism', 'DDoS', 'distributed denial',
            'denial of service', 'outage', 'downtime',
            
            # Industry specific
            'critical infrastructure', 'SCADA', 'ICS', 'OT security',
            'IoT security', 'cloud security', 'DevSecOps', 'container security',
            'kubernetes security', 'API security', 'mobile security',
            
            # Regulatory and legal
            'GDPR', 'CCPA', 'HIPAA', 'SOX', 'PCI DSS', 'regulatory',
            'fine', 'penalty', 'lawsuit', 'settlement', 'investigation',
            
            # Emerging threats
            'AI security', 'machine learning attacks', 'deepfake',
            'quantum computing threat', '5G security', 'blockchain security',
            
            # Common attack patterns
            'credential stuffing', 'password spraying', 'brute force',
            'dictionary attack', 'lateral movement', 'privilege escalation',
            'persistence', 'command and control', 'C2', 'exfiltration'
        ]
        
        title_lower = title.lower()
        return any(keyword.lower() in title_lower for keyword in cybersec_keywords)
    
    async def scrape_article_content(self, crawler, url: str, domain: str) -> Dict[str, str]:
        """Enhanced article content scraping with better error handling"""
        try:
            domain_config = self.get_domain_config(url)
            
            # Create enhanced config for article scraping
            article_config = CrawlerRunConfig(
                magic=True,
                simulate_user=True if domain_config['stealth_mode'] in ['high', 'maximum'] else False,
                override_navigator=True,
                delay_before_return_html=domain_config['scroll_pause'],
                page_timeout=domain_config['timeout'] - 10000,  # Slightly less than main timeout
                wait_until=domain_config['wait_until'],
                wait_for=domain_config['wait_for'],
                scan_full_page=True if domain_config['stealth_mode'] == 'maximum' else False,
                remove_overlay_elements=True,
                scroll_delay=domain_config['scroll_pause'],
                session_id=f"article_{hash(domain)}",
                verbose=False,
                excluded_tags=["nav", "footer", "header", "aside", "script", "style", "iframe", "noscript"]
            )
            
            # Multiple retry attempts for problematic sites
            max_retries = domain_config['retries']
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        delay = random.uniform(2, 5)
                        print(f"  🔄 Retry {attempt}/{max_retries} after {delay:.1f}s delay...")
                        await asyncio.sleep(delay)
                    
                    result = await asyncio.wait_for(
                        crawler.arun(url=url, config=article_config),
                        timeout=domain_config['timeout'] / 1000.0
                    )
                    
                    if result and result.success:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        
                        # Enhanced title extraction
                        title_selectors = ['h1', '.entry-title', '.post-title', '.article-title', 'title']
                        clean_title = "No title found"
                        
                        for selector in title_selectors:
                            title_element = soup.select_one(selector)
                            if title_element:
                                clean_title = title_element.get_text(strip=True)
                                break
                        
                        # Use markdown content or fallback
                        clean_content = result.markdown if result.markdown else result.cleaned_html
                        clean_content = self.enhanced_clean_content(clean_content)
                        
                        # Extract main image
                        main_image = self.extract_main_article_image(result.html, url)
                        
                        return {
                            'title': clean_title,
                            'url': url,
                            'content': clean_content,
                            'main_image': main_image,
                            'word_count': len(clean_content.split()) if clean_content else 0,
                            'domain': domain,
                            'scraped_at': datetime.now().isoformat(),
                            'status': 'success',
                            'attempt': attempt + 1
                        }
                    
                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    if attempt == max_retries:
                        return {
                            'title': 'Timeout error',
                            'url': url,
                            'content': f'Timeout after {max_retries + 1} attempts',
                            'main_image': '',
                            'word_count': 0,
                            'domain': domain,
                            'scraped_at': datetime.now().isoformat(),
                            'status': 'timeout'
                        }
                    continue
                    
            # If all retries failed
            return {
                'title': 'Failed to scrape',
                'url': url,
                'content': f'Failed after {max_retries + 1} attempts',
                'main_image': '',
                'word_count': 0,
                'domain': domain,
                'scraped_at': datetime.now().isoformat(),
                'status': 'failed'
            }
                    
        except Exception as e:
            return {
                'title': 'Error occurred',
                'url': url,
                'content': f'Error: {str(e)}',
                'main_image': '',
                'word_count': 0,
                'domain': domain,
                'scraped_at': datetime.now().isoformat(),
                'status': 'error'
            }
    
    def enhanced_clean_content(self, content: str) -> str:
        """Enhanced content cleaning with better preservation of article text"""
        if not content:
            return ""
        
        # Remove markdown links but keep text
        content = re.sub(r'\[([^\]]+)\]\(https?://[^\)]+\)', r'\1', content)
        # Remove standalone URLs
        content = re.sub(r'https?://[^\s\)\]]+', '', content)
        # Remove markdown images
        content = re.sub(r'!\[[^\]]*\]\([^\)]*\)', '', content)
        # Clean up underscores and asterisks
        content = re.sub(r'[_*]{2,}', '', content)
        # Reduce multiple newlines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Split into lines and filter
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Enhanced filtering for junk content
        cleaned_lines = []
        skip_patterns = [
            r'^(Follow|Share|Tweet|SHARE|Subscribe|Email|Connect|Written by|Photo of|Image:)',
            r'^\d+,?\d+\s+(Followers|Views|Shares)',
            r'^[A-Z\s]{3,20}$',  # All-caps navigation
            r'^©.*All Rights Reserved',
            r'javascript:void',
            r'^(Get Latest News|Trending News|Popular Resources|Latest News|Expert Insights)',
            r'^View → Trending',
            r'^\[__\]',
            r'^(Facebook|Twitter|LinkedIn|Instagram|YouTube)',
            r'^(Home|About|Contact|Privacy|Terms)',
            r'^Advertisement$'
        ]
        
        for line in lines:
            if (len(line) > 10 and  # Keep substantial content
                not any(re.match(pattern, line, re.I) for pattern in skip_patterns) and
                not line.startswith(('●', '•', '→', '▶')) and  # Skip bullet navigation
                line.count(' ') > 2):  # Ensure it's not just a short navigation item
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines[:100])  # Limit to first 100 lines

    def extract_main_article_image(self, html_content, base_url):
        """Enhanced main image extraction"""
        if not html_content:
            return ''
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Strategy 1: Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            return urljoin(base_url, image_url)
        
        # Strategy 2: Twitter card image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            image_url = twitter_image['content']
            return urljoin(base_url, image_url)
        
        # Strategy 3: Featured/hero images
        selectors = [
            'article img[src]:first-of-type',
            '.featured-image img[src]',
            '.article-image img[src]',
            '.hero-image img[src]',
            '.post-thumbnail img[src]',
            'img.featured[src]',
            'img.wp-post-image[src]',
            '.entry-content img[src]:first-of-type',
            'main img[src]:first-of-type'
        ]
        
        for selector in selectors:
            img = soup.select_one(selector)
            if img and img.get('src'):
                src = img['src']
                # Skip small icons, ads, and placeholder images
                if any(skip in src.lower() for skip in ['icon', 'logo', 'avatar', 'ad', 'banner', 'placeholder', 'sprite']):
                    continue
                # Check for reasonable dimensions if available
                if img.get('width') and img.get('height'):
                    try:
                        width, height = int(img['width']), int(img['height'])
                        if width < 200 or height < 150:  # Skip small images
                            continue
                    except (ValueError, TypeError):
                        pass
                
                return urljoin(base_url, src)
        
        return ''

    def save_article_instantly(self, article_data: Dict, timestamp_str: str) -> bool:
        """Save individual article instantly to JSON for immediate visibility"""
        try:
            live_file = os.path.join(self.data_dir, 'cybersecurity_news_live.json')
            
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Read existing data or create new structure
            if os.path.exists(live_file):
                try:
                    with open(live_file, 'r', encoding='utf-8') as f:
                        live_data = json.load(f)
                    
                    # Ensure proper structure
                    if not isinstance(live_data, dict):
                        live_data = {'articles': [], 'last_updated': ''}
                    elif 'articles' not in live_data:
                        live_data['articles'] = []
                    elif not isinstance(live_data['articles'], list):
                        live_data['articles'] = []
                    
                except (json.JSONDecodeError, FileNotFoundError):
                    live_data = {'articles': [], 'last_updated': ''}
            else:
                live_data = {'articles': [], 'last_updated': ''}
            
            # Check if article already exists (by URL)
            existing_urls = [a.get('url') for a in live_data.get('articles', [])]
            if article_data.get('url') not in existing_urls:
                # Only add if article has content and word count > 0
                if article_data.get('word_count', 0) > 0 and article_data.get('content', '').strip():
                    live_data['articles'].append(article_data)
                    live_data['last_updated'] = timestamp_str
                    
                    # Save updated data
                    with open(live_file, 'w', encoding='utf-8') as f:
                        json.dump(live_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"  💾 Article instantly saved to live feed: {article_data.get('title', '')[:50]}...")
                    return True
                else:
                    print(f"  🚫 Skipped saving article with no content or 0 word count")
                    return False
            else:
                print(f"  ⚠️ Article already exists in live feed")
                return False
                
        except Exception as e:
            print(f"  ❌ Error saving article instantly: {str(e)}")
            return False
    
    def transfer_live_articles_to_final(self, final_results: Dict) -> Dict:
        """Transfer articles from live feed to final results and clear live feed"""
        try:
            live_file = os.path.join(self.data_dir, 'cybersecurity_news_live.json')
            
            if not os.path.exists(live_file):
                print(f"  📝 No live feed file found - nothing to transfer")
                return final_results
            
            # Read live feed data
            with open(live_file, 'r', encoding='utf-8') as f:
                live_data = json.load(f)
            
            live_articles = live_data.get('articles', [])
            if not live_articles:
                print(f"  📝 No articles in live feed - nothing to transfer")
                return final_results
            
            print(f"  📦 Found {len(live_articles)} articles in live feed to transfer")
            
            # Group articles by domain for organized transfer
            articles_by_domain = {}
            for article in live_articles:
                domain = article.get('domain', 'unknown')
                if domain not in articles_by_domain:
                    articles_by_domain[domain] = []
                articles_by_domain[domain].append(article)
            
            # Add articles to final results by domain
            transferred_count = 0
            for domain, articles in articles_by_domain.items():
                # Find the corresponding site URL in results
                site_url = None
                for url in final_results.get('results', {}):
                    if domain in url:
                        site_url = url
                        break
                
                if site_url:
                    # Add to existing site results
                    if 'articles' not in final_results['results'][site_url]:
                        final_results['results'][site_url]['articles'] = []
                    
                    final_results['results'][site_url]['articles'].extend(articles)
                    final_results['results'][site_url]['articles_found'] = len(final_results['results'][site_url]['articles'])
                    transferred_count += len(articles)
                    print(f"    ✅ Transferred {len(articles)} articles to {domain}")
                else:
                    # Create new site entry for orphaned articles
                    site_url = f"https://{domain}/"
                    final_results['results'][site_url] = {
                        'website_url': site_url,
                        'website_name': domain,
                        'scraped_at': datetime.now().isoformat(),
                        'articles_found': len(articles),
                        'articles': articles,
                        'stealth_mode': 'live_transfer',
                        'attempts_needed': 1
                    }
                    transferred_count += len(articles)
                    print(f"    ✅ Created new entry and transferred {len(articles)} articles for {domain}")
            
            # Update totals in scraping_info
            final_results['scraping_info']['total_articles'] = (
                final_results['scraping_info'].get('total_articles', 0) + transferred_count
            )
            
            print(f"  🎯 Successfully transferred {transferred_count} articles from live feed")
            
            # 🧹 Clear the live feed after successful transfer
            self.clear_live_feed()
            
            return final_results
            
        except Exception as e:
            print(f"  ❌ Error transferring live articles: {str(e)}")
            return final_results
    
    def clear_live_feed(self):
        """Clear the live feed file after successful transfer"""
        try:
            live_file = os.path.join(self.data_dir, 'cybersecurity_news_live.json')
            
            # Reset to empty structure
            empty_structure = {
                "monitoring_info": {
                    "started_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_articles": 0,
                    "monitor_version": "2.0",
                    "status": "active",
                    "purpose": "Temporary storage for new articles only"
                },
                "results": {},
                "articles": []
            }
            
            with open(live_file, 'w', encoding='utf-8') as f:
                json.dump(empty_structure, f, indent=2, ensure_ascii=False)
            
            print(f"  🧹 Live feed cleared and reset for next scraping cycle")
            
        except Exception as e:
            print(f"  ❌ Error clearing live feed: {str(e)}")
    
    def clean_final_results(self, results: Dict) -> Dict:
        """Remove articles with word_count 0 or empty content from final results"""
        cleaned_results = results.copy()
        
        for site_url, site_data in cleaned_results.get('results', {}).items():
            if 'articles' in site_data:
                original_count = len(site_data['articles'])
                # Filter out articles with word_count 0 or empty content
                site_data['articles'] = [
                    article for article in site_data['articles'] 
                    if (article.get('word_count', 0) > 0 and 
                        article.get('content', '').strip() and 
                        article.get('status') == 'success')
                ]
                cleaned_count = len(site_data['articles'])
                
                if cleaned_count < original_count:
                    print(f"  🧹 Cleaned {site_url}: Removed {original_count - cleaned_count} articles with no content")
        
        return cleaned_results

    def save_scraped_urls_instantly(self, results: Dict) -> bool:
        """Save scraped URLs instantly to url_scraped.txt for tracking - DEPRECATED: Use URL Tracker instead"""
        try:
            # This method is deprecated - the URL tracker handles this more efficiently
            # But we'll keep the logic for backward compatibility
            
            if not self.url_tracker:
                safe_print("⚠️ URL tracker not available, falling back to legacy method")
                return self._legacy_save_scraped_urls(results)
            
            # Use URL tracker for proper duplicate prevention
            all_articles = []
            for site_data in results.get('results', {}).values():
                for article in site_data.get('articles', []):
                    if (article.get('status') == 'success' and 
                        article.get('word_count', 0) > 0 and 
                        article.get('url')):
                        all_articles.append(article)
            
            if all_articles:
                tracked_count = self.url_tracker.bulk_add_scraped_urls(all_articles)
                print(f"🔗 URL tracker processed {len(all_articles)} articles, {tracked_count} were new")
                return tracked_count > 0
            else:
                print(f"🔗 No successfully scraped URLs to track")
                return False
                
        except Exception as e:
            safe_print(f"❌ Error tracking scraped URLs: {str(e)}")
            return False
    
    def _legacy_save_scraped_urls(self, results: Dict) -> bool:
        """Legacy URL saving method (fallback when URL tracker unavailable)"""
        try:
            url_file = os.path.join(self.data_dir, 'url_scraped.txt')
            
            # Collect all successfully scraped URLs
            scraped_urls = []
            for site_data in results.get('results', {}).values():
                for article in site_data.get('articles', []):
                    if (article.get('status') == 'success' and 
                        article.get('word_count', 0) > 0 and 
                        article.get('url')):
                        scraped_urls.append(article['url'])
            
            if scraped_urls:
                # Read existing URLs to avoid duplicates (check for both formats)
                existing_urls = set()
                if os.path.exists(url_file):
                    try:
                        with open(url_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    # Handle both old format (just URL) and new format (URL|DATE|DOMAIN)
                                    if '|' in line:
                                        url = line.split('|')[0].strip()
                                    else:
                                        url = line
                                    existing_urls.add(url)
                    except Exception:
                        pass
                
                # Add new URLs only
                new_urls = [url for url in scraped_urls if url not in existing_urls]
                
                if new_urls:
                    with open(url_file, 'a', encoding='utf-8') as f:
                        for url in new_urls:
                            f.write(f"{url}\n")
                    
                    print(f"🔗 Saved {len(new_urls)} new URLs to {url_file} (legacy mode)")
                else:
                    print(f"🔗 No new URLs to save (all already tracked)")
                
                return True
            else:
                print(f"🔗 No successfully scraped URLs to save")
                return False
                
        except Exception as e:
            safe_print(f"❌ Error saving scraped URLs: {str(e)}")
            return False

    async def scrape_website(self, crawler, url: str) -> Dict:
        """Enhanced website scraping with sophisticated anti-bot handling"""
        try:
            safe_print(f"🌐 Scraping {url}...")
            
            domain = urlparse(url).netloc
            domain_config = self.get_domain_config(url)
            
            # Simple, reliable config that actually works
            site_config = CrawlerRunConfig(
                magic=True,
                page_timeout=30000,
                wait_until="domcontentloaded",
                verbose=False
            )
            
            # Multiple retry attempts with progressive delays
            max_retries = domain_config['retries']
            result = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # Progressive delay increase
                        delay = random.uniform(5, 15) * attempt
                        print(f"  🔄 Retry {attempt}/{max_retries} for {domain} after {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        
                        # Change user agent on retry
                        new_ua = random.choice(self.user_agents)
                        print(f"  🎭 Switching user agent for retry...")
                    
                    print(f"  🎯 Attempt {attempt + 1}: {domain_config['stealth_mode']} stealth mode")
                    
                    result = await asyncio.wait_for(
                        crawler.arun(url=url, config=site_config),
                        timeout=domain_config['timeout'] / 1000.0 + 30  # Extra buffer
                    )
                    
                    if result and result.success:
                        print(f"  ✅ Successfully scraped {domain} on attempt {attempt + 1}")
                        break
                    else:
                        error_msg = result.error_message if result else "Unknown error"
                        print(f"  ⚠️ Attempt {attempt + 1} failed for {domain}: {error_msg}")
                        
                        if attempt == max_retries:
                            print(f"  ❌ All attempts failed for {domain}")
                            result = type('obj', (object,), {
                                'success': False, 
                                'error_message': f'Failed after {max_retries + 1} attempts: {error_msg}',
                                'html': None
                            })()
                        
                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    print(f"  ⏰ Timeout on attempt {attempt + 1} for {domain}")
                    if attempt == max_retries:
                        result = type('obj', (object,), {
                            'success': False, 
                            'error_message': f'Timeout after {max_retries + 1} attempts',
                            'html': None
                        })()
                except Exception as e:
                    print(f"  💥 Error on attempt {attempt + 1} for {domain}: {str(e)[:100]}")
                    if attempt == max_retries:
                        result = type('obj', (object,), {
                            'success': False, 
                            'error_message': f'Error after {max_retries + 1} attempts: {str(e)}',
                            'html': None
                        })()
            
            if result and result.success:
                # Extract article links from main page
                articles = await self.extract_article_links(url, result.html)
                
                website_data = {
                    'website_url': url,
                    'website_name': domain,
                    'scraped_at': datetime.now().isoformat(),
                    'articles_found': len(articles),
                    'articles': [],
                    'stealth_mode': domain_config['stealth_mode'],
                    'attempts_needed': max_retries + 1 - (max_retries if result.success else 0)
                }
                
                # Scrape individual articles
                max_articles = min(len(articles), 8)  # Reasonable limit
                
                print(f"  📖 Found {len(articles)} articles, scraping {max_articles}...")
                
                # Get timestamp for instant saving
                timestamp_str = datetime.now().isoformat()
                
                for i, article_info in enumerate(articles[:max_articles], 1):
                    print(f"  📖 Scraping article {i}/{max_articles}: {article_info['title'][:50]}...")
                    
                    try:
                        # Add delay between articles based on stealth mode
                        if i > 1:
                            article_delay = random.uniform(1, 3) if domain_config['stealth_mode'] in ['high', 'maximum'] else random.uniform(0.5, 1.5)
                            await asyncio.sleep(article_delay)
                        
                        article_data = await asyncio.wait_for(
                            self.scrape_article_content(crawler, article_info['url'], domain),
                            timeout=60.0  # 1 minute per article
                        )
                        
                        website_data['articles'].append(article_data)
                        
                        # 🚀 INSTANT SAVING: Save article immediately if it has content
                        if (article_data.get('word_count', 0) > 0 and 
                            article_data.get('content', '').strip() and 
                            article_data.get('status') == 'success'):
                            self.save_article_instantly(article_data, timestamp_str)
                    
                    except asyncio.TimeoutError:
                        print(f"  ⏰ Timeout scraping article: {article_info['title'][:30]}...")
                        failed_article = {
                            'title': article_info['title'],
                            'url': article_info['url'],
                            'content': 'Timeout error during article scraping',
                            'word_count': 0,
                            'status': 'timeout',
                            'domain': domain,
                            'scraped_at': datetime.now().isoformat()
                        }
                        website_data['articles'].append(failed_article)
                    except Exception as article_error:
                        print(f"  ❌ Error scraping article: {str(article_error)[:50]}...")
                        failed_article = {
                            'title': article_info['title'], 
                            'url': article_info['url'],
                            'content': f'Error during article scraping: {str(article_error)}',
                            'word_count': 0,
                            'status': 'error',
                            'domain': domain,
                            'scraped_at': datetime.now().isoformat()
                        }
                        website_data['articles'].append(failed_article)
                
                return website_data
            else:
                return {
                    'website_url': url,
                    'website_name': domain,
                    'error': f"Failed to scrape: {result.error_message if result else 'Unknown error'}",
                    'articles': [],
                    'stealth_mode': domain_config['stealth_mode']
                }
                
        except Exception as e:
            return {
                'website_url': url,
                'website_name': urlparse(url).netloc,
                'error': f"Critical error: {str(e)}",
                'articles': [],
                'stealth_mode': 'unknown'
            }

    def load_urls_from_file(self, filename: str) -> List[str]:
        """Load URLs from a text file, ignoring comments and empty lines"""
        urls = []
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        urls.append(line)
            return urls
        except FileNotFoundError:
            safe_print(f"❌ File {filename} not found!")
            return []

    async def run_enhanced_scraper(self, save_to_file=True):
        """Enhanced main scraper with sophisticated anti-bot protection"""
        # Setup graceful shutdown handler
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            print(f"\n🚫 Shutdown signal received. Finishing current operations...")
            shutdown_event.set()
        
        # Register signal handlers for graceful shutdown
        if sys.platform != 'win32':
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)
        
        # Load URLs from file
        url_file_path = os.path.join(self.config_dir, 'url_fetch.txt')
        urls = self.load_urls_from_file(url_file_path)
        
        if not urls:
            safe_print(f"❌ No URLs found in {url_file_path}")
            return
            
        safe_print(f"📁 Loaded {len(urls)} URLs from {url_file_path}")
        safe_print(f"🚀 Starting ENHANCED multi-URL scraping with MAXIMUM anti-bot protection...")
        print(f"🛡️  Features: Dynamic stealth modes, user agent rotation, progressive retries")
        
        all_results = {}
        total_articles = 0
        successful_sites = 0
        failed_sites = 0
        
        try:
            # Use enhanced browser config
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                # Setup enhanced hooks
                try:
                    if hasattr(crawler, 'crawler_strategy') and hasattr(crawler.crawler_strategy, 'set_hook'):
                        crawler.crawler_strategy.set_hook("on_page_context_created", self.on_page_context_created)
                        crawler.crawler_strategy.set_hook("before_goto", self.before_goto)
                        safe_print("✅ Enhanced anti-bot hooks installed successfully")
                    else:
                        safe_print("⚠️ Warning: Hook installation not supported in this Crawl4AI version")
                except Exception as hook_error:
                    safe_print(f"⚠️ Warning: Could not install enhanced hooks: {hook_error}")
                
                print("🔄 Enhanced crawler initialized")
                
                # Process each URL with enhanced handling and progress indication
                for i, url in enumerate(urls, 1):
                    # Check for shutdown signal
                    if shutdown_event.is_set():
                        print(f"🚫 Shutdown requested. Stopping at site {i-1}/{len(urls)}")
                        break
                        
                    # Progress indicator
                    progress = (i / len(urls)) * 100
                    print(f"\n[{progress:.1f}%] Processing website {i}/{len(urls)}: {url}")
                    domain = urlparse(url).netloc
                    domain_config = self.get_domain_config(url)
                    
                    print(f"  🛡️ Using {domain_config['stealth_mode']} stealth mode for {domain}")
                    
                    try:
                        website_data = await asyncio.wait_for(
                            self.scrape_website(crawler, url),
                            timeout=180.0  # 3-minute hard timeout per site
                        )
                        
                        if website_data.get('articles'):
                            successful_sites += 1
                            article_count = len([a for a in website_data['articles'] if a.get('status') == 'success'])
                            total_articles += article_count
                            print(f"  ✅ Success: {article_count} articles scraped successfully")
                        else:
                            failed_sites += 1
                            print(f"  ❌ Failed: {website_data.get('error', 'No articles found')}")
                        
                        all_results[url] = website_data
                        
                    except asyncio.TimeoutError:
                        failed_sites += 1
                        error_msg = f"Site timeout after 3 minutes"
                        print(f"  ⏰ Timeout for {url}: {error_msg}")
                        all_results[url] = {
                            'website_url': url,
                            'website_name': domain,
                            'error': error_msg,
                            'articles': [],
                            'stealth_mode': domain_config['stealth_mode']
                        }
                    except Exception as site_error:
                        failed_sites += 1
                        error_msg = str(site_error)[:200]
                        print(f"  💥 Critical error for {url}: {error_msg}")
                        all_results[url] = {
                            'website_url': url,
                            'website_name': domain,
                            'error': f"Critical error: {error_msg}",
                            'articles': [],
                            'stealth_mode': domain_config['stealth_mode']
                        }
                    
                    # Enhanced delay between sites
                    if i < len(urls) and not shutdown_event.is_set():
                        site_delay = random.uniform(3.0, 8.0)  # Longer delays for better stealth
                        print(f"⏱️  Stealth delay: {site_delay:.1f}s before next site...")
                        try:
                            await asyncio.wait_for(asyncio.sleep(site_delay), timeout=site_delay + 1)
                        except asyncio.TimeoutError:
                            pass
                        except asyncio.CancelledError:
                            print("🚫 Delay cancelled, proceeding to next site...")
                            continue
        
        except KeyboardInterrupt:
            print(f"\n🚫 KeyboardInterrupt received. Saving partial results...")
        except Exception as e:
            print(f"\n💥 Unexpected error in enhanced scraper: {str(e)}")
        finally:
            # Enhanced final summary
            print(f"\n🎯 ENHANCED SCRAPING COMPLETED!")
            safe_print(f"📊 DETAILED SUMMARY:")
            print(f"  ✅ Successful sites: {successful_sites}/{len(urls)}")
            print(f"  ❌ Failed sites: {failed_sites}/{len(urls)}")
            print(f"  📰 Total articles: {total_articles}")
            if hasattr(self, 'filtered_urls_count') and self.filtered_urls_count > 0:
                print(f"  🧠 Smart filtering: {self.filtered_urls_count} duplicate URLs skipped")
                print(f"  ⚡ Processing efficiency: Saved significant computation time!")
            else:
                print(f"  🆕 All articles were new - no duplicates filtered")
            
            # Detailed breakdown by site
            print(f"\n📋 SITE-BY-SITE BREAKDOWN:")
            for url, data in all_results.items():
                domain = urlparse(url).netloc
                if data.get('articles'):
                    success_count = len([a for a in data['articles'] if a.get('status') == 'success'])
                    stealth_mode = data.get('stealth_mode', 'unknown')
                    print(f"  🌐 {domain}: {success_count} articles ({stealth_mode} stealth)")
                else:
                    error = data.get('error', 'Unknown error')[:50]
                    print(f"  ❌ {domain}: FAILED - {error}...")
            
            # Structure final results
            final_results = {
                'scraping_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_sites': len(urls),
                    'successful_sites': successful_sites,
                    'failed_sites': failed_sites,
                    'total_articles': total_articles,
                    'enhanced_stealth_enabled': True,
                    'interrupted': shutdown_event.is_set(),
                    'version': 'enhanced_v2.1_with_instant_saving'
                },
                'results': all_results
            }
            
            # 🔄 CRITICAL FIX: Always transfer articles from live feed to final results
            print(f"\n🔄 TRANSFERRING ARTICLES FROM LIVE FEED...")
            final_results_with_live = self.transfer_live_articles_to_final(final_results)
            
            # 🧹 Clean final results: Remove articles with word_count 0 or empty content
            print(f"\n🧹 CLEANING FINAL RESULTS...")
            cleaned_results = self.clean_final_results(final_results_with_live)
            
            # 💾 CRITICAL FIX: ALWAYS save to daily file regardless of save_to_file flag
            # This ensures data transfer happens in ALL modes (production, monitoring, etc.)
            timestamp = datetime.now().strftime("%Y%m%d")
            output_file = os.path.join(self.data_dir, f'News_today_{timestamp}.json')
            
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(cleaned_results, f, indent=2, ensure_ascii=False)
                
                print(f"💾 ✅ CRITICAL: Results saved to daily file: {output_file}")
                safe_print(f"📊 Total articles in daily file: {cleaned_results['scraping_info']['total_articles']}")
                
                # Save scraped URLs instantly for tracking
                self.save_scraped_urls_instantly(cleaned_results)
                
                # Track scraped URLs if URL tracker is available
                if self.url_tracker:
                    all_articles = []
                    for site_data in cleaned_results.get('results', {}).values():
                        all_articles.extend(site_data.get('articles', []))
                    
                    tracked_count = self.url_tracker.bulk_add_scraped_urls(all_articles)
                    print(f"🔗 Tracked {tracked_count} URLs in database")
                    
                # ✅ CRITICAL SUCCESS: Data transfer completed
                print(f"\n{Fore.GREEN}✅ CRITICAL SUCCESS: Data transfer flow completed!")
                print(f"{Fore.GREEN}   Live feed → Daily file transfer: SUCCESS")
                print(f"{Fore.GREEN}   File: {output_file}")
                print(f"{Fore.GREEN}   Articles: {cleaned_results['scraping_info']['total_articles']}")
                print(f"{Fore.GREEN}   AI Summarizer will now have content to process!{Style.RESET_ALL}")
                
            except Exception as e:
                safe_print(f"❌ CRITICAL ERROR: Failed to save daily file: {str(e)}")
                safe_print(f"⚠️ This will cause AI summarizer to fail with 'content is empty'")
                raise e
            
            return cleaned_results

def main():
    """Enhanced main entry point"""
    try:
        safe_print("🚀 Starting Enhanced Cybersecurity News Scraper v2.0")
        print("🛡️ Features: Maximum stealth, dynamic retries, enhanced extraction")
        
        scraper = EnhancedCyberSecurityNewsScraper()
        asyncio.run(scraper.run_enhanced_scraper())
    except KeyboardInterrupt:
        print(f"\n🚫 Script interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()