"""Heartbeat writer to signal liveness to external supervisor."""
from __future__ import annotations
import json, time, threading, os
from pathlib import Path

class Heartbeat:
    def __init__(self, path: str = 'logs/heartbeat.json', interval: int = 300):
        self.path = Path(path)
        self.interval = interval
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.thread.start()

    def _run(self):
        while not self._stop.is_set():
            payload = {
                'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'pid': os.getpid(),
                'status': 'alive'
            }
            try:
                with open(self.path, 'w', encoding='utf-8') as f:
                    json.dump(payload, f)
            except Exception:
                pass
            self._stop.wait(self.interval)

    def stop(self):
        self._stop.set()
        self.thread.join(timeout=2)
