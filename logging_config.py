import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[41m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class Logger:
    _configured = False

    def __init__(self, level=logging.INFO):
        if Logger._configured:
            return

        root = logging.getLogger()
        root.setLevel(level)
        root.handlers.clear()

        # -------- Console handler (all modules) --------
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        console.setFormatter(
            ColoredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        root.addHandler(console)

        # -------- File handlers per module --------
        self._add_file_handler("server", "server.log")
        self._add_file_handler("whatsapp_worker", "worker.log")
        self._add_file_handler("llm", "llm.log")
        self._add_file_handler("celery", "celery.log")

        # Reduce noise
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
        logging.getLogger("kombu").setLevel(logging.WARNING)
        logging.getLogger("billiard").setLevel(logging.WARNING)

        Logger._configured = True

    def _add_file_handler(self, logger_name: str, filename: str):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # CRITICAL: avoid duplicate logs

        handler = RotatingFileHandler(
            LOG_DIR / filename,
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

        logger.addHandler(handler)

    @classmethod
    def setup(cls, level=logging.INFO):
        cls(level)
        return cls


    @staticmethod
    def get_logger(name: str):
        return logging.getLogger(name)


def setup_logging():
    """
    Initialize the logging configuration.
    This function should be called at the entry point of the application.
    """
    Logger.setup()