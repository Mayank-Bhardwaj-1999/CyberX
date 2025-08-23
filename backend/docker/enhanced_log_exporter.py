#!/usr/bin/env python3
"""
📊 Enhanced Log Exporter for Grafana Dashboard
Provides real-time log metrics including Docker monitoring and terminal output
"""

import time
import json
import re
import threading
import subprocess
import docker
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
from pathlib import Path
from datetime import datetime, timedelta
import logging
import os
from collections import deque, defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedLogExporter:
    def __init__(self):
        self.logs_dir = Path('/app/logs')
        self.data_dir = Path('/app/data')
        
        # Cache for tracking log files
        self.log_positions = {}
        self.recent_logs = deque(maxlen=2000)
        self.api_requests = deque(maxlen=1000)
        
        # Docker client setup
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Could not connect to Docker: {e}")
            self.docker_client = None
        
        # Setup metrics
        self.setup_metrics()
        
        self.running = True
        self.start_time = time.time()
        
    def setup_metrics(self):
        """Setup Prometheus metrics for missing dashboard panels"""
        
        # Log Activity by Level (for "Live Log Activity (by Level)" panel)
        self.log_level_info = Gauge('cybersec_log_level_info_count', 'INFO level logs in last minute')
        self.log_level_warning = Gauge('cybersec_log_level_warning_count', 'WARNING level logs in last minute')
        self.log_level_error = Gauge('cybersec_log_level_error_count', 'ERROR level logs in last minute')
        self.log_level_debug = Gauge('cybersec_log_level_debug_count', 'DEBUG level logs in last minute')
        
        # API Traffic from Logs (for "API Traffic from Logs" panel)
        self.api_requests_per_minute = Gauge('cybersec_api_requests_per_minute', 'API requests per minute from logs')
        self.api_response_time_avg = Gauge('cybersec_api_response_time_avg', 'Average API response time')
        self.api_success_rate = Gauge('cybersec_api_success_rate', 'API success rate percentage')
        
        # Articles metrics (for "Today's Articles" panel)
        self.articles_scraped_today = Gauge('cybersec_articles_scraped_today_count', 'Articles scraped today')
        self.articles_processed_today = Gauge('cybersec_articles_processed_today_count', 'Articles processed today')
        self.articles_summarized_today = Gauge('cybersec_articles_summarized_today_count', 'Articles summarized today')
        
        # Error tracking (for "Recent Errors (5min)" panel)
        self.recent_errors_5min = Gauge('cybersec_recent_errors_5min', 'Error count in last 5 minutes')
        self.ai_summarization_errors = Gauge('cybersec_ai_summarization_errors', 'AI summarization errors')
        self.scraping_errors = Gauge('cybersec_scraping_errors', 'Web scraping errors')
        self.monitoring_failures = Gauge('cybersec_monitoring_failures', 'Monitoring system failures')
        self.connection_errors = Gauge('cybersec_connection_errors', 'Network connection errors')
        
        # Service Activity Status (for "Service Activity Status" panel)
        self.scraping_active = Gauge('cybersec_scraping_active', 'Scraping service activity status')
        self.ai_processing_active = Gauge('cybersec_ai_processing_active', 'AI processing service activity status')
        self.monitoring_active = Gauge('cybersec_monitoring_active', 'Monitoring service activity status')
        
        # Terminal Activity (for "Live Terminal Output" panel)
        self.terminal_activity_lines = Gauge('cybersec_terminal_activity_lines', 'Number of terminal activity lines')
        self.last_terminal_update = Gauge('cybersec_last_terminal_update', 'Last terminal update timestamp')
        
        # Docker monitoring metrics
        self.docker_containers_running = Gauge('cybersec_docker_containers_running', 'Number of running Docker containers')
        self.docker_containers_total = Gauge('cybersec_docker_containers_total', 'Total number of Docker containers')
        self.docker_images_total = Gauge('cybersec_docker_images_total', 'Total number of Docker images')
        self.docker_system_load = Gauge('cybersec_docker_system_load', 'Docker system load estimate')
        self.docker_memory_usage = Gauge('cybersec_docker_memory_usage', 'Docker memory usage estimate')
        
        # Container health status
        self.cybersec_api_container_status = Gauge('cybersec_api_container_health', 'Cybersecurity API container health')
        self.grafana_container_status = Gauge('cybersec_grafana_container_health', 'Grafana container health')
        self.prometheus_container_status = Gauge('cybersec_prometheus_container_health', 'Prometheus container health')
        
        # Terminal output metrics
        self.terminal_output = Gauge('cybersec_terminal_output_lines', 'Real-time terminal output line count')
        
    def process_log_files(self):
        """Process log files and extract entries"""
        if not self.logs_dir.exists():
            return
            
        for log_file in self.logs_dir.glob('*.log'):
            try:
                self.process_single_log_file(log_file)
            except Exception as e:
                logger.error(f"Error processing {log_file}: {e}")
    
    def process_single_log_file(self, log_file):
        """Process a single log file for new entries"""
        file_path = str(log_file)
        current_size = log_file.stat().st_size
        
        # Track file position to read only new content
        last_position = self.log_positions.get(file_path, 0)
        
        if current_size < last_position:
            # File was rotated or truncated
            last_position = 0
        
        if current_size == last_position:
            return  # No new content
        
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_content = f.read()
                
                for line in new_content.split('\n'):
                    if line.strip():
                        self.parse_log_line(line, log_file.name)
                
                self.log_positions[file_path] = f.tell()
                
        except Exception as e:
            logger.error(f"Error reading {log_file}: {e}")
    
    def parse_log_line(self, line, filename):
        """Parse a single log line and extract structured information"""
        # Enhanced regex to match actual log format: 2025-08-19 16:39:57,804 - cyberx_fastapi - INFO - message
        patterns = [
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)',  # Main format
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (\w+) - (.+)',        # Alternative
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+): (.+)',               # Bracket format
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)',                    # Simple format
        ]
        
        entry = None
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    try:
                        timestamp_str = groups[0]
                        # Parse timestamp - handle both formats
                        try:
                            if ',' in timestamp_str:
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f').timestamp()
                            else:
                                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                        except:
                            timestamp = time.time()
                        
                        if len(groups) == 4:
                            # Format: timestamp - service - level - message
                            level = groups[2].upper()
                            message = groups[3]
                        else:
                            # Format: timestamp level message
                            level = groups[1].upper()
                            message = groups[2]
                        
                        entry = {
                            'timestamp': timestamp,
                            'filename': filename,
                            'level': level,
                            'message': message,
                            'raw_line': line
                        }
                        break
                    except Exception as e:
                        logger.debug(f"Error parsing timestamp from {line}: {e}")
                        continue
        
        if not entry:
            # Fallback for unmatched lines
            entry = {
                'timestamp': time.time(),
                'filename': filename,
                'level': 'INFO',
                'message': line,
                'raw_line': line
            }
        
        self.recent_logs.append(entry)
        
        # Track API requests
        if 'request' in entry['message'].lower() or 'api' in entry['message'].lower():
            self.api_requests.append(entry)
    
    def collect_log_activity_metrics(self):
        """Collect log activity metrics by level"""
        now = time.time()
        one_minute_ago = now - 60
        
        level_counts = {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0}
        
        for entry in self.recent_logs:
            if entry['timestamp'] >= one_minute_ago:
                level = entry['level']
                if level in level_counts:
                    level_counts[level] += 1
        
        self.log_level_info.set(level_counts['INFO'])
        self.log_level_warning.set(level_counts['WARNING'])
        self.log_level_error.set(level_counts['ERROR'])
        self.log_level_debug.set(level_counts['DEBUG'])
        
        # Recent errors (5 minutes)
        five_minutes_ago = now - 300
        error_count = sum(1 for entry in self.recent_logs 
                         if entry['timestamp'] >= five_minutes_ago and entry['level'] == 'ERROR')
        self.recent_errors_5min.set(error_count)
    
    def collect_api_traffic_metrics(self):
        """Collect API traffic metrics from logs"""
        now = time.time()
        one_minute_ago = now - 60
        
        recent_api_requests = [
            req for req in self.api_requests 
            if req['timestamp'] >= one_minute_ago
        ]
        
        self.api_requests_per_minute.set(len(recent_api_requests))
        
        # Simple success rate calculation
        if recent_api_requests:
            successful = sum(1 for req in recent_api_requests 
                           if 'error' not in req['message'].lower() and 'failed' not in req['message'].lower())
            success_rate = (successful / len(recent_api_requests)) * 100
            self.api_success_rate.set(success_rate)
        else:
            self.api_success_rate.set(100)  # Default to 100% when no recent requests
        
        # Mock response time (in real implementation, parse from logs)
        self.api_response_time_avg.set(150)  # milliseconds
    
    def count_articles_from_urls_today(self):
        """Count articles scraped and summarized today from URL tracking files"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        articles_scraped_today = 0
        articles_summarized_today = 0
        
        # Count scraped URLs today from url_scraped.txt
        url_scraped_file = self.data_dir / 'url_scraped.txt'
        if url_scraped_file.exists():
            try:
                with open(url_scraped_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '|' in line and today in line:
                            articles_scraped_today += 1
            except Exception as e:
                logger.error(f"Error reading url_scraped.txt: {e}")
        
        # Count summarized URLs today from url_final_summarized.txt
        url_summarized_file = self.data_dir / 'url_final_summarized.txt'
        if url_summarized_file.exists():
            try:
                with open(url_summarized_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '|' in line and today in line:
                            articles_summarized_today += 1
            except Exception as e:
                logger.error(f"Error reading url_final_summarized.txt: {e}")
        
        return articles_scraped_today, articles_summarized_today

    def analyze_processing_errors(self):
        """Analyze logs for AI summarization and scraping errors"""
        error_counts = {
            'ai_summarization_errors': 0,
            'scraping_errors': 0,
            'monitoring_failures': 0,
            'connection_errors': 0
        }
        
        # Patterns to detect different types of errors
        error_patterns = {
            'ai_summarization_errors': [
                'ai summarization failed',
                'gemini api error',
                'summarization error',
                'failed to summarize',
                'ai processing failed',
                'ai model error'
            ],
            'scraping_errors': [
                'failed to scrape',
                'crawl4ai error',
                'scraping failed',
                'unable to fetch',
                'request failed',
                'scraping error'
            ],
            'monitoring_failures': [
                'monitoring error',
                'health check failed',
                'service unavailable',
                'monitoring failed',
                'heartbeat failed'
            ],
            'connection_errors': [
                'connection refused',
                'timeout',
                'connectionerror',
                'network error',
                'unable to connect'
            ]
        }
        
        # Check recent log entries for errors
        now = time.time()
        five_minutes_ago = now - 300
        
        for entry in self.recent_logs:
            if entry['timestamp'] >= five_minutes_ago:
                message_lower = entry['message'].lower()
                
                # Check each error pattern category
                for error_type, patterns in error_patterns.items():
                    for pattern in patterns:
                        if pattern in message_lower:
                            error_counts[error_type] += 1
                            break
        
        # Update metrics
        self.ai_summarization_errors.set(error_counts['ai_summarization_errors'])
        self.scraping_errors.set(error_counts['scraping_errors'])
        self.monitoring_failures.set(error_counts['monitoring_failures'])
        self.connection_errors.set(error_counts['connection_errors'])
        
        return error_counts

    def collect_activity_status(self):
        """Collect real-time activity status"""
        now = time.time()
        five_minutes_ago = now - 300
        
        scraping_active = False
        ai_active = False
        monitoring_active = False
        
        # Check recent log entries for activity
        for entry in list(self.recent_logs)[-100:]:  # Last 100 entries
            if entry['timestamp'] >= five_minutes_ago:
                message_lower = entry['message'].lower()
                
                if any(keyword in message_lower for keyword in 
                       ['scraping', 'processing website', 'crawling']):
                    scraping_active = True
                
                if any(keyword in message_lower for keyword in 
                       ['ai processing', 'summarizing', 'gemini']):
                    ai_active = True
                
                if any(keyword in message_lower for keyword in 
                       ['monitoring cycle', 'cycle completed']):
                    monitoring_active = True
        
        self.scraping_active.set(1 if scraping_active else 0)
        self.ai_processing_active.set(1 if ai_active else 0)
        self.monitoring_active.set(1 if monitoring_active else 0)

    def collect_articles_metrics(self):
        """Collect article processing metrics"""
        try:
            scraped_today, summarized_today = self.count_articles_from_urls_today()
            
            self.articles_scraped_today.set(scraped_today)
            self.articles_summarized_today.set(summarized_today)
            self.articles_processed_today.set(scraped_today)  # Same as scraped for now
            
            logger.debug(f"Articles metrics - Scraped: {scraped_today}, Summarized: {summarized_today}")
            
        except Exception as e:
            logger.error(f"Error in collect_articles_metrics: {e}", exc_info=True)
    
    def collect_docker_metrics(self):
        """Collect Docker container and system metrics"""
        try:
            if not self.docker_client:
                return
            
            # Get container information
            containers = self.docker_client.containers.list(all=True)
            running_containers = [c for c in containers if c.status == 'running']
            
            # Update container metrics
            self.docker_containers_running.set(len(running_containers))
            self.docker_containers_total.set(len(containers))
            
            # Get images count
            images = self.docker_client.images.list()
            self.docker_images_total.set(len(images))
            
            # Check specific container health
            container_health = {
                'cybersec_api_container_health': 0,
                'cybersec_grafana_container_health': 0,
                'cybersec_prometheus_container_health': 0
            }
            
            for container in running_containers:
                name = container.name.lower()
                if 'fastapi' in name or 'cybersecurity-api' in name:
                    self.cybersec_api_container_status.set(1)
                    container_health['cybersec_api_container_health'] = 1
                elif 'grafana' in name:
                    self.grafana_container_status.set(1)
                    container_health['cybersec_grafana_container_health'] = 1
                elif 'prometheus' in name:
                    self.prometheus_container_status.set(1)
                    container_health['cybersec_prometheus_container_health'] = 1
            
            # Update any containers not found as unhealthy
            if container_health['cybersec_api_container_health'] == 0:
                self.cybersec_api_container_status.set(0)
            if container_health['cybersec_grafana_container_health'] == 0:
                self.grafana_container_status.set(0)
            if container_health['cybersec_prometheus_container_health'] == 0:
                self.prometheus_container_status.set(0)
            
            # Get system stats (basic)
            try:
                stats_output = subprocess.run(['docker', 'system', 'df'], 
                                            capture_output=True, text=True, timeout=10)
                if stats_output.returncode == 0:
                    # Basic system load estimation
                    self.docker_system_load.set(len(running_containers) * 5)  # Simple estimation
                    self.docker_memory_usage.set(len(running_containers) * 10)  # Simple estimation
            except Exception as e:
                logger.debug(f"Could not get Docker system stats: {e}")
                
        except Exception as e:
            logger.error(f"Error collecting Docker metrics: {e}")
    
    def get_real_time_terminal_output(self):
        """Get real-time terminal output and process information"""
        try:
            terminal_lines = []
            
            # Get current processes
            try:
                ps_output = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=5)
                if ps_output.returncode == 0:
                    lines = ps_output.stdout.split('\n')[:10]  # Last 10 processes
                    terminal_lines.extend([f"PROC: {line}" for line in lines if line.strip()])
            except:
                pass
            
            # Get Docker container status
            try:
                docker_output = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                                             capture_output=True, text=True, timeout=5)
                if docker_output.returncode == 0:
                    lines = docker_output.stdout.split('\n')[:5]
                    terminal_lines.extend([f"DOCKER: {line}" for line in lines if line.strip()])
            except:
                pass
            
            # Get recent log tails
            try:
                log_files = ['fastapi.log', 'backend.log', 'main_launcher.log']
                for log_file in log_files:
                    log_path = self.logs_dir / log_file
                    if log_path.exists():
                        tail_output = subprocess.run(['tail', '-2', str(log_path)], 
                                                   capture_output=True, text=True, timeout=3)
                        if tail_output.returncode == 0:
                            lines = tail_output.stdout.split('\n')
                            terminal_lines.extend([f"LOG({log_file}): {line}" for line in lines if line.strip()])
            except:
                pass
            
            # Update metrics
            self.terminal_output.set(len(terminal_lines))
            self.terminal_activity_lines.set(len(terminal_lines))
            self.last_terminal_update.set(time.time())
            
            return terminal_lines
            
        except Exception as e:
            logger.error(f"Error getting terminal output: {e}")
            return []

    def run(self):
        """Main loop to collect all metrics"""
        logger.info("Enhanced Log Exporter started")
        
        while True:
            try:
                # Process log files
                self.process_log_files()
                
                # Collect all metrics
                self.collect_log_activity_metrics()
                self.collect_api_traffic_metrics()
                self.collect_articles_metrics()
                self.collect_docker_metrics()
                self.get_real_time_terminal_output()
                self.analyze_processing_errors()
                self.collect_activity_status()
                
                # Sleep for 30 seconds
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Shutting down Enhanced Log Exporter")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    exporter = EnhancedLogExporter()
    
    # Start HTTP server for metrics
    import threading
    from prometheus_client import start_http_server
    
    start_http_server(9201)
    logger.info("Enhanced Log Exporter HTTP server started on port 9201")
    
    # Start metrics collection
    exporter.run()
