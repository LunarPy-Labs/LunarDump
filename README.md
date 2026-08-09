<div align="center">
<img width="250" height="250" alt="LunarDump Logo" src="https://github.com/user-attachments/assets/d2a4805a-e374-46df-ba9e-176aaa6affad" />
</div>

# 🌖 LunarDump

[![PyPI version](https://img.shields.io/pypi/v/lunardump.svg?color=blue&nocache=1)](https://pypi.org/project/lunardump/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/lunardump?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/lunardump)
[![Documentation Status](https://readthedocs.org/projects/lunardump/badge/?version=latest)](https://lunardump.indhifarhandika.dev/)
[![Docker Pulls](https://img.shields.io/docker/pulls/indhifarhandika/lunardump.svg)](https://hub.docker.com/r/indhifarhandika/lunardump)
[![Coverage](https://img.shields.io/badge/coverage-83%25-brightgreen.svg)](https://pypi.org/project/lunardump/)
[![Memray Peak RAM](https://img.shields.io/badge/Peak_RAM-119.1MB_(8GB_Dump)-success)](https://lunardump.readthedocs.io/en/latest/architecture/#5-real-world-benchmark-memray-memory-profiler)
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

### Step 1: Generate Configuration & Environment Templates

Generate production-ready configuration and `.env` template files instantly without manual typing:

```bash
# Generate default templates (PostgreSQL + S3)
lunardump config generate

# Or specify database engine (postgres | mysql | mongo) and storage target (s3 | gcs | local)
lunardump config generate --db-type postgres --storage s3
```

This single command automatically generates 3 files:
1. `config.yaml`: Pre-configured backup job profile.
2. `migration.yaml`: Live database-to-database migration profile.
3. `.env`: Environment file containing an **auto-generated cryptographically secure 256-bit AES key**!

---

### Step 2: Configure Environment Credentials (`.env`)

Open `.env` to set your real database passwords and cloud credentials:

```env
# Database Passwords
DB_PASSWORD="your_database_password_here"
SOURCE_DB_PASS="password_server_a"
TARGET_DB_PASS="password_server_b"

# Cryptographic AES-256 Secret Key (Auto-Generated Hex)
LUNARDUMP_ENCRYPTION_KEY="f48a9b2c..."

# Cloud Storage Credentials (AWS S3)
AWS_ACCESS_KEY_ID="your_aws_access_key_id"
AWS_SECRET_ACCESS_KEY="your_aws_secret_access_key"

# Or for Google Cloud Storage (GCS)
GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Notifications
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
```

### Step 3: Verify System Connectivity (Health Check)

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

### Step 4: Execute Backup Pipeline

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

## ⏰ Automating with Daemon & Schedule (`--cron`)

LunarDump features a built-in continuous background daemon runner. You can automate recurring backup schedules directly using human-friendly schedule expressions or standard cron syntax:

### 1. Built-in Daemon Runner (`--cron`)

Run LunarDump continuously as a background daemon process:

```bash
# Run daily at 02:00 AM (Human-friendly string)
lunardump run --config config.yaml --cron "day-2"

# Run weekly on Monday at 14:30
lunardump run --config config.yaml --cron "week-mon-14.5"

# Run monthly on the 1st of every month at 02:00 AM
lunardump run --config config.yaml --cron "month-1-2"

# Run every 15 minutes
lunardump run --config config.yaml --cron "every-15m"

# Standard 5-field cron syntax
lunardump run --config config.yaml --cron "0 2 * * *"
```

> 💡 **Tip:** You can also define `cron: "day-2"` inside your `config.yaml` file so running `lunardump run --config config.yaml` automatically launches daemon mode.

### 2. System Crontab (OS-Level Scheduling)

Alternatively, schedule one-off backup runs via Linux system `crontab`:

```bash
# Open crontab editor
crontab -e

# Add daily backup entry at 02:00 AM
0 2 * * * cd /opt/lunardump && source .env && lunardump run --config config.yaml >> /var/log/lunardump.log 2>&1
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Whether it's reporting a bug, adding support for new database engines or storage providers, or improving documentation, your help is greatly appreciated.

For full development setup, testing standards, and pull request guidelines, please read our [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🔒 Security

For security policies, vulnerability reporting, and cryptographic safety guidelines, please read our [SECURITY.md](SECURITY.md).

---

## 🌐 OS Distribution

<a href="https://www.hacktrack-linux.org/" target="_blank"><img width="400" height="100" alt="mini-logotype-hacktrack" src="https://github.com/user-attachments/assets/e5a189ec-7f94-457e-9556-98603d273ac1" /></a>

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
