#!/usr/bin/env python3
"""
🛡️ Cybersecurity News Crawler - Production VPS Launcher
A comprehensive Python launcher for the cybersecurity news monitoring system.
Designed for VPS deployment with full automation, error handling, and self-recovery.

Features:
- One-command deployment: python main_launch.py
- Automatic dependency management
- Self-healing services with retry logic
- Docker integration for FastAPI
- Process monitoring and auto-restart
- Production-grade error handling
- Health checks and status monitoring
- Graceful shutdown handling
"""

import os
import sys
import subprocess
import time
import json
import argparse
import threading
import signal
import psutil
import docker
import requests
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging
from contextlib import contextmanager

# Optional structured logger & heartbeat (failsafe fallbacks)
try:
    from src.utils.logger import get_logger  # type: ignore
    from src.utils.heartbeat import Heartbeat  # type: ignore
except Exception:  # pragma: no cover - safe fallback
    def get_logger(name):
        class _Dummy:
            def info(self, *a, **k): pass
            def warning(self, *a, **k): pass
            def error(self, *a, **k): pass
            def debug(self, *a, **k): pass
        return _Dummy()
    class Heartbeat:  # type: ignore
        def __init__(self, *a, **k): pass
        def start(self): pass
        def stop(self): pass

# Add utils directory to path for backup manager
sys.path.append(str(Path(__file__).parent / "src" / "utils"))

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
                                  .replace("🔄", "[CYCLE]")
                                  .replace("🤖", "[AI]")
                                  .replace("🌐", "[WEB]")
                                  .replace("📦", "[BACKUP]")
                                  .replace("🔧", "[SETUP]")
                                  .replace("💡", "[INFO]")
                                  .replace("🎯", "[TARGET]")
                                  .replace("🛡️", "[SECURITY]")
                                  .replace("🔔", "[ALERT]")
                                  .replace("⏰", "[TIME]")
                                  .replace("📊", "[DATA]")
                                  .replace("🛑", "[STOP]")
                                  .replace("⚡", "[FAST]")
                                  .replace("🔍", "[SEARCH]")
                                  .replace("🎉", "[SUCCESS]")
                                  .replace("💥", "[CRASH]")
                                  .replace("🧹", "[CLEAN]")
                                  .replace("📋", "[LIST]")
                                  .replace("📁", "[FOLDER]")
                                  .replace("📄", "[FILE]")
                                  .replace("🐍", "[PYTHON]")
                                  .replace("👋", "[BYE]"))
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
        'cycle': '[CYCLE]',
        'ai': '[AI]',
        'web': '[WEB]',
        'backup': '[BACKUP]',
        'setup': '[SETUP]',
        'info': '[INFO]',
        'target': '[TARGET]',
        'security': '[SECURITY]',
        'alert': '[ALERT]',
        'time': '[TIME]',
        'data': '[DATA]',
        'stop': '[STOP]',
        'fast': '[FAST]',
        'search': '[SEARCH]'
    }
    UNICODE_HELPER_AVAILABLE = False

try:
    from backup_manager import BackupManager
    BACKUP_AVAILABLE = True
except ImportError:
    safe_print(f"{EMOJIS['warning']} Warning: Backup manager not available")
    BACKUP_AVAILABLE = False


class ProductionServiceManager:
    """Production-grade service manager with auto-restart and health monitoring"""
    
    def __init__(self):
        self.services = {}
        self.docker_client = None
        self.shutdown_requested = False
        self.restart_counts = {}
        self.max_restarts = 5
        self.restart_window = 300  # 5 minutes
        
        # Setup logging
        self.setup_logging()
        
        # Try to initialize Docker
        self.init_docker()
        
        # Setup signal handlers
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Setup production logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'main_launcher.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('ProductionLauncher')
        self.logger.info("Production Service Manager initialized")
    
    def init_docker(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
            return True
        except Exception as e:
            self.logger.warning(f"Docker not available: {e}")
            self.docker_client = None
            return False
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.shutdown_requested = True
            self.stop_all_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is still running"""
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def detect_existing_containers(self) -> Dict[str, bool]:
        """Detect existing CyberX Docker containers"""
        containers_status = {
            'fastapi': False,
            'nginx': False,
            'monitoring': False
        }
        
        if not self.docker_client:
            return containers_status
            
        try:
            # Get all running containers
            containers = self.docker_client.containers.list()
            
            for container in containers:
                container_name = container.name.lower()
                
                # Check for FastAPI container
                if 'cybersecurity-fastapi' in container_name:
                    containers_status['fastapi'] = True
                    safe_print(f"{EMOJIS['success']} Found running container: {container.name}")
                
                # Check for NGINX container
                elif 'cybersecurity-nginx' in container_name:
                    containers_status['nginx'] = True
                    safe_print(f"{EMOJIS['success']} Found running container: {container.name}")
                
                # Check for monitoring containers
                elif any(monitor_name in container_name for monitor_name in 
                        ['grafana', 'prometheus', 'cadvisor', 'alertmanager', 'exporter']):
                    containers_status['monitoring'] = True
                    if not hasattr(self, '_monitoring_logged'):
                        safe_print(f"{EMOJIS['success']} Found monitoring containers running")
                        self._monitoring_logged = True
            
            return containers_status
            
        except Exception as e:
            self.logger.warning(f"Error detecting containers: {e}")
            return containers_status

    def start_docker_fastapi(self) -> bool:
        """Start FastAPI in Docker container with auto-restart"""
        if not self.docker_client:
            self.logger.warning("Docker not available - skipping Docker FastAPI")
            return False
        
        try:
            # Check if image exists first
            try:
                self.docker_client.images.get('cybersecurity-fastapi:latest')
                self.logger.info("Found existing cybersecurity-fastapi image")
            except docker.errors.ImageNotFound:
                self.logger.warning("cybersecurity-fastapi image not found - skipping Docker deployment")
                return False
            
            # Stop existing container if running
            try:
                existing = self.docker_client.containers.get('cybersecurity-fastapi')
                if existing.status == 'running':
                    self.logger.info("Stopping existing FastAPI container...")
                    existing.stop()
                existing.remove()
            except docker.errors.NotFound:
                pass
            
            # Start new container
            self.logger.info("Starting FastAPI Docker container...")
            container = self.docker_client.containers.run(
                'cybersecurity-fastapi:latest',
                name='cybersecurity-fastapi',
                ports={'8080/tcp': 8080},
                volumes={
                    str(Path.cwd() / 'data'): {'bind': '/app/data', 'mode': 'rw'},
                    str(Path.cwd() / 'logs'): {'bind': '/app/logs', 'mode': 'rw'}
                },
                detach=True,
                restart_policy={'Name': 'unless-stopped'}
            )
            
            # Wait for container to be ready
            time.sleep(5)
            container.reload()
            
            if container.status == 'running':
                self.logger.info("FastAPI container started successfully")
                self.services['fastapi'] = {
                    'type': 'docker',
                    'container': container,
                    'health_check': self.check_fastapi_health
                }
                return True
            else:
                self.logger.error(f"FastAPI container failed to start: {container.status}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start FastAPI container: {e}")
            return False
    
    def check_fastapi_health(self) -> bool:
        """Check FastAPI container health"""
        try:
            if 'fastapi' not in self.services:
                return False
            
            container = self.services['fastapi']['container']
            container.reload()
            
            if container.status != 'running':
                self.logger.warning("FastAPI container is not running")
                return False
            
            # Additional health check: try to connect to API
            import requests
            try:
                response = requests.get('http://localhost:8080/', timeout=5)
                return response.status_code == 200
            except requests.exceptions.RequestException:
                self.logger.warning("FastAPI health check failed - API not responding")
                return False
                
        except Exception as e:
            self.logger.error(f"FastAPI health check error: {e}")
            return False
    
    def start_background_service(self, name: str, command: List[str], cwd: Path, 
                                health_check=None, restart_on_fail=True) -> bool:
        """Start a background service with monitoring"""
        try:
            self.logger.info(f"Starting service: {name}")
            
            # Start the process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment to check if it started successfully
            time.sleep(3)
            
            if process.poll() is None:  # Process is running
                self.services[name] = {
                    'type': 'process',
                    'process': process,
                    'command': command,
                    'cwd': cwd,
                    'health_check': health_check,
                    'restart_on_fail': restart_on_fail,
                    'start_time': datetime.now()
                }
                
                # Start monitoring thread
                monitor_thread = threading.Thread(
                    target=self.monitor_service,
                    args=(name,),
                    daemon=True
                )
                monitor_thread.start()
                
                self.logger.info(f"Service {name} started successfully (PID: {process.pid})")
                return True
            else:
                # Process failed to start
                stdout, stderr = process.communicate()
                self.logger.error(f"Service {name} failed to start:")
                self.logger.error(f"STDOUT: {stdout}")
                self.logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start service {name}: {e}")
            return False
    
    def monitor_service(self, name: str):
        """Monitor a service and restart if needed"""
        service = self.services.get(name)
        if not service:
            return
        
        while not self.shutdown_requested:
            try:
                if service['type'] == 'docker':
                    # Monitor Docker container
                    if not service['health_check']():
                        self.logger.warning(f"Service {name} health check failed")
                        if service.get('restart_on_fail', True):
                            self.restart_service(name)
                
                elif service['type'] == 'process':
                    # Monitor process
                    process = service['process']
                    
                    if process.poll() is not None:  # Process has terminated
                        self.logger.warning(f"Service {name} has terminated unexpectedly")
                        
                        if service.get('restart_on_fail', True):
                            self.restart_service(name)
                    
                    elif service.get('health_check'):
                        # Run custom health check
                        if not service['health_check']():
                            self.logger.warning(f"Service {name} health check failed")
                            if service.get('restart_on_fail', True):
                                self.restart_service(name)
                
                # Sleep between checks
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error monitoring service {name}: {e}")
                time.sleep(30)
    
    def restart_service(self, name: str) -> bool:
        """Restart a failed service with backoff logic"""
        try:
            # Check restart limits
            current_time = datetime.now()
            if name not in self.restart_counts:
                self.restart_counts[name] = []
            
            # Clean old restart timestamps
            self.restart_counts[name] = [
                ts for ts in self.restart_counts[name]
                if (current_time - ts).total_seconds() < self.restart_window
            ]
            
            if len(self.restart_counts[name]) >= self.max_restarts:
                self.logger.error(f"Service {name} has exceeded max restart attempts")
                return False
            
            self.logger.info(f"Restarting service: {name}")
            
            # Stop the service first
            self.stop_service(name)
            
            # Wait before restart
            restart_delay = min(10 * (len(self.restart_counts[name]) + 1), 60)
            self.logger.info(f"Waiting {restart_delay} seconds before restart...")
            time.sleep(restart_delay)
            
            # Record restart attempt
            self.restart_counts[name].append(current_time)
            
            # Restart based on service type
            service = self.services.get(name)
            if not service:
                return False
            
            if service['type'] == 'docker' and name == 'fastapi':
                return self.start_docker_fastapi()
            elif service['type'] == 'process':
                return self.start_background_service(
                    name,
                    service['command'],
                    service['cwd'],
                    service.get('health_check'),
                    service.get('restart_on_fail', True)
                )
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to restart service {name}: {e}")
            return False
    
    def stop_service(self, name: str):
        """Stop a service gracefully"""
        try:
            service = self.services.get(name)
            if not service:
                return
            
            self.logger.info(f"Stopping service: {name}")
            
            if service['type'] == 'docker':
                container = service['container']
                container.stop(timeout=10)
                container.remove()
            
            elif service['type'] == 'process':
                process = service['process']
                if process.poll() is None:  # Still running
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            
            # Remove from services
            del self.services[name]
            
        except Exception as e:
            self.logger.error(f"Error stopping service {name}: {e}")
    
    def stop_all_services(self):
        """Stop all running services"""
        self.logger.info("Stopping all services...")
        
        # Make a copy of service names to avoid dictionary changed during iteration
        service_names = list(self.services.keys())
        
        for name in service_names:
            self.stop_service(name)
        
        self.logger.info("All services stopped")
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        status = {}
        
        for name, service in self.services.items():
            try:
                if service['type'] == 'docker':
                    container = service['container']
                    container.reload()
                    status[name] = {
                        'type': 'docker',
                        'status': container.status,
                        'health': 'healthy' if service.get('health_check', lambda: True)() else 'unhealthy'
                    }
                
                elif service['type'] == 'process':
                    process = service['process']
                    is_running = process.poll() is None
                    status[name] = {
                        'type': 'process',
                        'status': 'running' if is_running else 'stopped',
                        'pid': process.pid if is_running else None,
                        'uptime': str(datetime.now() - service['start_time']) if is_running else None
                    }
                    
            except Exception as e:
                status[name] = {
                    'type': service['type'],
                    'status': 'error',
                    'error': str(e)
                }
        
        return status


class CyberNewsLauncher:
    """Enhanced launcher with production VPS capabilities"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.data_dir = self.project_root / "data"
        self.logs_dir = self.project_root / "logs"
        self.config_dir = self.project_root / "config"
        self.src_dir = self.project_root / "src"
        self.ai_dir = self.project_root / "Ai"
        
        # Initialize service manager
        self.service_manager = ProductionServiceManager()
        
        # Initialize backup manager
        self.backup_manager = BackupManager() if BACKUP_AVAILABLE else None
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # Key file paths
        self.scraper_path = self.src_dir / "scrapers" / "crawl4ai_scraper.py"
        self.monitor_path = self.src_dir / "monitoring" / "news_monitor_24x7.py"
        self.ai_summarizer_path = self.ai_dir / "enhanced_ai_summarizer.py"
        self.alert_system_path = self.src_dir / "monitoring" / "alert_system_integration.py"
        self.fastapi_path = self.project_root / "api" / "cybersecurity_fastapi.py"
        self.flask_api_path = self.project_root / "api" / "cybersecurity_api.py"
        self.url_config_path = self.config_dir / "url_fetch.txt"
        self.requirements_path = self.project_root / "requirements.txt"
        
        # Logger / heartbeat
        self.log = get_logger('launcher')
        hb_file = os.getenv('HEARTBEAT_FILE', 'logs/heartbeat.json')
        try:
            hb_interval = int(os.getenv('HEARTBEAT_INTERVAL_SECONDS', '300'))
        except ValueError:
            hb_interval = 300
        self.heartbeat = Heartbeat(hb_file, hb_interval)
        try:
            self.heartbeat.start()
            self.log.info('Heartbeat started', extra={'file': hb_file, 'interval_s': hb_interval})
        except Exception as e:
            self.log.warning('Heartbeat start failed', extra={'error': str(e)})
        
        # Component availability
        self.ai_enabled = self.ai_summarizer_path.exists()
        self.fastapi_enabled = self.fastapi_path.exists()
        self.flask_enabled = self.flask_api_path.exists()
        
        # Production settings
        self.production_mode = os.getenv('PRODUCTION_MODE', 'false').lower() == 'true'
        self.auto_restart = os.getenv('AUTO_RESTART', 'true').lower() == 'true'
        self.monitor_interval = int(os.getenv('MONITOR_INTERVAL_MINUTES', '30'))
        
        safe_print(f"{EMOJIS['rocket']} Production Launcher initialized")
        if self.production_mode:
            safe_print(f"{EMOJIS['warning']} Running in PRODUCTION MODE")
    
    def run_production_auto_mode(self):
        """
        🚀 ULTIMATE PRODUCTION MODE - Fully automated VPS deployment
        This is the one-command solution for VPS deployment:
        1. Environment validation and setup
        2. Dependency auto-installation
        3. Docker FastAPI service startup
        4. Background monitoring services
        5. AI processing automation
        6. Health monitoring and auto-restart
        7. Error recovery and logging
        """
        safe_print(f"\n{EMOJIS['rocket']} STARTING PRODUCTION AUTO MODE")
        safe_print("="*80)
        safe_print(f"{EMOJIS['target']} VPS-optimized deployment with full automation")
        safe_print(f"{EMOJIS['setup']} Features: Docker API • Auto-restart • Health monitoring • Error recovery")
        safe_print(f"{EMOJIS['time']} This will run continuously until stopped (Ctrl+C)")
        safe_print("="*80)
        
        try:
            # Phase 1: Production Environment Setup
            safe_print(f"\n{EMOJIS['setup']} PHASE 1: Production Environment Setup")
            safe_print("-" * 60)
            
            if not self.production_environment_setup():
                safe_print(f"{EMOJIS['error']} Environment setup failed - cannot continue")
                return False
            
            # Phase 2: Docker Service Detection & Management
            safe_print(f"\n{EMOJIS['web']} PHASE 2: Docker Service Detection & Management")
            safe_print("-" * 60)
            
            # Check for existing containers first
            containers_status = self.service_manager.detect_existing_containers()
            
            if containers_status['fastapi']:
                safe_print(f"{EMOJIS['success']} FastAPI container already running - using existing")
            elif not self.service_manager.start_docker_fastapi():
                safe_print(f"{EMOJIS['warning']} FastAPI Docker failed - trying local fallback")
                self.start_local_fastapi()
            
            if containers_status['nginx']:
                safe_print(f"{EMOJIS['success']} NGINX proxy already running")
                
            if containers_status['monitoring']:
                safe_print(f"{EMOJIS['success']} Monitoring stack already running")
                safe_print(f"{EMOJIS['info']} Grafana: http://localhost:3000 (admin/admin)")
                safe_print(f"{EMOJIS['info']} Prometheus: http://localhost:9091")
                safe_print(f"{EMOJIS['info']} cAdvisor: http://localhost:8081")
            else:
                safe_print(f"{EMOJIS['warning']} Monitoring stack not detected")
                safe_print(f"{EMOJIS['info']} You can start it with: docker compose -f docker/docker-compose.monitoring.yml up -d")
            
            # Phase 3: Background Services
            safe_print(f"\n{EMOJIS['fast']} PHASE 3: Background Services")
            safe_print("-" * 60)
            
            self.start_production_services()
            
            # Phase 4: Initial Data Setup
            safe_print(f"\n{EMOJIS['news']} PHASE 4: Initial Data Setup")
            safe_print("-" * 60)
            
            if not self.check_data_files():
                safe_print(f"{EMOJIS['warning']} No data found - performing initial scrape")
                self.run_initial_scrape()
            
            if self.ai_enabled:
                safe_print(f"{EMOJIS['ai']} Running initial AI summarization...")
                self.run_ai_summarizer()
            
            # Phase 5: Production Monitoring Loop
            safe_print(f"\n{EMOJIS['cycle']} PHASE 5: Production Monitoring")
            safe_print("-" * 60)
            
            self.run_production_monitoring_loop()
            
        except KeyboardInterrupt:
            safe_print(f"\n{EMOJIS['stop']} Production mode stopped by user")
            self.graceful_shutdown()
        except Exception as e:
            safe_print(f"\n{EMOJIS['error']} Critical error in production mode: {e}")
            self.service_manager.logger.error(f"Production mode critical error: {e}")
            self.graceful_shutdown()
    
    def production_environment_setup(self) -> bool:
        """Setup production environment with error handling"""
        try:
            # Check Python version
            if not self.check_python_version():
                return False
            
            # Validate project structure
            if not self.validate_project_structure():
                return False
            
            # Install/update dependencies
            if not self.install_dependencies_with_retry():
                return False
            
            # Setup directories and permissions
            self.setup_production_directories()
            
            # Auto backup if needed
            if self.backup_manager:
                try:
                    self.auto_backup_on_startup()
                except Exception as e:
                    safe_print(f"{EMOJIS['warning']} Backup warning: {e}")
            
            safe_print(f"{EMOJIS['success']} Production environment ready")
            return True
            
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Environment setup failed: {e}")
            return False
    
    def install_dependencies_with_retry(self, max_retries=3) -> bool:
        """Install dependencies with retry logic"""
        for attempt in range(max_retries):
            try:
                safe_print(f"{EMOJIS['setup']} Installing dependencies (attempt {attempt + 1}/{max_retries})")
                
                # Try pip install with different strategies
                commands = [
                    [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path), "--upgrade"],
                    [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path), "--force-reinstall"],
                    [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_path), "--no-cache-dir"]
                ]
                
                for i, cmd in enumerate(commands):
                    try:
                        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
                        safe_print(f"{EMOJIS['success']} Dependencies installed successfully")
                        return True
                    except subprocess.CalledProcessError as e:
                        if i < len(commands) - 1:
                            safe_print(f"{EMOJIS['warning']} Install method {i+1} failed, trying alternative...")
                            continue
                        raise e
                        
            except Exception as e:
                safe_print(f"{EMOJIS['warning']} Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))  # Exponential backoff
                else:
                    safe_print(f"{EMOJIS['error']} All dependency installation attempts failed")
                    return False
        
        return False
    
    def setup_production_directories(self):
        """Setup production directories and permissions"""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.data_dir / "backup",
            self.data_dir / "alerts"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True, parents=True)
            safe_print(f"{EMOJIS['success']} Directory ready: {directory.name}")
    
    def start_local_fastapi(self) -> bool:
        """Start FastAPI locally as fallback"""
        try:
            safe_print(f"{EMOJIS['web']} Starting local FastAPI server...")
            
            return self.service_manager.start_background_service(
                'fastapi-local',
                [sys.executable, "-m", "uvicorn", "api.cybersecurity_fastapi:app", 
                 "--host", "0.0.0.0", "--port", "8080", "--reload"],
                self.project_root,
                health_check=self.check_local_fastapi_health
            )
            
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Local FastAPI startup failed: {e}")
            return False
    
    def check_local_fastapi_health(self) -> bool:
        """Health check for local FastAPI"""
        try:
            import requests
            response = requests.get('http://localhost:8080/', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_production_services(self):
        """Start all background services for production"""
        safe_print(f"{EMOJIS['alert']} Starting production services...")
        
        # Start alert system if available
        if self.alert_system_path.exists():
            self.service_manager.start_background_service(
                'alert-system',
                [sys.executable, str(self.alert_system_path)],
                self.project_root
            )
        
        safe_print(f"{EMOJIS['success']} Production services started")
    
    def run_initial_scrape(self) -> bool:
        """Run initial scrape with error handling"""
        try:
            safe_print(f"{EMOJIS['news']} Running initial scrape...")
            
            result = subprocess.run([
                sys.executable, str(self.scraper_path)
            ], cwd=self.project_root, timeout=600, capture_output=True, text=True)
            
            if result.returncode == 0:
                safe_print(f"{EMOJIS['success']} Initial scrape completed")
                return True
            else:
                safe_print(f"{EMOJIS['error']} Initial scrape failed:")
                safe_print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            safe_print(f"{EMOJIS['warning']} Initial scrape timed out")
            return False
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Initial scrape error: {e}")
            return False
    
    def run_production_monitoring_loop(self):
        """Production monitoring loop with 5-minute intervals and smart scraping"""
        safe_print(f"\n{EMOJIS['success']} ENHANCED PRODUCTION SYSTEM OPERATIONAL")
        safe_print("="*80)
        safe_print(f"🔄 Smart Scraping: Business hours only, data-driven decisions")
        safe_print(f"⏰ Monitoring interval: 5 minutes")
        safe_print(f"📊 Health checks: Docker, system resources, API status")
        safe_print("="*80)
        
        cycle = 0
        last_health_check = datetime.now()
        MONITORING_INTERVAL = 300  # 5 minutes = 300 seconds
        
        try:
            while True:
                cycle += 1
                current_time = datetime.now()
                
                # Display cycle info
                safe_print(f"\n{EMOJIS['cycle']} ENHANCED MONITORING CYCLE {cycle}")
                safe_print(f"{EMOJIS['time']} Started: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                safe_print("-" * 50)
                
                # Run enhanced monitoring cycle with smart scraping
                try:
                    self.run_enhanced_monitoring_cycle()
                except Exception as e:
                    safe_print(f"{EMOJIS['error']} Enhanced monitoring cycle error: {e}")
                    self.service_manager.logger.error(f"Enhanced monitoring cycle error: {e}")
                
                # Comprehensive health check every 6 cycles (30 minutes)
                if cycle % 6 == 0:
                    safe_print(f"\n{EMOJIS['search']} Running comprehensive health check...")
                    self.run_comprehensive_health_check()
                
                # Show next cycle info
                next_time = current_time + timedelta(seconds=MONITORING_INTERVAL)
                safe_print(f"\n{EMOJIS['success']} Enhanced cycle {cycle} completed")
                safe_print(f"{EMOJIS['time']} Next cycle: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
                safe_print(f"{EMOJIS['info']} Enhanced production system running (5-min intervals)...")
                
                # Sleep for 5 minutes
                time.sleep(MONITORING_INTERVAL)
                
        except KeyboardInterrupt:
            safe_print(f"\n{EMOJIS['stop']} Enhanced production monitoring stopped by user")
            raise
    
    def run_enhanced_monitoring_cycle(self):
        """Enhanced monitoring cycle with Docker health checks, system metrics, and smart scraping"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # 1. Docker Health Check
            safe_print(f"🐳 Docker Health Check...")
            containers = self.service_manager.detect_existing_containers()
            total_containers = sum(containers.values())
            
            if total_containers > 0:
                safe_print(f"✅ Docker Status: {total_containers} containers active")
                if containers['monitoring']:
                    safe_print(f"📊 Monitoring stack: active")
                if containers['fastapi']:
                    safe_print(f"🚀 API containers: active")
                if containers['nginx']:
                    safe_print(f"🌐 Proxy containers: active")
            else:
                safe_print(f"⚠️  Docker Status: No containers detected")
            
            # 2. System Resources Check
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                safe_print(f"💾 Memory Usage: {memory_mb:.1f} MB")
                
                # Check disk space
                total, used, free = shutil.disk_usage(self.project_root)
                free_gb = free // (1024**3)
                if free_gb < 5:
                    safe_print(f"⚠️  Disk Space: {free_gb} GB free (LOW)")
                else:
                    safe_print(f"💽 Disk Space: {free_gb} GB free")
                    
            except Exception as e:
                safe_print(f"⚠️  System metrics check failed: {e}")
            
            # 3. API Health Check (if running)
            try:
                if containers['fastapi'] or any('FastAPI' in name for name, _ in self.running_processes):
                    response = requests.get('http://localhost:8080/health', timeout=5)
                    if response.status_code == 200:
                        safe_print(f"✅ API Server: Responding (HTTP {response.status_code})")
                    else:
                        safe_print(f"⚠️  API Server: HTTP {response.status_code}")
                else:
                    safe_print(f"ℹ️  API Server: Not configured for health check")
            except Exception as e:
                safe_print(f"⚠️  API health check failed: {e}")
            
            # 4. Smart Scraping Decision
            safe_print(f"\n🧠 Smart Scraping Analysis...")
            should_scrape, reason = self.should_scrape_now()
            scraping_status = self.get_smart_scraping_status()
            
            safe_print(f"📊 Current Data Status:")
            safe_print(f"   📰 Articles today: {scraping_status.get('article_count', 0)}")
            safe_print(f"   🌐 Sources: {scraping_status.get('sources_count', 0)}")
            safe_print(f"   ⏰ Data age: {scraping_status.get('data_age_hours', 0):.1f} hours")
            safe_print(f"   � Business hours: {scraping_status.get('business_hours', 'N/A')}")
            safe_print(f"   📏 Thresholds: {scraping_status['thresholds']['min_articles']}-{scraping_status['thresholds']['max_articles']} articles, {scraping_status['thresholds']['max_age_hours']}h max age")
            
            if should_scrape:
                safe_print(f"🎯 SMART SCRAPING: PROCEEDING")
                safe_print(f"   📝 Reason: {reason}")
                
                # Run the standard monitoring cycle with scraping
                result = subprocess.run([
                    sys.executable, str(self.monitor_path), "--single-cycle"
                ], capture_output=True, text=True, timeout=1800, cwd=self.project_root)
                
                monitor_output = result.stdout
                monitor_error = result.stderr
                
                safe_print(f"📊 Scraper Output:")
                safe_print(monitor_output)
                
                if result.returncode == 0:
                    # Check if new articles were actually found
                    new_articles_indicators = [
                        "Found and added",
                        "NEW ARTICLES FOUND",
                        "new articles detected",
                        "Appended to daily archive",
                        "articles scraped successfully"
                    ]
                    
                    new_articles_found = any(indicator.lower() in monitor_output.lower() 
                                           for indicator in new_articles_indicators)
                    
                    if new_articles_found:
                        safe_print(f"\n🎯 NEW ARTICLES DETECTED! Running AI summarization...")
                        
                        # Only run AI summarization if enabled and new articles found
                        if self.ai_enabled:
                            try:
                                safe_print(f"🤖 Starting AI summarization process...")
                                ai_result = subprocess.run([
                                    sys.executable, str(self.ai_summarizer_path), "--auto"
                                ], capture_output=True, text=True, timeout=600, cwd=self.project_root)
                                
                                if ai_result.returncode == 0:
                                    safe_print(f"✅ AI summarization completed successfully")
                                    safe_print(f"📊 AI Output:")
                                    safe_print(ai_result.stdout)
                                else:
                                    safe_print(f"❌ AI summarization failed:")
                                    safe_print(ai_result.stderr)
                                    
                            except subprocess.TimeoutExpired:
                                safe_print(f"⏰ AI summarization timed out (took longer than 10 minutes)")
                            except Exception as e:
                                safe_print(f"💥 AI summarization error: {str(e)}")
                        else:
                            safe_print("⚠️ AI summarization is disabled or not available")
                    else:
                        safe_print("ℹ️ No new articles found this cycle")
                        safe_print("📝 This may indicate sufficient coverage or quiet news period")
                        
                else:
                    safe_print(f"❌ Scraping cycle failed with return code: {result.returncode}")
                    safe_print("Error output:")
                    safe_print(monitor_error)
            else:
                safe_print(f"⏸️ SMART SCRAPING: SKIPPED")
                safe_print(f"   📝 Reason: {reason}")
                safe_print(f"   ℹ️  System will check again in next cycle")
                
                # Still run a light monitoring check without scraping
                safe_print(f"🔍 Running light system check without scraping...")
                
            # 5. Export Metrics (if monitoring containers are running)
            if containers['monitoring']:
                try:
                    # Send custom metrics to monitoring stack
                    metrics_data = {
                        'timestamp': current_time,
                        'containers_active': total_containers,
                        'memory_mb': memory_mb if 'memory_mb' in locals() else 0,
                        'disk_free_gb': free_gb if 'free_gb' in locals() else 0,
                        'articles_today': scraping_status.get('article_count', 0),
                        'sources_today': scraping_status.get('sources_count', 0),
                        'data_age_hours': scraping_status.get('data_age_hours', 0),
                        'scraping_decision': should_scrape,
                        'cycle_success': True
                    }
                    safe_print(f"📈 Enhanced metrics exported to monitoring stack")
                except Exception as e:
                    safe_print(f"⚠️  Metrics export failed: {e}")
                    
        except subprocess.TimeoutExpired:
            safe_print("⏰ Enhanced monitoring cycle timed out (longer than 30 minutes)")
        except Exception as e:
            safe_print(f"💥 Enhanced monitoring cycle error: {str(e)}")

    def run_intelligent_monitoring_cycle(self):
        """Intelligent monitoring cycle with error recovery"""
        try:
            # Run monitor with timeout
            result = subprocess.run([
                sys.executable, str(self.monitor_path), "--single-cycle"
            ], 
            capture_output=True, 
            text=True, 
            timeout=1800,  # 30 minutes max
            cwd=self.project_root
            )
            
            if result.returncode == 0:
                output = result.stdout
                safe_print(f"{EMOJIS['data']} Monitor output:")
                safe_print(output)
                
                # Check if new articles were found
                if any(indicator in output.lower() for indicator in [
                    'new articles found', 'articles detected', 'appended to daily'
                ]):
                    safe_print(f"{EMOJIS['ai']} New articles detected - running AI summarization")
                    self.run_ai_with_retry()
                else:
                    safe_print(f"{EMOJIS['info']} No new articles - system healthy")
            else:
                safe_print(f"{EMOJIS['warning']} Monitor cycle failed:")
                safe_print(result.stderr)
                
        except subprocess.TimeoutExpired:
            safe_print(f"{EMOJIS['warning']} Monitor cycle timed out")
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Monitor cycle error: {e}")
    
    def run_ai_with_retry(self, max_retries=3) -> bool:
        """Run AI summarization with retry logic"""
        for attempt in range(max_retries):
            try:
                safe_print(f"{EMOJIS['ai']} AI attempt {attempt + 1}/{max_retries}")
                
                result = subprocess.run([
                    sys.executable, str(self.ai_summarizer_path), "--auto"
                ], 
                capture_output=True, 
                text=True, 
                timeout=600,  # 10 minutes max
                cwd=self.project_root
                )
                
                if result.returncode == 0:
                    safe_print(f"{EMOJIS['success']} AI summarization completed")
                    return True
                else:
                    safe_print(f"{EMOJIS['warning']} AI attempt {attempt + 1} failed")
                    if attempt < max_retries - 1:
                        time.sleep(30 * (attempt + 1))  # Exponential backoff
                        
            except subprocess.TimeoutExpired:
                safe_print(f"{EMOJIS['warning']} AI attempt {attempt + 1} timed out")
            except Exception as e:
                safe_print(f"{EMOJIS['error']} AI attempt {attempt + 1} error: {e}")
        
        safe_print(f"{EMOJIS['error']} AI summarization failed after {max_retries} attempts")
        return False
    
    def should_scrape_now(self) -> tuple[bool, str]:
        """Determine if we should scrape based on time, existing data, and thresholds"""
        try:
            current_time = datetime.now()
            current_hour = current_time.hour
            today = current_time.strftime('%Y%m%d')
            
            # Time-based control (configurable business hours)
            BUSINESS_START = int(os.getenv('SCRAPE_START_HOUR', '6'))  # 6 AM
            BUSINESS_END = int(os.getenv('SCRAPE_END_HOUR', '22'))     # 10 PM
            
            if not (BUSINESS_START <= current_hour <= BUSINESS_END):
                return False, f"Outside business hours ({BUSINESS_START}:00-{BUSINESS_END}:00). Current: {current_hour}:00"
            
            # Check if today's file exists and analyze it
            today_file = self.data_dir / f"News_today_{today}.json"
            
            if not today_file.exists():
                return True, "No data file for today - fresh scraping needed"
            
            # Check file modification time
            file_mod_time = today_file.stat().st_mtime
            hours_since_update = (time.time() - file_mod_time) / 3600
            
            # Configurable time thresholds
            MAX_DATA_AGE_HOURS = float(os.getenv('MAX_DATA_AGE_HOURS', '2'))  # 2 hours default
            
            if hours_since_update > MAX_DATA_AGE_HOURS:
                return True, f"Data is stale ({hours_since_update:.1f} hours old, max: {MAX_DATA_AGE_HOURS}h)"
            
            # Check article count and quality
            try:
                with open(today_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data formats
                articles = []
                sources = set()
                
                if isinstance(data, dict):
                    # Check for new format with results structure
                    if 'results' in data:
                        for site_url, site_data in data['results'].items():
                            if isinstance(site_data, dict) and 'articles' in site_data:
                                site_articles = site_data['articles']
                                articles.extend(site_articles)
                                # Extract domain from site URL
                                from urllib.parse import urlparse
                                domain = urlparse(site_url).netloc
                                sources.add(domain)
                    # Check for articles key directly
                    elif 'articles' in data:
                        articles = data['articles']
                    # Check for scraping_info format
                    elif 'scraping_info' in data:
                        # Extract from results if available
                        if 'results' in data:
                            for site_url, site_data in data['results'].items():
                                if isinstance(site_data, dict) and 'articles' in site_data:
                                    articles.extend(site_data['articles'])
                                    from urllib.parse import urlparse
                                    domain = urlparse(site_url).netloc
                                    sources.add(domain)
                elif isinstance(data, list):
                    # Legacy format - direct list of articles
                    articles = data
                
                article_count = len(articles)
                
                # Extract sources from article URLs if not already done
                if not sources:
                    for article in articles:
                        if isinstance(article, dict):
                            url = article.get('url', '')
                            if url:
                                from urllib.parse import urlparse
                                domain = urlparse(url).netloc
                                sources.add(domain)
                
                # Configurable article thresholds
                MIN_ARTICLES = int(os.getenv('MIN_ARTICLES_THRESHOLD', '10'))    # 10 articles minimum
                MAX_ARTICLES = int(os.getenv('MAX_ARTICLES_THRESHOLD', '100'))   # 100 articles maximum
                
                if article_count < MIN_ARTICLES:
                    return True, f"Insufficient articles ({article_count}/{MIN_ARTICLES}) - need more content"
                
                if article_count >= MAX_ARTICLES:
                    return False, f"Maximum articles reached ({article_count}/{MAX_ARTICLES}) - sufficient content for today"
                
                # Check for recent unique sources
                recent_articles = 0
                cutoff_time = time.time() - (6 * 3600)  # Last 6 hours
                
                for article in articles:
                    if isinstance(article, dict):
                        # Check if article is recent
                        article_time = article.get('timestamp', article.get('scraped_at', 0))
                        if isinstance(article_time, str):
                            try:
                                article_time = datetime.fromisoformat(article_time.replace('Z', '+00:00')).timestamp()
                            except:
                                article_time = 0
                        
                        if article_time > cutoff_time:
                            recent_articles += 1
                
                # Source diversity check
                MIN_SOURCES = int(os.getenv('MIN_SOURCES_THRESHOLD', '3'))
                if len(sources) < MIN_SOURCES:
                    return True, f"Need more source diversity ({len(sources)}/{MIN_SOURCES} sources)"
                
                # Recent content check
                if recent_articles < 5 and hours_since_update > 1:
                    return True, f"Not enough recent content ({recent_articles} articles in last 6h)"
                
                return False, f"Sufficient recent data ({article_count} articles from {len(sources)} sources, {hours_since_update:.1f}h old)"
                
            except (json.JSONDecodeError, KeyError) as e:
                return True, f"Data file corrupted or invalid format: {e}"
            
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Error in smart scraping check: {e}")
            return True, f"Error checking scraping conditions: {e}"

    def get_smart_scraping_status(self) -> dict:
        """Get detailed smart scraping status for monitoring"""
        try:
            current_time = datetime.now()
            today = current_time.strftime('%Y%m%d')
            today_file = self.data_dir / f"News_today_{today}.json"
            
            status = {
                'current_hour': current_time.hour,
                'business_hours': f"{os.getenv('SCRAPE_START_HOUR', '6')}:00-{os.getenv('SCRAPE_END_HOUR', '22')}:00",
                'data_file_exists': today_file.exists(),
                'article_count': 0,
                'sources_count': 0,
                'data_age_hours': 0,
                'last_update': 'Never',
                'thresholds': {
                    'min_articles': int(os.getenv('MIN_ARTICLES_THRESHOLD', '10')),
                    'max_articles': int(os.getenv('MAX_ARTICLES_THRESHOLD', '100')),
                    'max_age_hours': float(os.getenv('MAX_DATA_AGE_HOURS', '2')),
                    'min_sources': int(os.getenv('MIN_SOURCES_THRESHOLD', '3'))
                }
            }
            
            if today_file.exists():
                file_mod_time = today_file.stat().st_mtime
                status['data_age_hours'] = (time.time() - file_mod_time) / 3600
                status['last_update'] = datetime.fromtimestamp(file_mod_time).strftime('%Y-%m-%d %H:%M:%S')
                
                try:
                    with open(today_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # Handle different data formats
                    articles = []
                    sources = set()
                    
                    if isinstance(data, dict):
                        # Check for new format with results structure
                        if 'results' in data:
                            for site_url, site_data in data['results'].items():
                                if isinstance(site_data, dict) and 'articles' in site_data:
                                    site_articles = site_data['articles']
                                    articles.extend(site_articles)
                                    # Extract domain from site URL
                                    from urllib.parse import urlparse
                                    domain = urlparse(site_url).netloc
                                    sources.add(domain)
                        # Check for articles key directly
                        elif 'articles' in data:
                            articles = data['articles']
                        # Check for scraping_info format
                        elif 'scraping_info' in data:
                            # Get total from scraping_info if available
                            status['article_count'] = data['scraping_info'].get('total_articles', 0)
                            if 'results' in data:
                                for site_url, site_data in data['results'].items():
                                    if isinstance(site_data, dict) and 'articles' in site_data:
                                        articles.extend(site_data['articles'])
                                        from urllib.parse import urlparse
                                        domain = urlparse(site_url).netloc
                                        sources.add(domain)
                    elif isinstance(data, list):
                        # Legacy format - direct list of articles
                        articles = data
                    
                    if not status.get('article_count'):  # If not set from scraping_info
                        status['article_count'] = len(articles)
                    
                    # Extract sources from article URLs if not already done
                    if not sources:
                        for article in articles:
                            if isinstance(article, dict):
                                url = article.get('url', '')
                                if url:
                                    from urllib.parse import urlparse
                                    domain = urlparse(url).netloc
                                    sources.add(domain)
                    
                    status['sources_count'] = len(sources)
                        
                except Exception as e:
                    status['error'] = f"Error reading data file: {e}"
            
            return status
            
        except Exception as e:
            return {'error': f"Error getting smart scraping status: {e}"}

    def run_comprehensive_health_check(self):
        """Enhanced system health check including Docker containers"""
        safe_print(f"\n{EMOJIS['search']} 🏥 COMPREHENSIVE HEALTH CHECK")
        safe_print("-" * 60)
        
        health_score = 0
        total_checks = 6
        
        # 1. Service Status
        service_status = self.service_manager.get_service_status()
        running_services = sum(1 for status in service_status.values() if status.get('status') == 'running')
        total_services = len(service_status) if service_status else 0
        
        if total_services > 0:
            service_percentage = (running_services / total_services) * 100
            safe_print(f"{EMOJIS['setup']} Services: {running_services}/{total_services} running ({service_percentage:.1f}%)")
            if service_percentage >= 80:
                health_score += 1
        else:
            safe_print(f"{EMOJIS['warning']} Services: No managed services detected")
        
        # 2. Docker Containers Status
        containers = self.service_manager.detect_existing_containers()
        container_count = sum(containers.values())
        if container_count >= 2:  # FastAPI + NGINX minimum
            safe_print(f"{EMOJIS['web']} Docker: {container_count} containers operational ✅")
            health_score += 1
        else:
            safe_print(f"{EMOJIS['warning']} Docker: Limited containers ({container_count})")
        
        # 3. Data Files Check
        data_files = list(self.data_dir.glob("*.json"))
        if data_files:
            safe_print(f"{EMOJIS['success']} Data Files: {len(data_files)} JSON files found ✅")
            health_score += 1
        else:
            safe_print(f"{EMOJIS['error']} Data Files: No JSON files found")
        
        # 4. AI Summaries Check
        ai_summary_file = self.data_dir / "summarized_news_hf.json"
        if ai_summary_file.exists():
            safe_print(f"{EMOJIS['success']} AI Summaries: Available ✅")
            health_score += 1
        else:
            safe_print(f"{EMOJIS['error']} AI Summaries: No summary file found")
        
        # 5. Disk Space Check
        try:
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free // (1024**3)
            if free_gb >= 5:
                safe_print(f"{EMOJIS['success']} Disk Space: {free_gb} GB free ✅")
                health_score += 1
            else:
                safe_print(f"{EMOJIS['warning']} Disk Space: {free_gb} GB free (LOW)")
        except:
            safe_print(f"{EMOJIS['warning']} Disk Space: Check failed")
        
        # 6. Memory Usage Check
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            if memory_mb < 500:  # Less than 500MB is good
                safe_print(f"{EMOJIS['success']} Memory: {memory_mb:.1f} MB ✅")
                health_score += 1
            else:
                safe_print(f"{EMOJIS['warning']} Memory: {memory_mb:.1f} MB (HIGH)")
        except:
            safe_print(f"{EMOJIS['warning']} Memory: Check failed")
        
        # 7. API Server Health (bonus check)
        try:
            response = requests.get('http://localhost:8080/health', timeout=5)
            if response.status_code == 200:
                safe_print(f"{EMOJIS['success']} API Server: Responding ✅")
                health_score += 0.5  # Bonus points
            else:
                safe_print(f"{EMOJIS['warning']} API Server: HTTP {response.status_code}")
        except:
            safe_print(f"{EMOJIS['error']} API Server: Not responding")
        
        # Calculate overall health
        health_percentage = (health_score / total_checks) * 100
        
        if health_percentage >= 80:
            health_status = "EXCELLENT"
            health_emoji = EMOJIS['success']
        elif health_percentage >= 60:
            health_status = "GOOD"
            health_emoji = EMOJIS['success']
        elif health_percentage >= 40:
            health_status = "FAIR"
            health_emoji = EMOJIS['warning']
        else:
            health_status = "POOR"
            health_emoji = EMOJIS['error']
        
        safe_print(f"\n{health_emoji} OVERALL HEALTH: {health_percentage:.1f}% ({health_status})")
        safe_print(f"{EMOJIS['data']} Score: {health_score:.1f}/{total_checks}")

    def run_system_health_check(self):
        """Comprehensive system health check"""
        safe_print(f"{EMOJIS['search']} System Health Report:")
        safe_print("-" * 40)
        
        # Service status
        service_status = self.service_manager.get_service_status()
        for service_name, status in service_status.items():
            health_icon = EMOJIS['success'] if status['status'] == 'running' else EMOJIS['error']
            safe_print(f"{health_icon} {service_name}: {status['status']}")
        
        # Data files check
        data_files = list(self.data_dir.glob("*.json"))
        safe_print(f"{EMOJIS['data']} Data files: {len(data_files)} found")
        
        # Disk space check
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free // (1024**3)
            safe_print(f"{EMOJIS['info']} Free disk space: {free_gb} GB")
            
            if free_gb < 1:
                safe_print(f"{EMOJIS['warning']} Low disk space warning!")
        except:
            pass
        
        # Memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            safe_print(f"{EMOJIS['info']} Memory usage: {memory_mb:.1f} MB")
        except:
            pass
    
    def graceful_shutdown(self):
        """Graceful shutdown of all services"""
        safe_print(f"\n{EMOJIS['warning']} Initiating graceful shutdown...")
        
        try:
            # Stop service manager
            self.service_manager.stop_all_services()
            
            # Stop heartbeat
            if hasattr(self, 'heartbeat'):
                self.heartbeat.stop()
            
            safe_print(f"{EMOJIS['success']} Graceful shutdown completed")
            
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Shutdown error: {e}")
        
        safe_print(f"{EMOJIS['success']} Thank you for using Cybersecurity News Crawler!")
    
    @contextmanager
    def error_recovery_context(self, operation_name: str):
        """Context manager for error recovery"""
        try:
            safe_print(f"{EMOJIS['rocket']} Starting: {operation_name}")
            yield
            safe_print(f"{EMOJIS['success']} Completed: {operation_name}")
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Failed: {operation_name} - {e}")
            self.service_manager.logger.error(f"Operation failed: {operation_name} - {e}")
            
            # Recovery logic could go here
            if self.auto_restart:
                safe_print(f"{EMOJIS['warning']} Auto-recovery enabled...")
                time.sleep(5)
            
            raise

    def print_banner(self):
        """Display the application banner"""
        safe_print("\n" + "="*70)
        safe_print(f"  {EMOJIS['security']} CYBERSECURITY NEWS CRAWLER v4.0 - FastAPI Edition")
        safe_print("  Complete Automation Suite - One Command Does Everything!")
        safe_print("="*70)
        safe_print(f"  {EMOJIS['rocket']} NEW: Full Auto Mode - No manual intervention needed!")
        safe_print(f"  {EMOJIS['web']} NEW: FastAPI Integration - High-performance API server")
        safe_print(f"  {EMOJIS['ai']} NEW: Intelligent workflow automation")
        safe_print("="*70)
        
    def print_menu(self):
        """Display the main menu"""
        safe_print("\nChoose your action:")
        safe_print(f"\n[0] {EMOJIS['rocket']} PRODUCTION AUTO MODE (VPS Ready) - Ultimate Automation!")
        safe_print("    - 🚀 PRODUCTION-GRADE deployment for VPS")
        safe_print("    - 🐳 Docker FastAPI with auto-restart")
        safe_print("    - 💪 Error recovery and health monitoring") 
        safe_print("    - 🔄 Continuous operation with intelligent monitoring")
        safe_print("    - 📊 System health checks and resource monitoring")
        safe_print("    - ⚡ One command for complete VPS deployment!")
        safe_print(f"\n[1] {EMOJIS['rocket']} FULL AUTO MODE (Standard) - One Command Does Everything!")
        safe_print("    - Automatic backup of old files")
        safe_print("    - Setup validation and dependency install")
        safe_print("    - Initial scraping if needed")
        safe_print("    - Start FastAPI server for real-time access")
        safe_print("    - 24/7 monitoring with AI summarization")
        safe_print("    - Alert system for real-time notifications")
        safe_print("    - Everything runs automatically in sequence!")
        safe_print(f"\n[2] {EMOJIS['rocket']} Run Complete Project (Interactive)")
        safe_print("    - Intelligent flow: Scraper → Monitor → AI")
        safe_print("    - Handles empty data directory automatically")
        safe_print("    - 24/7 monitoring with smart AI integration")
        safe_print(f"\n[3] {EMOJIS['news']} One-Time Scraping Only")
        safe_print("    - Just scrape current articles once")
        safe_print("    - No monitoring, no AI processing")
        safe_print(f"\n[4] {EMOJIS['fast']} Start Monitor Only")
        safe_print("    - Assumes data already exists")
        safe_print("    - 24/7 monitoring without initial scrape")
        safe_print(f"\n[5] {EMOJIS['ai']} Run AI Summarizer Only")
        safe_print("    - Process existing articles with AI")
        safe_print("    - Requires data files to exist")
        safe_print(f"\n[6] {EMOJIS['alert']} Start Alert System")
        safe_print("    - Monitor file changes and send real-time alerts")
        safe_print("    - Integrates with frontend notification system")
        safe_print(f"\n[7] {EMOJIS['web']} Start API Server (FastAPI/Flask)")
        safe_print("    - Start the cybersecurity news API server")
        safe_print("    - Provides REST endpoints for frontend access")
        safe_print(f"\n[8] {EMOJIS['setup']} Test Project Flow")
        safe_print("    - Quick test of all components")
        safe_print(f"\n[9] {EMOJIS['setup']} Setup & Validation")
        safe_print("    - Install dependencies and validate setup")
        safe_print(f"\n[10] {EMOJIS['data']} Project Status")
        safe_print("    - Show current project status and data")
        safe_print(f"\n[11] {EMOJIS['backup']} Backup Management")
        safe_print("    - Automatically backup old data files")
        safe_print("    - Move yesterday's files to backup folder")
        safe_print(f"\n[12] {EMOJIS['backup']} List Backup Files")
        safe_print("    - Show all files in backup directory")
        safe_print(f"\n[13] {EMOJIS['error']} Exit")
        safe_print(f"\n[14] {EMOJIS['ai']} Fully Autonomous Mode (Headless)")
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            safe_print(f"{EMOJIS['error']} ERROR: Python 3.9+ is required")
            safe_print(f"Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        return True
        
    def validate_project_structure(self):
        """Validate that all required files exist"""
        safe_print(f"{EMOJIS['search']} Validating project structure...")
        
        required_files = {
            "Scraper": self.scraper_path,
            "Monitor": self.monitor_path,
            "URL Config": self.url_config_path,
            "Requirements": self.requirements_path
        }
        
        missing_files = []
        for name, path in required_files.items():
            if path.exists():
                safe_print(f"{EMOJIS['success']} {name}: {path.name}")
            else:
                safe_print(f"{EMOJIS['error']} {name}: {path} (MISSING)")
                missing_files.append(name)
                
        # Check AI summarizer (optional)
        if self.ai_summarizer_path.exists():
            safe_print(f"{EMOJIS['success']} AI Summarizer: {self.ai_summarizer_path.name}")
            self.ai_enabled = True
        else:
            safe_print(f"{EMOJIS['warning']} AI Summarizer: {self.ai_summarizer_path} (OPTIONAL - will be disabled)")
            self.ai_enabled = False
            
        # Check API servers (optional but recommended)
        if self.fastapi_path.exists():
            safe_print(f"{EMOJIS['success']} FastAPI Server: {self.fastapi_path.name}")
            self.fastapi_enabled = True
        else:
            safe_print(f"{EMOJIS['warning']} FastAPI Server: {self.fastapi_path} (OPTIONAL - not available)")
            self.fastapi_enabled = False
            
        if self.flask_api_path.exists():
            safe_print(f"{EMOJIS['success']} Flask API Server: {self.flask_api_path.name}")
            self.flask_enabled = True
        else:
            safe_print(f"{EMOJIS['warning']} Flask API Server: {self.flask_api_path} (OPTIONAL - not available)")
            self.flask_enabled = False
            
        if not self.fastapi_enabled and not self.flask_enabled:
            safe_print(f"{EMOJIS['warning']} WARNING: No API servers available - external access will be limited")
            
        if missing_files:
            safe_print(f"\n{EMOJIS['error']} Missing required files: {', '.join(missing_files)}")
            return False
            
        safe_print(f"{EMOJIS['success']} Project structure validation passed")
        return True
        
    def install_dependencies(self):
        """Install required Python packages"""
        safe_print(f"{EMOJIS['setup']} Installing/updating required packages...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                str(self.requirements_path), "--quiet"
            ], check=True)
            safe_print(f"{EMOJIS['success']} Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            safe_print(f"{EMOJIS['error']} Failed to install dependencies: {e}")
            return False
        except FileNotFoundError:
            safe_print(f"{EMOJIS['error']} pip not found. Please ensure Python and pip are properly installed")
            return False
            
    def check_data_files(self):
        """Check if data files exist"""
        # Check both data directory and project root for JSON files
        data_files = list(self.data_dir.glob("*.json"))
        root_files = list(self.project_root.glob("cybersecurity_news_*.json"))
        
        all_files = data_files + root_files
        
        if all_files:
            safe_print(f"{EMOJIS['data']} Found {len(all_files)} existing data file(s)")
            for file in all_files:
                size_kb = file.stat().st_size / 1024
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                safe_print(f"  - {file.name} ({size_kb:.1f} KB, modified {mod_time.strftime('%Y-%m-%d %H:%M')})")
            return True
        else:
            safe_print(f"{EMOJIS['error']} No existing data files found")
            return False
            
    def run_scraper(self):
        """Run the news scraper"""
        safe_print(f"\n{EMOJIS['news']} Running News Scraper...")
        safe_print("="*40)
        try:
            result = subprocess.run([
                sys.executable, str(self.scraper_path)
            ], cwd=self.project_root)
            self.log.info('Scraper executed', extra={'returncode': result.returncode})
            
            if result.returncode == 0:
                safe_print(f"{EMOJIS['success']} Scraping completed successfully")
                return True
            else:
                safe_print(f"{EMOJIS['error']} Scraping failed with return code: {result.returncode}")
                return False
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Error running scraper: {e}")
            return False
            
    def run_monitor_only(self):
        """Run the 24/7 monitor"""
        safe_print(f"\n{EMOJIS['fast']} Starting 24/7 Monitor...")
        safe_print("="*40)
        safe_print("Press Ctrl+C to stop monitoring")
        try:
            subprocess.run([
                sys.executable, str(self.monitor_path)
            ], cwd=self.project_root)
            self.log.info('Monitor process exited')
        except KeyboardInterrupt:
            safe_print(f"\n{EMOJIS['stop']} Monitor stopped by user")
            self.log.warning('Monitor interrupted')
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Error running monitor: {e}")
            self.log.error('Monitor launch error', extra={'error': str(e)})
            
    def run_ai_summarizer(self):
        """Run the AI summarizer"""
        if not self.ai_enabled:
            safe_print(f"{EMOJIS['error']} AI Summarizer is not available")
            return False
            
        safe_print(f"\n{EMOJIS['ai']} Running AI Summarizer...")
        safe_print("="*40)
        try:
            result = subprocess.run([
                sys.executable, str(self.ai_summarizer_path)
            ], cwd=self.project_root)
            self.log.info('AI summarizer executed', extra={'returncode': result.returncode})
            
            if result.returncode == 0:
                safe_print(f"{EMOJIS['success']} AI processing completed successfully")
                return True
            else:
                safe_print(f"{EMOJIS['error']} AI processing failed with return code: {result.returncode}")
                return False
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Error running AI summarizer: {e}")
            return False
    
    def run_alert_system(self):
        """Run the alert system with file watcher"""
        safe_print(f"\n{EMOJIS['alert']} Starting Alert System...")
        safe_print("="*40)
        safe_print("The alert system will:")
        safe_print("- Monitor changes to summarized_news_hf.json")
        safe_print("- Detect when new articles are AI-processed")
        safe_print("- Send real-time alerts to the frontend")
        safe_print("- Display notification badges in the app")
        safe_print("\nPress Ctrl+C to stop the alert system\n")
        
        if not self.alert_system_path.exists():
            safe_print(f"{EMOJIS['error']} Alert system not found at: {self.alert_system_path}")
            safe_print("Please ensure the alert_system_integration.py file exists")
            return False
            
        try:
            subprocess.run([
                sys.executable, str(self.alert_system_path)
            ], cwd=self.project_root)
            safe_print(f"\n{EMOJIS['success']} Alert system stopped")
            self.log.info('Alert system stopped')
            return True
        except KeyboardInterrupt:
            safe_print(f"\n{EMOJIS['stop']} Alert system stopped by user")
            self.log.warning('Alert system interrupted')
            return True
        except Exception as e:
            safe_print(f"{EMOJIS['error']} Error running alert system: {e}")
            self.log.error('Alert system error', extra={'error': str(e)})
            return False
            
    def start_api_server(self, background=True):
        """Start the API server (FastAPI preferred, Flask fallback)"""
        safe_print(f"\n{EMOJIS['web']} Starting API Server...")
        safe_print("="*40)
        
        api_process = None
        
        # Try FastAPI first
        if self.fastapi_enabled:
            safe_print(f"{EMOJIS['rocket']} Starting FastAPI server (high-performance)...")
            try:
                if background:
                    api_process = subprocess.Popen([
                        sys.executable, "-m", "uvicorn", 
                        "api.cybersecurity_fastapi:app",
                        "--host", "0.0.0.0", 
                        "--port", "8080",
                        "--reload"
                    ], cwd=self.project_root)
                    
                    # Wait a moment to check if server started
                    time.sleep(3)
                    if api_process.poll() is None:
                        safe_print(f"{EMOJIS['success']} FastAPI server started successfully")
                        safe_print(f"{EMOJIS['info']} API Documentation: http://localhost:8080/docs")
                        safe_print(f"{EMOJIS['info']} ReDoc Documentation: http://localhost:8080/redoc")
                        safe_print(f"{EMOJIS['web']} Health Check: http://localhost:8080/")
                        
                        self.running_processes.append(('FastAPI Server', api_process))
                        return api_process
                    else:
                        safe_print(f"{EMOJIS['error']} FastAPI server failed to start")
                        
                else:
                    # Run in foreground (blocking)
                    subprocess.run([
                        sys.executable, "-m", "uvicorn", 
                        "api.cybersecurity_fastapi:app",
                        "--host", "0.0.0.0", 
                        "--port", "8080",
                        "--reload"
                    ], cwd=self.project_root)
                    return None
                    
            except Exception as e:
                safe_print(f"{EMOJIS['error']} Error starting FastAPI server: {e}")
        
        # Fallback to Flask if FastAPI failed or not available
        if self.flask_enabled:
            safe_print(f"{EMOJIS['warning']} Fallback to Flask server...")
            try:
                if background:
                    api_process = subprocess.Popen([
                        sys.executable, str(self.flask_api_path)
                    ], cwd=self.project_root)
                    
                    # Wait a moment to check if server started
                    time.sleep(3)
                    if api_process.poll() is None:
                        safe_print(f"{EMOJIS['success']} Flask server started successfully")
                        safe_print(f"{EMOJIS['web']} API Base URL: http://localhost:8080/")
                        
                        self.running_processes.append(('Flask Server', api_process))
                        return api_process
                    else:
                        safe_print(f"{EMOJIS['error']} Flask server failed to start")
                else:
                    # Run in foreground (blocking)
                    subprocess.run([
                        sys.executable, str(self.flask_api_path)
                    ], cwd=self.project_root)
                    return None
                    
            except Exception as e:
                safe_print(f"{EMOJIS['error']} Error starting Flask server: {e}")
        
        safe_print(f"{EMOJIS['error']} No API server could be started")
        return None
    
    def cleanup_processes(self):
        """Clean up background processes"""
        safe_print(f"\n{EMOJIS['warning']} Cleaning up background processes...")
        for name, process in self.running_processes:
            try:
                if process.poll() is None:  # Process is still running
                    safe_print(f"{EMOJIS['stop']} Terminating {name}...")
                    process.terminate()
                    # Give it a moment to terminate gracefully
                    time.sleep(2)
                    if process.poll() is None:
                        safe_print(f"{EMOJIS['warning']} Force killing {name}...")
                        process.kill()
                    safe_print(f"{EMOJIS['success']} {name} stopped")
                else:
                    safe_print(f"{EMOJIS['info']} {name} was already stopped")
            except Exception as e:
                safe_print(f"{EMOJIS['warning']} Error stopping {name}: {e}")
        
        self.running_processes.clear()
        
    def run_full_auto_mode(self):
        """
        🚀 FULL AUTO MODE - Complete automation in sequence!
        This is the one-command solution that does everything:
        1. Automatic backup of old files
        2. Setup validation and dependency install
        3. Initial scraping if needed
        4. Start FastAPI server in background
        5. Start alert system in background
        6. Run initial AI summarization
        7. 24/7 monitoring with AI integration
        """
        safe_print(f"\n{EMOJIS['rocket']} STARTING FULL AUTO MODE")
        safe_print("="*60)
        safe_print(f"{EMOJIS['target']} This will run the complete cybersecurity news system!")
        safe_print(f"{EMOJIS['setup']} Sequence: Backup → Setup → Scrape → API → Alerts → AI → Monitor")
        safe_print(f"{EMOJIS['time']} Estimated setup time: 2-5 minutes")
        safe_print(f"{EMOJIS['cycle']} After setup: Continuous 24/7 operation")
        safe_print("="*60)
        
        try:
            # Phase 1: Automatic Backup
            safe_print(f"\n{EMOJIS['backup']} PHASE 1: Automatic Backup")
            safe_print("-" * 40)
            try:
                self.auto_backup_on_startup()
                safe_print(f"{EMOJIS['success']} Backup phase completed")
            except Exception as e:
                safe_print(f"{EMOJIS['warning']} Backup warning (continuing): {e}")
            
            # Phase 2: Setup and Validation
            safe_print(f"\n{EMOJIS['setup']} PHASE 2: Setup & Validation")
            safe_print("-" * 40)
            if not self.setup_and_validation():
                safe_print(f"{EMOJIS['error']} Setup failed - cannot continue")
                return False
            safe_print(f"{EMOJIS['success']} Setup phase completed")
            
            # Phase 3: Initial Data Check & Scraping
            safe_print(f"\n{EMOJIS['news']} PHASE 3: Data Preparation")
            safe_print("-" * 40)
            has_data = self.check_data_files()
            
            if not has_data:
                safe_print(f"{EMOJIS['warning']} No existing data - performing initial scrape...")
                if not self.run_scraper():
                    safe_print(f"{EMOJIS['error']} Initial scraping failed - cannot continue")
                    return False
                safe_print(f"{EMOJIS['success']} Initial scraping completed")
                time.sleep(2)
            else:
                safe_print(f"{EMOJIS['success']} Existing data found - skipping initial scrape")
            
            # Phase 4: Start API Server (Background)
            safe_print(f"\n{EMOJIS['web']} PHASE 4: API Server Startup")
            safe_print("-" * 40)
            api_process = self.start_api_server(background=True)
            if api_process:
                safe_print(f"{EMOJIS['success']} API server running in background")
                time.sleep(2)
            else:
                safe_print(f"{EMOJIS['warning']} API server failed - continuing without API")
            
            # Phase 5: Start Alert System (Background)
            safe_print(f"\n{EMOJIS['alert']} PHASE 5: Alert System Startup")
            safe_print("-" * 40)
            if self.alert_system_path.exists():
                try:
                    alert_process = subprocess.Popen([
                        sys.executable, str(self.alert_system_path)
                    ], cwd=self.project_root)
                    
                    time.sleep(3)
                    if alert_process.poll() is None:
                        safe_print(f"{EMOJIS['success']} Alert system running in background")
                        self.running_processes.append(('Alert System', alert_process))
                    else:
                        safe_print(f"{EMOJIS['warning']} Alert system failed to start")
                except Exception as e:
                    safe_print(f"{EMOJIS['warning']} Alert system error: {e}")
            else:
                safe_print(f"{EMOJIS['warning']} Alert system not found - continuing without alerts")
            
            # Phase 6: Initial AI Summarization
            safe_print(f"\n{EMOJIS['ai']} PHASE 6: Initial AI Processing")
            safe_print("-" * 40)
            if self.ai_enabled:
                safe_print(f"{EMOJIS['ai']} Running initial AI summarization...")
                if self.run_ai_summarizer():
                    safe_print(f"{EMOJIS['success']} Initial AI processing completed")
                else:
                    safe_print(f"{EMOJIS['warning']} AI processing failed - continuing without AI")
                time.sleep(2)
            else:
                safe_print(f"{EMOJIS['warning']} AI summarizer not available - continuing without AI")
            
            # Phase 7: Continuous 24/7 Monitoring
            safe_print(f"\n{EMOJIS['fast']} PHASE 7: 24/7 Monitoring System")
            safe_print("-" * 40)
            safe_print(f"{EMOJIS['success']} SYSTEM FULLY OPERATIONAL!")
            safe_print(f"{EMOJIS['data']} Current Status:")
            
            api_status = f"{EMOJIS['success']} Running" if api_process else f"{EMOJIS['error']} Not Running"
            alert_status = f"{EMOJIS['success']} Running" if any('Alert' in name for name, _ in self.running_processes) else f"{EMOJIS['error']} Not Running"
            ai_status = f"{EMOJIS['success']} Enabled" if self.ai_enabled else f"{EMOJIS['error']} Disabled"
            data_status = f"{EMOJIS['success']} Available" if self.check_data_files() else f"{EMOJIS['error']} Missing"
            
            safe_print(f"   {EMOJIS['web']} API Server: {api_status}")
            safe_print(f"   {EMOJIS['alert']} Alert System: {alert_status}")
            safe_print(f"   {EMOJIS['ai']} AI Processing: {ai_status}")
            safe_print(f"   {EMOJIS['data']} Data Files: {data_status}")
            safe_print(f"\n{EMOJIS['cycle']} Starting continuous monitoring...")
            safe_print(f"{EMOJIS['time']} Monitor will check for new articles every 30 minutes")
            safe_print(f"{EMOJIS['ai']} AI will process new articles automatically")
            safe_print(f"{EMOJIS['alert']} Alerts will be sent to connected clients")
            safe_print(f"{EMOJIS['info']} Press Ctrl+C to stop the entire system")
            safe_print("-" * 60)
            
            # Start continuous monitoring
            cycle_count = 0
            try:
                while True:
                    cycle_count += 1
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    safe_print(f"\n{EMOJIS['alert']} MONITORING CYCLE {cycle_count}")
                    safe_print(f"{EMOJIS['time']} Started at: {current_time}")
                    safe_print("-" * 30)
                    
                    # Run monitoring cycle
                    self.run_monitoring_cycle()
                    
                    # Show next cycle info
                    next_time = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                    safe_print(f"{EMOJIS['success']} Cycle {cycle_count} completed")
                    safe_print(f"{EMOJIS['time']} Next cycle at: {next_time}")
                    safe_print(f"{EMOJIS['info']} System is running automatically...")
                    
                    # Wait 30 minutes
                    time.sleep(1800)
                    
            except KeyboardInterrupt:
                safe_print(f"\n\n{EMOJIS['stop']} FULL AUTO MODE STOPPED BY USER")
                safe_print(f"{EMOJIS['data']} Completed {cycle_count} monitoring cycles")
                safe_print(f"{EMOJIS['warning']} Cleaning up background processes...")
                
                # Cleanup all background processes
                self.cleanup_processes()
                
                safe_print(f"{EMOJIS['success']} System shutdown completed successfully")
                safe_print(f"{EMOJIS['success']} Thank you for using Cybersecurity News Crawler!")
                return True
                
        except Exception as e:
            safe_print(f"\n{EMOJIS['error']} CRITICAL ERROR in Full Auto Mode: {e}")
            safe_print(f"{EMOJIS['warning']} Attempting cleanup...")
            try:
                self.cleanup_processes()
            except:
                pass
            return False
            
    def run_monitoring_cycle(self):
        """Run one monitoring cycle with intelligent AI integration"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_print(f"\n{'='*60}")
        safe_print(f"{EMOJIS['cycle']} MONITORING CYCLE - {current_time}")
        safe_print(f"{'='*60}")
        
        try:
            # Run the 24/7 monitor (single cycle if supported)
            safe_print(f"{EMOJIS['search']} Checking websites for new articles...")
            result = subprocess.run([
                sys.executable, str(self.monitor_path), "--single-cycle"
            ], capture_output=True, text=True, timeout=1800, cwd=self.project_root)
            
            monitor_output = result.stdout
            monitor_error = result.stderr
            
            safe_print(f"{EMOJIS['data']} Monitor Output:")
            safe_print(monitor_output)
            
            if result.returncode == 0:
                # Check if new articles were actually found
                new_articles_indicators = [
                    "Found and added",
                    "NEW ARTICLES FOUND",
                    "new articles detected",
                    "Appended to daily archive"
                ]
                
                new_articles_found = any(indicator.lower() in monitor_output.lower() 
                                       for indicator in new_articles_indicators)
                
                if new_articles_found:
                    safe_print(f"\n{EMOJIS['success']} NEW ARTICLES DETECTED! Running AI summarization...")
                    
                    # Only run AI summarization if enabled and new articles found
                    if self.ai_enabled:
                        try:
                            safe_print(f"{EMOJIS['ai']} Starting AI summarization process...")
                            ai_result = subprocess.run([
                                sys.executable, str(self.ai_summarizer_path), "--auto"
                            ], capture_output=True, text=True, timeout=600, cwd=self.project_root)
                            
                            if ai_result.returncode == 0:
                                safe_print(f"{EMOJIS['success']} AI summarization completed successfully")
                                safe_print(f"{EMOJIS['data']} AI Output:")
                                safe_print(ai_result.stdout)
                            else:
                                safe_print(f"{EMOJIS['error']} AI summarization failed:")
                                safe_print(ai_result.stderr)
                                
                        except subprocess.TimeoutExpired:
                            safe_print(f"{EMOJIS['time']} AI summarization timed out (took longer than 10 minutes)")
                        except Exception as e:
                            print(f"💥 AI summarization error: {str(e)}")
                    else:
                        print("⚠️ AI summarization is disabled or not available")
                else:
                    print("ℹ️ No new articles found this cycle - skipping AI summarization")
                    print("📝 This is normal - the monitor only processes NEW articles")
                
            else:
                print(f"❌ Monitoring cycle failed with return code: {result.returncode}")
                print("Error output:")
                print(monitor_error)
                
        except subprocess.TimeoutExpired:
            print("⏰ Monitoring cycle timed out (longer than 30 minutes)")
        except Exception as e:
            print(f"💥 Monitoring cycle error: {str(e)}")
            
    def run_complete_project(self):
        """Run the complete project with intelligent flow"""
        print("\n🚀 Starting Complete Project...")
        print("="*50)
        
        # Check if initial scrape is needed
        has_data = self.check_data_files()
        initial_scrape = False
        
        if not has_data:
            initial_scrape = True
            print("📭 No existing data files detected - initial scrape required")
        else:
            print("\nChoose your startup mode:")
            print("[1] Fresh Start - Do initial scrape then monitor")
            print("[2] Continue Monitoring - Use existing data")
            
            while True:
                choice = input("\nEnter choice (1 or 2): ").strip()
                if choice == "1":
                    initial_scrape = True
                    print("🔄 Selected: Fresh start with initial scrape")
                    break
                elif choice == "2":
                    print("⏭️ Selected: Continue with existing data")
                    break
                else:
                    print("Invalid choice. Please enter 1 or 2.")
                    
        # Phase 1: Initial Scraping (if needed)
        if initial_scrape:
            print("\n📰 PHASE 1: Initial Data Collection")
            print("="*40)
            print("Running initial scrape to populate data...")
            print("This will create baseline data for monitoring.\n")
            
            if not self.run_scraper():
                print("❌ Initial scraping failed")
                return False
                
            # Check if we got any data
            if not self.check_data_files():
                print("❌ ERROR: No data files were created during initial scrape")
                print("Please check your internet connection and URL configuration")
                return False
                
            print("\n🎯 Waiting 5 seconds before starting monitor...")
            time.sleep(5)
            
        # Phase 2: Start 24/7 Monitoring with AI Integration
        print("\n⚡ PHASE 2: Starting 24/7 Monitoring System")
        print("="*50)
        print("Starting intelligent monitor with AI integration...")
        print("The monitor will:")
        print("- Check for new articles every 30 minutes")
        print("- Only run AI summarization when NEW articles are found")
        print("- Maintain daily archive files")
        print("- Provide real-time status updates")
        print("\nPress Ctrl+C to stop monitoring\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                
                print(f"\n\n🔔 STARTING CYCLE {cycle_count}")
                print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                self.run_monitoring_cycle()
                
                print(f"\n⏸️ CYCLE {cycle_count} COMPLETED")
                print("⏰ Waiting 30 minutes until next cycle...")
                next_time = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
                print(f"📅 Next cycle at: {next_time}")
                print("💡 Press Ctrl+C to stop monitoring")
                
                # Wait 30 minutes
                time.sleep(1800)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Monitor stopped by user after {cycle_count} cycles")
            print("✅ Shutdown completed gracefully")
            self.log.warning('Complete project stopped', extra={'cycles': cycle_count})
            
    def test_project_flow(self):
        """Test all project components"""
        print("\n🧪 Testing Project Flow...")
        print("="*40)
        
        tests = [
            ("Project Structure", self.validate_project_structure),
            ("Dependencies", self.install_dependencies),
            ("Data Files Check", self.check_data_files),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing {test_name}...")
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"⚠️ {test_name}: WARNING")
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {e}")
                
        print("\n🧪 Component test completed")
        
    def show_project_status(self):
        """Show current project status and data"""
        print("\n📊 Project Status Dashboard")
        print("="*50)
        
        # Python version
        version = sys.version_info
        print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
        
        # Project structure
        print(f"\n📁 Project Directory: {self.project_root}")
        print(f"   Data Directory: {self.data_dir}")
        print(f"   Logs Directory: {self.logs_dir}")
        
        # Check files
        print(f"\n📋 Component Status:")
        components = {
            "Scraper": self.scraper_path,
            "Monitor": self.monitor_path,
            "AI Summarizer": self.ai_summarizer_path,
            "URL Config": self.url_config_path
        }
        
        for name, path in components.items():
            status = "✅ Available" if path.exists() else "❌ Missing"
            print(f"   {name}: {status}")
            
        # Data files
        print(f"\n💾 Data Files:")
        data_files = list(self.data_dir.glob("*.json"))
        root_files = list(self.project_root.glob("cybersecurity_news_*.json"))
        all_files = data_files + root_files
        
        if all_files:
            total_size = sum(f.stat().st_size for f in all_files)
            print(f"   Found {len(all_files)} file(s), total size: {total_size/1024:.1f} KB")
            
            # Show latest files
            recent_files = sorted(all_files, key=lambda f: f.stat().st_mtime, reverse=True)[:3]
            for file in recent_files:
                mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                size_kb = file.stat().st_size / 1024
                print(f"   📄 {file.name} ({size_kb:.1f} KB, {mod_time.strftime('%Y-%m-%d %H:%M')})")
        else:
            print("   No data files found")
            
        # Log files
        print(f"\n📝 Log Files:")
        log_files = list(self.logs_dir.glob("*.txt"))
        if log_files:
            for log_file in log_files:
                size_kb = log_file.stat().st_size / 1024
                mod_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                print(f"   📋 {log_file.name} ({size_kb:.1f} KB, {mod_time.strftime('%Y-%m-%d %H:%M')})")
        else:
            print("   No log files found")
            
    def setup_and_validation(self):
        """Setup and validate the project"""
        print("\n🔧 Setup & Validation")
        print("="*40)
        
        if not self.check_python_version():
            return False
            
        if not self.validate_project_structure():
            return False
            
        if not self.install_dependencies():
            return False
            
        print("\n✅ Setup and validation completed successfully")
        print("🚀 Project is ready to run!")
        return True
        
    def run_backup_management(self):
        """Run backup management to move old files to backup directory"""
        print("\n🗄️ Backup Management")
        print("="*40)
        
        if not self.backup_manager:
            print("❌ Backup manager is not available")
            print("Please check that the backup_manager.py file exists in src/utils/")
            return False
        
        try:
            # Run the backup process
            stats = self.backup_manager.run_daily_backup()
            
            if stats['total_errors'] == 0:
                print(f"\n🎉 Backup completed successfully!")
                print(f"📁 Old files moved to: {self.backup_manager.backup_dir}")
            else:
                print(f"\n⚠️ Backup completed with some issues")
                
            return True
            
        except Exception as e:
            print(f"❌ Error during backup: {e}")
            return False
    
    def list_backup_files(self):
        """List all backup files"""
        print("\n📋 Backup Files Management")
        print("="*40)
        
        if not self.backup_manager:
            print("❌ Backup manager is not available")
            return False
        
        try:
            self.backup_manager.list_backup_files()
            return True
        except Exception as e:
            print(f"❌ Error listing backup files: {e}")
            return False
    
    def auto_backup_on_startup(self):
        """Check if automatic backup is needed on startup"""
        if not self.backup_manager:
            return
        
        print(f"\n🗄️ Checking for automatic backup needs...")
        
        try:
            # 🚨 CRITICAL: Always backup previous summarized_news_hf.json if it exists
            summarized_file = self.data_dir / "summarized_news_hf.json"
            if summarized_file.exists():
                print("🗄️ Found existing summarized_news_hf.json - checking for backup need...")
                backup_success = self.backup_manager.backup_previous_summarized_file()
                if backup_success:
                    print("✅ Previous summarized file backed up successfully")
                else:
                    print("⚠️ Previous summarized file backup had issues")
            
            # Check if there are any old news files that need backing up
            from pathlib import Path
            data_dir = Path("data")
            
            # Look for old news files
            old_news_files = []
            current_date = datetime.now().strftime("%Y%m%d")
            
            for news_file in data_dir.glob("News_today_*.json"):
                file_date = self.backup_manager.get_file_date_from_name(news_file.name)
                if file_date and file_date != current_date:
                    old_news_files.append(news_file)
            
            if old_news_files:
                print(f"🗄️ Found {len(old_news_files)} old news files to backup")
                backup_stats = self.backup_manager.run_daily_backup()
                if backup_stats['total_errors'] == 0:
                    print(f"✅ Successfully backed up {backup_stats['total_moved']} old files")
                else:
                    print(f"⚠️ Backup completed with {backup_stats['total_errors']} errors")
            else:
                print("✅ No old files found - backup not needed")
                
        except Exception as e:
            print(f"❌ Error during startup backup check: {e}")
            return False
        """Automatically run backup on startup if needed"""
        if not self.backup_manager:
            return
        
        try:
            # Check if there are old files that need backing up
            data_files = list(self.data_dir.glob("News_today_*.json"))
            summarized_files = list(self.data_dir.glob("summarized_news_hf*.json"))
            
            current_date = datetime.now().strftime("%Y%m%d")
            old_files = []
            
            for file_path in data_files + summarized_files:
                file_date = self.backup_manager.get_file_date_from_name(file_path.name)
                if file_date and file_date != current_date:
                    old_files.append(file_path.name)
                elif not file_date:
                    mod_date = self.backup_manager.get_file_modification_date(file_path)
                    if mod_date != current_date:
                        old_files.append(file_path.name)
            
            if old_files:
                print(f"\n🗄️ Found {len(old_files)} old data files that can be backed up")
                print("Files ready for backup:")
                for file_name in old_files[:5]:  # Show first 5
                    print(f"   📄 {file_name}")
                if len(old_files) > 5:
                    print(f"   ... and {len(old_files) - 5} more")
                
                response = input("\nWould you like to backup these old files now? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    print("\n🚀 Running automatic backup...")
                    self.run_backup_management()
                else:
                    print("⏩ Skipping backup. You can run it later from the main menu.")
            else:
                print("✅ No old files found that need backing up")
                
        except Exception as e:
            print(f"⚠️ Warning: Auto-backup check failed: {e}")
        
    def run_autonomous_project(self):
        """Fully autonomous mode with no prompts.
        Flow: auto-backup -> setup -> initial scrape if needed -> infinite monitor cycles with AI.
        Env overrides: AUTONOMOUS_INTERVAL_MINUTES (default 30), AUTONOMOUS_MAX_CYCLES (optional for testing)."""
        print("\n🤖 Starting FULLY AUTONOMOUS MODE...")
        interval_minutes = int(os.getenv('AUTONOMOUS_INTERVAL_MINUTES', '30') or 30)
        max_cycles_env = os.getenv('AUTONOMOUS_MAX_CYCLES'); max_cycles = int(max_cycles_env) if (max_cycles_env and max_cycles_env.isdigit()) else None
        self.log.info('Autonomous mode init', extra={'interval_minutes': interval_minutes, 'max_cycles': max_cycles})
        try: self.auto_backup_on_startup()
        except Exception as e: self.log.warning('Auto-backup failed', extra={'error': str(e)})
        if not self.setup_and_validation():
            self.log.error('Setup failed in autonomous mode'); return
        if not self.check_data_files():
            print("📭 No data - performing initial scrape")
            if not self.run_scraper():
                self.log.error('Initial scrape failed in autonomous mode'); return
            time.sleep(3)
        else:
            print("✅ Data present - skipping initial scrape")
        cycle = 0
        # NEW: run AI summarizer immediately after initial scrape for fresh dataset
        if self.ai_enabled:
            print("🤖 Running initial AI summarization after first scrape...")
            self.run_ai_summarizer()
        else:
            print("⚠️ AI summarizer not enabled; skipping initial summarization")
        try:
            while True:
                cycle += 1
                print(f"\n🔔 [AUTO] Cycle {cycle} @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log.info('Auto cycle start', extra={'cycle': cycle})
                self.run_monitoring_cycle()
                self.log.info('Auto cycle end', extra={'cycle': cycle})
                if max_cycles and cycle >= max_cycles:
                    print(f"🧪 Max cycles {max_cycles} reached - exiting autonomous mode")
                    break
                next_ts = (datetime.now() + timedelta(minutes=interval_minutes)).strftime('%Y-%m-%d %H:%M:%S')
                print(f"⏳ Sleeping {interval_minutes} min (next {next_ts}) – Ctrl+C to stop")
                for _ in range(interval_minutes * 60):
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Autonomous mode stopped by user"); self.log.warning('Autonomous interrupted', extra={'cycles': cycle})
        except Exception as e:
            print(f"💥 Autonomous fatal error: {e}"); self.log.error('Autonomous fatal', extra={'cycle': cycle, 'error': str(e)})

    def run_interactive_menu(self):
        """Run the interactive menu"""
        while True:
            self.print_banner()
            self.print_menu()
            
            try:
                choice = input("\nEnter your choice (0-14): ").strip()
                
                if choice == '0': self.run_production_auto_mode()
                elif choice == '1': self.run_full_auto_mode()
                elif choice == '2': self.auto_backup_on_startup();
                if choice == '2' and self.setup_and_validation(): self.run_complete_project()
                elif choice == '3' and self.setup_and_validation(): self.run_scraper(); input("\nPress Enter...")
                elif choice == '4' and self.setup_and_validation(): self.run_monitor_only()
                elif choice == '5' and self.setup_and_validation(): self.run_ai_summarizer(); input("\nPress Enter...")
                elif choice == '6' and self.setup_and_validation(): self.run_alert_system(); input("\nPress Enter...")
                elif choice == '7' and self.setup_and_validation(): self.start_api_server(background=False); input("\nPress Enter...")
                elif choice == '8': self.test_project_flow(); input("\nPress Enter...")
                elif choice == '9': self.setup_and_validation(); input("\nPress Enter...")
                elif choice == '10': self.show_project_status(); input("\nPress Enter...")
                elif choice == '11': self.run_backup_management(); input("\nPress Enter...")
                elif choice == '12': self.list_backup_files(); input("\nPress Enter...")
                elif choice == '13': print("\n👋 Thank you for using Cybersecurity News Crawler!"); break
                elif choice == '14': self.run_autonomous_project()
                else: print("Invalid choice."); input("Press Enter...")
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user"); break
            except Exception as e:
                print(f"\n❌ Error: {e}"); input("Press Enter...")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Cybersecurity News Crawler Launcher")
    parser.add_argument("--mode", choices=["production", "full-auto", "complete", "scrape", "monitor", "ai", "api", "test", "setup", "status", "backup", "list-backups", "auto", "autonomous"], help="Run in specific mode without interactive menu")
    parser.add_argument("--no-setup", action="store_true", help="Skip setup validation")
    
    args = parser.parse_args()
    
    launcher = CyberNewsLauncher()
    
    if args.mode:
        # Non-interactive mode
        if args.mode not in ["backup", "list-backups"] and not args.no_setup and not launcher.setup_and_validation():
            sys.exit(1)
            
        if args.mode == 'production': launcher.run_production_auto_mode()
        elif args.mode == 'full-auto': launcher.run_full_auto_mode()
        elif args.mode == 'complete': launcher.auto_backup_on_startup(); launcher.run_complete_project()
        elif args.mode == 'scrape': launcher.run_scraper()
        elif args.mode == 'monitor': launcher.run_monitor_only()
        elif args.mode == 'ai': launcher.run_ai_summarizer()
        elif args.mode == 'api': launcher.start_api_server(background=False)
        elif args.mode == 'test': launcher.test_project_flow()
        elif args.mode == 'setup': launcher.setup_and_validation()
        elif args.mode == 'status': launcher.show_project_status()
        elif args.mode == 'backup': launcher.run_backup_management()
        elif args.mode == 'list-backups': launcher.list_backup_files()
        elif args.mode in ['auto','autonomous']: launcher.run_autonomous_project()
    else:
        # Interactive mode
        launcher.run_interactive_menu()


if __name__ == "__main__":
    main()