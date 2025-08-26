from fastapi import FastAPI, HTTPException, Query, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any, Union
import json
import os
import re
import urllib.parse
from datetime import datetime, timedelta
import sys
import logging
from logging.handlers import RotatingFileHandler
import feedparser
import requests
from bs4 import BeautifulSoup
from html import unescape
from functools import lru_cache
from urllib.parse import urlencode
import asyncio
import httpx
import time
import psutil
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

# Redis support for distributed caching (optional)
REDIS_AVAILABLE = False
redis_client = None
try:
    import redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()  # Test connection
    REDIS_AVAILABLE = True
    print(f"✅ Redis connected: {REDIS_URL}")
except Exception as e:
    print(f"⚠️  Redis not available (using local cache): {e}")
    REDIS_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global cache for news data with file modification tracking
news_data_cache = {
    "data": None,
    "last_modified": 0,
    "file_path": None
}

# Worker ID for distributed systems
WORKER_ID = os.getenv('WORKER_ID', '1')

class NewsFileWatcher(FileSystemEventHandler):
    """File watcher to detect changes in news data files"""
    
    def __init__(self, cache_ref):
        self.cache_ref = cache_ref
        self.logger = logging.getLogger("news_file_watcher")
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Check if the modified file is our summarized news file
        if event.src_path.endswith('summarized_news_hf.json'):
            self.logger.info(f"🔄 News file updated: {event.src_path}")
            # Invalidate cache by setting last_modified to 0
            self.cache_ref["last_modified"] = 0
            self.cache_ref["data"] = None
            self.logger.info("✅ Cache invalidated - fresh data will be loaded on next request")

# Initialize FastAPI app
app = FastAPI(
    title="🛡️ Cybersecurity News API - FastAPI Edition",
    description="High-performance cybersecurity news aggregation API with dynamic source configuration",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Note: File watcher is optional - the system works with file modification time checking
file_observer = None

@app.on_event("startup")
async def startup_event():
    """Initialize file watcher for real-time data updates (optional)"""
    global file_observer
    
    try:
        # Try to set up file watcher for real-time updates
        event_handler = NewsFileWatcher(news_data_cache)
        file_observer = Observer()
        
        # Watch the data directory for changes to summarized_news_hf.json
        watch_directory = DATA_DIR
        file_observer.schedule(event_handler, watch_directory, recursive=False)
        file_observer.start()
        
        logger.info(f"🔍 File watcher started - monitoring {watch_directory} for news updates")
        logger.info("🚀 Real-time news data updates enabled!")
        
    except Exception as e:
        logger.warning(f"File watcher not available (using fallback mode): {e}")
        logger.info("📊 Using file modification time checking for updates")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup file watcher on shutdown"""
    global file_observer
    
    if file_observer:
        try:
            file_observer.stop()
            file_observer.join()
            logger.info("🛑 File watcher stopped")
        except Exception as e:
            logger.warning(f"Error stopping file watcher: {e}")

# Setup logging with rotating file handler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cyberx_fastapi")

try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "fastapi.log"), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(file_handler)
except Exception as _e:
    # Fall back silently if file logging cannot be configured
    pass

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
ALERTS_DIR = os.path.join(DATA_DIR, "alerts")

# Ensure alerts directory exists
os.makedirs(ALERTS_DIR, exist_ok=True)

# In-memory notifications queue for frontend polling
notifications_queue = []

# Metrics tracking
start_time = time.time()
request_count = 0
error_count = 0
request_duration_sum = 0.0
endpoint_stats = {}

# 🚀 SPEED OPTIMIZATION: Response caching middleware
@app.middleware("http")
async def response_cache_middleware(request: Request, call_next):
    """Cache complete responses for GET requests to achieve sub-100ms response times"""
    start_time = time.time()
    
    # Check for cached response for GET requests
    if request.method == "GET" and REDIS_AVAILABLE:
        cache_key = f"cyberx:response_cache:{request.url.path}:{request.url.query}"
        try:
            cached_response = redis_client.get(cache_key)
            if cached_response:
                response_data = json.loads(cached_response)
                process_time = time.time() - start_time
                
                response = Response(
                    content=response_data["content"],
                    status_code=response_data["status_code"],
                    headers=response_data["headers"]
                )
                response.headers["X-Process-Time"] = str(process_time)
                response.headers["X-Cache-Hit"] = "true"
                response.headers["X-Cache-Source"] = "response_middleware"
                return response
        except Exception as e:
            logger.debug(f"Response cache read error: {e}")
    
    # Process request normally
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Cache successful GET responses for API endpoints
    if (request.method == "GET" and response.status_code == 200 and 
        REDIS_AVAILABLE and "/api/" in request.url.path):
        try:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Prepare cache data
            cache_data = {
                "content": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
            
            # Store in cache with 90-second TTL for ultra-fast responses
            cache_key = f"cyberx:response_cache:{request.url.path}:{request.url.query}"
            redis_client.setex(cache_key, 90, json.dumps(cache_data))
            
            # Recreate response with cached body
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except Exception as e:
            logger.debug(f"Response cache write error: {e}")
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Cache-Hit"] = "false"
    
    return response

# Middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    global request_count, error_count, request_duration_sum, endpoint_stats
    
    start_time_req = time.time()
    request_count += 1
    
    # Track endpoint usage
    endpoint = f"{request.method} {request.url.path}"
    if endpoint not in endpoint_stats:
        endpoint_stats[endpoint] = {"count": 0, "errors": 0}
    endpoint_stats[endpoint]["count"] += 1
    
    response = await call_next(request)
    
    # Track errors
    if response.status_code >= 400:
        error_count += 1
        endpoint_stats[endpoint]["errors"] += 1
    
    # Track duration
    duration = time.time() - start_time_req
    request_duration_sum += duration
    
    return response

# Pydantic models for request/response validation
class ArticleResponse(BaseModel):
    id: str
    source: Dict[str, Any]
    title: str
    # description: Optional[str] = None  # REMOVED: Not used by frontend
    summary: str
    # content: str  # REMOVED: Large field causing slow response times
    url: str
    urlToImage: str
    publishedAt: str
    # author: str  # REMOVED: Not displayed in frontend feed
    # scraped_at: str  # REMOVED: Internal field
    # word_count: int  # REMOVED: Not needed for feed view
    domain: str

class SourceResponse(BaseModel):
    id: str
    name: str
    url: str
    domain: str
    category: str
    description: str
    articles_count: Optional[int] = 0
    last_updated: Optional[str] = None

class NewsResponse(BaseModel):
    status: str
    totalResults: int
    page: int
    limit: int
    articles: List[ArticleResponse]
    sources_available: int
    data_sources_used: Optional[List[str]] = None

class SearchResponse(BaseModel):
    status: str
    query: str
    source_filter: Optional[str] = None
    totalResults: int
    articles: List[ArticleResponse]
    sources_searched: int

class NotificationRequest(BaseModel):
    type: str
    count: int = 0
    timestamp: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    body: Optional[str] = None
    priority: str = "normal"

class GoogleNewsSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query for Google News")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of articles to return")

class AlertMarkReadRequest(BaseModel):
    alert_ids: List[str] = []
    mark_all: bool = False

class ExtractionRequest(BaseModel):
    url: HttpUrl

# =====================================
# REAL-TIME DATA CACHE MANAGEMENT
# =====================================

def get_fresh_news_data():
    """
    Get fresh news data with intelligent caching.
    Supports both local cache and distributed Redis cache for scalability.
    """
    global news_data_cache
    
    summarized_file = os.path.join(DATA_DIR, "summarized_news_hf.json")
    cache_key = "cyberx:news_data"
    cache_mtime_key = "cyberx:news_mtime"
    
    try:
        if not os.path.exists(summarized_file):
            logger.warning(f"Summarized file not found: {summarized_file}")
            return []
            
        current_modified = os.path.getmtime(summarized_file)
        
        # Check Redis cache first (if available)
        if REDIS_AVAILABLE:
            try:
                cached_mtime = redis_client.get(cache_mtime_key)
                if cached_mtime and float(cached_mtime) >= current_modified:
                    cached_data = redis_client.get(cache_key)
                    if cached_data:
                        data = json.loads(cached_data)
                        logger.info(f"🚀 Loaded {len(data)} articles from Redis cache (Worker {WORKER_ID})")
                        return data
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        # Check local cache
        if (news_data_cache["data"] is not None and 
            news_data_cache["last_modified"] >= current_modified):
            logger.info(f"📦 Loaded {len(news_data_cache['data'])} articles from local cache (Worker {WORKER_ID})")
            return news_data_cache["data"]
        
        # Load fresh data from file
        logger.info(f"🔄 Loading fresh news data from {summarized_file} (Worker {WORKER_ID})")
        
        with open(summarized_file, "r", encoding="utf-8") as f:
            fresh_data = json.load(f)
        
        # Update local cache
        news_data_cache["data"] = fresh_data
        news_data_cache["last_modified"] = current_modified
        news_data_cache["file_path"] = summarized_file
        
        # Update Redis cache (if available)
        if REDIS_AVAILABLE and fresh_data:
            try:
                redis_client.setex(cache_key, 3600, json.dumps(fresh_data))  # 1 hour TTL
                redis_client.setex(cache_mtime_key, 3600, str(current_modified))
                logger.info(f"💾 Updated Redis cache (Worker {WORKER_ID})")
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")
        
        logger.info(f"✅ Loaded {len(fresh_data)} fresh articles (Worker {WORKER_ID})")
        return fresh_data
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in summarized file: {e}")
        return []
    except Exception as e:
        logger.error(f"Error reading summarized file: {e}")
        return []

def invalidate_distributed_cache():
    """Invalidate cache across all instances"""
    global news_data_cache
    
    # Invalidate local cache
    news_data_cache["last_modified"] = 0
    news_data_cache["data"] = None
    
    # Invalidate Redis cache
    if REDIS_AVAILABLE:
        try:
            redis_client.delete("cyberx:news_data")
            redis_client.delete("cyberx:news_mtime")
            logger.info(f"🗑️  Redis cache invalidated (Worker {WORKER_ID})")
        except Exception as e:
            logger.warning(f"Redis cache invalidation error: {e}")

class DynamicNewsAPI:
    """Dynamic News API that adapts to URL configuration changes"""
    
    def __init__(self):
        self.base_dir = BASE_DIR
        self.data_dir = DATA_DIR
        self.config_dir = CONFIG_DIR
        self.url_config_file = os.path.join(self.config_dir, "url_fetch.txt")
        self._url_sources = None
        self._last_config_check = 0
        
    def get_url_sources(self):
        """Dynamically parse URL configuration file to get all sources"""
        config_mtime = os.path.getmtime(self.url_config_file) if os.path.exists(self.url_config_file) else 0
        
        # Cache sources for 5 minutes or until config file changes
        if (self._url_sources is None or 
            config_mtime > self._last_config_check or 
            (datetime.now().timestamp() - self._last_config_check) > 300):
            
            self._url_sources = self._parse_url_config()
            self._last_config_check = config_mtime
            
        return self._url_sources
    
    def _parse_url_config(self):
        """Parse the URL configuration file to extract source information"""
        sources = {}
        
        if not os.path.exists(self.url_config_file):
            logger.warning(f"URL config file not found: {self.url_config_file}")
            return sources
            
        try:
            with open(self.url_config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                    
                # Extract URL
                if line.startswith('http'):
                    url = line.rstrip('/')
                    domain = self._extract_domain(url)
                    source_id = self._generate_source_id(domain)
                    source_name = self._generate_source_name(domain)
                    
                    sources[source_id] = {
                        "id": source_id,
                        "name": source_name,
                        "url": url,
                        "domain": domain,
                        "category": "cybersecurity",
                        "description": f"Latest cybersecurity news from {source_name}"
                    }
                    
            logger.info(f"Loaded {len(sources)} dynamic sources from configuration")
            return sources
            
        except Exception as e:
            logger.error(f"Error parsing URL config: {e}")
            return {}
    
    def _extract_domain(self, url):
        """Extract clean domain name from URL"""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url
            
    def _generate_source_id(self, domain):
        """Generate a clean source ID from domain"""
        # Remove special characters and convert to lowercase
        source_id = re.sub(r'[^a-zA-Z0-9]', '', domain.replace('.', ''))
        return source_id.lower()
        
    def _generate_source_name(self, domain):
        """Generate a readable source name from domain"""
        # Remove common prefixes and suffixes
        name = domain.replace('www.', '').replace('.com', '').replace('.org', '').replace('.net', '')
        
        # Handle special cases for better naming
        name_mapping = {
            'thehackernews': 'The Hacker News',
            'bleepingcomputer': 'BleepingComputer',
            'krebsonsecurity': 'Krebs on Security',
            'the420': 'The420.in',
            'darkreading': 'Dark Reading',
            'securityweek': 'Security Week',
            'threatpost': 'Threatpost',
            'infosecurity-magazine': 'Infosecurity Magazine',
            'scmagazine': 'SC Magazine',
            'cybersecuritynews': 'Cybersecurity News'
        }
        
        return name_mapping.get(name.lower(), name.replace('-', ' ').replace('_', ' ').title())
    
    def get_data_files(self):
        """Get all available data files in the data directory"""
        data_files = {}
        
        if not os.path.exists(self.data_dir):
            return data_files
            
        # Primary data sources
        primary_files = [
            'summarized_news_hf.json',    # AI-processed summary file
            'cybersecurity_news_live.json',  # Live monitoring file
        ]
        
        # Daily archive files (News_today_YYYYMMDD.json pattern)
        daily_pattern = re.compile(r'News_today_\d{8}\.json')
        
        for file in os.listdir(self.data_dir):
            if file.endswith('.json'):
                file_path = os.path.join(self.data_dir, file)
                file_stat = os.stat(file_path)
                
                data_files[file] = {
                    'path': file_path,
                    'size': file_stat.st_size,
                    'modified': datetime.fromtimestamp(file_stat.st_mtime),
                    'type': self._classify_data_file(file)
                }
                
        return data_files
    
    def _classify_data_file(self, filename):
        """Classify data file type"""
        if filename == 'summarized_news_hf.json':
            return 'summarized'
        elif filename == 'cybersecurity_news_live.json':
            return 'live'
        elif filename.startswith('News_today_'):
            return 'daily_archive'
        else:
            return 'unknown'

# Initialize the dynamic API
dynamic_api = DynamicNewsAPI()

def load_articles_from_file(filename):
    """Load articles from JSON file with enhanced error handling and intelligent caching"""
    
    # For summarized_news_hf.json, use the cached fresh data function
    if filename == "summarized_news_hf.json":
        return get_fresh_news_data()
    
    # For other files, use regular loading
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            return []
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            logger.warning(f"Empty file: {filepath}")
            return []
            
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
                
            data = json.loads(content)
            
            # Handle different data structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Handle daily archive format
                if 'results' in data:
                    articles = []
                    for site_data in data['results'].values():
                        if 'articles' in site_data:
                            articles.extend(site_data['articles'])
                    return articles
                # Handle live monitoring format  
                elif 'monitoring_info' in data and 'results' in data:
                    articles = []
                    for site_data in data['results'].values():
                        if 'articles' in site_data:
                            articles.extend(site_data['articles'])
                    return articles
                else:
                    return [data] if data else []
            else:
                return []
                
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {filename}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error loading articles from {filename}: {e}")
        return []

def format_article_for_api(article, source_info=None):
    """Format article for consistent API response with dynamic source detection - OPTIMIZED FOR SPEED"""
    # Handle articles that already have proper source structure (from summarized files)
    if isinstance(article.get("source"), dict) and article["source"].get("name"):
        return {
            "id": generate_article_id(article),
            "source": article.get("source"),
            "title": article.get("title", ""),
            # "description": article.get("description", "") or article.get("summary", ""),  # REMOVED: Not used by frontend
            "summary": article.get("summary", article.get("description", "")),
            # "content": article.get("content", ""),  # REMOVED: Large field not needed for feed view
            "url": article.get("url", ""),
            "urlToImage": article.get("urlToImage", "") or article.get("main_image", ""),
            "publishedAt": article.get("publishedAt", "") or article.get("scraped_at", ""),
            # "author": article.get("author", ""),  # REMOVED: Not displayed in feed
            # "scraped_at": article.get("scraped_at", ""),  # REMOVED: Internal field
            # "word_count": article.get("word_count", 0),  # REMOVED: Not needed for feed
            "domain": article.get("domain", "")
        }
    
    # Handle raw articles from monitoring/scraping (need source detection)
    source_name = "Unknown"
    source_url = ""
    source_id = "unknown"
    
    if source_info:
        source_name = source_info.get("name", "Unknown")
        source_url = source_info.get("url", "")
        source_id = source_info.get("id", "unknown")
    else:
        # Try to detect source from article URL or domain
        article_url = article.get("url", "")
        article_domain = article.get("domain", "")
        
        if article_url or article_domain:
            detected_source = detect_source_from_url(article_url or f"https://{article_domain}")
            if detected_source:
                source_name = detected_source["name"]
                source_url = detected_source["url"]
                source_id = detected_source["id"]
    
    return {
        "id": generate_article_id(article),
        "source": {
            "id": source_id,
            "name": source_name,
            "url": source_url
        },
        "title": article.get("title", ""),
        # "description": article.get("description", ""),  # REMOVED: Not used by frontend
        "summary": article.get("summary", article.get("description", "")),
        # "content": article.get("content", ""),  # REMOVED: Large field not needed for feed view
        "url": article.get("url", ""),
        "urlToImage": article.get("urlToImage", "") or article.get("main_image", ""),
        "publishedAt": article.get("publishedAt", "") or article.get("scraped_at", ""),
        # "author": article.get("author", ""),  # REMOVED: Not displayed in feed
        # "scraped_at": article.get("scraped_at", ""),  # REMOVED: Internal field
        # "word_count": article.get("word_count", 0),  # REMOVED: Not needed for feed
        "domain": article.get("domain", "")
    }

def generate_article_id(article):
    """Generate a unique article ID"""
    url = article.get("url", "")
    title = article.get("title", "")
    
    if url:
        return f"article-{hash(url) % 1000000}"
    elif title:
        return f"article-{hash(title) % 1000000}"
    else:
        return f"article-{hash(str(article)) % 1000000}"

def detect_source_from_url(url):
    """Detect source information from article URL"""
    sources = dynamic_api.get_url_sources()
    
    try:
        parsed_url = urllib.parse.urlparse(url.lower())
        domain = parsed_url.netloc.replace('www.', '')
        
        for source_id, source_info in sources.items():
            source_domain = source_info["domain"]
            if domain == source_domain or domain.endswith(f'.{source_domain}'):
                return source_info
                
    except Exception as e:
        logger.error(f"Error detecting source from URL {url}: {e}")
    
    return None

# FastAPI Routes

@app.get("/", response_model=Dict[str, Any])
async def home():
    """Enhanced health check endpoint with dynamic source information"""
    try:
        sources = dynamic_api.get_url_sources()
        data_files = dynamic_api.get_data_files()
        
        # Count total articles
        total_articles = 0
        for filename in data_files.keys():
            try:
                articles = load_articles_from_file(filename)
                total_articles += len(articles)
            except:
                pass
        
        return {
            "message": "🛡️ Cybersecurity News API - FastAPI Edition",
            "version": "4.0.0",
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "total_sources": len(sources),
                "total_articles": total_articles,
                "data_files": len(data_files)
            },
            "endpoints": {
                "news": {
                    "/api/news": "Get all cybersecurity news with pagination",
                    "/api/news/sources": "Get all configured news sources",
                    "/api/news/source/{source_id}": "Get news from specific source",
                    "/api/news/search": "Search articles by content"
                },
                "utilities": {
                    "/api/article/{encoded_url}": "Get specific article by URL",
                    "/api/stats": "Get comprehensive API statistics",
                    "/api/config": "Get API configuration details",
                    "/api/config/reload": "Reload source configuration (POST)",
                    "/api/health": "Health check endpoint",
                    "/api/notifications": "Frontend polling endpoint for notifications (GET)"
                },
                "real_time": {
                    "/api/notify": "Receive notifications from monitoring system (POST)"
                }
            },
            "features": [
                "🔄 Dynamic source configuration",
                "📊 Multi-format data support",
                "🔍 Advanced search with relevance",
                "⚡ Real-time updates",
                "🛡️ Comprehensive error handling",
                "📈 Performance monitoring",
                "🚀 FastAPI high-performance async"
            ],
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "🛡️ Cybersecurity News API - FastAPI Edition",
                "version": "4.0.0",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/news", response_model=NewsResponse)
async def get_all_news(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of articles per page"),
    source: Optional[str] = Query(None, description="Filter by source ID")
):
    """Get all cybersecurity news from summarized AI-processed data only - REAL-TIME UPDATES"""
    try:
        # 🚀 SPEED OPTIMIZATION: Check Redis cache for paginated response first
        cache_key = f"cyberx:paginated_news:{page}:{limit}:{source or 'all'}"
        
        if REDIS_AVAILABLE:
            try:
                cached_response = redis_client.get(cache_key)
                if cached_response:
                    logger.info(f"🚀 Loaded paginated news from Redis cache (Worker {WORKER_ID})")
                    return NewsResponse.parse_raw(cached_response)
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")
        
        # 🚀 Load fresh data with automatic cache invalidation
        all_articles = get_fresh_news_data()
        
        # If no data found, return empty response
        if not all_articles:
            logger.warning("No articles found in summarized data file")
            return NewsResponse(
                status="success",
                totalResults=0,
                page=page,
                limit=limit,
                articles=[],
                sources_available=0,
                data_sources_used=["summarized"]
            )
        
        # Apply source filtering if requested
        if source:
            all_articles = [
                article for article in all_articles 
                if article.get("source", {}).get("url", "").lower().find(source.lower()) != -1
            ]
        
        # Sort by publishedAt (newest first)
        all_articles.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_articles = all_articles[start_idx:end_idx]
        
        # Format articles for consistent API response (optimized for speed - minimal fields only)
        formatted_articles = []
        for article in paginated_articles:
            formatted_articles.append({
                "id": generate_article_id(article),
                "source": article.get("source", {}),
                "title": article.get("title", ""),
                "summary": article.get("summary", ""),
                "url": article.get("url", ""),
                "urlToImage": article.get("urlToImage", ""),
                "publishedAt": article.get("publishedAt", ""),
                "domain": article.get("source", {}).get("url", "").replace("https://", "").replace("http://", "").split("/")[0]
            })
        
        response = NewsResponse(
            status="success",
            totalResults=len(all_articles),
            page=page,
            limit=limit,
            articles=formatted_articles,
            sources_available=len(set(article.get("source", {}).get("url", "") for article in all_articles)),
            data_sources_used=["summarized"]
        )
        
        # 🚀 SPEED OPTIMIZATION: Cache the paginated response in Redis
        if REDIS_AVAILABLE:
            try:
                redis_client.setex(cache_key, 300, response.json())  # Cache for 5 minutes
                logger.info(f"💾 Cached paginated response in Redis (Worker {WORKER_ID})")
            except Exception as e:
                logger.warning(f"Redis response cache write error: {e}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting all news: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch news",
                "error": str(e)
            }
        )

@app.get("/api/news/sources", response_model=Dict[str, Any])
async def get_sources():
    """Get all available news sources dynamically from configuration"""
    try:
        sources = dynamic_api.get_url_sources()
        sources_list = list(sources.values())
        
        # Add statistics about each source
        data_files = dynamic_api.get_data_files()
        for source in sources_list:
            source["articles_count"] = 0  # This could be enhanced to count actual articles per source
            source["last_updated"] = None
        
        return {
            "status": "success",
            "total_sources": len(sources_list),
            "sources": sources_list,
            "last_config_update": datetime.fromtimestamp(dynamic_api._last_config_check).isoformat() if dynamic_api._last_config_check else None
        }
        
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch sources",
                "error": str(e)
            }
        )

@app.get("/api/news/source/{source_id}", response_model=Dict[str, Any])
async def get_news_by_source(source_id: str):
    """Get news from specific source with dynamic source detection"""
    try:
        sources = dynamic_api.get_url_sources()
        
        if source_id not in sources:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"Source '{source_id}' not found",
                    "available_sources": list(sources.keys())
                }
            )
        
        source_info = sources[source_id]
        all_articles = []
        
        # Load articles from all available data files
        data_files = dynamic_api.get_data_files()
        
        for file_type in ['summarized', 'live', 'daily_archive']:
            type_files = [f for f, info in data_files.items() if info['type'] == file_type]
            
            for filename in type_files:
                articles = load_articles_from_file(filename)
                for article in articles:
                    formatted_article = format_article_for_api(article, source_info)
                    # Filter by source
                    if formatted_article.get("source", {}).get("id") == source_id:
                        all_articles.append(formatted_article)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
            elif not url:  # Include articles without URLs
                unique_articles.append(article)
        
        # Sort by scraped date (newest first)
        unique_articles.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
        
        return {
            "status": "success",
            "source": source_info,
            "totalResults": len(unique_articles),
            "articles": unique_articles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting news for source {source_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to fetch news for source {source_id}",
                "error": str(e)
            }
        )

@app.get("/api/article/{article_url:path}", response_model=Dict[str, Any])
async def get_article_by_id(article_url: str):
    """Get specific article by URL - FULL CONTENT for article detail view"""
    try:
        # Decode the URL
        decoded_url = urllib.parse.unquote(article_url)
        
        # Load all articles from summarized_news_hf.json
        articles = load_articles_from_file("summarized_news_hf.json")
        
        # Find the article by URL
        for article in articles:
            if article.get("url") == decoded_url:
                # Return FULL article data for detail view (including content)
                return {
                    "status": "success",
                    "article": {
                        "id": generate_article_id(article),
                        "source": article.get("source"),
                        "title": article.get("title", ""),
                        "summary": article.get("summary", ""),
                        "content": article.get("content", ""),  # FULL content for detail view
                        "url": article.get("url", ""),
                        "urlToImage": article.get("urlToImage", "") or article.get("main_image", ""),
                        "publishedAt": article.get("publishedAt", "") or article.get("scraped_at", ""),
                        "author": article.get("author", ""),
                        "word_count": article.get("word_count", 0),
                        "domain": article.get("domain", "")
                    }
                }
        
        # If not found, return error
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": "Article not found"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article by URL {article_url}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch article"
            }
        )

@app.get("/api/news/search", response_model=SearchResponse)
async def search_news(
    q: str = Query(..., description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source ID")
):
    """Search news articles by title, content, or summary with dynamic source support"""
    try:
        query = q.lower().strip()
        if not query:
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "message": "Search query is required (use 'q' parameter)"
                }
            )
        
        all_articles = []
        data_files = dynamic_api.get_data_files()
        
        # Search in all available data files
        for file_type in ['summarized', 'live', 'daily_archive']:
            type_files = [f for f, info in data_files.items() if info['type'] == file_type]
            
            for filename in type_files:
                articles = load_articles_from_file(filename)
                for article in articles:
                    # Search in multiple fields
                    title = article.get("title", "").lower()
                    content = article.get("content", "").lower()
                    description = article.get("description", "").lower()
                    summary = article.get("summary", "").lower()
                    
                    # Check if query matches any field
                    if (query in title or query in content or 
                        query in description or query in summary):
                        
                        formatted_article = format_article_for_api(article)
                        
                        # Apply source filter if provided
                        if source:
                            article_source = formatted_article.get("source", {}).get("id", "")
                            if article_source.lower() != source.lower():
                                continue
                        
                        # Add relevance score for sorting
                        relevance_score = 0
                        if query in title:
                            relevance_score += 3  # Title matches are most relevant
                        if query in summary:
                            relevance_score += 2  # Summary matches are very relevant
                        if query in description:
                            relevance_score += 1  # Description matches are relevant
                        if query in content:
                            relevance_score += 0.5  # Content matches are least relevant
                        
                        formatted_article["relevance_score"] = relevance_score
                        all_articles.append(formatted_article)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
            elif not url:
                unique_articles.append(article)
        
        # Sort by relevance score first, then by date
        unique_articles.sort(key=lambda x: (
            -x.get("relevance_score", 0),  # Higher relevance first (negative for descending)
            x.get("scraped_at", "")        # Then by date descending
        ), reverse=True)
        
        # Remove relevance score from response
        for article in unique_articles:
            article.pop("relevance_score", None)
        
        return SearchResponse(
            status="success",
            query=query,
            source_filter=source,
            totalResults=len(unique_articles),
            articles=unique_articles,
            sources_searched=len(dynamic_api.get_url_sources())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Search failed",
                "error": str(e)
            }
        )

@app.post("/api/notify", response_model=Dict[str, Any])
async def notify_new_articles(notification: NotificationRequest):
    """Endpoint for real-time notifications from the monitoring system"""
    try:
        logger.info(f"📱 Real-time notification: {notification.type}, {notification.count} articles")
        
        # Store a compact notification object for frontend polling
        notifications_queue.insert(0, {
            "title": notification.title or ("Breaking News" if notification.count == 1 else f"{notification.count} New Articles"),
            "body": notification.message or notification.body or "New cybersecurity updates are available",
            "count": notification.count,
            "priority": notification.priority,
            "timestamp": notification.timestamp or datetime.now().isoformat(),
            "grouped": True
        })
        
        # Keep queue bounded
        del notifications_queue[50:]
        
        return {
            "status": "success",
            "message": "Notification received",
            "type": notification.type,
            "count": notification.count,
            "timestamp": notification.timestamp or datetime.now().isoformat(),
            "response_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing notification: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error", 
                "message": "Failed to process notification"
            }
        )

@app.get("/api/notifications", response_model=Dict[str, Any])
async def poll_notifications(clear: bool = Query(False, description="Clear notifications after reading")):
    """Lightweight polling endpoint the app can call periodically."""
    try:
        payload = {
            "status": "success",
            "count": len(notifications_queue),
            "notifications": notifications_queue[:5]  # return recent few
        }
        
        if clear:
            notifications_queue.clear()
            
        return payload
        
    except Exception as e:
        logger.error(f"Error in poll_notifications: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error", 
                "message": "Failed to fetch notifications"
            }
        )

@app.get("/api/health", response_model=Dict[str, Any])
async def health_check():
    """Enhanced health check endpoint for monitoring"""
    try:
        sources = dynamic_api.get_url_sources()
        data_files = dynamic_api.get_data_files()
        
        # Check primary data file availability
        primary_files = ['summarized_news_hf.json', 'cybersecurity_news_live.json']
        file_status = "healthy"
        
        for primary_file in primary_files:
            if primary_file in data_files:
                file_status = "healthy"
                break
        else:
            # Check if any daily archive files exist
            archive_files = [f for f, info in data_files.items() if info['type'] == 'daily_archive']
            file_status = "partial" if archive_files else "missing_data"
        
        # Calculate uptime and performance metrics
        health_status = {
            "status": "healthy" if file_status in ["healthy", "partial"] else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "api_version": "4.0-fastapi",
            "configuration": {
                "sources_configured": len(sources),
                "data_files_available": len(data_files)
            },
            "data_status": file_status,
            "endpoints_active": [
                "/api/news",
                "/api/news/sources", 
                "/api/news/search",
                "/api/stats",
                "/api/config"
            ],
            "features_enabled": [
                "dynamic_sources",
                "multi_format_support", 
                "intelligent_search",
                "real_time_updates",
                "async_processing"
            ]
        }
        
        if health_status["status"] != "healthy":
            raise HTTPException(status_code=503, detail=health_status)
            
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "api_version": "4.0-fastapi"
            }
        )

@app.get("/health")
async def simple_health_check():
    """Simple health check for Docker/load balancer"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/api/refresh-cache")
async def refresh_news_cache():
    """Manually refresh the news data cache across all instances - forces reload of fresh data"""
    global news_data_cache
    
    try:
        # Force cache invalidation across all instances
        old_count = len(news_data_cache["data"]) if news_data_cache["data"] else 0
        invalidate_distributed_cache()
        
        # Load fresh data
        fresh_data = get_fresh_news_data()
        new_count = len(fresh_data) if fresh_data else 0
        
        return {
            "status": "success",
            "message": f"News cache refreshed successfully across all instances (Worker {WORKER_ID})",
            "timestamp": datetime.now().isoformat(),
            "worker_id": WORKER_ID,
            "articles_before": old_count,
            "articles_after": new_count,
            "cache_info": {
                "file_path": news_data_cache["file_path"],
                "last_modified": datetime.fromtimestamp(news_data_cache["last_modified"]).isoformat() if news_data_cache["last_modified"] else None,
                "redis_available": REDIS_AVAILABLE
            }
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"Failed to refresh cache: {str(e)}",
                "worker_id": WORKER_ID,
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/cache-info")
async def get_cache_info():
    """Get information about the current cache state across all instances"""
    global news_data_cache
    
    cache_info = {
        "local_cache": {
            "worker_id": WORKER_ID,
            "has_data": news_data_cache["data"] is not None,
            "articles_count": len(news_data_cache["data"]) if news_data_cache["data"] else 0,
            "file_path": news_data_cache["file_path"],
            "last_modified": datetime.fromtimestamp(news_data_cache["last_modified"]).isoformat() if news_data_cache["last_modified"] else None
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Add Redis cache info if available
    if REDIS_AVAILABLE:
        try:
            redis_mtime = redis_client.get("cyberx:news_mtime")
            redis_data_exists = redis_client.exists("cyberx:news_data")
            redis_ttl = redis_client.ttl("cyberx:news_data")
            
            cache_info["redis_cache"] = {
                "available": True,
                "has_data": bool(redis_data_exists),
                "last_modified": datetime.fromtimestamp(float(redis_mtime)).isoformat() if redis_mtime else None,
                "ttl_seconds": redis_ttl if redis_ttl > 0 else None,
                "redis_url": REDIS_URL
            }
        except Exception as e:
            cache_info["redis_cache"] = {
                "available": False,
                "error": str(e)
            }
    else:
        cache_info["redis_cache"] = {
            "available": False,
            "reason": "Redis not configured"
        }
    
    return cache_info

@app.get("/api/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get comprehensive real-time statistics about the news data"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "api_version": "4.0-fastapi",
            "configuration": {}
        }
        
        # Dynamic source information
        sources = dynamic_api.get_url_sources()
        stats["configuration"] = {
            "total_sources": len(sources),
            "sources": list(sources.keys()),
            "last_config_update": datetime.fromtimestamp(dynamic_api._last_config_check).isoformat() if dynamic_api._last_config_check else None
        }
        
        # Data files analysis
        data_files = dynamic_api.get_data_files()
        stats["data_files"] = {}
        
        total_articles = 0
        for filename, info in data_files.items():
            try:
                articles = load_articles_from_file(filename)
                article_count = len(articles)
                total_articles += article_count
                
                stats["data_files"][filename] = {
                    "type": info["type"],
                    "count": article_count,
                    "size_bytes": info["size"],
                    "size_kb": round(info["size"] / 1024, 2),
                    "last_modified": info["modified"].isoformat(),
                    "status": "healthy" if article_count > 0 else "empty"
                }
            except Exception as e:
                stats["data_files"][filename] = {
                    "type": info["type"],
                    "error": str(e),
                    "size_bytes": info["size"],
                    "last_modified": info["modified"].isoformat(),
                    "status": "error"
                }
        
        # Summary statistics
        stats["summary"] = {
            "total_articles_across_all_files": total_articles,
            "total_data_files": len(data_files),
            "healthy_files": len([f for f in stats["data_files"].values() if f.get("status") == "healthy"]),
            "empty_files": len([f for f in stats["data_files"].values() if f.get("status") == "empty"]),
            "error_files": len([f for f in stats["data_files"].values() if f.get("status") == "error"])
        }
        
        # Recent activity (from live monitoring if available)
        live_files = [f for f, info in data_files.items() if info['type'] == 'live']
        if live_files:
            try:
                live_data = load_articles_from_file(live_files[0])
                if live_data:
                    recent_articles = sorted(live_data, key=lambda x: x.get("scraped_at", ""), reverse=True)[:5]
                    stats["recent_activity"] = [
                        {
                            "title": article.get("title", "")[:100] + ("..." if len(article.get("title", "")) > 100 else ""),
                            "source": article.get("domain", "unknown"),
                            "scraped_at": article.get("scraped_at", ""),
                            "url": article.get("url", "")
                        }
                        for article in recent_articles
                    ]
            except Exception as e:
                stats["recent_activity"] = {"error": str(e)}
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/config", response_model=Dict[str, Any])
async def get_config():
    """Get current API configuration and source information"""
    try:
        sources = dynamic_api.get_url_sources()
        data_files = dynamic_api.get_data_files()
        
        config_info = {
            "api_version": "4.0-fastapi",
            "timestamp": datetime.now().isoformat(),
            "configuration_file": dynamic_api.url_config_file,
            "total_configured_sources": len(sources),
            "sources": sources,
            "data_directory": dynamic_api.data_dir,
            "available_data_files": {
                filename: {
                    "type": info["type"],
                    "size_kb": round(info["size"] / 1024, 2),
                    "modified": info["modified"].isoformat()
                }
                for filename, info in data_files.items()
            },
            "features": [
                "Dynamic source detection from URL config",
                "Multi-format data file support",
                "Intelligent article deduplication",
                "Advanced search with relevance scoring",
                "Real-time configuration updates",
                "Comprehensive error handling",
                "FastAPI async performance",
                "Automatic API documentation"
            ]
        }
        
        return config_info
        
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/api/config/reload", response_model=Dict[str, Any])
async def reload_config():
    """Manually reload the URL configuration"""
    try:
        # Force reload of URL sources
        dynamic_api._url_sources = None
        dynamic_api._last_config_check = 0
        
        # Get fresh sources
        sources = dynamic_api.get_url_sources()
        
        return {
            "status": "success",
            "message": "Configuration reloaded successfully",
            "timestamp": datetime.now().isoformat(),
            "total_sources": len(sources),
            "sources": list(sources.keys())
        }
        
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to reload configuration",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# ====== ALERT SYSTEM ENDPOINTS ======

@app.get("/api/alerts", response_model=Dict[str, Any])
async def get_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Number of alerts per page"),
    unread_only: bool = Query(False, description="Show only unread alerts")
):
    """Get recent alerts and notifications with pagination"""
    try:
        alerts_file = os.path.join(ALERTS_DIR, "alerts_log.json")
        
        if not os.path.exists(alerts_file):
            return {
                "status": "success",
                "alerts": [],
                "totalResults": 0,
                "unreadCount": 0,
                "page": page,
                "limit": limit,
                "message": "No alerts available yet"
            }
        
        with open(alerts_file, 'r', encoding='utf-8') as f:
            all_alerts = json.load(f)
        
        # Sort by timestamp (newest first)
        all_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Filter unread if requested
        if unread_only:
            all_alerts = [alert for alert in all_alerts if not alert.get('read', False)]
        
        # Calculate unread count
        unread_count = len([alert for alert in all_alerts if not alert.get('read', False)])
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_alerts = all_alerts[start_idx:end_idx]
        
        return {
            "status": "success",
            "alerts": paginated_alerts,
            "totalResults": len(all_alerts),
            "unreadCount": unread_count,
            "page": page,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch alerts",
                "error": str(e)
            }
        )

@app.post("/api/alerts/mark-read", response_model=Dict[str, Any])
async def mark_alerts_read(request: AlertMarkReadRequest):
    """Mark specific alerts as read"""
    try:
        alerts_file = os.path.join(ALERTS_DIR, "alerts_log.json")
        
        if not os.path.exists(alerts_file):
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": "No alerts file found"
                }
            )
        
        with open(alerts_file, 'r', encoding='utf-8') as f:
            alerts = json.load(f)
        
        modified_count = 0
        
        if request.mark_all:
            # Mark all alerts as read
            for alert in alerts:
                if not alert.get('read', False):
                    alert['read'] = True
                    alert['read_at'] = datetime.now().isoformat()
                    modified_count += 1
        else:
            # Mark specific alerts as read
            for alert in alerts:
                alert_timestamp = alert.get('timestamp', '')
                if alert_timestamp in request.alert_ids and not alert.get('read', False):
                    alert['read'] = True
                    alert['read_at'] = datetime.now().isoformat()
                    modified_count += 1
        
        # Save updated alerts
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2, default=str, ensure_ascii=False)
        
        return {
            "status": "success",
            "message": f"Marked {modified_count} alerts as read",
            "modified_count": modified_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking alerts as read: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to mark alerts as read",
                "error": str(e)
            }
        )

@app.get("/api/alerts/stats", response_model=Dict[str, Any])
async def get_alert_stats():
    """Get alert statistics and metrics"""
    try:
        alerts_file = os.path.join(ALERTS_DIR, "alerts_log.json")
        alert_state_file = os.path.join(ALERTS_DIR, "alert_state.json")
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_alerts": 0,
            "unread_alerts": 0,
            "today_alerts": 0,
            "this_week_alerts": 0,
            "alert_trends": [],
            "file_watcher_stats": {}
        }
        
        # Load alerts if available
        if os.path.exists(alerts_file):
            with open(alerts_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
            
            stats["total_alerts"] = len(alerts)
            stats["unread_alerts"] = len([a for a in alerts if not a.get('read', False)])
            
            # Calculate date-based stats
            now = datetime.now()
            today = now.date()
            week_ago = now - timedelta(days=7)
            
            stats["today_alerts"] = len([
                a for a in alerts 
                if datetime.fromisoformat(a.get('timestamp', '2000-01-01')).date() == today
            ])
            
            stats["this_week_alerts"] = len([
                a for a in alerts 
                if datetime.fromisoformat(a.get('timestamp', '2000-01-01')) >= week_ago
            ])
            
            # Generate trend data (last 7 days)
            trend_data = {}
            for i in range(7):
                date = (now - timedelta(days=i)).date()
                trend_data[date.isoformat()] = 0
            
            for alert in alerts:
                try:
                    alert_date = datetime.fromisoformat(alert.get('timestamp', '')).date()
                    if alert_date.isoformat() in trend_data:
                        trend_data[alert_date.isoformat()] += 1
                except:
                    continue
            
            stats["alert_trends"] = [
                {"date": date, "count": count} 
                for date, count in sorted(trend_data.items())
            ]
        
        # Load file watcher stats if available
        if os.path.exists(alert_state_file):
            with open(alert_state_file, 'r', encoding='utf-8') as f:
                watcher_stats = json.load(f)
                stats["file_watcher_stats"] = watcher_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to fetch alert statistics",
                "error": str(e)
            }
        )

@app.post("/api/alerts/test", response_model=Dict[str, Any])
async def test_alert_system():
    """Test endpoint to create a sample alert"""
    try:
        # Create a test alert
        test_alert = {
            "type": "test_alert",
            "timestamp": datetime.now().isoformat(),
            "count": 1,
            "articles": [{
                "title": "Test Cybersecurity Alert - System Verification",
                "source": "System Test",
                "url": "https://test.example.com",
                "published_at": datetime.now().isoformat(),
                "summary": "This is a test alert to verify the alert system is working correctly."
            }],
            "summary": {
                "total_new": 1,
                "sources": ["System Test"],
                "keywords": ["test", "verification"]
            },
            "read": False
        }
        
        # Save to alerts log
        alerts_file = os.path.join(ALERTS_DIR, "alerts_log.json")
        
        alerts = []
        if os.path.exists(alerts_file):
            with open(alerts_file, 'r', encoding='utf-8') as f:
                alerts = json.load(f)
        
        alerts.append(test_alert)
        
        # Keep only last 100 alerts
        if len(alerts) > 100:
            alerts = alerts[-100:]
        
        with open(alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2, default=str, ensure_ascii=False)
        
        # Also add to notifications queue for real-time polling
        notifications_queue.insert(0, {
            "title": "Test Alert",
            "body": "System test alert generated successfully",
            "count": 1,
            "priority": "normal",
            "timestamp": datetime.now().isoformat(),
            "grouped": False,
            "test": True
        })
        
        return {
            "status": "success",
            "message": "Test alert created successfully",
            "alert": test_alert
        }
        
    except Exception as e:
        logger.error(f"Error creating test alert: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to create test alert",
                "error": str(e)
            }
        )

@app.post("/api/google-news/search", response_model=Dict[str, Any])
async def google_news_search(request: GoogleNewsSearchRequest):
    """Search Google News for cybersecurity-related articles"""
    try:
        # Build Google News RSS URL
        base_url = "https://news.google.com/rss/search"
        params = {
            'q': request.query,
            'hl': 'en-IN',
            'gl': 'IN',
            'ceid': 'IN:en'
        }
        
        search_url = f"{base_url}?{urlencode(params)}"
        
        # Fetch RSS feed
        logger.info(f"Fetching Google News RSS: {search_url}")
        
        # Use httpx for async HTTP requests
        async with httpx.AsyncClient() as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = await client.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
        
        # Parse RSS feed
        feed = feedparser.parse(response.content)
        
        articles = []
        for entry in feed.entries[:request.limit]:
            # Extract image from content if available
            image_url = None
            if hasattr(entry, 'media_content') and entry.media_content:
                image_url = entry.media_content[0].get('url')
            elif hasattr(entry, 'enclosures') and entry.enclosures:
                image_url = entry.enclosures[0].href
            
            # Clean the title (remove source name)
            title = entry.title
            if ' - ' in title:
                title = title.rsplit(' - ', 1)[0]
            
            # Extract source from link
            source_name = "Google News"
            if hasattr(entry, 'source'):
                source_name = entry.source.get('title', 'Google News')
            
            article = {
                'title': title,
                'url': entry.link,
                'description': getattr(entry, 'summary', ''),
                'source': source_name,
                'publishedAt': getattr(entry, 'published', datetime.now().isoformat()),
                'urlToImage': image_url
            }
            
            articles.append(article)
        
        return {
            "status": "success",
            "query": request.query,
            "totalResults": len(articles),
            "articles": articles
        }
        
    except httpx.RequestError as e:
        logger.error(f"Error fetching Google News: {e}")
        raise HTTPException(
            status_code=502,
            detail={
                "status": "error",
                "message": "Failed to fetch news from Google",
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error in Google News search: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Internal server error",
                "error": str(e)
            }
        )

@app.get("/api/google-news/trending", response_model=Dict[str, Any])
async def google_news_trending():
    """Get trending cybersecurity topics"""
    try:
        trending_topics = [
            "recent malware attacks",
            "data breaches 2025",
            "cybersecurity news today",
            "ransomware attacks",
            "phishing campaigns",
            "zero-day vulnerabilities",
            "cyber threats India",
            "security incidents",
            "hacking news",
            "cyber crime reports"
        ]
        
        return {
            "status": "success",
            "topics": trending_topics
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Failed to get trending topics",
                "error": str(e)
            }
        )

# ========= ARTICLE EXTRACTION / READABILITY FALLBACK ========= #

SAFE_TAGS = {
    'p','h1','h2','h3','h4','h5','h6','ul','ol','li','strong','em','b','i','code','pre','blockquote','img','figure','figcaption','a'
}
SAFE_ATTRS = {'href','src','alt','title'}

def _clean_html(raw_html: str, base_url: str):
    try:
        soup = BeautifulSoup(raw_html, 'lxml')
        # Remove scripts/styles/forms
        for tag in soup(['script','style','noscript','iframe','form','footer','header','nav','aside']):
            tag.decompose()
        # Keep only safe tags & attributes
        for el in soup.find_all(True):
            if el.name not in SAFE_TAGS:
                el.unwrap()
                continue
            # Strip dangerous attrs
            attrs = dict(el.attrs)
            for attr in attrs:
                if attr not in SAFE_ATTRS:
                    del el.attrs[attr]
            # Convert relative image src to absolute
            if el.name == 'img' and el.get('src') and el['src'].startswith('/'):
                try:
                    parsed = urllib.parse.urlparse(base_url)
                    el['src'] = f"{parsed.scheme}://{parsed.netloc}{el['src']}"
                except:
                    pass
        # Basic heuristic: collect top content container
        candidates = sorted(
            [(len(p.get_text(strip=True)), p) for p in soup.select('article, main, .content, .post, .entry, body')],
            key=lambda x: x[0], reverse=True
        )
        main = candidates[0][1] if candidates else soup.body or soup
        # Extract title
        title_tag = soup.find('h1') or soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ''
        # Extract first image
        img = main.find('img')
        image = img['src'] if img and img.get('src') else ''
        # Build blocks (paragraphs & headings)
        blocks = []
        for node in main.descendants:
            if node.name in ('h1','h2','h3','p','li'):
                text = node.get_text(' ', strip=True)
                if text and len(text) > 3:
                    blocks.append({'type': 'heading' if node.name.startswith('h') else 'text', 'text': text})
        content_text = '\n\n'.join(b['text'] for b in blocks if b['type'] == 'text')
        word_count = len(content_text.split())
        return {
            'title': title,
            'image': image,
            'blocks': blocks[:500],  # safety cap
            'word_count': word_count,
            'html': str(main)[:150000]  # capped
        }
    except Exception as e:
        logger.error(f"HTML cleaning error: {e}")
        return {'title':'','image':'','blocks':[], 'word_count':0, 'html':''}

@lru_cache(maxsize=256)
async def _cached_fetch_async(url: str):
    async with httpx.AsyncClient() as client:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        resp = await client.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text

@app.post('/api/extract', response_model=Dict[str, Any])
async def extract_article(request: ExtractionRequest):
    """Fetch and extract readable article content for fallback rendering.
    Request JSON: {"url": "https://..."}
    Response: { status, meta: {title,image,source,domain}, content: { blocks: [...], word_count, html }}
    """
    try:
        url = str(request.url)
        html = await _cached_fetch_async(url)
        cleaned = _clean_html(html, url)
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.replace('www.','')
        
        return {
            'status':'success',
            'fetched_at': datetime.utcnow().isoformat()+ 'Z',
            'meta': {
                'title': cleaned['title'] or url,
                'url': url,
                'domain': domain,
                'image': cleaned['image']
            },
            'content': {
                'blocks': cleaned['blocks'],
                'word_count': cleaned['word_count']
            }
        }
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail={
                'status': 'error',
                'message': 'fetch failed',
                'error': str(e)
            }
        )
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': 'internal extraction failure'
            }
        )

@app.get("/test-metrics")
async def test_metrics():
    """Simple test metrics endpoint"""
    return {"status": "ok", "message": "Test metrics endpoint working"}

@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Prometheus metrics endpoint for monitoring dashboard"""
    global request_count, error_count, request_duration_sum, endpoint_stats
    
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Calculate uptime
        uptime_seconds = time.time() - start_time
        
        # Calculate average response time
        avg_response_time = request_duration_sum / max(request_count, 1)
        
        # Count articles and sources
        articles_count = 0
        sources_count = 0
        
        # Check data files
        data_files = [
            "cybersecurity_news_live.json",
            "News_today_*.json",
            "summarized_news_hf.json"
        ]
        
        for filename in os.listdir(DATA_DIR) if os.path.exists(DATA_DIR) else []:
            if filename.endswith('.json') and any(pattern.replace('*', '') in filename for pattern in data_files):
                try:
                    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'articles' in data:
                            articles_count += len(data['articles'])
                        elif isinstance(data, list):
                            articles_count += len(data)
                except:
                    continue
        
        # Count URL sources
        api_instance = DynamicNewsAPI()
        sources = api_instance.get_url_sources()
        sources_count = len(sources)
        
        # Generate Prometheus metrics format
        metrics = f"""# HELP fastapi_requests_total Total number of HTTP requests
# TYPE fastapi_requests_total counter
fastapi_requests_total {request_count}

# HELP fastapi_request_errors_total Total number of HTTP request errors
# TYPE fastapi_request_errors_total counter
fastapi_request_errors_total {error_count}

# HELP fastapi_request_duration_seconds Average request duration in seconds
# TYPE fastapi_request_duration_seconds gauge
fastapi_request_duration_seconds {avg_response_time:.4f}

# HELP fastapi_uptime_seconds Application uptime in seconds
# TYPE fastapi_uptime_seconds counter
fastapi_uptime_seconds {uptime_seconds:.0f}

# HELP system_cpu_usage_percent Current CPU usage percentage
# TYPE system_cpu_usage_percent gauge
system_cpu_usage_percent {cpu_percent}

# HELP system_memory_usage_percent Current memory usage percentage
# TYPE system_memory_usage_percent gauge
system_memory_usage_percent {memory.percent}

# HELP system_disk_usage_percent Current disk usage percentage
# TYPE system_disk_usage_percent gauge
system_disk_usage_percent {disk.percent}

# HELP cybersecurity_articles_total Total number of cybersecurity articles
# TYPE cybersecurity_articles_total gauge
cybersecurity_articles_total {articles_count}

# HELP cybersecurity_sources_total Total number of configured sources
# TYPE cybersecurity_sources_total gauge
cybersecurity_sources_total {sources_count}

# HELP api_endpoint_requests_total Requests per endpoint
# TYPE api_endpoint_requests_total counter
"""

        # Add per-endpoint metrics
        for endpoint, stats in endpoint_stats.items():
            safe_endpoint = endpoint.replace(' ', '_').replace('/', '_').replace('{', '').replace('}', '').replace(':', '')
            metrics += f'api_endpoint_requests_total{{endpoint="{safe_endpoint}"}} {stats["count"]}\n'
            metrics += f'api_endpoint_errors_total{{endpoint="{safe_endpoint}"}} {stats["errors"]}\n'

        return metrics
        
    except Exception as e:
        logger.error(f"Metrics generation error: {e}")
        return f"# Error generating metrics: {str(e)}\n"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("cybersecurity_fastapi:app", host="0.0.0.0", port=8080, reload=True)
