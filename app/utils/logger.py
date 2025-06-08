\
import logging
import os
from logging.handlers import RotatingFileHandler

# Define the logs directory and log file path
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

# Configure the root logger
logger = logging.getLogger('dune_companion_app')
logger.setLevel(logging.DEBUG)  # Set the default level for the logger

# Store handlers to allow for proper shutdown and re-initialization
_managed_handlers = []

def initialize_handlers():
    """
    Initializes and adds console and file handlers to the main application logger.
    Ensures the logs directory exists. Clears existing managed handlers before setup.
    """
    global _managed_handlers

    # If handlers are already managed and presumably active, no need to re-initialize.
    # The test fixture should call shutdown_logging() first for a clean state if re-init is desired.
    if _managed_handlers:
        return

    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Clear any handlers that might be on the logger from previous states.
    # This ensures we only have our managed handlers after this function.
    for handler in list(logger.handlers): # Iterate over a copy
        logger.removeHandler(handler)
    
    # _managed_handlers is confirmed to be empty here, or we would have returned earlier.

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Console output level
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    _managed_handlers.append(console_handler)

    # File Handler (Rotating)
    # Rotates logs when they reach 2MB, keeping up to 5 backup logs.
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # File output level
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    _managed_handlers.append(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance with the specified name,
    configured to be a child of the main application logger.
    Ensures handlers are initialized if they haven't been.
    """
    # If no managed handlers are set up (e.g., first call or after shutdown_logging)
    if not _managed_handlers:
        initialize_handlers()
    
    child_logger = logging.getLogger(f'dune_companion_app.{name}')
    return child_logger

def shutdown_logging():
    """
    Flushes, closes, and removes all managed handlers associated with the main application logger.
    This is important for releasing file locks and resetting state, especially during testing.
    """
    global _managed_handlers
    for handler in _managed_handlers:
        handler.flush() # Ensure all pending logs are written
        handler.close()
        logger.removeHandler(handler)
    _managed_handlers = [] # Clear the list of managed handlers

# Initial setup of handlers when the module is first imported.
initialize_handlers()

# Example usage (can be removed or commented out)
# if __name__ == '__main__':
#     logger.debug('This is a debug message.')
#     logger.info('This is an info message.')
#     logger.warning('This is a warning message.')
#     logger.error('This is an error message.')
#     logger.critical('This is a critical message.')
#     shutdown_logging() # Example of shutting down

