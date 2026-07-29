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

app = typer.Typer(
    name=__app_name__,
    help="LunarDump - Open-Source Zero-Trust Database Backup & Streaming Tool",
    add_completion=False,
    rich_markup_mode="markdown",
)

db_app = typer.Typer(help="Direct database dump and connection commands")
config_app = typer.Typer(help="Configuration inspection and validation commands")

app.add_typer(db_app, name="db")
app.add_typer(config_app, name="config")


def version_callback(value: bool):
    if value:
        console.print(f"[bold cyan]{__app_name__}[/bold cyan] version [bold yellow]{__version__}[/bold yellow]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    )
):
    """LunarDump CLI tool."""
    pass


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
    file: Path = typer.Option(
        ..., "--file", "-f", help="Path to encrypted backup file", exists=True
    ),
    key: str = typer.Option(
        ..., "--key", "-k", help="Secret key hex string or path to secret key file"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Path to save decrypted output file"
    ),
):
    """Decrypt an encrypted LunarDump file (.enc) and save or restore."""
    secret_key = key
    if os.path.exists(key):
        with open(key, "r", encoding="utf-8") as f:
            secret_key = f.read().strip()

    cipher = StreamCipher(secret_key)

    def file_stream():
        with open(file, "rb") as f:
            while chunk := f.read(64 * 1024):
                yield chunk

    console.print(f"[cyan]Decrypting encrypted file '{file}'...[/cyan]")

    try:
        decrypted_stream = cipher.decrypt_stream(file_stream())
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
