# Quickstart Guide

Get up and running with **LunarDump** in less than 5 minutes.

---

## Step 1: Generate an Encryption Key

Generate a cryptographically secure 256-bit AES key:

```bash
lunardump keygen --output secret.key
```

---

## Step 2: Create Configuration (`config.yaml`)

Create `config.yaml` in your project directory:

```yaml
version: "1.0"
backup:
  name: "production-postgres-daily"
  database:
    type: "postgres"
    host: "localhost"
    port: 5432
    name: "main_db"
    user: "postgres"
    password_env: "DB_PASSWORD"

  security:
    encrypt: true
    algorithm: "aes-256-gcm"
    key_env: "LUNARDUMP_ENCRYPTION_KEY"

  storage:
    provider: "s3"
    bucket: "company-db-backups"
    region: "ap-southeast-1"
    path: "daily/postgres/"
    retention_days: 30

  notifications:
    on_success: true
    on_failure: true
    channels:
      - type: "telegram"
        bot_token_env: "TELEGRAM_BOT_TOKEN"
        chat_id: "-100123456789"
```

---

## Step 3: Configure Environment Variables (`.env`)

Create a `.env` file to hold secret credentials safely:

```env
DB_PASSWORD=your_secure_db_password
LUNARDUMP_ENCRYPTION_KEY=f77693f31ebef68d774913969a3f6a57ee927f5e3243f221bff70c435f3fdb49
TELEGRAM_BOT_TOKEN=1660452017:AAHcoJg5lbfv7aAqGXaZaEk3-QXq130bD2k

# S3 Credentials
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## Step 4: Validate Configuration

Run a health check to verify database connectivity, client binary availability, and storage credentials:

```bash
lunardump config check --config config.yaml
```

---

## Step 5: Run Backup

Execute the backup pipeline:

```bash
lunardump run --config config.yaml
```
