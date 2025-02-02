"""
Logging configuration for the API
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import override

import logging_loki
from dotenv import load_dotenv


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

# Check if the logger already has handlers to avoid adding them multiple times
if not logger.hasHandlers():
    # Create a console handler and set the level
    ch = logging.StreamHandler()

    # Create a file handler and set the level
    # Mode 'w' will overwrite the log file each time the API is started, 'a' will append
    LOG_FILE = 'log/api.log'
    fh = logging.FileHandler(LOG_FILE, mode='a')

    # Create a Loki handler
    logging_loki.emitter.LokiEmitter.level_tag = 'level'

    lh = logging_loki.LokiHandler(
        url='http://localhost:3100/loki/api/v1/push',
        version='1',
    )

    logger.debug('API Env set to: %s', os.getenv('API_ENV'))
    load_dotenv(dotenv_path='env/local.env')

    # Set the level for the logger
    log_level_var = os.getenv('LOG_LEVEL').upper()
    logger.setLevel(log_level_var)

    # Create a formatter and set it for the handler
    file_log_formatter = logging.Formatter(
        '%(levelname)s: [%(name)s] %(asctime)s => %(message)s (%(filename)s:%(lineno)d)'
    )

    # Set date format
    file_log_formatter.datefmt = '%Y-%m-%d %H:%M:%S'

    # Used separate formatters as color ASCII threw off the file log formatting
    ch.setFormatter(CustomFormatter())
    fh.setFormatter(file_log_formatter)

    # add a rotating handler
    handler = RotatingFileHandler(LOG_FILE, maxBytes=10485760, backupCount=10)
    logger.addHandler(handler)

    # Add the handler to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.addHandler(lh)
