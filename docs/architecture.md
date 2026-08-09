# Zero-Disk Pipe Streaming Architecture

LunarDump is engineered from the ground up to solve the memory and storage bottlenecks common in traditional database backup scripts.

---

## 1. The Zero-Disk Streaming Principle

Traditional backup scripts dump database contents into temporary files on the local server disk (e.g. `/tmp/backup.sql`), compress them into `.tar.gz`, encrypt them, and upload the final archive to cloud storage. 

This legacy approach presents major drawbacks:

1. **High Disk Overhead**: Requires at least 2x-3x the database size in available disk space.

2. **Security Vulnerabilities**: Plaintext database dumps sit temporarily unencrypted on local disk storage.

3. **I/O Bottlenecks**: Heavy disk read/write cycles degrade server performance.

**LunarDump eliminates local disk usage entirely** by using OS-level process stdout pipes combined with 64KB memory chunking.

---

## 2. Technical Pipeline Architecture

```text
┌──────────────────────────┐
│  Database Engine Client  │
│ (pg_dump / mysqldump)    │
└────────────┬─────────────┘
             │ OS Standard Output Pipe (stdout = subprocess.PIPE)
             ▼
┌──────────────────────────┐
│    64KB Memory Buffer    │ (Streamed in RAM)
└────────────┬─────────────┘
             │ Raw Bytes Chunks Generator
             ▼
┌──────────────────────────┐
│  AES-256-GCM Encryptor   │ (Local Authenticated Cipher)
└────────────┬─────────────┘
             │ Encrypted Ciphertext + Nonce + Tag
             ▼
┌──────────────────────────┐
│  Cloud Storage Driver    │ (AWS S3 / GCS / MinIO / R2)
└──────────────────────────┘ (Multipart Upload Stream)
```

---

## 3. Cryptographic Pipeline (AES-256-GCM)

LunarDump enforces a **Zero-Trust Security** model. Data is encrypted locally before transmitting over the network:

### Key Derivation (PBKDF2-HMAC-SHA256)
- **Salt Generation**: A cryptographically secure random 16-byte salt (`os.urandom(16)`) is generated per backup stream.
- **Key Derivation**: The user's secret key string is passed through `PBKDF2HMAC` with SHA-256, 100,000 iterations, producing a derived 256-bit symmetric key.

### Stream Cipher Layout
Every encrypted backup file (`.enc`) follows a strict binary layout:

```text
┌──────────────────┬──────────────┬──────────────────────────────────────────┐
│  MAGIC HEADER    │     SALT     │              CHUNK PACKETS               │
│  "LUNARDUMP_V1\n"│   16 Bytes   │  [Len (4B)] [Nonce (12B)] [Payload + Tag]│
└──────────────────┴──────────────┴──────────────────────────────────────────┘
```

!!! tip "Authenticated Encryption (AEAD)"
    AES-256-GCM automatically computes a 16-byte authentication tag per 64KB chunk. If a single byte of the backup archive is tampered with or corrupted in cloud storage, decryption will immediately fail with a cryptographic authentication error.

---

## 4. RAM Overhead & Memray Benchmark Characteristics

| Metric | Legacy Disk Script | LunarDump Pipe Streaming |
| :--- | :--- | :--- |
| **Local Disk Space Used** | Equal to DB Size (e.g. 50 GB) | **0 Bytes** |
| **Peak RAM Usage** | 500 MB - 2 GB | **~119 MB (Constant $O(1)$)** |
| **Encryption Mode** | Post-processing / CBC | On-the-fly AES-256-GCM |
| **Disk I/O Wear** | High | **Zero** |

---

## 5. Real-World Benchmark (Memray Memory Profiler)

In a live production benchmark profiling an **8 GB database backup** over a 1+ hour execution run:

```text
Command line: memray run -o lunardump_memory.bin lunardump run --config config.yaml
Start time  : Mon Aug 03 2026 12:02:01 GMT+0700
End time    : Mon Aug 03 2026 13:03:59 GMT+0700
Duration    : 1:01:57.692000 (1 Hour 1 Minute)
Allocations : 5,941,989 allocations
Peak RAM    : 119.1 MB RAM
Allocator   : pymalloc
```

!!! success "Constant $O(1)$ Memory Scaling"
    Even while streaming, encrypting, and uploading **8 GB of raw data** across **5.9 million allocations**, LunarDump's peak memory footprint remained capped at **119.1 MB RAM** (~1.4% of total dataset size), proving zero memory leaks and complete suitability for low-spec VPS servers (512MB / 1GB RAM).
