"""Database migration module using Zero-Disk Pipe Streaming."""

import time
from typing import Optional
from rich.panel import Panel

from lunardump.config.schema import DatabaseConfig
from lunardump.core.dumpers import get_dumper
from lunardump.core.restorers import get_restorer
from lunardump.core.security import StreamCipher
from lunardump.core.utils.logger import console, create_progress_bar, wrap_stream_with_progress


class DatabaseMigrator:
    """Manages Zero-Disk Pipe Streaming migration between Source DB and Target DB."""

    def __init__(
        self,
        source_db: DatabaseConfig,
        target_db: DatabaseConfig,
        encryption_key: Optional[str] = None,
    ):
        self.source_db = source_db
        self.target_db = target_db
        self.encryption_key = encryption_key
        self.source_dumper = get_dumper(source_db)
        self.target_restorer = get_restorer(target_db)

    def check_prerequisites(self) -> bool:
        """Validate dumper & restorer tools and database connectivity."""
        if not self.source_dumper.check_tool():
            raise RuntimeError(f"Source database tool for '{self.source_db.type}' is missing.")

        if not self.target_restorer.check_tool():
            raise RuntimeError(f"Target database tool for '{self.target_db.type}' is missing.")

        return True

    def execute_migration(self) -> bool:
        """Execute live database migration via zero-disk RAM streaming."""
        self.check_prerequisites()

        mode_desc = (
            "Zero-Disk In-Flight Encrypted Pipe Streaming (AES-256-GCM)"
            if self.encryption_key
            else "Zero-Disk RAM Pipe Streaming (0 Bytes Disk Usage)"
        )

        console.print(
            Panel(
                f"[bold cyan]🚀 Starting Zero-Disk Database Migration[/bold cyan]\n\n"
                f"• Source DB: [yellow]{self.source_db.type}://{self.source_db.host}:{self.source_db.port}/{self.source_db.name}[/yellow]\n"
                f"• Target DB: [green]{self.target_db.type}://{self.target_db.host}:{self.target_db.port}/{self.target_db.name}[/green]\n"
                f"• Mode: [bold white]{mode_desc}[/bold white]",
                title="Migration Pipeline",
                border_style="cyan",
            )
        )

        start_time = time.time()
        dump_stream = self.source_dumper.dump_stream()

        if self.encryption_key:
            cipher = StreamCipher(self.encryption_key)
            encrypted_stream = cipher.encrypt_stream(dump_stream)
            dump_stream = cipher.decrypt_stream(encrypted_stream)

        with create_progress_bar() as progress:
            task_id = progress.add_task(
                f"Migrating [bold yellow]{self.source_db.name}[/bold yellow] ➔ [bold green]{self.target_db.name}[/bold green]...",
                total=None,
            )
            data_stream = wrap_stream_with_progress(dump_stream, progress, task_id)
            success = self.target_restorer.restore_stream(data_stream)

        elapsed = time.time() - start_time
        if success:
            console.print(
                Panel(
                    f"[bold green]✓ Database Migration Completed Successfully![/bold green]\n"
                    f"Time Elapsed: [cyan]{elapsed:.2f} seconds[/cyan]",
                    title="Migration Success",
                    border_style="green",
                )
            )
            return True
        else:
            raise RuntimeError("Database migration failed during restorer execution.")
