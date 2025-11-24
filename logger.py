import logging
import sys
from config import Config

# Map string log levels to logging constants
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    grey = "\x1b[38;21m"
    cyan = "\x1b[36m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_str = "[%(asctime)s] %(levelname)s %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: cyan + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger():
    logger = logging.getLogger('AmaranthBot')
    
    # Set level
    level = LOG_LEVEL_MAP.get(Config.LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    # Create console handler
    # Force UTF-8 for console output to avoid cp949 errors on Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
        
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    # Set formatter
    ch.setFormatter(CustomFormatter())

    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(ch)

    return logger

logger = setup_logger()
