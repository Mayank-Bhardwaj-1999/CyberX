# Gunicorn configuration for production
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests, with up to 50 requests variation
preload_app = True

# Timeout for graceful workers restart
timeout = 120
keepalive = 5

# Logging - simplified to avoid conflicts
loglevel = "info"
# Don't log to files to avoid permission issues
# accesslog = "/app/logs/access.log"
# errorlog = "/app/logs/error.log"
accesslog = "-"  # stdout
errorlog = "-"   # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'cybersecurity_fastapi'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment if you have SSL certificates)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Enable auto-reload in development (disable in production)
reload = os.getenv('ENVIRONMENT', 'production') == 'development'

# Graceful timeout
graceful_timeout = 30

# Maximum time a worker can take to restart
worker_timeout = 120
