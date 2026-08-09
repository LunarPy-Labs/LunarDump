"""Logging and CLI output utilities using Rich."""

import logging
from typing import Generator
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeElapsedColumn,
    TaskProgressColumn,
)

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


def create_progress_bar() -> Progress:
    """Create a styled interactive Rich progress bar for streaming tasks."""
    return Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=None, style="blue", complete_style="cyan"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def wrap_stream_with_progress(
    stream: Generator[bytes, None, None],
    progress: Progress,
    task_id: int,
) -> Generator[bytes, None, None]:
    """Wraps a byte generator to update the Rich progress bar on every yielded chunk."""
    for chunk in stream:
        if chunk:
            progress.update(task_id, advance=len(chunk))
            yield chunk
