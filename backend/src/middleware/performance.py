"""
Production-ready middleware for FastAPI with caching, rate limiting, and monitoring
Designed to handle 1000-2000 concurrent users efficiently
"""

import time
import asyncio
import json
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import logging
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
REQUEST_COUNT = Counter('fastapi_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('fastapi_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('fastapi_active_connections', 'Active connections')
CACHE_HITS = Counter('fastapi_cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('fastapi_cache_misses_total', 'Cache misses')
RATE_LIMIT_BLOCKS = Counter('fastapi_rate_limit_blocks_total', 'Rate limit blocks')

logger = logging.getLogger(__name__)

class RedisCache:
    """High-performance Redis cache for API responses"""
    
    def __init__(self, redis_url: str = "redis://redis:6379/0"):
        self.redis_url = redis_url
        self.redis_client = None
        self.default_ttl = 300  # 5 minutes
        
    async def get_client(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    def generate_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include query params and headers for better cache granularity
        query_string = str(request.query_params)
        user_agent = request.headers.get("user-agent", "")
        
        # Create hash of request components
        key_data = f"{request.method}:{request.url.path}:{query_string}:{user_agent}"
        return f"api_cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Dict[Any, Any]]:
        """Get cached response"""
        try:
            client = await self.get_client()
            cached_data = await client.get(key)
            if cached_data:
                CACHE_HITS.inc()
                return json.loads(cached_data)
            CACHE_MISSES.inc()
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            CACHE_MISSES.inc()
            return None
    
    async def set(self, key: str, data: Dict[Any, Any], ttl: int = None) -> bool:
        """Set cached response"""
        try:
            client = await self.get_client()
            ttl = ttl or self.default_ttl
            await client.setex(key, ttl, json.dumps(data, default=str))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> bool:
        """Delete cache entries matching pattern"""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                await client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

class RateLimiter:
    """Advanced rate limiter with sliding window and burst protection"""
    
    def __init__(self, redis_url: str = "redis://rate-limiter:6380"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Rate limits (requests per minute)
        self.limits = {
            'default': 60,      # 60 requests per minute for general endpoints
            'search': 30,       # 30 requests per minute for search
            'news': 100,        # 100 requests per minute for news
            'health': 300,      # 300 requests per minute for health checks
        }
        
        # Burst limits (requests per 10 seconds)
        self.burst_limits = {
            'default': 20,
            'search': 10,
            'news': 30,
            'health': 60,
        }
    
    async def get_client(self):
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
        return self.redis_client
    
    def get_endpoint_category(self, path: str) -> str:
        """Categorize endpoint for rate limiting"""
        if '/health' in path:
            return 'health'
        elif '/search' in path:
            return 'search'
        elif '/news' in path:
            return 'news'
        return 'default'
    
    async def is_allowed(self, request: Request) -> tuple[bool, Dict[str, Any]]:
        """Check if request is allowed based on rate limits"""
        try:
            client = await self.get_client()
            
            # Get client identifier (IP + User-Agent hash for better identification)
            client_ip = request.client.host
            user_agent = request.headers.get("user-agent", "")
            client_id = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
            
            endpoint_category = self.get_endpoint_category(str(request.url.path))
            
            # Check sliding window rate limit (1 minute)
            minute_key = f"rate_limit:minute:{client_id}:{endpoint_category}:{int(time.time() // 60)}"
            minute_limit = self.limits.get(endpoint_category, self.limits['default'])
            
            # Check burst rate limit (10 seconds)
            burst_key = f"rate_limit:burst:{client_id}:{endpoint_category}:{int(time.time() // 10)}"
            burst_limit = self.burst_limits.get(endpoint_category, self.burst_limits['default'])
            
            # Use pipeline for atomic operations
            pipe = client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)
            pipe.incr(burst_key)
            pipe.expire(burst_key, 10)
            
            results = await pipe.execute()
            minute_count = results[0]
            burst_count = results[2]
            
            # Check limits
            if minute_count > minute_limit:
                RATE_LIMIT_BLOCKS.inc()
                return False, {
                    'error': 'Rate limit exceeded',
                    'limit_type': 'minute',
                    'limit': minute_limit,
                    'current': minute_count,
                    'reset_time': (int(time.time() // 60) + 1) * 60
                }
            
            if burst_count > burst_limit:
                RATE_LIMIT_BLOCKS.inc()
                return False, {
                    'error': 'Burst limit exceeded',
                    'limit_type': 'burst',
                    'limit': burst_limit,
                    'current': burst_count,
                    'reset_time': (int(time.time() // 10) + 1) * 10
                }
            
            return True, {
                'minute_remaining': minute_limit - minute_count,
                'burst_remaining': burst_limit - burst_count
            }
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True, {}  # Allow on error

class PerformanceMonitor:
    """Performance monitoring and analytics"""
    
    def __init__(self, postgres_url: str = None):
        self.postgres_url = postgres_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://cybersec_user:secure_password_123@postgres:5432/cybersec_analytics'
        )
        self.worker_id = os.getenv('WORKER_ID', 'unknown')
    
    async def log_request(self, request: Request, response: Response, duration: float):
        """Log request analytics to PostgreSQL"""
        try:
            # Use connection pooling in production
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            
            # Calculate response size
            response_size = 0
            if hasattr(response, 'body'):
                response_size = len(response.body) if response.body else 0
            
            cursor.execute("""
                INSERT INTO api_analytics 
                (endpoint, method, status_code, response_time_ms, ip_address, 
                 user_agent, response_size, worker_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(request.url.path),
                request.method,
                response.status_code,
                int(duration * 1000),  # Convert to milliseconds
                request.client.host,
                request.headers.get("user-agent", ""),
                response_size,
                self.worker_id
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Analytics logging error: {e}")

# Initialize global instances
cache = RedisCache()
rate_limiter = RateLimiter()
performance_monitor = PerformanceMonitor()

async def performance_middleware(request: Request, call_next):
    """Main performance middleware"""
    start_time = time.time()
    
    # Increment active connections
    ACTIVE_CONNECTIONS.inc()
    
    try:
        # Rate limiting check
        is_allowed, rate_info = await rate_limiter.is_allowed(request)
        if not is_allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "details": rate_info,
                    "retry_after": rate_info.get('reset_time', time.time() + 60) - time.time()
                }
            )
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=429
            ).inc()
            return response
        
        # Check cache for GET requests
        if request.method == "GET" and not request.url.path.startswith("/health"):
            cache_key = cache.generate_key(request)
            cached_response = await cache.get(cache_key)
            
            if cached_response:
                response = JSONResponse(
                    content=cached_response['content'],
                    status_code=cached_response['status_code'],
                    headers={"X-Cache": "HIT", **cached_response.get('headers', {})}
                )
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status=response.status_code
                ).inc()
                return response
        
        # Process request
        response = await call_next(request)
        
        # Cache successful GET responses
        if (request.method == "GET" and 
            response.status_code == 200 and 
            not request.url.path.startswith("/health")):
            
            # Extract response content for caching
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            try:
                content = json.loads(response_body.decode())
                cache_data = {
                    'content': content,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                
                # Set different TTL based on endpoint
                ttl = 300  # 5 minutes default
                if '/news' in request.url.path:
                    ttl = 180  # 3 minutes for news
                elif '/search' in request.url.path:
                    ttl = 600  # 10 minutes for search
                
                await cache.set(cache_key, cache_data, ttl)
                
                # Recreate response with cache header
                response = JSONResponse(
                    content=content,
                    status_code=response.status_code,
                    headers={"X-Cache": "MISS", **dict(response.headers)}
                )
                
            except Exception as e:
                logger.error(f"Cache storage error: {e}")
        
        # Add performance headers
        duration = time.time() - start_time
        response.headers["X-Process-Time"] = str(duration)
        response.headers["X-Worker-ID"] = performance_monitor.worker_id
        
        # Update metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.observe(duration)
        
        # Log analytics (async to not block response)
        asyncio.create_task(
            performance_monitor.log_request(request, response, duration)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Middleware error: {e}")
        response = JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        return response
        
    finally:
        # Decrement active connections
        ACTIVE_CONNECTIONS.dec()

async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")

# Cache invalidation functions
async def invalidate_cache_pattern(pattern: str = "api_cache:*"):
    """Invalidate cache entries matching pattern"""
    return await cache.delete_pattern(pattern)

async def invalidate_news_cache():
    """Invalidate news-related cache"""
    return await cache.delete_pattern("api_cache:*news*")
