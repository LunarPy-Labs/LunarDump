"""Daemon scheduler runner loop for LunarDump."""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

from rich.panel import Panel

from lunardump.core.scheduler.parser import parse_schedule
from lunardump.core.utils.logger import console, logger


class DaemonScheduler:
    """Continuous daemon loop executing LunarDump backup pipeline on schedule."""

    def __init__(self, expression: str, run_callback: Callable[[], None]):
        self.expression = expression
        self.run_callback = run_callback
        self.parser = parse_schedule(expression)
        self.running = True
        self._setup_signals()

    def _setup_signals(self):
        def _handle_signal(sig, frame):
            console.print("\n[yellow]Received stop signal. Shutting down LunarDump daemon scheduler...[/yellow]")
            self.running = False

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

    def start(self, once: bool = False):
        """Start the continuous daemon loop."""
        next_run = self.parser.get_next_run()
        time_until = next_run - datetime.now()
        hours, remainder = divmod(int(time_until.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        countdown_str = f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"

        console.print(
            Panel(
                f"[bold cyan]⏰ LunarDump Daemon Scheduler Active[/bold cyan]\n\n"
                f"• Schedule Pattern: [bold yellow]{self.expression}[/bold yellow]\n"
                f"• Description: [green]{self.parser.description}[/green]\n"
                f"• Next Execution: [bold white]{next_run.strftime('%Y-%m-%d %H:%M:%S')}[/bold white] (in {countdown_str})\n\n"
                f"[dim]Running continuously in background. Press Ctrl+C to terminate.[/dim]",
                title="Scheduler Daemon",
                border_style="cyan",
            )
        )

        while self.running:
            now = datetime.now()
            next_run = self.parser.get_next_run(now)
            sleep_secs = max(0.1, (next_run - now).total_seconds())

            # Sleep in short 0.5s ticks to respond instantly to Ctrl+C
            end_time = time.time() + sleep_secs
            while self.running and time.time() < end_time:
                time.sleep(min(0.5, max(0.01, end_time - time.time())))

            if not self.running:
                break

            console.print(f"\n[bold green]⏰ [{datetime.now().strftime('%H:%M:%S')}] Triggering Scheduled Backup Execution...[/bold green]")
            try:
                self.run_callback()
            except Exception as err:
                logger.error(f"Scheduled backup execution error: {err}")

            if once:
                break

        console.print("[bold cyan]LunarDump daemon scheduler terminated cleanly.[/bold cyan]")
