"""Logging and CLI output utilities using Rich."""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()
error_console = Console(stderr=True)


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Setup and return standard logger styled with Rich."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    logger = logging.getLogger("lunardump")
    logger.setLevel(level)
    return logger


logger = setup_logger()
