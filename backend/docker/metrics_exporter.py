#!/usr/bin/env python3
"""
📊 Enhanced Cybersecurity Backend Metrics Exporter
Exports comprehensive real-time metrics for Grafana dashboard
"""

import time
import json
import requests
import psutil
import re
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info, Enum
from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
import threading
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCybersecurityMetricsExporter:
    def __init__(self):
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8080')
        self.data_dir = Path('/app/data')
        self.logs_dir = Path('/app/logs')
        
        # Cache for log parsing
        self.log_cache = {}
        self.last_log_positions = {}
        self.recent_logs = deque(maxlen=1000)  # Keep last 1000 log entries
        self.api_requests = deque(maxlen=500)   # Keep last 500 API requests
        
        # Define metrics
        self.setup_metrics()
        
        # Start metrics collection
        self.running = True
        self.start_time = time.time()
        
    def setup_metrics(self):
        """Setup comprehensive Prometheus metrics for Grafana dashboard"""
        
        # API Health & Traffic Metrics
        self.api_health = Gauge('cybersec_api_health', 'API health status (1=healthy, 0=unhealthy)')
        self.api_response_time = Histogram('cybersec_api_response_time_seconds', 'API response time')
        self.api_requests_total = Counter('cybersec_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
        self.api_traffic_per_minute = Gauge('cybersec_api_traffic_per_minute', 'API requests per minute')
        
        # News Processing Metrics (for Today's Articles & Current Articles)
        self.articles_scraped_total = Counter('cybersec_articles_scraped_total', 'Total articles scraped')
        self.articles_processed_total = Counter('cybersec_articles_processed_total', 'Total articles AI processed')
        self.articles_current = Gauge('cybersec_articles_current', 'Current number of articles in live feed')
        self.articles_today = Gauge('cybersec_articles_today', 'Articles processed today')
        self.articles_summarized_today = Gauge('cybersec_articles_summarized_today', 'Articles summarized today')
        
        # Real-time Activity Metrics
        self.monitoring_cycles_per_minute = Gauge('cybersec_monitoring_cycles_per_minute', 'Monitoring cycles per minute')
        self.scraping_activity = Gauge('cybersec_scraping_activity', 'Current scraping activity (1=active, 0=idle)')
        self.ai_processing_activity = Gauge('cybersec_ai_processing_activity', 'Current AI processing activity (1=active, 0=idle)')
        
        # Log Activity Metrics (by Level)
        self.log_activity_info = Gauge('cybersec_log_activity_info', 'INFO level log entries in last minute')
        self.log_activity_warning = Gauge('cybersec_log_activity_warning', 'WARNING level log entries in last minute')
        self.log_activity_error = Gauge('cybersec_log_activity_error', 'ERROR level log entries in last minute')
        self.log_activity_debug = Gauge('cybersec_log_activity_debug', 'DEBUG level log entries in last minute')
        
        # Recent Issues & Errors
        self.recent_errors_count = Gauge('cybersec_recent_errors_count', 'Error count in last 5 minutes')
        self.recent_warnings_count = Gauge('cybersec_recent_warnings_count', 'Warning count in last 5 minutes')
        self.critical_issues = Gauge('cybersec_critical_issues', 'Critical issues requiring attention')
        
        # System Resource Metrics (Enhanced)
        self.system_cpu_usage = Gauge('cybersec_system_cpu_usage_percent', 'System CPU usage percentage')
        self.system_memory_usage = Gauge('cybersec_system_memory_usage_percent', 'System memory usage percentage')
        self.system_disk_usage = Gauge('cybersec_system_disk_usage_percent', 'System disk usage percentage')
        self.system_disk_free_gb = Gauge('cybersec_system_disk_free_gb', 'Free disk space in GB')
        self.process_count = Gauge('cybersec_process_count', 'Number of backend processes running')
        
        # Data File Metrics (Enhanced)
        self.data_file_size = Gauge('cybersec_data_file_size_kb', 'Data file size in KB', ['filename'])
        self.data_file_age_hours = Gauge('cybersec_data_file_age_hours', 'Data file age in hours', ['filename'])
        self.backup_files_count = Gauge('cybersec_backup_files_count', 'Number of backup files')
        self.data_freshness_score = Gauge('cybersec_data_freshness_score', 'Data freshness score (0-100)')
        
        # Service Health & Performance
        self.service_uptime_seconds = Gauge('cybersec_service_uptime_seconds', 'Service uptime in seconds')
        self.service_restarts_total = Counter('cybersec_service_restarts_total', 'Total service restarts')
        self.monitoring_cycles_total = Counter('cybersec_monitoring_cycles_total', 'Total monitoring cycles completed')
        self.health_check_failures = Counter('cybersec_health_check_failures', 'Health check failures', ['component'])
        
        # Processing Performance
        self.scraping_duration = Histogram('cybersec_scraping_duration_seconds', 'Time taken for scraping cycle')
        self.ai_processing_duration = Histogram('cybersec_ai_processing_duration_seconds', 'Time taken for AI processing')
        self.monitoring_duration = Histogram('cybersec_monitoring_duration_seconds', 'Time taken for monitoring cycle')
        
        # Real-time Status Indicators
        self.last_scrape_success = Gauge('cybersec_last_scrape_success', 'Last scrape success timestamp')
        self.last_ai_processing = Gauge('cybersec_last_ai_processing', 'Last AI processing timestamp')
        self.last_monitoring_cycle = Gauge('cybersec_last_monitoring_cycle', 'Last monitoring cycle timestamp')
        
        # Info metrics
        self.info = Info('cybersec_backend_info', 'Backend information')
        self.info.info({
            'version': '4.0',
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'start_time': datetime.now().isoformat(),
            'features': 'smart_filtering,progress_indicators,real_time_monitoring'
        })
    
    def collect_api_metrics(self):
        """Collect API health and traffic metrics for dashboard"""
        try:
            start_time = time.time()
            response = requests.get(f'{self.backend_url}/health', timeout=5)
            response_time = time.time() - start_time
            
            # Update API health
            self.api_health.set(1 if response.status_code == 200 else 0)
            self.api_response_time.observe(response_time)
            
            # Record API request
            self.api_requests.append({
                'timestamp': time.time(),
                'method': 'GET',
                'endpoint': '/health',
                'status': response.status_code
            })
            
            # Calculate API traffic per minute
            now = time.time()
            recent_requests = [req for req in self.api_requests if now - req['timestamp'] <= 60]
            self.api_traffic_per_minute.set(len(recent_requests))
            
            # Try to get additional API stats
            try:
                endpoints = ['/api/articles', '/api/status', '/api/health']
                for endpoint in endpoints:
                    try:
                        resp = requests.get(f'{self.backend_url}{endpoint}', timeout=3)
                        self.api_requests_total.labels(
                            method='GET', 
                            endpoint=endpoint, 
                            status=resp.status_code
                        ).inc()
                    except:
                        pass
            except:
                pass
                
        except Exception as e:
            logger.error(f"Failed to collect API metrics: {e}")
            self.api_health.set(0)
            self.health_check_failures.labels(component='api').inc()
    
    def collect_enhanced_data_metrics(self):
        """Collect comprehensive data metrics for dashboard panels"""
        try:
            current_articles = 0
            today_articles = 0
            summarized_today = 0
            
            # Current Articles (from live file)
            live_file = self.data_dir / 'cybersecurity_news_live.json'
            if live_file.exists():
                try:
                    with open(live_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            current_articles = len(data)
                            self.articles_current.set(current_articles)
                            
                    # File metrics
                    stat = live_file.stat()
                    self.data_file_size.labels(filename='cybersecurity_news_live.json').set(stat.st_size / 1024)
                    self.data_file_age_hours.labels(filename='cybersecurity_news_live.json').set(
                        (time.time() - stat.st_mtime) / 3600
                    )
                except Exception as e:
                    logger.debug(f"Error reading live file: {e}")
            
            # Today's Articles (from daily file)
            today = datetime.now().strftime('%Y%m%d')
            daily_file = self.data_dir / f'News_today_{today}.json'
            if daily_file.exists():
                try:
                    with open(daily_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            today_articles = len(data)
                            self.articles_today.set(today_articles)
                            
                    # File metrics
                    stat = daily_file.stat()
                    self.data_file_size.labels(filename=f'News_today_{today}.json').set(stat.st_size / 1024)
                except Exception as e:
                    logger.debug(f"Error reading daily file: {e}")
            
            # Summarized Articles
            summary_file = self.data_dir / 'summarized_news_hf.json'
            if summary_file.exists():
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            # Count today's summaries
                            today_str = datetime.now().strftime('%Y-%m-%d')
                            summarized_today = sum(1 for article in data 
                                                 if article.get('publishedAt', '').startswith(today_str))
                            self.articles_summarized_today.set(summarized_today)
                            
                    # File metrics
                    stat = summary_file.stat()
                    self.data_file_size.labels(filename='summarized_news_hf.json').set(stat.st_size / 1024)
                except Exception as e:
                    logger.debug(f"Error reading summary file: {e}")
            
            # Backup Files Count
            backup_dir = self.data_dir / 'backup'
            if backup_dir.exists():
                backup_count = len(list(backup_dir.glob('*.json')))
                self.backup_files_count.set(backup_count)
            
            # Data freshness score
            if live_file.exists():
                age_hours = (time.time() - live_file.stat().st_mtime) / 3600
                freshness = max(0, 100 - (age_hours * 10))  # Decrease by 10 points per hour
                self.data_freshness_score.set(freshness)
                
        except Exception as e:
            logger.error(f"Failed to collect data metrics: {e}")
    
    def collect_log_activity_metrics(self):
        """Collect real-time log activity metrics for dashboard"""
        try:
            now = time.time()
            five_minutes_ago = now - 300
            one_minute_ago = now - 60
            
            # Initialize counters
            recent_errors = 0
            recent_warnings = 0
            log_levels = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
            
            # Parse all log files
            log_files = [
                'backend.log', 'fastapi.log', 'main_launcher.log', 
                'api.log', 'automation.log', 'error.log'
            ]
            
            for log_file in log_files:
                log_path = self.logs_dir / log_file
                if log_path.exists():
                    try:
                        # Get file position from cache
                        file_key = str(log_path)
                        last_position = self.last_log_positions.get(file_key, 0)
                        
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            new_position = f.tell()
                            
                        # Update position cache
                        self.last_log_positions[file_key] = new_position
                        
                        # Parse new lines
                        for line in new_lines:
                            log_entry = self.parse_log_line(line)
                            if log_entry:
                                self.recent_logs.append(log_entry)
                                
                                # Count by time and level
                                if log_entry['timestamp'] >= five_minutes_ago:
                                    if log_entry['level'] == 'ERROR':
                                        recent_errors += 1
                                    elif log_entry['level'] == 'WARNING':
                                        recent_warnings += 1
                                
                                if log_entry['timestamp'] >= one_minute_ago:
                                    level = log_entry['level']
                                    if level in log_levels:
                                        log_levels[level] += 1
                    except Exception as e:
                        logger.debug(f"Error parsing {log_file}: {e}")
            
            # Update metrics
            self.recent_errors_count.set(recent_errors)
            self.recent_warnings_count.set(recent_warnings)
            self.log_activity_info.set(log_levels['INFO'])
            self.log_activity_warning.set(log_levels['WARNING'])
            self.log_activity_error.set(log_levels['ERROR'])
            self.log_activity_debug.set(log_levels['DEBUG'])
            
            # Critical issues (errors in last 5 minutes)
            self.critical_issues.set(recent_errors)
            
        except Exception as e:
            logger.error(f"Failed to collect log metrics: {e}")
    
    def parse_log_line(self, line):
        """Parse a log line and extract timestamp, level, and message"""
        try:
            # Common log formats
            patterns = [
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+ - .+ - (\w+) - (.+)',  # Python logging
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)',  # Simple format
                r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)',  # Bracketed format
            ]
            
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    timestamp_str, level, message = match.groups()
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                    return {
                        'timestamp': timestamp,
                        'level': level.upper(),
                        'message': message.strip(),
                        'raw_line': line.strip()
                    }
            
            # If no pattern matches, treat as INFO level with current timestamp
            return {
                'timestamp': time.time(),
                'level': 'INFO',
                'message': line.strip(),
                'raw_line': line.strip()
            }
            
        except Exception:
            return None
    
    def collect_data_metrics(self):
        """Collect data file and processing metrics"""
        try:
            # Check main data files
            critical_files = [
                'cybersecurity_news_live.json',
                'summarized_news_hf.json'
            ]
            
            for filename in critical_files:
                file_path = self.data_dir / filename
                if file_path.exists():
                    stat = file_path.stat()
                    size_kb = stat.st_size / 1024
                    age_hours = (time.time() - stat.st_mtime) / 3600
                    
                    self.data_file_size.labels(filename=filename).set(size_kb)
                    self.data_file_age_hours.labels(filename=filename).set(age_hours)
                    
                    # Count articles if JSON
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                if filename == 'cybersecurity_news_live.json':
                                    self.articles_current.set(len(data))
                                elif filename == 'summarized_news_hf.json':
                                    self.articles_processed_total._value._value = len(data)
                    except:
                        pass
            
            # Count backup files
            backup_dir = self.data_dir / 'backup'
            if backup_dir.exists():
                backup_count = len(list(backup_dir.glob('*.json')))
                self.backup_files_count.set(backup_count)
                
            # Check today's daily file
            today = datetime.now().strftime('%Y%m%d')
            daily_file = self.data_dir / f'News_today_{today}.json'
            if daily_file.exists():
                try:
                    with open(daily_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.articles_daily.set(len(data))
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to collect data metrics: {e}")
    
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_disk_usage.set(disk.percent)
            self.system_disk_free_gb.set(disk.free / (1024**3))
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def collect_log_metrics(self):
        """Collect metrics from log files"""
        try:
            # Parse logs for errors and events
            log_files = [
                'backend.log',
                'fastapi.log',
                'main_launcher.log'
            ]
            
            for log_file in log_files:
                log_path = self.logs_dir / log_file
                if log_path.exists():
                    # Count recent errors (simplified example)
                    try:
                        with open(log_path, 'r') as f:
                            lines = f.readlines()
                            # Look at last 100 lines for recent errors
                            recent_lines = lines[-100:] if len(lines) > 100 else lines
                            error_count = sum(1 for line in recent_lines if 'ERROR' in line.upper())
                            
                            if error_count > 0:
                                self.errors_total.labels(component=log_file.replace('.log', '')).inc(error_count)
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.error(f"Failed to collect log metrics: {e}")
    
    def collect_all_metrics(self):
        """Collect all metrics"""
        logger.info("Collecting metrics...")
        
        self.collect_api_metrics()
        self.collect_data_metrics()
        self.collect_system_metrics()
        self.collect_log_metrics()
        
        # Increment monitoring cycles
        self.monitoring_cycles_total.inc()
        
        logger.info("Metrics collection completed")
    
    def run_metrics_collection(self):
        """Run continuous metrics collection"""
        logger.info("Starting metrics collection loop...")
        
        while self.running:
            try:
                self.collect_all_metrics()
                time.sleep(15)  # Collect every 15 seconds
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(30)  # Wait longer on error
    
    def start(self, port=9200):
        """Start the metrics server"""
        logger.info(f"Starting metrics exporter on port {port}")
        
        # Start Prometheus metrics server
        start_http_server(port)
        
        # Start metrics collection in background thread
        collection_thread = threading.Thread(target=self.run_metrics_collection)
        collection_thread.daemon = True
        collection_thread.start()
        
        logger.info("Metrics exporter started successfully")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping metrics exporter...")
            self.running = False

def main():
    """Main function"""
    exporter = EnhancedCybersecurityMetricsExporter()
    exporter.start()

if __name__ == "__main__":
    main()
