<div align="center">
<img width="250" height="250" alt="LunarDump Logo" src="https://github.com/user-attachments/assets/d2a4805a-e374-46df-ba9e-176aaa6affad" />
</div>

# 🌖 LunarDump

[![PyPI version](https://img.shields.io/pypi/v/lunardump.svg?color=blue&nocache=1)](https://pypi.org/project/lunardump/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/lunardump?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/lunardump)
[![Documentation Status](https://readthedocs.org/projects/lunardump/badge/?version=latest)](https://lunardump.readthedocs.io/)
[![Docker Pulls](https://img.shields.io/docker/pulls/indhifarhandika/lunardump.svg)](https://hub.docker.com/r/indhifarhandika/lunardump)
[![Python Version](https://img.shields.io/pypi/pyversions/lunardump.svg)](https://pypi.org/project/lunardump/)
[![Coverage](https://img.shields.io/badge/coverage-82%25-brightgreen.svg)](https://pypi.org/project/lunardump/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Community](https://img.shields.io/badge/Telegram-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/lunardump)

> **Lightweight, Fast, Zero-Trust Database Backup Engine**

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

### 1. Install LunarDump via PyPI or uv

#### Via `pip`:
```bash
# Standard installation
pip install lunardump

# With Google Cloud Storage support
pip install "lunardump[gcs]"
```

#### Via `uv` (Fastest Python Tool Manager):
```bash
# Global CLI Tool Installation (Recommended for servers & workstations)
uv tool install lunardump

# One-Off Instant Execution without installing (like npx)
uvx lunardump run --config config.yaml
```

#### Via `Docker` (Zero Host Dependency Setup):
```bash
# Run LunarDump using official Docker image
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/.env:/app/.env:ro \
  indhifarhandika/lunardump:latest run --config /app/config.yaml
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

#### 🐧 Ubuntu
```bash
# For MySQL
sudo apt update && sudo apt install -y mysql-client

# For PostgreSQL
sudo apt install -y postgresql-client

# For MongoDB
sudo apt install -y mongodb-org-tools

```
#### 🐧 Debian
```bash
# For MySQL
sudo apt update && sudo apt install -y mariadb-client-compat

# For PostgreSQL
sudo apt install -y postgresql-client

# For MongoDB
sudo apt-get install gnupg curl
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg  --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
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
    type: "mysql"            # Options: postgres | mysql | mongo
    host: "127.0.0.1"
    port: 3306
    name: "username"
    user: "db_user"
    password_env: "DB_PASSWORD" # Environment variable holding database password

  security:
    encrypt: true
    algorithm: "aes-256-gcm"
    key_env: "LUNARDUMP_ENCRYPTION_KEY" # Env var name, key file path, or raw hex key string

  storage:
    # Target storage provider options:
    # - "s3"    : AWS S3, Cloudflare R2, MinIO, Wasabi, DigitalOcean Spaces
    # - "gcs"   : Google Cloud Storage
    # - "local" : Local server directory path
    provider: "s3"

    # Bucket name for cloud storage (S3/GCS), or root folder path for local storage (e.g., "/var/backups")
    bucket: "company-db-backups"

    # Storage region (Required for AWS S3; optional for GCS or Local)
    region: "ap-southeast-1"

    # Remote folder path prefix inside the bucket where backup files (.enc) will be stored
    path: "daily/mysql/"

    # Retention policy: automatic purge of backup archives older than the specified days
    retention_days: 30

    # Custom S3 endpoint URL (Required ONLY for MinIO, Cloudflare R2, or custom S3-compatible providers)
    # Examples:
    # - Cloudflare R2: "https://<ACCOUNT_ID>.r2.cloudflarestorage.com"
    # - MinIO        : "http://minio.internal:9000"
    endpoint_url: ""

  notifications:
    on_success: true
    on_failure: true

    # Notification Channels:
    # - Must contain AT LEAST 1 channel or CAN contain MULTIPLE channels (e.g. Telegram + Slack together).
    # - Supported types: "telegram" and "slack".
    channels:
      - type: "telegram"
        bot_token_env: "TELEGRAM_BOT_TOKEN"
        chat_id: "-82764827364"
      - type: "slack"
        webhook_url_env: "SLACK_WEBHOOK_URL"
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
│ DB Connection            │ 127.0.0.1:3306/db_user        │ CONNECTED                          │
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

### 🛡️ Verify Backup Integrity & Checksums (`--verify`)

Verify that a backup archive is authentic, uncorrupted, and decryptable without restoring it to database or disk:

```bash
# Verify local encrypted backup file
lunardump restore --file backup_20260730.enc --key secret.key --verify

# Download and verify directly from cloud storage (AWS S3 / GCS)
lunardump restore --config config.yaml --remote-key daily/mysql/backup_20260730.enc --verify
```

### Direct Database Dump Command

Perform an instant database dump directly to a local file or stdout without requiring a configuration file:

```bash
# Dump MySQL directly to file
lunardump db dump --type mysql --host localhost --user root --name db_name --output dump.sql

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

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Whether it's reporting a bug, adding support for new database engines or storage providers, or improving documentation, your help is greatly appreciated.

For full development setup, testing standards, and pull request guidelines, please read our [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Start for Contributors:

1. **Fork the Repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/indhifarhandika/LunarDump.git
   cd LunarDump
   ```
3. **Set up virtual environment & development dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,gcs]"
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
5. **Run test suite & ensure code coverage passes**:
   ```bash
   pytest --cov=lunardump --cov-report=term-missing
   ```
6. **Commit & Push your changes**, then submit a **Pull Request**!

---

## 🔒 Security

For security policies, vulnerability reporting, and cryptographic safety guidelines, please read our [SECURITY.md](SECURITY.md).

---

## 🌐 OS Distribution

<img width="400" height="100" alt="mini-logotype-hacktrack" src="https://github.com/user-attachments/assets/e5a189ec-7f94-457e-9556-98603d273ac1" />

* **HackTrack:** Pre-installed natively. You can run `lunardump` directly from the terminal or launch it from the system menu under **Extra Tools**.

---

## 💬 Community & Support

Have questions, need help setting up your backup pipeline, or want to discuss feature requests with other developers? Join our official Telegram Community:

[![Telegram Community](https://img.shields.io/badge/Telegram-Join_Community-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/lunardump)

---

## ☕ Support the Project

If you find **LunarDump** useful for your projects or infrastructure, please consider supporting its development:

[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-FF5252?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/indhifarhandika)

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
