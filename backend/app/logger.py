"""
Logging configuration for Nail RAG Service
"""
import logging
import sys
from typing import Optional

# Configure the root logger
def setup_logger(name: str = "nail_rag", level: str = "INFO") -> logging.Logger:
    """
    Setup and configure a centralized logger for the application.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Create formatter - simplified for cleaner output
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger

# Create default logger instance
logger = setup_logger()

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance. If name is provided, creates a child logger.
    
    Args:
        name: Optional logger name for child logger
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"nail_rag.{name}")
    return logger

