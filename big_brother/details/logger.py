import os
import time
import logging
import logging.handlers


def create_rotating_logger(log_path=None, no_console_log=False, log_name="mklog", level=logging.DEBUG):
    """Handy logger with timed rotating file"""
    # Logger
    logger = logging.getLogger(log_name)
    logger.setLevel(level)
    # Reset
    if logger.hasHandlers():
        logger.handlers.clear()
    # Define handlers
    if not no_console_log:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    if log_path:
        # Create log dir if needed
        log_path = os.path.abspath(log_path)
        log_dir = os.path.dirname(log_path)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        # File handler
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_path, when="midnight", interval=1, backupCount=7)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '[%(asctime)s %(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    return logger
