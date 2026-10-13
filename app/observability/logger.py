import logging
import sys


def configure_logging() -> None:
    """
    Configure the application's root logging system.

    The function sends logs to standard output using a consistent format
    containing timestamp, severity, logger name, and message.

    It should be called once during application startup, before creating
    or using module-level loggers.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger for an application module.

    Named loggers make it possible to identify the source of each event
    without coupling modules to a global logger instance.

    Args:
        name: Logger name, normally supplied through ``__name__``.

    Returns:
        A configured standard-library logger.
    """

    return logging.getLogger(name)