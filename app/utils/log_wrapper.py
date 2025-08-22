import inspect
import logging

from logging import Logger
from typing import Any, Optional


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Public accessor for a logger. Prefer get_logger(__name__) at module scope
    if you want a bound logger rather than the static facade.
    """
    return logging.getLogger(name or "")


def _caller_module_name() -> str:
    """
    Determine the caller's module name so the facade can attribute logs correctly.
    """
    frame = inspect.currentframe()
    if frame is None:
        return ""
    # current -> _caller_module_name -> Log.method -> caller
    method_frame = frame.f_back
    if method_frame is None:
        return ""
    facade_frame = method_frame.f_back
    if facade_frame is None:
        return ""
    module_name = facade_frame.f_globals.get("__name__", "")
    return module_name if isinstance(module_name, str) else ""


class Log:
    """
    Thin facade over stdlib logging.
    """

    @staticmethod
    def _logger() -> Logger:
        return get_logger(_caller_module_name())

    @staticmethod
    def debug(message: str, **context: Any) -> None:
        Log._logger().debug(message, extra=(context or None))

    @staticmethod
    def info(message: str, **context: Any) -> None:
        Log._logger().info(message, extra=(context or None))

    @staticmethod
    def warning(message: str, **context: Any) -> None:
        Log._logger().warning(message, extra=(context or None))

    @staticmethod
    def error(message: str, **context: Any) -> None:
        # Standardize error formatting here if desired.
        Log._logger().error(message, extra=(context or None))

    @staticmethod
    def critical(message: str, **context: Any) -> None:
        Log._logger().critical(message, extra=(context or None))

    @staticmethod
    def exception(message: str, **context: Any) -> None:
        """
        Log an error with traceback. Use inside an `except` block.
        """
        Log._logger().exception(message, extra=(context or None))
