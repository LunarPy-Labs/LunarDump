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
from lunardump.core.security import StreamCipher, generate_key_file, generate_key_hex
from lunardump.core.storage import get_storage
from lunardump.core.notification import notify_event
from lunardump.core.utils.logger import console, logger, error_console

def get_banner_panel() -> Panel:
    banner_content = (
        "[bold cyan]"
        " █░░ █░█ █▄░█ █▀█ █▀█ █▀▄ █░█ █▀▄▀█ █▀█\n"
        " █▄▄ █▄█ █░▀█ █▀█ █▀▄ █▄▀ █▄█ █░▀░█ █▀▀"
        "[/bold cyan]\n\n"
        "[bold white]LunarDump[/bold white] - Open-Source Zero-Trust Database Backup Engine"
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
):
    """Run full automated database backup pipeline according to rules in configuration file."""
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    console.print(
        Panel(
            f"[bold green]Starting LunarDump Pipeline[/bold green]\n"
            f"Config File: [yellow]{config_file}[/yellow]\n"
            f"Timestamp: [cyan]{timestamp_str}[/cyan]",
            title="LunarDump Execution",
        )
    )

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

    # 3. Stream Dump -> Encrypt -> Upload Pipeline
    ext = "enc" if profile.security.encrypt else "dump"
    filename = f"{profile.database.name}_{timestamp_str}.{ext}"

    console.print(f"[cyan]Streaming database dump for '[bold]{profile.database.name}[/bold]'...[/cyan]")
    try:
        data_stream = dumper.dump_stream()

        if profile.security.encrypt and encryption_key:
            console.print("[cyan]Encrypting dump stream on-the-fly with AES-256-GCM...[/cyan]")
            cipher = StreamCipher(encryption_key)
            data_stream = cipher.encrypt_stream(data_stream)

        storage_driver = get_storage(profile.storage)
        console.print(f"[cyan]Uploading encrypted backup to target ({profile.storage.provider})...[/cyan]")
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
            # Fall back to default config.yaml if available
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

            # Format byte size
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

    # 4. Normal Decrypt & Restore execution
    console.print(f"[cyan]Decrypting encrypted file '{file_label}'...[/cyan]")

    try:
        decrypted_stream = cipher.decrypt_stream(data_stream_gen)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            with open(output, "wb") as out_f:
                for chunk in decrypted_stream:
                    out_f.write(chunk)
            console.print(f"[bold green]Decrypted backup saved to:[/bold green] [yellow]{output}[/yellow]")
        else:
            # Stream to stdout
            for chunk in decrypted_stream:
                sys.stdout.buffer.write(chunk)
    except Exception as err:
        error_console.print(f"[bold red]Decryption Failed:[/bold red] {err}")
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


if __name__ == "__main__":
    app()
