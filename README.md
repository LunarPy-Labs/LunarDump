# 🌖 LunarDump

> **Secure, Automated, and Zero-Trust Database Backup Engine**

**LunarDump** is a modern, developer-friendly Command-Line Interface (CLI) tool designed to streamline and secure your database backup workflows. Built with Python, it automates the entire lifecycle of database disaster recovery—from streaming dumps without memory overhead, applying military-grade AES-256 encryption, to syncing backups directly across cloud providers.

---

### ✨ Key Features

* 🗄️ **Multi-Engine Support:** Seamlessly handles PostgreSQL, MySQL, MariaDB, and MongoDB out-of-the-box.
* 🔐 **Zero-Trust Encryption:** End-to-end AES-256-GCM encryption applied locally before any data leaves your server.
* ⚡ **Memory-Efficient Streaming:** Streams database dumps and compresses them on-the-fly, preventing memory spikes even on multi-gigabyte databases.
* ☁️ **Multi-Cloud Syncing:** Direct integration with AWS S3, Google Cloud Storage, Cloudflare R2, and S3-compatible providers (like MinIO).
* 🧹 **Automated Retention Cleaner:** Automatically purges outdated backup archives based on your custom retention policy.
* 🔔 **Instant Telemetry:** Real-time progress indicators via Rich Terminal UI and automatic status alerts to Telegram, Slack, or Discord webhooks.

---

### 🚀 Why LunarDump?

Traditional shell script backups are fragile, hard to maintain, and often store unencrypted data on local disks. **LunarDump** solves these pain points by offering an enterprise-grade, configuration-driven pipeline in a single, easy-to-use CLI.

```bash
# Example: Run full backup pipeline via configuration file
lunardump run --config config.yaml

# Example: Verify connectivity to database, cloud storage, and webhooks
lunardump config check

## ☕ Support the Project

If you find **LunarDump** useful, please consider supporting its development:

[![Ko-Fi](https://img.shields.io/badge/Ko--Fi-FF5252?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/indhifarhandika)