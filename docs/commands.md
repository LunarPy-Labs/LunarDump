# CLI Commands Reference

Complete command-line interface specification for LunarDump.

---

## 1. `lunardump run`

Execute the full automated backup pipeline according to `config.yaml`.

```bash
lunardump run --config config.yaml [--cron "day-2"] [--dry-run]
```

- `--config`, `-c`: Path to YAML configuration file.
- `--cron`, `-cr`: Run continuously in daemon mode on schedule (e.g., `"day-2"`, `"day-14.5"`, `"week-14.5"`, `"month-1-2"`, `"every-15m"`, `"0 2 * * *"`).
- `--dry-run`: Validate configurations and test connections without performing actual uploads or writes.

### Supported `--cron` Expressions

| Expression | Description |
| :--- | :--- |
| `day-2` | Daily at 02:00 AM |
| `day-14.5` / `day-14.05` | Daily at 14:05 (14.5 = 14:05) |
| `day-14.30` / `day-14:30` | Daily at 14:30 |
| `week-14.5` | Weekly on Sunday at 14:05 |
| `week-mon-14.30` | Weekly on Monday at 14:30 |
| `month-1-2` | 1st of every month at 02:00 AM |
| `month-15-14.5` | 15th of every month at 14:05 |
| `every-15m` | Every 15 minutes |
| `0 2 * * *` | Standard 5-field cron syntax |

---

## 2. `lunardump config check`

Inspect, validate, and run health checks against your database, client binaries, and storage targets.

```bash
lunardump config check --config config.yaml
```

---

## 3. `lunardump config generate`

Generate production-ready `config.yaml` (backup), `migration.yaml` (live migration), and `.env` (environment variables) template files with an auto-generated 256-bit AES encryption key.

```bash
lunardump config generate [--db-type postgres] [--storage s3] [--force]
```

- `--config`, `-c`: Path for generated YAML backup configuration file (default: `config.yaml`).
- `--migrate`, `-m`: Path for generated YAML live migration configuration file (default: `migration.yaml`).
- `--env`, `-e`: Path for generated environment variables file (default: `.env`).
- `--db-type`, `-t`: Database engine type (`postgres`, `mysql`, `mongo`).
- `--storage`, `-s`: Target storage provider (`s3`, `gcs`, `local`).
- `--force`, `-f`: Overwrite existing files if present.

---

## 4. `lunardump keygen`

Generate a cryptographically secure 256-bit AES encryption key.

```bash
lunardump keygen [--output secret.key]
```

---

## 4. `lunardump restore`

Decrypt encrypted `.enc` backup files back to plain SQL/dump format, verify integrity, or stream-inject directly into a target database engine.

```bash
# Decrypt local file to disk
lunardump restore --file backup.enc --key secret.key [--output restored.sql] [--verify]

# Stream-decrypt from Cloud Storage & inject directly into Target Database (Zero-Disk)
lunardump restore \
  --remote-key "daily/postgres/main_db_20260804.enc" \
  --config config.yaml \
  --target-db-type postgres \
  --target-db-host target-db.internal \
  --target-db-name main_dest \
  --target-db-user postgres
```

- `--file`, `-f`: Path to local encrypted file.
- `--remote-key`, `-r`: Remote file key in cloud storage bucket.
- `--key`, `-k`: Secret key string or path to key file.
- `--output`, `-o`: Output path to write decrypted file.
- `--target-db-type`: Target database engine (`postgres`, `mysql`, `mongo`) for direct injection.
- `--target-db-host`: Target database host.
- `--target-db-name`: Target database name to inject payload.
- `--verify`: Verify integrity and checksums without saving to disk.

---

## 5. `lunardump migrate`

Perform direct live database-to-database migration from **Server A (Source DB)** to **Server B (Target DB)** using Zero-Disk Pipe Streaming (0 bytes disk space used).

### Method 1: Via CLI Flags (Password in Environment Variables)

Passwords for Source DB and Target DB are safely passed via Environment Variables:

```bash
# 1. Set passwords in environment variables
export SOURCE_DB_PASS="password_server_a"
export TARGET_DB_PASS="password_server_b"

# 2. Execute live migration command
lunardump migrate \
  --source-type postgres \
  --source-host 192.168.1.10 \
  --source-port 5432 \
  --source-name db_prod \
  --source-user postgres \
  --source-password-env SOURCE_DB_PASS \
  --target-type postgres \
  --target-host 192.168.1.20 \
  --target-port 5432 \
  --target-name db_dest \
  --target-user postgres \
  --target-password-env TARGET_DB_PASS \
  [--dry-run]
```

### Method 2: Via YAML Configuration (`migration.yaml`)

Define both `database` (Source DB) and `target_database` (Target DB) in a YAML configuration file:

```yaml
version: "1.0"
backup:
  name: "live-db-migration"

  # Source Database (Server A)
  database:
    type: "postgres"
    host: "192.168.1.10"
    port: 5432
    name: "db_prod"
    user: "postgres"
    password_env: "SOURCE_DB_PASS"

  # Target Database (Server B)
  target_database:
    type: "postgres"
    host: "192.168.1.20"
    port: 5432
    name: "db_dest"
    user: "postgres"
    password_env: "TARGET_DB_PASS"
```

Then execute:

```bash
export SOURCE_DB_PASS="password_server_a"
export TARGET_DB_PASS="password_server_b"

lunardump migrate --config migration.yaml
```

---

## 6. `lunardump db dump`

Direct database dump to file or stdout without requiring a configuration file.

```bash
lunardump db dump --type mysql --host localhost --user root --name main_db --output dump.sql
```

---

## 7. `lunardump ui` (Web Dashboard)

Launch the interactive, real-time LunarDump Web Dashboard control panel directly in your browser.

```bash
lunardump ui [--host 127.0.0.1] [--port 8080] [--no-open]
```

- `--host`, `-h`: Web UI bind host address (default: `127.0.0.1`).
- `--port`, `-p`: Web UI bind port number (default: `8080`).
- `--open` / `--no-open`: Automatically open browser upon server startup (default: `--open`).
