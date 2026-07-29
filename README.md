# 🌖 LunarDump

[![PyPI version](https://img.shields.io/pypi/v/lunardump.svg?color=blue)](https://pypi.org/project/lunardump/)
[![Python Version](https://img.shields.io/pypi/pyversions/lunardump.svg)](https://pypi.org/project/lunardump/)
[![Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen.svg)](https://pypi.org/project/lunardump/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-FF5252?style=flat-square&logo=kofi&logoColor=white)](https://ko-fi.com/indhifarhandika)

> **Secure, Automated, and Zero-Trust Database Backup Engine**

**LunarDump** is a modern, developer-friendly Command-Line Interface (CLI) tool designed to streamline and secure your database backup workflows. Built with Python, it automates the entire lifecycle of database disaster recovery—from streaming dumps without memory overhead, applying military-grade AES-256-GCM encryption, to syncing backups directly across cloud providers.

---

## ✨ Key Features

* 🗄️ **Multi-Engine Support:** Seamlessly handles **PostgreSQL**, **MySQL**, **MariaDB**, and **MongoDB** out-of-the-box.
* 🔐 **Zero-Trust Encryption:** End-to-end authenticated **AES-256-GCM** encryption applied locally before any data leaves your server.
* ⚡ **Memory-Efficient Streaming:** Streams database dumps directly through encryption into cloud storage, preventing RAM spikes even on multi-gigabyte databases.
* ☁️ **Multi-Cloud Syncing:** Direct integration with **AWS S3**, **Google Cloud Storage (GCS)**, **Cloudflare R2**, and **MinIO**.
* 🧹 **Automated Retention Cleaner:** Automatically purges outdated backup archives according to your custom retention window.
* 🔔 **Instant Telemetry:** Rich terminal UI with progress bars, health-check tables, and webhook alerts to **Telegram** & **Slack**.

---

## 📦 Installation & Requirements

### 1. Install LunarDump via PyPI

```bash
# Standard installation
pip install lunardump

# Optional: Install with Google Cloud Storage support
pip install "lunardump[gcs]"
```

### 2. System Binary Prerequisites

LunarDump leverages native client dump tools for streaming efficiency. Ensure the CLI client for your database engine is installed on your system:

#### 🍏 macOS (Homebrew)
```bash
# For MySQL / MariaDB
brew install mysql-client
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"

# For PostgreSQL
brew install libpq

# For MongoDB
brew install mongodb-database-tools
```

#### 🐧 Ubuntu / Debian
```bash
# For MySQL
sudo apt update && sudo apt install -y mysql-client

# For PostgreSQL
sudo apt install -y postgresql-client

# For MongoDB
sudo apt install -y mongodb-org-tools
```

---

## 🚀 Step-by-Step Tutorial & Usage Guide

### Step 1: Generate Encryption Key

Generate a cryptographically secure 256-bit (64-character hex) key:

```bash
# Print key to terminal stdout
lunardump keygen

# Or save key directly to a secure secret file (with 0600 permissions)
lunardump keygen --output secret.key
```

### Step 2: Create Configuration (`config.yaml`)

Create your `config.yaml` file to define backup jobs and target destinations:

```yaml
version: "1.0"
backup:
  name: "production-mysql-daily"
  
  database:
    type: "mysql"            # postgres | mysql | mongo
    host: "127.0.0.1"
    port: 3306
    name: "username"
    user: "db_user"
    password_env: "DB_PASSWORD" # Environment variable holding database password

  security:
    encrypt: true
    algorithm: "aes-256-gcm"
    key_env: "LUNARDUMP_ENCRYPTION_KEY" # Env var holding secret key

  storage:
    provider: "s3"           # s3 | gcs | local
    bucket: "company-db-backups"
    region: "ap-southeast-1"
    path: "daily/mysql/"
    retention_days: 30
    endpoint_url: ""         # Optional for S3-compatible (MinIO / Cloudflare R2)

  notifications:
    on_success: true
    on_failure: true
    channels:
      - type: "telegram"
        bot_token_env: "TELEGRAM_BOT_TOKEN"
        chat_id: "-82764827364"
```

### Step 3: Setup Environment Variables (`.env`)

Keep secret credentials out of your configuration files using a `.env` file or environment variables:

```bash
# Create .env file
cat <<EOF > .env
DB_PASSWORD="your_database_password_here"
LUNARDUMP_ENCRYPTION_KEY="a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8"
TELEGRAM_BOT_TOKEN="872642874:HkajbsdakJkajSAs2kdad-hadkjaKJHS"

# Cloud Storage Credentials (AWS S3)
AWS_ACCESS_KEY_ID="AKIAXXXXXXXXXXXXXXXX"
AWS_SECRET_ACCESS_KEY="XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Or for Google Cloud Storage (GCS)
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
EOF

# Load environment variables in your current shell
source .env
```

### Step 4: Verify System Connectivity (Health Check)

Before running your backup job, test connectivity to your database, CLI tools, encryption keys, and cloud storage:

```bash
lunardump config check --config config.yaml
```

Output preview:
```text
                                  LunarDump System Health Check                                  
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component                ┃ Details                       ┃ Status                             ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Config File              │ config.yaml                   │ VALID (Pydantic v2)                │
│ DB Engine (mysql)        │ Tool binary check             │ INSTALLED                          │
│ DB Connection            │ 127.0.0.1:3306/live_chat      │ CONNECTED                          │
│ Encryption (AES-256-GCM) │ Env: LUNARDUMP_ENCRYPTION_KEY │ KEY READY                          │
│ Storage Target           │ s3://company-db-backups       │ REACHABLE                          │
└──────────────────────────┴───────────────────────────────┴────────────────────────────────────┘
```

### Step 5: Execute Backup Pipeline

Run the automated backup pipeline:

```bash
# Dry-run mode: validates configuration without creating files
lunardump run --config config.yaml --dry-run

# Run full backup (Dump -> Encrypt -> Upload -> Retention Cleanup -> Webhook Alert)
lunardump run --config config.yaml
```

---

## 🔓 Decryption & Disaster Recovery

### Decrypt and Restore Encrypted Backup (`.enc`)

Decrypt an AES-256-GCM encrypted backup file back to plain database SQL/dump format:

```bash
# Decrypt using key file
lunardump restore --file backup_20260729.enc --key secret.key --output backup_decrypted.sql

# Decrypt using raw key string
lunardump restore --file backup_20260729.enc --key f77693f31ebef68d774913969a3f6a57ee... --output backup_decrypted.sql
```

### Direct Database Dump Command

Perform an instant database dump directly to a local file or stdout without requiring a configuration file:

```bash
# Dump MySQL directly to file
lunardump db dump --type mysql --host localhost --user root --name live_chat --output dump.sql

# Dump PostgreSQL directly to stdout
lunardump db dump --type postgres --host localhost --user postgres --name main_db > dump.sql
```

---

## ⏰ Automating with Cron Jobs

Automate daily database backups by setting up a cron job on your server:

```bash
# Open crontab editor
crontab -e

# Add daily backup entry at 02:00 AM
0 2 * * * cd /opt/lunardump && source .env && lunardump run --config config.yaml >> /var/log/lunardump.log 2>&1
```

---

## ☕ Support the Project

If you find **LunarDump** useful for your projects or infrastructure, please consider supporting its development:

[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-FF5252?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/indhifarhandika)

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.