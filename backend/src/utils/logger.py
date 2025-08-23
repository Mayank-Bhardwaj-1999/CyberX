"""Central logging utility with optional JSON + rotation."""
from __future__ import annotations
import logging, os, json, time
from logging.handlers import RotatingFileHandler

_CACHE = {}

class JsonFormatter(logging.Formatter):
    def format(self, record):  # type: ignore[override]
        base = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(record.created)),
            'level': record.levelname,
            'msg': record.getMessage(),
            'logger': record.name,
        }
        if record.exc_info:
            base['exc_info'] = self.formatException(record.exc_info)
        for k, v in record.__dict__.items():
            if k not in logging.LogRecord.__dict__ and k not in base and not k.startswith('_'):
                try:
                    json.dumps(v)
                    base[k] = v
                except Exception:
                    base[k] = str(v)
        return json.dumps(base, ensure_ascii=False)

def get_logger(name: str = 'app'):
    if name in _CACHE:
        return _CACHE[name]
    level = os.getenv('LOG_LEVEL', 'INFO').upper()
    enable_structured = os.getenv('ENABLE_STRUCTURED_LOGGING', '0') == '1'
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    log_path = os.path.join(log_dir, 'backend.log')
    handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5, encoding='utf-8')
    handler.setFormatter(JsonFormatter() if enable_structured else logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s'))
    logger.addHandler(handler)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(ch)
    _CACHE[name] = logger
    logger.debug('Logger initialized', extra={'structured': enable_structured})
    return logger
