#!/usr/bin/env python3
"""
logging_manager.py (in networkCommon)

Centralized logging configuration and management for the interpreter, compiler,
MEGA, and environment systems. Allows for component-specific logging levels.
"""

import os
import logging
import datetime
from typing import Dict, Optional, Union

# Define custom VERBOSE log level
VERBOSE_LEVEL_NUM = 15
logging.addLevelName(VERBOSE_LEVEL_NUM, "VERBOSE")

def verbose(self, message, *args, **kws):
    if self.isEnabledFor(VERBOSE_LEVEL_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(VERBOSE_LEVEL_NUM, message, args, **kws)

logging.Logger.verbose = verbose

# Define log directory relative to the project root
LOG_DIR = "logs" # Changed from logs_and_log_tools
if not os.path.exists(LOG_DIR):
    try:
        os.makedirs(LOG_DIR)
    except OSError as e:
        # Handle potential race condition or permission issues
        print(f"CRITICAL: Could not create log directory {LOG_DIR}: {e}. Logging disabled.", flush=True)
        # If we can't create the log dir, logging is fundamentally broken.
        # Avoid falling back to '.' as it might spam the root dir.
        # Consider raising an exception or exiting depending on severity.
        LOG_DIR = None # Indicate failure


class LoggingManager:
    """
    Manages logging configuration and provides access to loggers with
    component-specific level control.
    """

    _loggers: Dict[str, logging.Logger] = {}
    _component_levels: Dict[str, int] = {} # Store levels for specific components
    _root_logger_name = "NetworkSystem"
    _root_logger: Optional[logging.Logger] = None
    _default_level = logging.INFO
    _initialized = False
    _log_file_path: Optional[str] = None
    _console_handler: Optional[logging.StreamHandler] = None
    _file_handler: Optional[logging.FileHandler] = None

    # Define major components expected
    KNOWN_COMPONENTS = ["Interpreter", "MEGA", "Compiler", "Environment", "Common", "Main"] # Added Main

    @classmethod
    def initialize(cls,
                   default_level: Union[int, str] = logging.INFO,
                   component_levels: Optional[Dict[str, Union[int, str]]] = None,
                   log_file: Optional[str] = None,
                   force_reinit: bool = False) -> None:
        """
        Initialize the logging system.

        Args:
            default_level: The default logging level for the root logger and
                           unspecified components (default: INFO). Can be int or str.
            component_levels: A dictionary mapping component names (str) to their
                              specific logging levels (int or str).
            log_file: The path to the log file (default: auto-generated).
            force_reinit: If True, forces re-initialization.
        """
        if cls._initialized and not force_reinit:
            # Allow updating levels even if initialized
            cls.set_level(default_level) # Update root/default level
            if component_levels:
                for name, level in component_levels.items():
                    cls.set_level(level, name)
            return

        if not LOG_DIR: # Check if log directory creation failed
             print("CRITICAL: Logging directory not available. Logging disabled.", flush=True)
             return # Cannot initialize logging

        # --- Convert string levels to int ---
        if isinstance(default_level, str):
            default_level = logging.getLevelName(default_level.upper())
        cls._default_level = default_level

        if component_levels:
            cls._component_levels = {
                name: logging.getLevelName(level.upper()) if isinstance(level, str) else level
                for name, level in component_levels.items()
            }
        else:
            cls._component_levels = {}

        # --- Setup Root Logger ---
        root_logger = logging.getLogger(cls._root_logger_name)
        root_logger.setLevel(cls._default_level) # Root logger uses default level initially
        root_logger.propagate = False # Prevent duplicate messages

        # --- Clear existing handlers if needed ---
        if force_reinit or not root_logger.hasHandlers():
            if root_logger.hasHandlers():
                root_logger.handlers.clear()
                cls._console_handler = None
                cls._file_handler = None

            # --- Console Handler ---
            cls._console_handler = logging.StreamHandler()
            cls._console_handler.setLevel(cls._default_level) # Console mirrors root default
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)-8s - %(name)-20s - %(message)s' # Wider name field
            )
            cls._console_handler.setFormatter(console_formatter)
            root_logger.addHandler(cls._console_handler)

            # --- File Handler ---
            if log_file is None:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                log_file = os.path.join(LOG_DIR, f"{cls._root_logger_name}_{timestamp}.log")

            try:
                cls._log_file_path = os.path.abspath(log_file)
                cls._file_handler = logging.FileHandler(cls._log_file_path, encoding='utf-8')
                cls._file_handler.setLevel(logging.DEBUG) # File handler captures everything >= DEBUG by default
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)-8s - %(name)-20s - %(funcName)-20s - %(message)s' # Add function name
                )
                cls._file_handler.setFormatter(file_formatter)
                root_logger.addHandler(cls._file_handler)
            except Exception as e:
                 # Use print because logger might not be fully functional
                print(f"ERROR: Failed to initialize file handler for {log_file}: {e}", flush=True)
                cls._log_file_path = "Error"
                cls._file_handler = None # Ensure it's None on failure

        cls._root_logger = root_logger
        cls._loggers[cls._root_logger_name] = root_logger
        cls._initialized = True

        # Apply initial component levels after root is set up
        for name, level in cls._component_levels.items():
             cls.set_level(level, name, initializing=True) # Use internal flag

        root_logger.info(f"Logging initialized. Default Level: {logging.getLevelName(cls._default_level)}")
        root_logger.info(f"Component Levels: { {name: logging.getLevelName(lvl) for name, lvl in cls._component_levels.items()} }")
        root_logger.info(f"Log file: {cls._log_file_path}")


    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger for a specific component.

        Args:
            name: The name of the component (e.g., "Interpreter", "Compiler.Validator").
                  Should match one of the keys in KNOWN_COMPONENTS or be a sub-component.

        Returns:
            The logger instance.
        """
        if not cls._initialized:
            if LOG_DIR: # Only initialize if log dir is valid
                cls.initialize() # Initialize with defaults
            else:
                # Return a dummy logger if initialization failed
                return logging.getLogger("DisabledLogger")


        # Determine the base component name (e.g., "Compiler" from "Compiler.Validator")
        base_component = name.split('.')[0]
        if base_component not in cls.KNOWN_COMPONENTS and base_component != cls._root_logger_name:
             # Log a warning using the root logger if an unknown component is requested
             if cls._root_logger:
                 cls._root_logger.warning(f"Requested logger for potentially unknown component: '{name}'. "
                                          f"Known components: {cls.KNOWN_COMPONENTS}")
             # We still allow creating it, but warn the user.

        full_name = f"{cls._root_logger_name}.{name}"

        if full_name in cls._loggers:
            return cls._loggers[full_name]

        logger = logging.getLogger(full_name)

        # Determine the effective level for this new logger
        specific_level = cls._component_levels.get(base_component)
        if specific_level is not None:
            logger.setLevel(specific_level)
            # Removed debug print
        else:
            # Inherit from root logger's default level if no component level is set
            logger.setLevel(cls._default_level)
            # Removed debug print


        # Ensure logger doesn't propagate to the standard root logger,
        # but relies on *our* root logger's handlers.
        logger.propagate = False

        # Add logger to dict
        cls._loggers[full_name] = logger
        # Removed debug print
        return logger

    @classmethod
    def set_level(cls, level: Union[int, str], name: Optional[str] = None, initializing: bool = False) -> None:
        """
        Set the logging level for a component or the default level.

        Args:
            level: The logging level (e.g., logging.DEBUG, "VERBOSE").
            name: The name of the component (e.g., "Compiler").
                  If None, sets the default level for the root logger, console handler,
                  and unspecified components.
            initializing: Internal flag to suppress logging during initial setup.
        """
        if isinstance(level, str):
            level_int = logging.getLevelName(level.upper())
            if not isinstance(level_int, int):
                 print(f"WARNING: Invalid log level string '{level}'. Ignoring set_level call.", flush=True)
                 return
            level = level_int # Use the integer level internally

        if not cls._initialized and not initializing:
            # If called before init (and not *during* init), initialize with this level as default
            component_levels = {name: level} if name else None
            default_level = level if name is None else cls._default_level # Keep existing default if setting component
            cls.initialize(default_level=default_level, component_levels=component_levels)
            return

        if name is None or name == cls._root_logger_name:
            # Set default level for root, console, and future loggers
            cls._default_level = level
            if cls._root_logger:
                cls._root_logger.setLevel(level)
                if not initializing:
                    cls._root_logger.info(f"Set default logging level to {logging.getLevelName(level)}")
            if cls._console_handler:
                cls._console_handler.setLevel(level)
                if not initializing and cls._root_logger:
                     cls._root_logger.debug(f"Set console handler level to {logging.getLevelName(level)}")
            # Update existing loggers that were using the old default
            for logger_name, logger_instance in cls._loggers.items():
                 # Extract base component name correctly (last part after the root name)
                 if logger_name.startswith(cls._root_logger_name + '.'):
                      base_component = logger_name.split('.')[-1]
                      if base_component not in cls._component_levels:
                           logger_instance.setLevel(level)
                 # Handle the root logger itself if name is None
                 elif name is None and logger_name == cls._root_logger_name:
                      logger_instance.setLevel(level)


        else:
            # Set level for a specific component
            base_component = name.split('.')[0] # Apply to base component
            if base_component not in cls.KNOWN_COMPONENTS:
                 if cls._root_logger and not initializing:
                      cls._root_logger.warning(f"Setting level for potentially unknown component: '{name}'.")

            cls._component_levels[base_component] = level
            # Update all existing loggers belonging to this component/sub-component
            updated_any = False
            for logger_name, logger_instance in cls._loggers.items():
                 # Check if logger_name starts with Root.Component
                 if logger_name.startswith(f"{cls._root_logger_name}.{base_component}"):
                      logger_instance.setLevel(level)
                      updated_any = True

            # Log the change using the component's logger *if* it exists, otherwise root
            target_logger = cls.get_logger(base_component) # Ensures logger exists
            if not initializing:
                 target_logger.info(f"Set component '{base_component}' logging level to {logging.getLevelName(level)}")


    # --- Convenience Methods ---
    # These now require the component name

    @classmethod
    def log(cls, level: int, message: str, name: str, *args, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.log(level, message, *args, **kwargs)

    @classmethod
    def debug(cls, message: str, name: str, *args, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.debug(message, *args, **kwargs)

    @classmethod
    def verbose(cls, message: str, name: str, *args, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        # Check level explicitly before calling the potentially non-standard method
        if logger_instance.isEnabledFor(VERBOSE_LEVEL_NUM):
             logger_instance.verbose(message, *args, **kwargs)


    @classmethod
    def info(cls, message: str, name: str, *args, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.info(message, *args, **kwargs)

    @classmethod
    def warning(cls, message: str, name: str, *args, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.warning(message, *args, **kwargs)

    @classmethod
    def error(cls, message: str, name: str, *args, exc_info=False, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.error(message, *args, exc_info=exc_info, **kwargs)

    @classmethod
    def critical(cls, message: str, name: str, *args, exc_info=False, **kwargs) -> None:
        logger_instance = cls.get_logger(name)
        logger_instance.critical(message, *args, exc_info=exc_info, **kwargs)


# Example Usage (for testing within this file)
if __name__ == "__main__":
    # Configure logging levels per component
    initial_levels = {
        "Interpreter": "INFO",
        "Compiler": "DEBUG",
        "MEGA": "VERBOSE",
        "Environment": logging.WARNING, # Can use int or str
        "UnknownComponent": "INFO" # Test handling unknown
    }

    # Initialize the manager
    LoggingManager.initialize(default_level="INFO", component_levels=initial_levels)

    # Get loggers for different components
    interp_logger = LoggingManager.get_logger("Interpreter")
    compiler_logger = LoggingManager.get_logger("Compiler")
    compiler_val_logger = LoggingManager.get_logger("Compiler.Validator") # Sub-component
    mega_logger = LoggingManager.get_logger("MEGA")
    env_logger = LoggingManager.get_logger("Environment")
    unknown_logger = LoggingManager.get_logger("UnknownComponent.Sub") # Test unknown
    common_logger = LoggingManager.get_logger("Common") # Uses default level

    # Log messages at various levels
    interp_logger.debug("This interpreter debug message should NOT appear by default.")
    interp_logger.info("Interpreter starting.")
    interp_logger.verbose("Interpreter verbose message should NOT appear.") # Below INFO

    compiler_logger.debug("Compiler debug message should appear.")
    compiler_logger.info("Compiler info message should appear.")
    compiler_val_logger.debug("Compiler validator sub-component debug message should appear.") # Inherits Compiler level

    mega_logger.debug("MEGA debug message should NOT appear.") # Below VERBOSE
    mega_logger.verbose("MEGA verbose message should appear.")
    mega_logger.info("MEGA info message should appear.")
    mega_logger.warning("MEGA warning message should appear.")

    env_logger.info("Environment info message should NOT appear.") # Below WARNING
    env_logger.warning("Environment warning message should appear.")
    env_logger.error("Environment error message should appear.")

    unknown_logger.info("Unknown component info message should appear.")
    unknown_logger.debug("Unknown component debug message should NOT appear.")

    common_logger.info("Common component info message should appear.")
    common_logger.debug("Common component debug message should NOT appear.")


    # --- Test changing levels ---
    print("\n--- Changing Interpreter level to DEBUG ---")
    LoggingManager.set_level(logging.DEBUG, "Interpreter")
    interp_logger.debug("This interpreter debug message SHOULD now appear.")
    interp_logger.verbose("Interpreter verbose message should still NOT appear.") # VERBOSE < DEBUG

    print("\n--- Changing Default level to WARNING ---")
    LoggingManager.set_level("WARNING") # Set default level
    common_logger.info("Common component info message should NOT appear now.")
    common_logger.warning("Common component warning message SHOULD appear now.")
    # Compiler level should remain DEBUG as it was explicitly set
    compiler_logger.info("Compiler info message should still appear (component level overrides default).")
    compiler_logger.debug("Compiler debug message should still appear.")

    print("\n--- Changing MEGA level to INFO ---")
    LoggingManager.set_level(logging.INFO, "MEGA")
    mega_logger.verbose("MEGA verbose message should NOT appear now.")
    mega_logger.info("MEGA info message should still appear.")

    print(f"\nLog file located at: {LoggingManager._log_file_path}")
    print("Check the log file for messages >= DEBUG.")