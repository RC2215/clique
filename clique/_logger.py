import logging
import sys
from os import PathLike
from typing import Any, ClassVar, TextIO


class BaseFormatter(logging.Formatter):
    default_msec_format = '%s.%03d'
    default_record_format = '%(asctime)s | %(levelname)s | %(name)s.%(funcName)s:%(lineno)d | %(message)s'

    def __init__(self, fmt: str | None = None, *args: Any, **kwargs: Any) -> None:
        fmt = self.default_record_format if fmt is None else fmt
        super().__init__(fmt, *args, **kwargs)


class ColoredStreamFormatter(BaseFormatter):
    GREY = '\x1b[38;20m'
    YELLOW = '\x1b[33;20m'
    RED = '\x1b[31;20m'
    BOLD_RED = '\x1b[31;1m'
    RESET = '\x1b[0m'

    COLORS_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG: GREY,
        logging.INFO: GREY,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return self.COLORS_MAP.get(record.levelno, '') + formatted + self.RESET


def set_logger(level: int, stream: TextIO = sys.stdout, file_path: str | PathLike[str] | None = None) -> None:
    """
    Configure the root logger for the entire application.
    Note: This function is intended to be called once at the application's entry point.

    :param level: Logging level applied to the logger and all handlers.
    :param stream: Text stream for console logging, e.g. ``sys.stdout`` or ``sys.stderr``.
    :param file_path: Path to a log file. If provided, a file handler is added in append mode.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(ColoredStreamFormatter())
    logger.addHandler(handler)

    if file_path:
        file_handler = logging.FileHandler(file_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(BaseFormatter())
        logger.addHandler(file_handler)
