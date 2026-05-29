import logging
from typing import ClassVar, Any


class BaseFormatter(logging.Formatter):
    """
    TBD
    """

    default_msec_format = '%s.%03d'
    default_record_format = '%(asctime)s | %(levelname)s | %(name)s.%(funcName)s:%(lineno)d | %(message)s'

    def __init__(self, fmt: str | None = None, *args: Any, **kwargs: Any) -> None:
        fmt = self.default_record_format if fmt is None else fmt
        super().__init__(fmt, *args, **kwargs)


class ColoredStreamFormatter(BaseFormatter):
    """
    TBD
    """

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
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return self.COLOROS_MAP.get(record.levelno, '') + formatted + self.RESET


def set_logger(level, stream, file_path=None):
    """

    :param level:
    :param stream:
    :param file_path:
    :return:
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(ColoredStreamFormatter())
    logger.addHandler(handler)

    if file_path:
        file_handler = logging.FileHandler(file_path, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(BaseFormatter())
        logger.addHandler(file_handler)
