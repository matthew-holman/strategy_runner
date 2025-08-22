import logging
import os
import sys

from typing import Optional


def _level_from_env(default_level: int) -> int:
    value = os.getenv("LOG_LEVEL")
    if not value:
        return default_level
    try:
        # Accept names (INFO/DEBUG/…) or ints ("20")
        return (
            int(value)
            if value.isdigit()
            else logging._nameToLevel.get(value.upper(), default_level)
        )
    except Exception:
        return default_level


def configure_logging(
    logger_name: str,
    *,
    level: int = logging.INFO,
    stream: Optional[object] = None,
    use_utc: bool = False,
    force: bool = True,  # replace any prior handlers so we own the config
) -> None:
    """
    Configure the root logger once with a fixed formatter.
    Ensures every LogRecord has `logger_name` via a LogRecordFactory.
    """
    root = logging.getLogger()

    # Optionally clear any pre-existing handlers (e.g., basicConfig from a library)
    if force and root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "logger_name"):
            record.logger_name = logger_name
        return record

    logging.setLogRecordFactory(record_factory)

    if stream is None:
        stream = sys.stdout

    handler = logging.StreamHandler(stream)  # type: ignore[arg-type]
    formatter = logging.Formatter(
        fmt="%(name)s :: %(logger_name)s - %(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S(%Z)",
    )
    if use_utc:
        import time

        formatter.converter = time.gmtime  # type: ignore[attr-defined]

    handler.setFormatter(formatter)
    root.setLevel(level)
    root.addHandler(handler)
