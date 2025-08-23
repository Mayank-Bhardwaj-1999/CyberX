#!/usr/bin/env python3
"""
Progress Indicator Utility
Simple, clean progress indicators for terminal operations
"""

import sys
import time
import threading
from typing import Optional


class ProgressIndicator:
    """Simple progress indicator that shows completion percentage"""
    
    def __init__(self, total: int, description: str = "Progress", show_percentage: bool = True):
        self.total = total
        self.current = 0
        self.description = description
        self.show_percentage = show_percentage
        self.start_time = time.time()
        self._lock = threading.Lock()
        
    def update(self, increment: int = 1):
        """Update progress by increment amount"""
        with self._lock:
            self.current = min(self.current + increment, self.total)
            self._display()
    
    def set_progress(self, value: int):
        """Set absolute progress value"""
        with self._lock:
            self.current = min(max(value, 0), self.total)
            self._display()
    
    def _display(self):
        """Display current progress"""
        if self.total == 0:
            percentage = 100
        else:
            percentage = (self.current / self.total) * 100
        
        if self.show_percentage:
            # Clean single-line output
            sys.stdout.write(f"\r{self.description}: {percentage:.1f}% ({self.current}/{self.total})")
        else:
            sys.stdout.write(f"\r{self.description}: {self.current}/{self.total}")
        
        sys.stdout.flush()
        
        # Print newline when complete
        if self.current >= self.total:
            elapsed = time.time() - self.start_time
            print(f" - Completed in {elapsed:.1f}s")
    
    def finish(self):
        """Mark progress as complete"""
        self.set_progress(self.total)


class SpinnerIndicator:
    """Simple spinner for unknown duration tasks"""
    
    def __init__(self, description: str = "Processing"):
        self.description = description
        self.spinning = False
        self.spinner_chars = ['|', '/', '-', '\\']
        self.current_char = 0
        self._thread = None
        
    def start(self):
        """Start the spinner"""
        self.spinning = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the spinner"""
        self.spinning = False
        if self._thread:
            self._thread.join()
        # Clear the spinner line
        sys.stdout.write(f"\r{self.description}: Complete\n")
        sys.stdout.flush()
        
    def _spin(self):
        """Internal spinner animation"""
        while self.spinning:
            char = self.spinner_chars[self.current_char]
            sys.stdout.write(f"\r{self.description}: {char}")
            sys.stdout.flush()
            self.current_char = (self.current_char + 1) % len(self.spinner_chars)
            time.sleep(0.3)


class TaskProgressManager:
    """Manages progress for multiple tasks"""
    
    def __init__(self):
        self.tasks = {}
        self.current_task = None
        
    def start_task(self, task_name: str, total: Optional[int] = None, description: str = None):
        """Start a new task with progress tracking"""
        if description is None:
            description = task_name
            
        if total is not None:
            indicator = ProgressIndicator(total, description)
        else:
            indicator = SpinnerIndicator(description)
            indicator.start()
            
        self.tasks[task_name] = indicator
        self.current_task = task_name
        return indicator
        
    def update_task(self, task_name: str = None, increment: int = 1):
        """Update progress for a task"""
        if task_name is None:
            task_name = self.current_task
            
        if task_name in self.tasks:
            indicator = self.tasks[task_name]
            if isinstance(indicator, ProgressIndicator):
                indicator.update(increment)
                
    def finish_task(self, task_name: str = None):
        """Finish a task"""
        if task_name is None:
            task_name = self.current_task
            
        if task_name in self.tasks:
            indicator = self.tasks[task_name]
            if isinstance(indicator, ProgressIndicator):
                indicator.finish()
            elif isinstance(indicator, SpinnerIndicator):
                indicator.stop()
            del self.tasks[task_name]
            
        if self.current_task == task_name:
            self.current_task = None
            
    def finish_all(self):
        """Finish all active tasks"""
        for task_name in list(self.tasks.keys()):
            self.finish_task(task_name)


# Global instance for easy access
progress_manager = TaskProgressManager()
