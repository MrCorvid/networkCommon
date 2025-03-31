#!/usr/bin/env python3
"""
logging_manager.py (in networkCommon)

Centralized logging configuration and management for the interpreter and compiler systems.
"""

import os
import logging
import datetime
from typing import Dict, Optional

# Define log directory relative to the project root (assuming common location)
# Adjust if logs should be stored elsewhere
LOG_DIR = "logs_and_log_tools"
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        # Handle potential race condition or permission issues
        print(f"Warning: Could not create log directory {LOG_DIR}: {e}")
        LOG_DIR = "." # Fallback to current directory


class LoggingManager:
    """
    Manages logging configuration and provides access to loggers.

    This class handles the creation and configuration of loggers for the interpreter
    and compiler systems, ensuring consistent logging behavior across all components.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _root_logger_name = "NetworkSystem" # Define a common root logger name
    _root_logger: Optional[logging.Logger] = None
    _default_level = logging.INFO
    _initialized = False
    _log_file_path: Optional[str] = None

    @classmethod
    def initialize(cls, level: int = logging.INFO, log_file: Optional[str] = None, force_reinit: bool = False) -> None:
        """
        Initialize the logging system with the specified level and log file.

        Args:
            level: The logging level to use (default: INFO)
            log_file: The path to the log file (default: auto-generated based on date)
            force_reinit: If True, forces re-initialization even if already initialized.
        """
        if cls._initialized and not force_reinit:
            # If already initialized and not forcing, just ensure level is updated if different
            if cls._default_level != level:
                 cls.set_level(level)
            return

        cls._default_level = level
        # Use the common root logger name
        root_logger = logging.getLogger(cls._root_logger_name)
        root_logger.setLevel(level)
        # Prevent duplicate messages if handlers are added multiple times
        root_logger.propagate = False

        # Clear existing handlers only if forcing reinitialization or first time
        if force_reinit or not root_logger.hasHandlers():
            if root_logger.hasHandlers():
                root_logger.handlers.clear()

            # Console Handler (always add or re-add)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            # Use a more informative default format
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s')
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

            # File Handler (add or re-add)
            if log_file is None:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                # Use the root logger name in the filename for clarity
                log_file = os.path.join(LOG_DIR, f"{cls._root_logger_name}_{timestamp}.log")

            try:
                # Use absolute path for consistency
                cls._log_file_path = os.path.abspath(log_file)
                file_handler = logging.FileHandler(cls._log_file_path)
                file_handler.setLevel(level)
                # Consistent formatter
                file_formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s')
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                root_logger.error(f"Failed to initialize file handler for {log_file}: {e}", exc_info=True)
                cls._log_file_path = "Error" # Indicate failure

        cls._root_logger = root_logger
        # Store under the specific root name
        cls._loggers[cls._root_logger_name] = root_logger
        cls._initialized = True

        root_logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
        root_logger.info(f"Log file: {cls._log_file_path}")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger with the specified name, inheriting from the common root.

        If the logger doesn't exist, it will be created and configured.

        Args:
            name: The name of the logger (e.g., "Interpreter", "Compiler.Validator")

        Returns:
            The logger instance
        """
        if not cls._initialized:
            cls.initialize() # Initialize with defaults if not done yet

        # Use hierarchical naming based on the common root
        if name == cls._root_logger_name or not name:
             return cls._root_logger

        # Ensure logger name is relative to the root logger
        full_name = f"{cls._root_logger_name}.{name}"

        if full_name in cls._loggers:
            return cls._loggers[full_name]

        logger = logging.getLogger(full_name)
        # Logger level will be controlled by the root unless set explicitly later
        # logger.setLevel(cls._default_level) # Don't set level here, let it inherit
        logger.propagate = False # Let the root handler manage output
        # Add logger to dict using its full name for uniqueness
        cls._loggers[full_name] = logger
        return logger

    @classmethod
    def set_level(cls, level: int, name: Optional[str] = None) -> None:
        """
        Set the logging level for the specified logger or the root logger and handlers.

        Args:
            level: The logging level to set (e.g., logging.DEBUG)
            name: The name of the specific logger (e.g., "Compiler.Validator").
                  If None, sets the level for the root logger and its handlers.
        """
        if not cls._initialized:
            cls.initialize(level=level)
            # Initialization already sets the level, so return
            return

        if name is None or name == cls._root_logger_name:
            # Set level for the root logger and all its handlers
            if cls._root_logger:
                cls._root_logger.setLevel(level)
                for handler in cls._root_logger.handlers:
                    handler.setLevel(level)
                cls._root_logger.info(f"Set root logger ('{cls._root_logger_name}') level to {logging.getLevelName(level)}")
            # Update default level for future loggers
            cls._default_level = level
        else:
            # Set level for a specific child logger
            full_name = f"{cls._root_logger_name}.{name}"
            if full_name in cls._loggers:
                cls._loggers[full_name].setLevel(level)
                cls._loggers[full_name].info(f"Set logger '{full_name}' level to {logging.getLevelName(level)}")
            else:
                # If logger doesn't exist yet, get_logger will create it,
                # but its level will be controlled by the root unless explicitly set here.
                # We can log a warning or pre-create it. Let's log a warning.
                 if cls._root_logger:
                      cls._root_logger.warning(f"Attempted to set level for non-existing logger '{full_name}'. Level will be inherited from root.")


    @classmethod
    def add_file_handler(cls, log_file: str, level: Optional[int] = None) -> None:
        """
        Add an additional file handler to the root logger.

        Args:
            log_file: The path to the log file
            level: The logging level for this specific handler (default: root logger's level)
        """
        if not cls._initialized:
            # Initialize first if needed, potentially creating the default log file
            cls.initialize()

        if cls._root_logger:
            abs_log_file = os.path.abspath(log_file)
            # Check if a handler for this exact file already exists
            if any(
                isinstance(h, logging.FileHandler) and hasattr(h, 'baseFilename') and h.baseFilename == abs_log_file
                for h in cls._root_logger.handlers
            ):
                cls._root_logger.warning(f"File handler for {abs_log_file} already exists. Skipping.")
                return

            try:
                # Use root's level if specific level isn't provided
                handler_level = level if level is not None else cls._root_logger.level
                file_handler = logging.FileHandler(abs_log_file)
                file_handler.setLevel(handler_level)
                # Use the same formatter as the root logger's handlers for consistency
                formatter = cls._root_logger.handlers[0].formatter if cls._root_logger.handlers else logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s')
                file_handler.setFormatter(formatter)
                cls._root_logger.addHandler(file_handler)
                cls._root_logger.info(f"Added file handler for {abs_log_file} at level {logging.getLevelName(handler_level)}")
            except Exception as e:
                cls._root_logger.error(f"Failed to add file handler for {abs_log_file}: {e}", exc_info=True)

    # Convenience methods to log directly using logger name
    @classmethod
    def log(cls, level: int, message: str, name: str) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.log(level, message)

    @classmethod
    def debug(cls, message: str, name: str) -> None:
        cls.log(logging.DEBUG, message, name)

    @classmethod
    def info(cls, message: str, name: str) -> None:
        cls.log(logging.INFO, message, name)

    @classmethod
    def warning(cls, message: str, name: str) -> None:
        cls.log(logging.WARNING, message, name)

    @classmethod
    def error(cls, message: str, name: str, exc_info=False) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.error(message, exc_info=exc_info)

    @classmethod
    def critical(cls, message: str, name: str, exc_info=False) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.critical(message, exc_info=exc_info)