import logging
import sys

LOG_NAME = "trading-bot-stock-picker"


class Log:
    @staticmethod
    def setup(application_name: str, log_name: str = LOG_NAME) -> logging.Logger:
        logger = logging.getLogger(log_name)
        if not logger.hasHandlers():
            formatter = logging.Formatter(
                fmt=f"%(name)s :: {application_name} - "  # type: ignore
                f"%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S(%Z)",
            )

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(formatter)

            logger = logging.getLogger(log_name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            return logger
        else:
            return logger

    @staticmethod
    def debug(message: str, log_name=LOG_NAME) -> None:
        logger = logging.getLogger(log_name)
        logger.debug(message)

    @staticmethod
    def info(message: str, log_name=LOG_NAME) -> None:
        logger = logging.getLogger(log_name)
        logger.info(message)

    @staticmethod
    def warning(message: str, log_name=LOG_NAME) -> None:
        logger = logging.getLogger(log_name)
        logger.warning(message)

    @staticmethod
    def error(message: str, log_name=LOG_NAME) -> None:
        logger = logging.getLogger(log_name)
        logger.error(message)

    @staticmethod
    def critical(message: str, log_name=LOG_NAME) -> None:
        logger = logging.getLogger(log_name)
        logger.critical(message)
