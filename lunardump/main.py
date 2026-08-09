"""LunarDump CLI Main Entrypoint application using Typer."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

import typer
from rich.panel import Panel
from rich.table import Table

from lunardump import __version__, __app_name__
from lunardump.config import load_config, LunarDumpConfig, DatabaseConfig
from lunardump.core.dumpers import get_dumper
from lunardump.core.restorers import get_restorer
from lunardump.core.migration import DatabaseMigrator
from lunardump.core.security import StreamCipher, generate_key_file, generate_key_hex
from lunardump.core.storage import get_storage
from lunardump.core.notification import notify_event
from lunardump.core.scheduler.runner import DaemonScheduler
from lunardump.core.utils.logger import (
    console,
    logger,
    error_console,
    create_progress_bar,
    wrap_stream_with_progress,
)

def get_banner_panel() -> Panel:
    banner_content = (
        "[bold cyan]"
        " █░░ █░█ █▄░█ █▀█ █▀█ █▀▄ █░█ █▀▄▀█ █▀█\n"
        " █▄▄ █▄█ █░▀█ █▀█ █▀▄ █▄▀ █▄█ █░▀░█ █▀▀"
        "[/bold cyan]\n\n"
        "[bold white]- Lightweight. Fast. Zero-Trust -[/bold white]"
    )
    return Panel(banner_content, border_style="cyan", expand=False)


app = typer.Typer(
    name=__app_name__,
    help="LunarDump - Open-Source Zero-Trust Database Backup Engine",
    add_completion=False,
    rich_markup_mode="rich",
)

db_app = typer.Typer(help="Direct database dump and connection commands")
config_app = typer.Typer(help="Configuration inspection and validation commands")

app.add_typer(db_app, name="db")
app.add_typer(config_app, name="config")


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]{__app_name__}[/bold cyan] version [bold yellow]{__version__}[/bold yellow]")
        raise typer.Exit()


def help_callback(ctx: typer.Context, value: bool):
    if value and not ctx.resilient_parsing:
        console.print(get_banner_panel())
        console.print(ctx.get_help())
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    help_flag: Optional[bool] = typer.Option(
        None,
        "--help",
        help="Show this message and exit.",
        callback=help_callback,
        is_eager=True,
    ),
):
    """LunarDump CLI tool."""
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        console.print(get_banner_panel())
        console.print("\nUse [bold cyan]lunardump --help[/bold cyan] for available commands and options.\n")
        raise typer.Exit()


@app.command("run")
def run_backup(
    config_file: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Path to YAML configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Validate configuration and connectivity without writing files"
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
        "-cr",
        help="Run continuously on schedule (e.g. 'day-2', 'week-14.5', 'month-1-2', 'every-15m', '0 2 * * *')",
    ),
):
    """Run full automated database backup pipeline according to rules in configuration file."""
    try:
        cfg: LunarDumpConfig = load_config(config_file)
        profile = cfg.backup
    except Exception as err:
        error_console.print(f"[bold red]Configuration Load Error:[/bold red] {err}")
        raise typer.Exit(code=1)

    # 1. Initialize & Validate Dumper Tool
    try:
        dumper = get_dumper(profile.database)
        if not dumper.check_tool():
            error_console.print(
                f"[bold red]Binary Tool Error:[/bold red] Dumper tool for engine '{profile.database.type}' is not installed."
            )
            raise typer.Exit(code=1)
    except Exception as err:
        error_console.print(f"[bold red]Dumper Initialization Error:[/bold red] {err}")
        raise typer.Exit(code=1)

    # 2. Check Encryption Key if enabled
    encryption_key = profile.security.key
    if profile.security.encrypt and not encryption_key:
        error_console.print(
            f"[bold red]Security Error:[/bold red] Encryption is enabled but key is missing. Set key in {profile.security.key_env} env variable or config key_path."
        )
        raise typer.Exit(code=1)

    if dry_run:
        console.print("[bold yellow]Dry-run mode completed successfully. All validations passed.[/bold yellow]")
        raise typer.Exit(code=0)

    schedule_expr = cron or profile.cron

    def _execute_single_run():
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = "enc" if profile.security.encrypt else "dump"
        filename = f"{profile.database.name}_{timestamp_str}.{ext}"

        try:
            with create_progress_bar() as progress:
                task_id = progress.add_task(
                    f"Streaming & Encrypting [bold white]{profile.database.name}[/bold white]...",
                    total=None,
                )

                data_stream = dumper.dump_stream()

                if profile.security.encrypt and encryption_key:
                    cipher = StreamCipher(encryption_key)
                    data_stream = cipher.encrypt_stream(data_stream)

                data_stream = wrap_stream_with_progress(data_stream, progress, task_id)

                storage_driver = get_storage(profile.storage)
                target_location = storage_driver.upload_stream(data_stream, filename)

            # 4. Retention Cleanup
            if profile.storage.retention_days > 0:
                console.print(
                    f"[cyan]Applying retention policy (purging backups older than {profile.storage.retention_days} days)...[/cyan]"
                )
                purged_items = storage_driver.clean_retention(profile.storage.retention_days)
                if purged_items:
                    console.print(f"[yellow]Purged {len(purged_items)} expired backup item(s).[/yellow]")

            # 5. Notify Success
            success_msg = (
                f"✅ *LunarDump Backup Completed Successfully*\n"
                f"• Job Name: `{profile.name}`\n"
                f"• Target DB: `{profile.database.name}` ({profile.database.type})\n"
                f"• Storage: `{target_location}`\n"
                f"• Encrypted: `{profile.security.encrypt}`\n"
                f"• Timestamp: `{timestamp_str}`"
            )
            notify_event(profile.notifications, success_msg, status="success")

            console.print(
                Panel(
                    f"[bold green]Backup Completed Successfully![/bold green]\nTarget Location: [yellow]{target_location}[/yellow]",
                    title="Success",
                )
            )

        except Exception as err:
            err_msg = str(err)
            error_console.print(f"[bold red]Backup Execution Failed:[/bold red] {err_msg}")
            fail_msg = (
                f"❌ *LunarDump Backup Failed*\n"
                f"• Job Name: `{profile.name}`\n"
                f"• Target DB: `{profile.database.name}`\n"
                f"• Error: `{err_msg}`"
            )
            notify_event(profile.notifications, fail_msg, status="failure")
            raise typer.Exit(code=1)

    if schedule_expr:
        scheduler = DaemonScheduler(schedule_expr, run_callback=_execute_single_run)
        scheduler.start()
    else:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        console.print(
            Panel(
                f"[bold green]Starting LunarDump Pipeline[/bold green]\n"
                f"Config File: [yellow]{config_file}[/yellow]\n"
                f"Timestamp: [cyan]{timestamp_str}[/cyan]",
                title="LunarDump Execution",
            )
        )
        _execute_single_run()


@app.command("keygen")
def keygen(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Optional file path to save generated encryption key"
    )
):
    """Generate a cryptographically secure 256-bit AES encryption key."""
    if output:
        key = generate_key_file(output)
        console.print(f"[green]Generated encryption key saved to:[/green] [bold yellow]{output}[/bold yellow]")
    else:
        key = generate_key_hex()
        console.print("[green]Generated 256-bit Encryption Key (Hex):[/green]")
        console.print(f"[bold yellow]{key}[/bold yellow]")
        console.print("\n[dim]Set this key in your environment variable (e.g. LUNARDUMP_ENCRYPTION_KEY)[/dim]")


@app.command("restore")
def restore_backup(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to local encrypted backup file (.enc)"
    ),
    key: Optional[str] = typer.Option(
        None, "--key", "-k", help="Secret key hex string or path to secret key file"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Path to save decrypted output file"
    ),
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to YAML configuration file for remote storage download"
    ),
    remote_key: Optional[str] = typer.Option(
        None, "--remote-key", "-r", help="Remote key/filename in cloud storage to download & verify/restore"
    ),
    target_db_type: Optional[str] = typer.Option(
        None, "--target-db-type", help="Target DB engine type (postgres, mysql, mongo) for direct restore"
    ),
    target_db_host: str = typer.Option(
        "localhost", "--target-db-host", help="Target DB host for direct restore"
    ),
    target_db_port: Optional[int] = typer.Option(
        None, "--target-db-port", help="Target DB port for direct restore"
    ),
    target_db_name: Optional[str] = typer.Option(
        None, "--target-db-name", help="Target DB name to inject restored payload"
    ),
    target_db_user: Optional[str] = typer.Option(
        None, "--target-db-user", help="Target DB user for direct restore"
    ),
    target_db_password_env: Optional[str] = typer.Option(
        None, "--target-db-password-env", help="Environment variable name containing target DB password"
    ),
    target_db_uri: Optional[str] = typer.Option(
        None, "--target-db-uri", help="Direct target DB connection URI"
    ),
    verify: bool = typer.Option(
        False, "--verify", help="Verify backup integrity, decrypt stream, and validate checksums without restoring to DB/disk"
    ),
):
    """Decrypt and restore an encrypted backup file, or verify its integrity and checksums with --verify."""
    secret_key = key
    data_stream_gen = None
    file_label = ""

    # Resolve configuration if provided for cloud storage download or key lookup
    cfg: Optional[LunarDumpConfig] = None
    if config_file and config_file.exists():
        try:
            cfg = load_config(config_file)
            if not secret_key and cfg.backup.security.key:
                secret_key = cfg.backup.security.key
        except Exception as err:
            error_console.print(f"[bold red]Configuration Load Error:[/bold red] {err}")
            raise typer.Exit(code=1)

    # 1. Determine input data stream source (local file or cloud storage)
    if remote_key:
        if not cfg:
            default_cfg_path = Path("config.yaml")
            if default_cfg_path.exists():
                cfg = load_config(default_cfg_path)
            else:
                error_console.print("[bold red]Configuration Error:[/bold red] --remote-key requires --config <path> or config.yaml")
                raise typer.Exit(code=1)

        try:
            storage_driver = get_storage(cfg.backup.storage)
            console.print(f"[cyan]Downloading '{remote_key}' from storage provider ({cfg.backup.storage.provider})...[/cyan]")
            data_stream_gen = storage_driver.download_stream(remote_key)
            file_label = f"{cfg.backup.storage.provider}://{cfg.backup.storage.bucket}/{remote_key}"
            if not secret_key and cfg.backup.security.key:
                secret_key = cfg.backup.security.key
        except Exception as err:
            error_console.print(f"[bold red]Cloud Storage Download Error:[/bold red] {err}")
            raise typer.Exit(code=1)

    elif file:
        if not file.exists():
            error_console.print(f"[bold red]File Error:[/bold red] Local backup file '{file}' does not exist.")
            raise typer.Exit(code=1)

        def _local_file_stream():
            with open(file, "rb") as f:
                while chunk := f.read(64 * 1024):
                    yield chunk

        data_stream_gen = _local_file_stream()
        file_label = str(file)

    else:
        error_console.print("[bold red]Argument Error:[/bold red] Please specify --file <path> or --remote-key <key> --config <config.yaml>")
        raise typer.Exit(code=1)

    # 2. Determine Secret Key
    if not secret_key:
        secret_key = os.getenv("LUNARDUMP_ENCRYPTION_KEY")

    if not secret_key:
        error_console.print("[bold red]Key Error:[/bold red] Encryption key is missing. Provide --key <string/file> or set LUNARDUMP_ENCRYPTION_KEY.")
        raise typer.Exit(code=1)

    if os.path.exists(secret_key):
        with open(secret_key, "r", encoding="utf-8") as f:
            secret_key = f.read().strip()

    cipher = StreamCipher(secret_key)

    # 3. Handle --verify Integrity Verification
    if verify:
        console.print(f"[cyan]Verifying integrity and decrypting payload for '[bold]{file_label}[/bold]'...[/cyan]")
        try:
            is_valid, byte_count, sha256_hex, md5_hex, total_chunks = cipher.verify_stream(data_stream_gen)

            kb = byte_count / 1024
            mb = kb / 1024
            size_str = f"{mb:.2f} MB ({byte_count:,} bytes)" if mb >= 1 else f"{kb:.2f} KB ({byte_count:,} bytes)"

            table = Table(title="LunarDump Backup Integrity & Verification Report", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Details", style="magenta")

            table.add_row("Backup Source", file_label)
            table.add_row("Integrity Status", "[bold green]PASSED (AES-256-GCM Authenticated)[/bold green]")
            table.add_row("Decrypted Size", size_str)
            table.add_row("SHA-256 Checksum", f"[bold yellow]{sha256_hex}[/bold yellow]")
            table.add_row("MD5 Checksum", f"[yellow]{md5_hex}[/yellow]")
            table.add_row("Validated Chunks", f"{total_chunks} chunk(s)")

            console.print(table)
            console.print("\n[bold green]✓ Backup file is authentic, uncorrupted, and ready for disaster recovery.[/bold green]")
            return

        except Exception as err:
            table = Table(title="LunarDump Backup Integrity & Verification Report", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Details", style="magenta")

            table.add_row("Backup Source", file_label)
            table.add_row("Integrity Status", "[bold red]FAILED / CORRUPTED[/bold red]")
            table.add_row("Error Details", str(err))

            console.print(table)
            error_console.print(f"\n[bold red]✗ Verification Failed: Backup file is corrupted, invalid format, or key mismatch.[/bold red]")
            raise typer.Exit(code=1)

    # 4. Decrypt Execution (Direct Target DB Injection OR File/stdout)
    try:
        decrypted_stream = cipher.decrypt_stream(data_stream_gen)

        target_db_cfg: Optional[DatabaseConfig] = None
        if target_db_type and target_db_name:
            target_db_cfg = DatabaseConfig(
                type=target_db_type,
                host=target_db_host,
                port=target_db_port,
                name=target_db_name,
                user=target_db_user or "postgres",
                password_env=target_db_password_env,
                uri=target_db_uri,
            )
        elif cfg and cfg.backup.target_database:
            target_db_cfg = cfg.backup.target_database

        if target_db_cfg:
            console.print(f"[cyan]Decrypting and injecting backup stream directly into target DB '[bold]{target_db_cfg.name}[/bold]' ({target_db_cfg.type})...[/cyan]")
            restorer = get_restorer(target_db_cfg)
            if not restorer.check_tool():
                error_console.print(f"[bold red]Restorer Tool Error:[/bold red] Client tool for engine '{target_db_cfg.type}' is not installed.")
                raise typer.Exit(code=1)

            with create_progress_bar() as progress:
                task_id = progress.add_task(
                    f"Decrypting & Injecting into [bold white]{target_db_cfg.name}[/bold white]...",
                    total=None,
                )
                stream_with_prog = wrap_stream_with_progress(decrypted_stream, progress, task_id)
                restorer.restore_stream(stream_with_prog)

            console.print(Panel(f"[bold green]✓ Successfully decrypted and restored backup directly into target database '{target_db_cfg.name}'![/bold green]", title="Restore Success"))
            return

        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "wb") as out_f:
                for chunk in decrypted_stream:
                    out_f.write(chunk)
            console.print(f"[bold green]Decrypted backup saved to:[/bold green] [yellow]{output}[/yellow]")
        else:
            for chunk in decrypted_stream:
                sys.stdout.buffer.write(chunk)
    except Exception as err:
        error_console.print(f"[bold red]Decryption / Restore Failed:[/bold red] {err}")
        raise typer.Exit(code=1)


@app.command("migrate")
def migrate_database(
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Path to YAML configuration file containing database and target_database"
    ),
    source_type: Optional[str] = typer.Option(None, "--source-type", help="Source DB engine: postgres, mysql, mongo"),
    source_host: str = typer.Option("localhost", "--source-host", help="Source DB host"),
    source_port: Optional[int] = typer.Option(None, "--source-port", help="Source DB port"),
    source_name: Optional[str] = typer.Option(None, "--source-name", help="Source DB name"),
    source_user: Optional[str] = typer.Option(None, "--source-user", help="Source DB user"),
    source_password_env: Optional[str] = typer.Option(None, "--source-password-env", help="Source DB password env var"),
    source_uri: Optional[str] = typer.Option(None, "--source-uri", help="Source DB URI"),
    target_type: Optional[str] = typer.Option(None, "--target-type", help="Target DB engine: postgres, mysql, mongo"),
    target_host: str = typer.Option("localhost", "--target-host", help="Target DB host"),
    target_port: Optional[int] = typer.Option(None, "--target-port", help="Target DB port"),
    target_name: Optional[str] = typer.Option(None, "--target-name", help="Target DB name"),
    target_user: Optional[str] = typer.Option(None, "--target-user", help="Target DB user"),
    target_password_env: Optional[str] = typer.Option(None, "--target-password-env", help="Target DB password env var"),
    target_uri: Optional[str] = typer.Option(None, "--target-uri", help="Target DB URI"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate connections without executing migration"),
):
    """Migrate database from Server A (Source DB) directly to Server B (Target DB) using Zero-Disk Pipe Streaming."""
    source_cfg: Optional[DatabaseConfig] = None
    target_cfg: Optional[DatabaseConfig] = None

    enc_key: Optional[str] = None
    if config_file and config_file.exists():
        try:
            cfg = load_config(config_file)
            source_cfg = cfg.backup.database
            target_cfg = cfg.backup.target_database
            if cfg.backup.security.encrypt and cfg.backup.security.key:
                enc_key = cfg.backup.security.key
        except Exception as err:
            error_console.print(f"[bold red]Configuration Load Error:[/bold red] {err}")
            raise typer.Exit(code=1)

    if not source_cfg and source_type and source_name:
        source_cfg = DatabaseConfig(
            type=source_type,
            host=source_host,
            port=source_port,
            name=source_name,
            user=source_user or "postgres",
            password_env=source_password_env,
            uri=source_uri,
        )

    if not target_cfg and target_type and target_name:
        target_cfg = DatabaseConfig(
            type=target_type,
            host=target_host,
            port=target_port,
            name=target_name,
            user=target_user or "postgres",
            password_env=target_password_env,
            uri=target_uri,
        )

    if not source_cfg or not target_cfg:
        error_console.print("[bold red]Argument Error:[/bold red] Specify --config <yaml> or provide both --source-... and --target-... flags.")
        raise typer.Exit(code=1)

    try:
        migrator = DatabaseMigrator(source_cfg, target_cfg, encryption_key=enc_key)
        migrator.check_prerequisites()

        if dry_run:
            console.print("[bold yellow]Migration dry-run completed successfully. Both source dumper and target restorer tools are available.[/bold yellow]")
            return

        migrator.execute_migration()

    except Exception as err:
        error_console.print(f"[bold red]Migration Error:[/bold red] {err}")
        raise typer.Exit(code=1)


@db_app.command("dump")
def db_dump_command(
    db_type: str = typer.Option(..., "--type", "-t", help="Database type: postgres, mysql, mongo"),
    uri: Optional[str] = typer.Option(None, "--uri", help="Database connection URI"),
    host: str = typer.Option("localhost", "--host", "-h", help="Database host"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Database port"),
    name: str = typer.Option("main_db", "--name", "-n", help="Database name"),
    user: str = typer.Option("postgres", "--user", "-u", help="Database username"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Execute raw database dump directly to file or stdout without config file."""
    cfg = DatabaseConfig(
        type=db_type,
        host=host,
        port=port,
        name=name,
        user=user,
        uri=uri,
    )
    dumper = get_dumper(cfg)
    if not dumper.check_tool():
        error_console.print(f"[bold red]Tool Missing:[/bold red] CLI binary for '{db_type}' is not installed.")
        raise typer.Exit(code=1)

    try:
        stream = dumper.dump_stream()
        if output:
            with open(output, "wb") as f:
                for chunk in stream:
                    f.write(chunk)
            console.print(f"[bold green]Database dump saved to:[/bold green] [yellow]{output}[/yellow]")
        else:
            for chunk in stream:
                sys.stdout.buffer.write(chunk)
    except Exception as err:
        error_console.print(f"[bold red]Direct Dump Error:[/bold red] {err}")
        raise typer.Exit(code=1)


@config_app.command("check")
def check_config(
    config_file: Path = typer.Option(
        Path("config.yaml"), "--config", "-c", help="Path to YAML configuration file", exists=True
    )
):
    """Test connectivity to database, storage target, and webhook channels."""
    console.print(f"[cyan]Testing LunarDump configuration from '{config_file}'...[/cyan]\n")

    table = Table(title="LunarDump System Health Check", show_header=True)
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="magenta")
    table.add_column("Status", style="bold")

    try:
        cfg = load_config(config_file)
        table.add_row("Config File", str(config_file), "[green]VALID (Pydantic v2)[/green]")
    except Exception as err:
        table.add_row("Config File", str(config_file), f"[red]INVALID: {err}[/red]")
        console.print(table)
        raise typer.Exit(code=1)

    profile = cfg.backup

    # Dumper tool & db connection check
    try:
        dumper = get_dumper(profile.database)
        tool_status = "[green]INSTALLED[/green]" if dumper.check_tool() else "[red]MISSING[/red]"
        table.add_row(f"DB Engine ({profile.database.type})", f"Tool binary check", tool_status)

        conn_ok = dumper.check_connection()
        conn_status = "[green]CONNECTED[/green]" if conn_ok else "[yellow]UNREACHABLE / UNTESTABLE[/yellow]"
        table.add_row(f"DB Connection", f"{profile.database.host}:{profile.database.port}/{profile.database.name}", conn_status)
    except Exception as err:
        table.add_row("DB Dumper", profile.database.type, f"[red]ERROR: {err}[/red]")

    # Security Key Check
    if profile.security.encrypt:
        key_ok = bool(profile.security.key)
        key_status = "[green]KEY READY[/green]" if key_ok else "[red]KEY MISSING[/red]"
        table.add_row("Encryption (AES-256-GCM)", f"Env: {profile.security.key_env}", key_status)
    else:
        table.add_row("Encryption", "Disabled", "[yellow]DISABLED[/yellow]")

    # Storage Check
    try:
        storage = get_storage(profile.storage)
        storage_ok = storage.test_connection()
        st_status = "[green]REACHABLE[/green]" if storage_ok else "[red]UNREACHABLE[/red]"
        table.add_row("Storage Target", f"{profile.storage.provider}://{profile.storage.bucket}", st_status)
    except Exception as err:
        table.add_row("Storage Target", profile.storage.provider, f"[red]ERROR: {err}[/red]")

    console.print(table)


@config_app.command("generate")
def generate_config(
    output_config: Path = typer.Option(
        Path("config.yaml"), "--config", "-c", help="Output path for generated YAML backup configuration file"
    ),
    output_migrate: Path = typer.Option(
        Path("migration.yaml"), "--migrate", "-m", help="Output path for generated YAML live migration configuration file"
    ),
    output_env: Path = typer.Option(
        Path(".env"), "--env", "-e", help="Output path for generated .env environment variables file"
    ),
    db_type: str = typer.Option(
        "postgres", "--db-type", "-t", help="Database engine type: postgres, mysql, mongo"
    ),
    storage: str = typer.Option(
        "s3", "--storage", "-s", help="Target storage provider: s3, gcs, local"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing config.yaml, migration.yaml, and .env files if present"
    ),
):
    """Generate production-ready config.yaml, migration.yaml, and .env template files with generated 256-bit AES key."""
    db_type_lower = db_type.lower()
    if db_type_lower not in ["postgres", "mysql", "mongo"]:
        error_console.print(f"[bold red]Argument Error:[/bold red] Invalid database engine type '{db_type}'. Choose postgres, mysql, or mongo.")
        raise typer.Exit(code=1)

    storage_lower = storage.lower()
    if storage_lower not in ["s3", "gcs", "local"]:
        error_console.print(f"[bold red]Argument Error:[/bold red] Invalid storage provider '{storage}'. Choose s3, gcs, or local.")
        raise typer.Exit(code=1)

    default_ports = {"postgres": 5432, "mysql": 3306, "mongo": 27017}
    default_users = {"postgres": "postgres", "mysql": "root", "mongo": "admin"}

    port = default_ports[db_type_lower]
    user = default_users[db_type_lower]

    gen_key = generate_key_hex()

    yaml_config_content = f"""# ==============================================================================
# LunarDump Backup Configuration File (Schema v1.0)
# Documentation: https://lunardump.readthedocs.io
# ==============================================================================
version: "1.0"
backup:
  name: "production-{db_type_lower}-backup"

  # Optional Daemon Schedule Pattern:
  # Examples: "day-2" (daily 02:00), "day-14.5" (daily 14:30), "week-14.5" (weekly), "month-1-2" (monthly), "every-15m", "0 2 * * *"
  # cron: "day-2"

  database:
    type: "{db_type_lower}"          # Options: postgres | mysql | mongo
    host: "localhost"
    port: {port}
    name: "production_db"
    user: "{user}"
    password_env: "DB_PASSWORD" # Environment variable name holding database password

  security:
    encrypt: true
    algorithm: "aes-256-gcm"
    key_env: "LUNARDUMP_ENCRYPTION_KEY" # Env variable name or direct hex key string

  storage:
    # Storage provider options: "s3" | "gcs" | "local"
    provider: "{storage_lower}"
    bucket: "company-db-backups"
    region: "ap-southeast-1"
    path: "daily/{db_type_lower}/"
    retention_days: 30
    endpoint_url: ""           # Optional: Custom S3 URL for MinIO or Cloudflare R2

  notifications:
    on_success: true
    on_failure: true
    channels:
      - type: "telegram"
        bot_token_env: "TELEGRAM_BOT_TOKEN"
        chat_id: "-100123456789"
      - type: "slack"
        webhook_url_env: "SLACK_WEBHOOK_URL"
"""

    yaml_migrate_content = f"""# ==============================================================================
# LunarDump Live DB Migration Configuration File (Schema v1.0)
# Documentation: https://lunardump.readthedocs.io
# ==============================================================================
version: "1.0"
backup:
  name: "production-{db_type_lower}-migration"

  # 1. SOURCE DATABASE (Server A - Database Asal)
  database:
    type: "{db_type_lower}"          # Options: postgres | mysql | mongo
    host: "192.168.1.10"
    port: {port}
    name: "production_db"
    user: "{user}"
    password_env: "SOURCE_DB_PASS" # Environment variable name for Source DB password

  # 2. TARGET DATABASE (Server B - Database Tujuan)
  target_database:
    type: "{db_type_lower}"          # Options: postgres | mysql | mongo
    host: "192.168.1.20"
    port: {port}
    name: "destination_db"
    user: "{user}"
    password_env: "TARGET_DB_PASS" # Environment variable name for Target DB password
"""

    env_content = f"""# ==============================================================================
# LunarDump Environment Variables Template
# Keep this file secure and NEVER commit it to git repositories!
# ==============================================================================

# Database Password
DB_PASSWORD="your_database_password_here"

# Migration Passwords (for lunardump migrate)
SOURCE_DB_PASS="password_server_a"
TARGET_DB_PASS="password_server_b"

# Cryptographic AES-256 Secret Encryption Key (Auto-Generated 256-bit Hex)
LUNARDUMP_ENCRYPTION_KEY="{gen_key}"

# Cloud Storage Credentials (AWS S3 / Cloudflare R2 / MinIO / GCS)
AWS_ACCESS_KEY_ID="your_aws_access_key_id"
AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"

# Google Cloud Storage (GCS) Service Account Key File Path
GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-service-account-key.json"

# Notification Webhooks & Bot Tokens
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
"""

    if output_config.exists() and not force:
        error_console.print(f"[bold yellow]File Warning:[/bold yellow] Config file '{output_config}' already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)

    if output_migrate.exists() and not force:
        error_console.print(f"[bold yellow]File Warning:[/bold yellow] Migration file '{output_migrate}' already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)

    if output_env.exists() and not force:
        error_console.print(f"[bold yellow]File Warning:[/bold yellow] Environment file '{output_env}' already exists. Use --force to overwrite.")
        raise typer.Exit(code=1)

    output_config.parent.mkdir(parents=True, exist_ok=True)
    output_config.write_text(yaml_config_content, encoding="utf-8")

    output_migrate.parent.mkdir(parents=True, exist_ok=True)
    output_migrate.write_text(yaml_migrate_content, encoding="utf-8")

    output_env.parent.mkdir(parents=True, exist_ok=True)
    output_env.write_text(env_content, encoding="utf-8")

    console.print(
        Panel(
            f"[bold green]✓ Templates Generated Successfully (3 Files)![/bold green]\n\n"
            f"• Backup Configuration: [bold yellow]{output_config}[/bold yellow]\n"
            f"• Migration Configuration: [bold yellow]{output_migrate}[/bold yellow]\n"
            f"• Environment File: [bold yellow]{output_env}[/bold yellow]\n"
            f"• Generated AES-256 Key: [bold cyan]{gen_key}[/bold cyan]\n\n"
            f"[dim]Edit '{output_env}' to set your real DB passwords and cloud credentials before running backups or migrations.[/dim]",
            title="LunarDump Template Generator",
            border_style="green",
        )
    )


@app.command("ui")
def ui_command(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Web UI bind host address"),
    port: int = typer.Option(8080, "--port", "-p", help="Web UI bind port number"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Automatically open browser upon server startup"),
):
    """Launch the interactive LunarDump Web Dashboard control panel."""
    try:
        from lunardump.ui import start_ui_server
    except ImportError:
        error_console.print(
            "[bold red]Module Error:[/bold red] Web UI dependencies are missing.\n"
            "Install them via: [bold cyan]pip install \"lunardump[ui]\"[/bold cyan]"
        )
        raise typer.Exit(code=1)

    start_ui_server(host=host, port=port, open_browser=open_browser)


if __name__ == "__main__":
    app()
