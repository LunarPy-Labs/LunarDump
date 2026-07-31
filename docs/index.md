# 🌔 LunarDump CLI Documentation

Welcome to the official documentation for **LunarDump**, a modern, developer-friendly Command-Line Interface (CLI) tool designed to streamline, encrypt, and automate your database backup workflows.

---

## 🌟 Key Architecture & Features

- **Multi-Engine Support**: Seamlessly handles **PostgreSQL**, **MySQL**, **MariaDB**, and **MongoDB**.
- **Zero-Trust AES-256-GCM Encryption**: Local, authenticated end-to-end encryption applied before any data leaves your server.
- **Memory-Efficient Streaming**: Direct pipe streaming through 64KB chunks in RAM directly into cloud storage endpoints—preventing RAM spikes even on multi-gigabyte databases.
- **Multi-Cloud Target**: Built-in support for **AWS S3**, **Google Cloud Storage (GCS)**, **Cloudflare R2**, **MinIO**, and local storage.
- **Backup Verification (`--verify`)**: On-the-fly stream decryption, integrity authentication, and checksum generation (SHA-256 / MD5).
- **Automated Retention Cleaner**: Automatically purges expired backup archives based on your custom `retention_days` window.
- **Rich Telemetry**: Interactive progress UI and webhook notifications to **Telegram** & **Slack**.

---

## 🚀 Quick Navigation

- [Installation & Setup](installation.md) - Install via `pip`, `uv`, and verify system binary dependencies.
- [Quickstart Guide](quickstart.md) - Set up your first `config.yaml` and `.env` in 5 minutes.
- [Configuration Reference](configuration.md) - Complete schema reference guide for database, security, and cloud storage settings.
- [CLI Commands](commands.md) - Reference for `run`, `config check`, `keygen`, `restore`, and `db dump`.
- [Backup Integrity Verification](verification.md) - Validate backup files with `--verify`.
