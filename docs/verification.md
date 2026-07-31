# Backup Integrity & Verification (`--verify`)

The `--verify` flag provides automated disaster recovery confidence by stream-decrypting, authenticating AES-256-GCM signatures, and computing payload checksums without restoring to a live database or writing unencrypted bytes to disk.

---

## Verifying Local Encrypted Backup Files

```bash
lunardump restore --file backup_20260730.enc --key secret.key --verify
```

---

## Verifying Remote Cloud Storage Backups (AWS S3 / GCS)

Directly stream and verify backup archives stored in S3, GCS, MinIO, or Cloudflare R2:

```bash
lunardump restore --config config.yaml --remote-key daily/postgres/backup_20260730.enc --verify
```

---

## Verification Output Report

```text
                     LunarDump Backup Integrity & Verification Report                     
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric                   ┃ Details                                                              ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Backup Source            │ s3://company-db-backups/daily/postgres/backup_20260730.enc          │
│ Integrity Status         │ PASSED (AES-256-GCM Authenticated)                                   │
│ Decrypted Size           │ 14.28 MB (14,972,812 bytes)                                          │
│ SHA-256 Checksum         │ a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8a8       │
│ MD5 Checksum             │ c4ca4238a0b923820dcc509a6f75849b                                      │
│ Validated Chunks         │ 228 chunk(s)                                                         │
└━━━━━━━━━━━━━━━━━━━━━━━━━━┴━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┘

✓ Backup file is authentic, uncorrupted, and ready for disaster recovery.
```
