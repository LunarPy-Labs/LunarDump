# FAQ & Troubleshooting

Common questions, error resolutions, and best practices for LunarDump.

---

## ❓ Frequently Asked Questions

### Q: Does LunarDump require local disk space for backups?
**A:** No! LunarDump streams database dumps directly through memory (64KB chunks) into local AES-256-GCM encryption and uploads directly to cloud storage endpoints. Disk space used is **0 bytes**.

### Q: What database engines are supported?
**A:** PostgreSQL (`pg_dump`), MySQL / MariaDB (`mysqldump`), and MongoDB (`mongodump`).

### Q: How do I restore an encrypted backup?
**A:** You can decrypt and restore an encrypted `.enc` file using:
```bash
lunardump restore --file backup_20260801.enc --key secret.key --output restored.sql
```

### Q: How can I verify that a backup file is valid and not corrupted?
**A:** Use the `--verify` flag:
```bash
lunardump restore --file backup_20260801.enc --key secret.key --verify
```

---

## 🛠️ Troubleshooting Common Errors

### 1. `Dumper tool for engine 'mysql' is not installed`

!!! failure "Cause"
    The system binary `mysqldump` (or `pg_dump` / `mongodump`) is not installed or not in your system `PATH`.

!!! success "Solution"
    Install the client binaries for your OS:
    
    - **macOS**: `brew install mysql-client` (then add `/opt/homebrew/opt/mysql-client/bin` to your `PATH`).
    - **Ubuntu**: `sudo apt install mysql-client postgresql-client`.
    - **Docker**: Use the official Docker image `indhifarhandika/lunardump:latest` which comes pre-packaged with all database binaries!

---

### 2. `Encryption (AES-256-GCM) | Env: LUNARDUMP_ENCRYPTION_KEY | KEY MISSING`

!!! failure "Cause"
    The environment variable specified in `key_env` is not set or python-dotenv could not locate `.env`.

!!! success "Solution"
    1. Ensure your `.env` file contains `LUNARDUMP_ENCRYPTION_KEY=...`.
    2. Alternatively, generate a new key file with `lunardump keygen --output secret.key` and set `key_path: "secret.key"` in `config.yaml`.

---

### 3. `Google Cloud Storage Auth Error`

!!! failure "Cause"
    GCS credentials are missing or the service account lacks storage write permissions.

!!! success "Solution"
    Set your service account credentials environment variable:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
    ```
    Ensure the service account has the `Storage Object Admin` or `Storage Object Creator` IAM role.

---

### 4. `S3 Bucket Access Denied`

!!! failure "Cause"
    AWS Access Key ID / Secret Access Key is missing or lacks `s3:PutObject` / `s3:ListBucket` permissions.

!!! success "Solution"
    Set your AWS credentials in `.env`:
    ```env
    AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
    AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```
