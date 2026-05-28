import logging
from typing import ClassVar


class LoggingLevel:
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class ColoredStreamFormatter(logging.Formatter):
    default_msec_format = '%s.%03d'
    default_record_format = '%(asctime)s | %(levelname)s | %(name)s.%(funcName)s:%(lineno)d | %(message)s'

    GREY = '\x1b[38;20m'
    YELLOW = '\x1b[33;20m'
    RED = '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    RESET = '\x1b[0m'

    COLOROS_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG: GREY,
        logging.INFO: GREY,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED
    }

    def __init__(self, fmt=None, datefmt=None, style='%', validate=True, *, defaults=None):
        fmt = self.default_record_format if fmt is None else fmt
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return self.COLOROS_MAP.get(record.levelno, '') + formatted + self.RESET
