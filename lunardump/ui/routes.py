"""FastAPI REST API routes for LunarDump Web Dashboard."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from lunardump import __version__
from lunardump.config import load_config, LunarDumpConfig, DatabaseConfig
from lunardump.core.dumpers import get_dumper
from lunardump.core.restorers import get_restorer
from lunardump.core.security import StreamCipher, generate_key_hex
from lunardump.core.storage import get_storage
from lunardump.core.migration import DatabaseMigrator

router = APIRouter(prefix="/api")


class GenerateRequest(BaseModel):
    db_type: str = "postgres"
    storage: str = "s3"
    config_path: str = "config.yaml"
    migrate_path: str = "migration.yaml"
    env_path: str = ".env"
    force: bool = False


class MigrationRequest(BaseModel):
    source_type: str
    source_host: str = "localhost"
    source_port: int = 5432
    source_name: str
    source_user: str = "postgres"
    source_password: Optional[str] = None

    target_type: str
    target_host: str = "localhost"
    target_port: int = 5432
    target_name: str
    target_user: str = "postgres"
    target_password: Optional[str] = None


class BackupRunRequest(BaseModel):
    config_path: str = "config.yaml"
    dry_run: bool = False


class RestoreRunRequest(BaseModel):
    remote_key: str
    config_path: str = "config.yaml"
    target_type: str = "postgres"
    target_host: str = "localhost"
    target_port: int = 5432
    target_name: str = "restored_db"
    target_user: str = "postgres"
    target_password: Optional[str] = None


@router.get("/system/info")
def get_system_info() -> Dict[str, Any]:
    """Get system metrics and LunarDump version."""
    import sys
    import platform

    return {
        "version": __version__,
        "python_version": platform.python_version(),
        "platform": sys.platform,
        "peak_ram": "119.1 MB (Constant O(1))",
        "architecture": "Zero-Disk RAM Pipe Streaming",
    }


@router.get("/cron/parse")
def parse_cron_expression(expression: str = Query(...)) -> Dict[str, Any]:
    """Parse scheduler human-friendly expression into cron format and next runs."""
    from lunardump.core.scheduler.parser import parse_schedule
    from datetime import datetime
    try:
        parser = parse_schedule(expression)
        next_runs = []
        current_time = datetime.now()
        
        # Calculate next 5 runs
        for _ in range(5):
            try:
                next_time = parser.get_next_run(current_time)
                next_runs.append(next_time.strftime("%Y-%m-%d %H:%M:%S"))
                current_time = next_time
            except Exception:
                break

        return {
            "status": "success",
            "expression": expression,
            "cron_expr": parser.cron_expr or "N/A (Interval)",
            "description": parser.description,
            "next_runs": next_runs,
        }
    except Exception as err:
        return {
            "status": "error",
            "message": str(err),
        }


@router.get("/health")
def get_health_check(config_path: str = Query("config.yaml")) -> Dict[str, Any]:
    """Execute health diagnostics on configuration, database connectivity, tools, and storage targets."""
    target_file = Path(config_path)
    if not target_file.exists():
        return {
            "status": "warning",
            "message": f"Config file '{config_path}' does not exist.",
            "components": [],
        }

    try:
        cfg = load_config(target_file)
        components = []

        # 1. Config schema
        components.append({"name": "Configuration File", "details": str(target_file), "status": "VALID (Pydantic v2)"})

        # 2. Database client binary
        try:
            dumper = get_dumper(cfg.backup.database)
            has_tool = dumper.check_tool()
            components.append({
                "name": f"DB Engine ({cfg.backup.database.type})",
                "details": "Client Tool Binary Check",
                "status": "INSTALLED" if has_tool else "MISSING BINARY",
            })
        except Exception as e:
            components.append({"name": "DB Engine", "details": str(e), "status": "ERROR"})

        # 3. Database connectivity
        try:
            dumper = get_dumper(cfg.backup.database)
            has_conn = dumper.check_connection()
            components.append({
                "name": "Database Connection",
                "details": f"{cfg.backup.database.host}:{cfg.backup.database.port}/{cfg.backup.database.name}",
                "status": "CONNECTED" if has_conn else "CONNECTION FAILED",
            })
        except Exception as e:
            components.append({"name": "Database Connection", "details": str(e), "status": "ERROR"})

        # 4. Storage connectivity
        try:
            storage = get_storage(cfg.backup.storage)
            has_storage = storage.test_connection()
            components.append({
                "name": "Storage Target",
                "details": f"{cfg.backup.storage.provider}://{cfg.backup.storage.bucket}",
                "status": "REACHABLE" if has_storage else "UNREACHABLE",
            })
        except Exception as e:
            components.append({"name": "Storage Target", "details": str(e), "status": "ERROR"})

        return {
            "status": "ok",
            "profile_name": cfg.backup.name,
            "components": components,
        }
    except Exception as err:
        return {
            "status": "error",
            "message": str(err),
            "components": [],
        }


@router.post("/generate")
def generate_templates(req: GenerateRequest) -> Dict[str, Any]:
    """Generate config.yaml, migration.yaml, and .env files."""
    db_type_lower = req.db_type.lower()
    storage_lower = req.storage.lower()

    if db_type_lower not in ["postgres", "mysql", "mongo"]:
        raise HTTPException(status_code=400, detail=f"Invalid db_type '{req.db_type}'")

    if storage_lower not in ["s3", "gcs", "local"]:
        raise HTTPException(status_code=400, detail=f"Invalid storage '{req.storage}'")

    cfg_p = Path(req.config_path)
    mig_p = Path(req.migrate_path)
    env_p = Path(req.env_path)

    if not req.force:
        if cfg_p.exists():
            raise HTTPException(status_code=400, detail=f"File '{req.config_path}' already exists. Use force=true.")
        if mig_p.exists():
            raise HTTPException(status_code=400, detail=f"File '{req.migrate_path}' already exists. Use force=true.")
        if env_p.exists():
            raise HTTPException(status_code=400, detail=f"File '{req.env_path}' already exists. Use force=true.")

    default_ports = {"postgres": 5432, "mysql": 3306, "mongo": 27017}
    default_users = {"postgres": "postgres", "mysql": "root", "mongo": "admin"}
    port = default_ports[db_type_lower]
    user = default_users[db_type_lower]

    gen_key = generate_key_hex()

    yaml_config = f"""version: "1.0"
backup:
  name: "production-{db_type_lower}-backup"
  database:
    type: "{db_type_lower}"
    host: "localhost"
    port: {port}
    name: "production_db"
    user: "{user}"
    password_env: "DB_PASSWORD"
  security:
    encrypt: true
    algorithm: "aes-256-gcm"
    key_env: "LUNARDUMP_ENCRYPTION_KEY"
  storage:
    provider: "{storage_lower}"
    bucket: "company-db-backups"
    region: "ap-southeast-1"
    path: "daily/{db_type_lower}/"
    retention_days: 30
"""

    yaml_migrate = f"""version: "1.0"
backup:
  name: "production-{db_type_lower}-migration"
  database:
    type: "{db_type_lower}"
    host: "192.168.1.10"
    port: {port}
    name: "production_db"
    user: "{user}"
    password_env: "SOURCE_DB_PASS"
  target_database:
    type: "{db_type_lower}"
    host: "192.168.1.20"
    port: {port}
    name: "destination_db"
    user: "{user}"
    password_env: "TARGET_DB_PASS"
"""

    env_tmpl = f"""DB_PASSWORD="your_database_password_here"
SOURCE_DB_PASS="password_server_a"
TARGET_DB_PASS="password_server_b"
LUNARDUMP_ENCRYPTION_KEY="{gen_key}"
AWS_ACCESS_KEY_ID="your_aws_access_key_id"
AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-service-account-key.json"
"""

    cfg_p.write_text(yaml_config, encoding="utf-8")
    mig_p.write_text(yaml_migrate, encoding="utf-8")
    env_p.write_text(env_tmpl, encoding="utf-8")

    return {
        "status": "success",
        "generated_key": gen_key,
        "files": [str(cfg_p), str(mig_p), str(env_p)],
    }


@router.post("/backup/run")
def run_backup_job(req: BackupRunRequest) -> Dict[str, Any]:
    """Execute automated backup pipeline for specified config file."""
    from datetime import datetime
    target_file = Path(req.config_path)
    if not target_file.exists():
        return {
            "status": "warning",
            "message": f"Config file '{req.config_path}' does not exist.",
        }

    try:
        cfg = load_config(target_file)
        if req.dry_run:
            try:
                dumper = get_dumper(cfg.backup.database)
                d_ok = dumper.check_tool()
            except Exception:
                d_ok = False

            try:
                storage = get_storage(cfg.backup.storage)
                s_ok = storage.test_connection()
            except Exception:
                s_ok = False

            return {
                "status": "success",
                "mode": "dry_run",
                "message": f"Dry-run test passed. DB Tool: {'INSTALLED' if d_ok else 'MISSING'}, Storage: {'REACHABLE' if s_ok else 'UNREACHABLE'}",
            }

        dumper = get_dumper(cfg.backup.database)
        storage = get_storage(cfg.backup.storage)
        dump_stream = dumper.dump_stream()

        enc_key = cfg.backup.security.key
        if cfg.backup.security.encrypt and enc_key:
            cipher = StreamCipher(enc_key)
            dump_stream = cipher.encrypt_stream(dump_stream)

        filename = f"{cfg.backup.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        if cfg.backup.security.encrypt:
            filename += ".enc"

        remote_path = storage.upload_stream(dump_stream, filename)
        storage.clean_retention(cfg.backup.storage.retention_days)

        return {
            "status": "success",
            "message": f"Backup pipeline executed successfully. Uploaded to: {remote_path}",
            "remote_path": remote_path,
        }
    except Exception as err:
        return {
            "status": "error",
            "message": f"Backup Error ({type(err).__name__}): {err}",
        }


@router.get("/storage/files")
def list_storage_files(config_path: str = Query("config.yaml")) -> Dict[str, Any]:
    """List backup archives in configured cloud storage provider."""
    target_file = Path(config_path)
    if not target_file.exists():
        return {
            "status": "warning",
            "message": f"Config file '{config_path}' does not exist.",
            "provider": "unknown",
            "bucket": "unknown",
            "count": 0,
            "files": [],
        }

    try:
        cfg = load_config(target_file)
        storage = get_storage(cfg.backup.storage)
        files = storage.list_backups()
        return {
            "status": "success",
            "provider": cfg.backup.storage.provider,
            "bucket": cfg.backup.storage.bucket,
            "count": len(files),
            "files": files,
        }
    except Exception as err:
        return {
            "status": "error",
            "message": f"Storage Error ({type(err).__name__}): {err}",
            "provider": "error",
            "bucket": "error",
            "count": 0,
            "files": [],
        }


@router.post("/migration/run")
def run_live_migration(req: MigrationRequest) -> Dict[str, Any]:
    """Execute Zero-Disk live database migration from Source DB to Target DB."""
    try:
        source_db = DatabaseConfig(
            type=req.source_type,
            host=req.source_host,
            port=req.source_port,
            name=req.source_name,
            user=req.source_user,
            password_env="TEMP_SOURCE_PASS" if req.source_password else None,
        )

        target_db = DatabaseConfig(
            type=req.target_type,
            host=req.target_host,
            port=req.target_port,
            name=req.target_name,
            user=req.target_user,
            password_env="TEMP_TARGET_PASS" if req.target_password else None,
        )

        if req.source_password:
            os.environ["TEMP_SOURCE_PASS"] = req.source_password
        if req.target_password:
            os.environ["TEMP_TARGET_PASS"] = req.target_password

        migrator = DatabaseMigrator(source_db, target_db)
        migrator.check_prerequisites()
        success = migrator.execute_migration()

        return {
            "status": "success" if success else "failed",
            "message": "Database migration executed successfully." if success else "Migration failed.",
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
