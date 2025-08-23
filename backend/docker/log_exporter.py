#!/usr/bin/env python3
"""
Real-time Log Exporter for Cybersecurity Backend
Exposes log metrics to Prometheus for Grafana visualization
"""

import time
import json
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Info
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
log_lines_total = Counter('cybersec_log_lines_total', 'Total log lines processed', ['level', 'component'])
log_errors_total = Counter('cybersec_log_errors_total', 'Total errors in logs', ['component'])
log_warnings_total = Counter('cybersec_log_warnings_total', 'Total warnings in logs', ['component'])
api_requests_from_logs = Counter('cybersec_api_requests_from_logs_total', 'API requests detected in logs', ['endpoint', 'method'])
active_sessions = Gauge('cybersec_active_sessions', 'Current active sessions/connections')
log_file_size = Gauge('cybersec_log_file_size_bytes', 'Log file sizes', ['filename'])
log_last_update = Gauge('cybersec_log_last_update_timestamp', 'Last update timestamp for log files', ['filename'])

# Recent logs queue for real-time display
recent_logs = deque(maxlen=100)
log_stats = defaultdict(lambda: {'info': 0, 'warning': 0, 'error': 0, 'debug': 0})

class LogTailer:
    def __init__(self, log_dir="logs"):
        self.log_dir = Path(log_dir)
        self.file_positions = {}
        self.running = True
        
        # Log file patterns to monitor
        self.log_files = [
            'api.log', 'fastapi.log', 'backend.log', 'error.log',
            'access.log', 'automation.log', 'health_monitor.log'
        ]
        
        # Regex patterns for parsing
        self.log_pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (\w+) - (.+)'
        )
        self.api_pattern = re.compile(
            r'(GET|POST|PUT|DELETE)\s+(/[^\s]*)\s+.*?(\d{3})'
        )
        
    def get_file_stats(self, filepath):
        """Get file size and modification time"""
        try:
            stat = filepath.stat()
            return stat.st_size, stat.st_mtime
        except FileNotFoundError:
            return 0, 0
    
    def tail_file(self, filepath):
        """Tail a single log file and yield new lines"""
        try:
            # Get current position
            current_pos = self.file_positions.get(str(filepath), 0)
            
            if not filepath.exists():
                return
                
            file_size, mtime = self.get_file_stats(filepath)
            
            # Update metrics
            log_file_size.labels(filename=filepath.name).set(file_size)
            log_last_update.labels(filename=filepath.name).set(mtime)
            
            # If file was truncated, reset position
            if file_size < current_pos:
                current_pos = 0
                
            # Read new content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(current_pos)
                new_lines = f.readlines()
                self.file_positions[str(filepath)] = f.tell()
                
            return new_lines
            
        except Exception as e:
            logger.error(f"Error tailing {filepath}: {e}")
            return []
    
    def parse_log_line(self, line, filename):
        """Parse a log line and extract metrics"""
        try:
            # Match standard log format
            match = self.log_pattern.match(line.strip())
            if match:
                timestamp_str, component, level, message = match.groups()
                
                # Update counters
                log_lines_total.labels(level=level.lower(), component=component).inc()
                
                if level.upper() == 'ERROR':
                    log_errors_total.labels(component=component).inc()
                elif level.upper() == 'WARNING':
                    log_warnings_total.labels(component=component).inc()
                
                # Check for API requests
                api_match = self.api_pattern.search(message)
                if api_match:
                    method, endpoint, status_code = api_match.groups()
                    api_requests_from_logs.labels(endpoint=endpoint, method=method).inc()
                
                # Add to recent logs
                recent_logs.append({
                    'timestamp': timestamp_str,
                    'component': component,
                    'level': level,
                    'message': message[:200],  # Truncate long messages
                    'filename': filename
                })
                
                # Update stats
                log_stats[component][level.lower()] += 1
                
        except Exception as e:
            logger.error(f"Error parsing log line: {e}")
    
    def monitor_logs(self):
        """Main monitoring loop"""
        logger.info("Starting log monitoring...")
        
        while self.running:
            try:
                for log_file in self.log_files:
                    filepath = self.log_dir / log_file
                    new_lines = self.tail_file(filepath)
                    
                    if new_lines:
                        for line in new_lines:
                            if line.strip():
                                self.parse_log_line(line, log_file)
                
                # Update active sessions (estimate from recent activity)
                recent_activity = len([log for log in recent_logs 
                                     if 'api' in log.get('filename', '').lower()])
                active_sessions.set(min(recent_activity, 50))  # Cap at 50
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False

def main():
    """Main function"""
    logger.info("🔍 Starting Cybersecurity Log Exporter")
    
    # Change to the backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Start Prometheus HTTP server
    start_http_server(9201)  # Different port from backend exporter
    logger.info("📊 Prometheus metrics server started on port 9201")
    
    # Start log monitoring
    log_tailer = LogTailer()
    
    try:
        log_tailer.monitor_logs()
    except KeyboardInterrupt:
        logger.info("Shutting down log exporter...")
        log_tailer.stop()

if __name__ == "__main__":
    main()
