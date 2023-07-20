"""
Logger configurations, this uses loguru to handle logs
Reference: https://github.com/Delgan/loguru
"""

import os
import sys
import logging
from loguru import logger

logging.root.setLevel(logging.INFO)

root = logging.getLogger()


def configure_log_sink(log_type: str):
    """
    Configures log sing based on the log type and the enrironment
    @param log_type log type could be either info, error, warn, debug, etc
    @returns the log sink to use
    """
    return (
        f"logs/{log_type}.log" if os.environ.get("ENV") == "development" else sys.stdout
    )


def backtrace() -> bool:
    """Configures backtrace based on the env"""
    return os.environ.get("ENV", "development") == "development"


# info log configurations
logger.add(
    sink=configure_log_sink("info"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="INFO",
)

# error logs
logger.add(
    sink=configure_log_sink("error"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="ERROR",
)

# debug logs
logger.add(
    sink=configure_log_sink("debug"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="DEBUG",
)

# warning logs
logger.add(
    sink=configure_log_sink("warn"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="WARNING",
)

# critical logs
logger.add(
    sink=configure_log_sink("critical"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="CRITICAL",
)

# trace logs
logger.add(
    sink=configure_log_sink("trace"),
    backtrace=backtrace(),
    colorize=True,
    format="<green>{time}</green> <level>{message}</level>",
    # format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
    enqueue=True,
    level="TRACE",
)
