import pytest
import logging
import os
import time
from app.utils.logger import get_logger, shutdown_logging, initialize_handlers, LOG_FILE, LOGS_DIR

# Ensure the logs directory exists before any tests run, if not created by logger itself
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR, exist_ok=True)

@pytest.fixture(autouse=True)
def manage_logger_state(request):
    """Ensures logger is initialized before each test and shut down after."""
    shutdown_logging() # Clean slate before test
    initialize_handlers() # Initialize for the current test
    yield
    shutdown_logging() # Clean slate after test
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            time.sleep(0.1)
            try:
                os.remove(LOG_FILE)
            except PermissionError:
                print(f"Warning: Could not remove log file {LOG_FILE} after test.")


def test_get_logger_returns_logger_instance():
    """Test that get_logger returns a Logger instance."""
    logger = get_logger('test_module')
    assert isinstance(logger, logging.Logger)
    assert logger.name == 'dune_companion_app.test_module'

def test_logger_writes_to_file_and_console(caplog):
    """Test that the logger writes messages to the file and console (using caplog for console)."""
    logger_name = 'file_console_test_caplog'
    logger = get_logger(logger_name)
    # Ensure the logger itself is at a level that allows DEBUG messages to pass to handlers
    logger.setLevel(logging.DEBUG) 

    test_debug_msg = "This is a debug message for file (caplog test)."
    test_info_msg = "This is an info message for file and console (caplog test)."

    # Capture logs at the level of the console handler for the specific logger
    # The root logger 'dune_companion_app' has handlers, one of which is the console (INFO)
    # We want to see what messages from our specific child logger make it to the console via propagation
    with caplog.at_level(logging.INFO, logger='dune_companion_app'): # Capture from root to see propagated console msgs
        logger.debug(test_debug_msg) # Should go to file handler (DEBUG)
        logger.info(test_info_msg)  # Should go to file handler (DEBUG) and console handler (INFO)

    # Check console output via caplog records
    # We are interested in messages from our specific child logger that were INFO level or higher
    console_emitted_records = [rec for rec in caplog.records if rec.name == logger.name and rec.levelname == 'INFO']
    assert any(test_info_msg in rec.message for rec in console_emitted_records), \
        f"Info message '{test_info_msg}' should be in caplog INFO records for logger {logger.name}. Records: {caplog.text}"
    
    # Ensure the DEBUG message was not part of the INFO records for this logger from console
    assert not any(test_debug_msg in rec.message for rec in console_emitted_records), \
        f"Debug message '{test_debug_msg}' should not be in caplog INFO records for logger {logger.name}. Records: {caplog.text}"

    # Flush file handler to ensure messages are written to file
    main_app_logger = logging.getLogger('dune_companion_app')
    for handler in main_app_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()

    # Check file output (DEBUG and above)
    assert os.path.exists(LOG_FILE), "Log file should be created."
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_content = f.read()
    assert test_debug_msg in log_content, f"Debug message '{test_debug_msg}' should be in log file. Content: {log_content}"
    assert test_info_msg in log_content, f"Info message '{test_info_msg}' should be in log file. Content: {log_content}"

def test_logger_level_configuration():
    """Test that logger levels are configured correctly for handlers."""
    main_logger = logging.getLogger('dune_companion_app')
    assert main_logger.level == logging.DEBUG

    console_handler_found = False
    file_handler_found = False

    for handler in main_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            assert handler.level == logging.INFO
            console_handler_found = True
        elif isinstance(handler, logging.FileHandler):
            assert handler.level == logging.DEBUG
            file_handler_found = True
    
    assert console_handler_found, "Console handler should be present."
    assert file_handler_found, "File handler should be present."

def test_log_file_rotation_not_easily_testable_here():
    """Placeholder for log file rotation. Actual rotation is hard to unit test reliably and quickly."""
    # This test is more of an integration test and would require writing large amounts of data.
    # For now, we trust the RotatingFileHandler implementation.
    pass

def test_shutdown_logging_removes_handlers_and_closes_files():
    """Test that shutdown_logging correctly removes handlers and allows file to be deleted."""
    logger = get_logger('shutdown_test')
    logger.info("Test message before shutdown.")

    main_app_logger = logging.getLogger('dune_companion_app')
    for handler in main_app_logger.handlers:
        handler.flush()
        # No need to explicitly close file handlers here, shutdown_logging should handle it.
    assert os.path.exists(LOG_FILE)

    shutdown_logging()
    assert not main_app_logger.handlers
    
    # Try to re-initialize and log again to ensure it works
    initialize_handlers()
    logger_after_shutdown = get_logger('after_shutdown')
    logger_after_shutdown.info("Test message after re-initialization.")
    
    assert len(main_app_logger.handlers) > 0, "Handlers should be re-added after initialize_handlers()."

def test_multiple_get_logger_calls_share_handlers():
    """Test that multiple get_logger calls use the same, correctly initialized handlers,
    and that the log file is handled correctly across shutdown/re-init within a test."""
    main_app_logger = logging.getLogger('dune_companion_app')

    logger1 = get_logger('module1')
    logger2 = get_logger('module2')
    assert len(main_app_logger.handlers) == 2

    test_msg1 = "Message from logger1 for multi-test"
    test_msg2 = "Message from logger2 for multi-test"

    logger1.info(test_msg1)
    logger2.info(test_msg2)

    for handler in main_app_logger.handlers:
        handler.flush()

    assert os.path.exists(LOG_FILE)
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_content_before_reinit = f.read()
    assert test_msg1 in log_content_before_reinit
    assert test_msg2 in log_content_before_reinit

    # --- Shutdown, clean log file, and re-initialize --- 
    shutdown_logging()
    assert not main_app_logger.handlers, "Handlers should be cleared after shutdown."
    # Explicitly remove the log file here to test re-initialization with a clean slate
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError: # pragma: no cover
            time.sleep(0.1)
            os.remove(LOG_FILE)
    
    initialize_handlers()
    assert len(main_app_logger.handlers) == 2, "Handlers should be restored after re-initialization."
    
    logger3 = get_logger('module3')
    test_msg3 = "Message from logger3 after re-init for multi-test"
    logger3.info(test_msg3)
    for handler in main_app_logger.handlers:
        handler.flush()
    
    assert os.path.exists(LOG_FILE), "Log file should exist after re-init and logging."
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        log_content_after_reinit = f.read()
    
    assert test_msg3 in log_content_after_reinit
    assert test_msg1 not in log_content_after_reinit, \
        f"Old message (msg1) '{test_msg1}' should not be present in log file after explicit clear and re-init. Content: {log_content_after_reinit}"
    assert test_msg2 not in log_content_after_reinit, \
        f"Old message (msg2) '{test_msg2}' should not be present in log file after explicit clear and re-init. Content: {log_content_after_reinit}"
