# CLI Commands Reference

Complete command-line interface specification for LunarDump.

---

## 1. `lunardump run`

Execute the full automated backup pipeline according to `config.yaml`.

```bash
lunardump run --config config.yaml [--dry-run]
```

- `--config`, `-c`: Path to YAML configuration file.
- `--dry-run`: Validate configurations and test connections without performing actual uploads or writes.

---

## 2. `lunardump config check`

Inspect, validate, and run health checks against your database, client binaries, and storage targets.

```bash
lunardump config check --config config.yaml
```

---

## 3. `lunardump keygen`

Generate a cryptographically secure 256-bit AES encryption key.

```bash
lunardump keygen [--output secret.key]
```

---

## 4. `lunardump restore`

Decrypt encrypted `.enc` backup files back to plain SQL/dump format or verify integrity.

```bash
lunardump restore --file backup.enc --key secret.key [--output restored.sql] [--verify]
```

- `--file`, `-f`: Path to local encrypted file.
- `--key`, `-k`: Secret key string or path to key file.
- `--output`, `-o`: Output path to write decrypted file.
- `--verify`: Verify integrity and checksums without saving to disk.

---

## 5. `lunardump db dump`

Direct database dump to file or stdout without requiring a configuration file.

```bash
lunardump db dump --type mysql --host localhost --user root --name main_db --output dump.sql
```
