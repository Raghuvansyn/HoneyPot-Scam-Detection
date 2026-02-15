import logging
import sys
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
SESSIONS_DIR = LOGS_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m', 'INFO': '\033[32m', 'WARNING': '\033[33m',
        'ERROR': '\033[31m', 'CRITICAL': '\033[35m', 'RESET': '\033[0m',
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logger(name: str = "honeypot") -> logging.Logger:
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)
    if _logger.handlers:
        return _logger

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S',
    ))
    _logger.addHandler(console)
    return _logger


def get_session_logger(session_id: str) -> logging.Logger:
    logger_name = f"session_{session_id}"
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.DEBUG)
    if _logger.handlers:
        return _logger

    handler = logging.FileHandler(SESSIONS_DIR / f"session-{session_id}.log", mode='a', encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
    ))
    _logger.addHandler(handler)
    return _logger


class PerformanceLogger:
    def __init__(self, operation: str, _logger: logging.Logger = None):
        self.operation = operation
        self.logger = _logger or setup_logger()
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.debug(f"{self.operation} completed in {duration:.3f}s")
        else:
            self.logger.error(f"{self.operation} failed after {duration:.3f}s: {exc_val}")
        return False


def log_request(session_id: str, message: str):
    setup_logger().info(f"REQ [{session_id}]: {message[:100]}")

def log_response(session_id: str, response: str):
    setup_logger().info(f"RES [{session_id}]: {response[:100]}")

def log_error(error: Exception, context: str = ""):
    setup_logger().error(f"ERROR {context}: {error}", exc_info=True)

def log_intelligence(session_id: str, intelligence: dict):
    items = sum(len(v) for v in intelligence.values() if isinstance(v, list))
    setup_logger().info(f"INTEL [{session_id}]: {items} items")


logger = setup_logger()
