"""
Logging configuration for the API
"""

import logging
from logging.handlers import RotatingFileHandler
from typing import override

import logging_loki

from app.config import get_settings


class CustomFormatter(logging.Formatter):
    """
    Creates custom formatter to color log messages.
    """

    green = '\x1b[32;20m'
    blue = '\x1b[34;20m'
    grey = '\x1b[38;20m'
    yellow = '\x1b[33;20m'
    red = '\x1b[31;20m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'
    line_level = '%(levelname)s'
    line_format = ': [%(name)s] %(asctime)s => %(message)s (%(filename)s:%(lineno)d)'

    FORMATS = {
        logging.DEBUG: blue + line_level + reset + line_format,
        logging.INFO: green + line_level + reset + line_format,
        logging.WARNING: yellow + line_level + reset + line_format,
        logging.ERROR: red + line_level + reset + line_format,
        logging.CRITICAL: bold_red + line_level + reset + line_format,
    }

    @override
    def format(self, record):
        """
        Provides formatting for log messages.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.datefmt = '%Y-%m-%d %H:%M:%S'
        return formatter.format(record)


# Create or retrieve a logger
logger = logging.getLogger('aleonard_api')


def configure_logger():
    """
    Configure logger handlers. This function must be called after the .env file is loaded.
    """
    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return

    settings = get_settings()

    # Create a console handler and set the level
    ch = logging.StreamHandler()

    # Set the level for the logger
    logger.setLevel(settings.log_level.upper())

    # Create a formatter and set it for the handler
    file_log_formatter = logging.Formatter(
        '%(levelname)s: [%(name)s] %(asctime)s => %(message)s (%(filename)s:%(lineno)d)'
    )
    file_log_formatter.datefmt = '%Y-%m-%d %H:%M:%S'

    # Used separate formatters as color ASCII threw off the file log formatting
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)

    logger.debug('API env set to: %s', settings.env)

    # File + Loki handlers are noise in CI; only attach them when deployed/local.
    if settings.is_ci:
        return

    # Mode 'a' appends to the log file across restarts.
    log_file = 'app/log/api.log'
    fh = logging.FileHandler(log_file, mode='a')
    fh.setFormatter(file_log_formatter)

    # Rotating file handler
    rotating_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=10)
    logger.addHandler(rotating_handler)
    logger.addHandler(fh)

    # Ship logs to Grafana Loki when a URL is configured.
    if settings.loki_url:
        logging_loki.emitter.LokiEmitter.level_tag = 'level'
        loki_handler = logging_loki.LokiHandler(
            url=f'{settings.loki_url}/loki/api/v1/push',
            version='1',
            tags={
                'service': 'aleonard-us-api',
                'environment': settings.env,
                'landing_zone': settings.lz,
            },
        )
        logger.addHandler(loki_handler)
