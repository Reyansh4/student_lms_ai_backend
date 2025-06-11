import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Create logs directory if it doesn't exist
log_dir = settings.LOG_DIR
log_dir.mkdir(exist_ok=True)

# Log format
log_format = logging.Formatter(settings.LOG_FORMAT)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name (str): The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Remove existing handlers to avoid duplicate logs
    logger.handlers = []

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = RotatingFileHandler(
        filename=log_dir / settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger

# Create a default logger instance
logger = get_logger(__name__) 