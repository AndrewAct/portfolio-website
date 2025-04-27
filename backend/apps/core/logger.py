import logging
import sys
from typing import Any


def setup_logging(logger_name="url_shortener") -> Any:
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Check if any handlers already exist (to avoid duplicate handlers)
    if not root_logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        root_logger.addHandler(handler)

    # Create and return the specific logger requested
    specific_logger = logging.getLogger(logger_name)
    specific_logger.setLevel(logging.INFO)

    return specific_logger