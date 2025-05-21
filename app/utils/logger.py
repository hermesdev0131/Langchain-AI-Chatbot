import logging

# Flag to ensure logging is configured only once
_logging_configured = False

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance by name.
    On the first call, it configures the root logger for the application
    and sets specific logging levels for verbose third-party libraries.
    """
    global _logging_configured

    if not _logging_configured:
        # Configure root logger for the application.
        # This setup runs only once.
        logging.basicConfig(
            level=logging.INFO,  # Default level for your application's logs.
                                 # logger.debug() calls in your app will be hidden
                                 # unless this is set to logging.DEBUG or the specific
                                 # app logger's level is set to DEBUG.
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Set higher (less verbose) logging levels for noisy third-party libraries.
        # This helps in reducing clutter from libraries like httpx, azure sdk, etc.
        libraries_to_quiet = {
            "httpx": logging.WARNING,
            "azure": logging.WARNING,  # Broadly covers Azure SDK logs, including azure.core.
            "uvicorn.access": logging.WARNING, # Quiets Uvicorn's per-request access logs.
            # Add other libraries here if they become too verbose at INFO level.
            # e.g., "openai": logging.WARNING, "langchain": logging.WARNING
        }
        
        for lib_name, level in libraries_to_quiet.items():
            logging.getLogger(lib_name).setLevel(level)
            # Optionally, you can also prevent propagation if needed, though setLevel is usually enough.
            # logging.getLogger(lib_name).propagate = False 
        
        _logging_configured = True
        
        # Log that the one-time configuration has been applied.
        # Use the logger for *this* module to make it clear where the message originates.
        logging.getLogger(__name__).info("Logging configured: Application default level INFO, specific libraries set to WARNING.")

    return logging.getLogger(name)
