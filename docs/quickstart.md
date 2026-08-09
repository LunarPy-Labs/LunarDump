# Quickstart Guide

Get up and running with **LunarDump** in less than 2 minutes without writing configuration files manually.

---

## Step 1: Generate Configuration & Environment Templates

Run `lunardump config generate` to automatically create production-ready `config.yaml`, `migration.yaml`, and `.env` template files (pre-populated with an auto-generated 256-bit AES encryption key):

```bash
# Generate default templates (PostgreSQL + S3)
lunardump config generate

# Or specify your database engine (postgres | mysql | mongo) and storage target (s3 | gcs | local)
lunardump config generate --db-type mysql --storage s3
```

This generates three files instantly:
- `config.yaml`: Backup pipeline configuration.
- `migration.yaml`: Live database-to-database migration template.
- `.env`: Pre-configured environment file with a cryptographically secure 256-bit AES key.

---

## Step 2: Edit Credentials in `.env`

Open `.env` and fill in your actual database password and cloud storage credentials:

```env
DB_PASSWORD="your_actual_db_password"
LUNARDUMP_ENCRYPTION_KEY="f48a9b2c..." # Auto-generated AES-256 key

# Cloud Storage Credentials
AWS_ACCESS_KEY_ID="your_aws_access_key_id"
AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"

# Notifications (Optional)
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
```

---

## Step 3: Validate Configuration & Connectivity

Run a health check to verify database connectivity, client binary availability, and storage credentials:

```bash
lunardump config check --config config.yaml
```

---

## Step 4: Execute Backup

Run your first automated, zero-disk pipe streaming backup:

```bash
lunardump run --config config.yaml
```
