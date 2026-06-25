import logging
from app.config import settings

def setup_logging():
    """
    Configures colored logging using colorlog if available,
    or falls back to standard output if not installed.
    Uses LOG_LEVEL from settings.
    """
    try:
        import colorlog
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            secondary_log_colors={},
            datefmt='%Y-%m-%d %H:%M:%S',
        ))
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        root_logger.addHandler(handler)
        logging.debug("colorlog configured for colored console output.")
    except ImportError:
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
            format='[%(asctime)s] %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        logging.warning("colorlog not found, using default logger.")
