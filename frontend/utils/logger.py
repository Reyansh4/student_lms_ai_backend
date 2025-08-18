"""
Unified logging utility for frontend that writes to the same app.log file as backend
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os

# Get the project root directory (two levels up from frontend/utils/)
project_root = Path(__file__).parent.parent.parent
log_dir = project_root / "logs"
log_file = log_dir / "app.log"

# Create logs directory if it doesn't exist
log_dir.mkdir(exist_ok=True)

# Log format matching backend
log_format = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def get_frontend_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for frontend components that writes to the unified app.log file.
    
    Args:
        name (str): The name of the logger (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(f"frontend.{name}")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicate logs
    logger.handlers = []

    # Console Handler (for terminal output)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler (writes to the same app.log as backend)
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    return logger

# Create a default frontend logger
frontend_logger = get_frontend_logger(__name__)
