# app/utils/logger.py
"""
Centralized Logging System
Provides structured logging with file and console output.
"""

import logging
import sys

# Force UTF-8 on Windows for emoji support
# if sys.platform == "win32":
#     sys.stdout.reconfigure(encoding='utf-8', errors='replace')
#     sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from datetime import datetime
import os

# ============================================
# LOGGING CONFIGURATION
# ============================================

# Create logs directory
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Create sessions directory
SESSIONS_DIR = LOGS_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# ============================================
# CUSTOM FORMATTER WITH COLORS
# ============================================

class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors for console output.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


# ============================================
# MAIN LOGGER SETUP
# ============================================

def setup_logger(name: str = "honeypot") -> logging.Logger:
    """
    Set up the main application logger.
    
    Features:
    - Console output with colors
    - File output (app.log) with rotation
    - Error-only file (error.log)
    - Structured format with timestamps
    
    Args:
        name: Logger name (default: "honeypot")
        
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # ============================================
    # CONSOLE HANDLER (colored output)
    # ============================================
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    console_format = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # ============================================
    # FILE HANDLER (all logs)
    # ============================================
    
    file_handler = logging.FileHandler(
        LOGS_DIR / "app.log",
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # ============================================
    # ERROR FILE HANDLER (errors only)
    # ============================================
    
    error_handler = logging.FileHandler(
        LOGS_DIR / "error.log",
        mode='a',
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    
    # ============================================
    # ADD HANDLERS TO LOGGER
    # ============================================
    
    logger.addHandler(console_handler)
    # logger.addHandler(file_handler)  # Disabled for Hackathon
    # logger.addHandler(error_handler) # Disabled for Hackathon
    
    return logger


# ============================================
# SESSION-SPECIFIC LOGGER
# ============================================

def get_session_logger(session_id: str) -> logging.Logger:
    """
    Create a session-specific logger.
    
    Logs to: logs/sessions/session-{session_id}.log
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Logger instance for this session
    """
    
    logger_name = f"session_{session_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Session-specific file
    session_file = SESSIONS_DIR / f"session-{session_id}.log"
    
    handler = logging.FileHandler(
        session_file,
        mode='a',
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


# ============================================
# PERFORMANCE LOGGING
# ============================================

class PerformanceLogger:
    """
    Context manager for logging execution time.
    
    Usage:
        with PerformanceLogger("Detection Agent"):
            result = detect_scam(text)
    """
    
    def __init__(self, operation: str, logger: logging.Logger = None):
        self.operation = operation
        self.logger = logger or setup_logger()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"START: {self.operation} - Starting")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.debug(f"OK: {self.operation} - Completed in {duration:.3f}s")
        else:
            self.logger.error(f"ERR: {self.operation} - Failed after {duration:.3f}s: {exc_val}")
        
        return False  # Don't suppress exceptions


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def log_request(session_id: str, message: str):
    """Log incoming request"""
    logger = setup_logger()
    logger.info(f"REQ: Request [{session_id}]: {message[:100]}...")


def log_response(session_id: str, response: str):
    """Log outgoing response"""
    logger = setup_logger()
    logger.info(f"RES: Response [{session_id}]: {response[:100]}...")


def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    logger = setup_logger()
    logger.error(f"ERROR: Error {context}: {str(error)}", exc_info=True)


def log_intelligence(session_id: str, intelligence: dict):
    """Log extracted intelligence"""
    logger = setup_logger()
    
    items_count = sum(
        len(v) for v in intelligence.values() 
        if isinstance(v, list)
    )
    
    logger.info(f"INTEL: Extracted [{session_id}]: {items_count} items - {intelligence}")


# ============================================
# INITIALIZE DEFAULT LOGGER
# ============================================

# Create default logger instance
logger = setup_logger()