"""
Application Logging Utility

Provides:
- init_logger(app)
- log_info(message)
- log_error(message)
- request logging middleware

Creates logs at:
    /logs/app.log
    /logs/error.log
"""

import os
import logging
from flask import request


# -----------------------------------------------------
# CREATE LOG DIRECTORY
# -----------------------------------------------------
LOG_DIR = os.path.join(os.getcwd(), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# -----------------------------------------------------
# LOGGER INSTANCES
# -----------------------------------------------------
app_logger = logging.getLogger("app_logger")
error_logger = logging.getLogger("error_logger")

app_logger.setLevel(logging.INFO)
error_logger.setLevel(logging.ERROR)


# -----------------------------------------------------
# FILE HANDLERS
# -----------------------------------------------------
app_file_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
error_file_handler = logging.FileHandler(os.path.join(LOG_DIR, "error.log"))

app_file_handler.setLevel(logging.INFO)
error_file_handler.setLevel(logging.ERROR)


# -----------------------------------------------------
# LOG FORMAT
# -----------------------------------------------------
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
)

app_file_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)

app_logger.addHandler(app_file_handler)
error_logger.addHandler(error_file_handler)


# -----------------------------------------------------
# PUBLIC HELPERS
# -----------------------------------------------------
def log_info(message: str):
    app_logger.info(message)


def log_error(message: str):
    error_logger.error(message)


# -----------------------------------------------------
# REQUEST LOGGING MIDDLEWARE
# -----------------------------------------------------
def register_request_logging(app):
    """
    Logs every incoming request:
    - method
    - path
    - IP address
    - user-agent
    """

    @app.before_request
    def log_request():
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        method = request.method
        path = request.path
        ua = request.headers.get("User-Agent")

        msg = f"{ip} {method} {path} | UA: {ua}"
        log_info(msg)
