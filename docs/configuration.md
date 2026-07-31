# Configuration Reference

Complete field-by-field reference guide for `config.yaml`.

---

## Configuration Schema Structure

### `database`
- **`type`**: Database engine type (`postgres`, `mysql`, or `mongo`).
- **`host`**: Hostname or IP address (e.g. `localhost` or `127.0.0.1`).
- **`port`**: Port number (Default: `5432` for Postgres, `3306` for MySQL, `27017` for Mongo).
- **`name`**: Target database name.
- **`user`**: Database username.
- **`password_env`**: Name of environment variable containing the password (e.g. `DB_PASSWORD`).

### `security`
- **`encrypt`**: Boolean flag (`true` / `false`) to enable/disable AES-256-GCM encryption.
- **`algorithm`**: Cryptographic algorithm (Default: `aes-256-gcm`).
- **`key_env`**: Name of environment variable holding key hex string, path to `.key` file, or raw 64-char hex key string.

### `storage`
- **`provider`**: Storage driver target (`s3`, `gcs`, or `local`).
- **`bucket`**: Bucket name (S3/GCS) or base directory path (`local`).
- **`region`**: Cloud region (e.g. `ap-southeast-1` for S3).
- **`path`**: Remote folder prefix path (e.g. `daily/postgres/`).
- **`retention_days`**: Retention window (integer, minimum `1`). Older backups will be automatically purged.
- **`endpoint_url`**: Optional custom S3 endpoint URL for Cloudflare R2 or MinIO (e.g. `http://minio.local:9000`).

### `notifications`
- **`on_success`**: Send alerts on successful backups (`true` / `false`).
- **`on_failure`**: Send alerts on backup failures (`true` / `false`).
- **`channels`**: List of notification channels (must contain at least 1 channel).
  - **Telegram**: `type: "telegram"`, `bot_token_env`, `chat_id`.
  - **Slack**: `type: "slack"`, `webhook_url_env`.
