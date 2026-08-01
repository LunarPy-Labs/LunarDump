# Automated Retention & Lifecycle Management

Managing backup lifecycle and preventing cloud storage bloat is built directly into LunarDump.

---

## 1. How the Retention Cleaner Works

Every time `lunardump run` completes a successful upload of today's database backup, the retention cleaner automatically runs in the background.

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Successful Upload of Today's Backup File                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Calculate Cutoff Timestamp                               │
│    Cutoff = Current UTC Time - retention_days               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Scan Target Storage Path (Prefix Scoped)                 │
│    List objects matching 'path:' (e.g. daily/mysql/)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Purge Expired Files (LastModified < Cutoff)              │
│    Delete expired archives & report count in log/webhook    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Storage Driver Mechanics

### AWS S3 / MinIO / Cloudflare R2
- Uses `boto3` paginator `list_objects_v2` scoped to `config.path`.
- Compares `LastModified` UTC date against `Cutoff Date`.
- Deletes expired objects via `s3_client.delete_object()`.

### Google Cloud Storage (GCS)
- Uses `google.cloud.storage.Client` scoped to `config.path`.
- Compares `blob.time_created` UTC timestamp.
- Deletes expired blobs via `blob.delete()`.

### Local File System
- Scans `base_dir.glob("**/*")` under target directory.
- Compares POSIX `st_mtime` (*last modification time*).
- Deletes expired files via `Path.unlink()`.

---

## 3. Configuration Example

```yaml
backup:
  name: "daily-mysql"
  storage:
    provider: "s3"
    bucket: "my-company-backups"
    path: "daily/mysql/"
    retention_days: 30 # Keep backups for 30 days
```

!!! note "Safety & Path Scoping"
    The retention cleaner only scans objects inside the configured `path` prefix. Objects in other folders or buckets will never be touched.

---

## 4. Crontab Automation Example

Automate daily backups and retention purging via crontab:

```bash
# Open crontab editor
crontab -e

# Run daily backup every day at 02:00 AM WIB
0 2 * * * cd /opt/lunardump && source .env && lunardump run --config config.yaml >> /var/log/lunardump.log 2>&1
```
