# Installation & Setup

## 1. Installation Options

### Installing via PyPI (`pip`)

```bash
# Standard installation
pip install lunardump

# With Google Cloud Storage (GCS) support
pip install "lunardump[gcs]"
```

### Installing via `uv` (Fastest Python Tool Manager)

```bash
# Global CLI tool installation (recommended for servers and workstations)
uv tool install lunardump

# With GCS support
uv tool install "lunardump[gcs]"

# One-off instant execution without permanent installation
uvx lunardump run --config config.yaml
```

---

## 2. System Prerequisites & Client Binaries

LunarDump leverages native client tools for max streaming efficiency. Ensure the CLI binary tool for your target database engine is installed on your host system:

### 🍏 macOS (Homebrew)

```bash
# For MySQL / MariaDB
brew install mysql-client
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"

# For PostgreSQL
brew install libpq

# For MongoDB
brew install mongodb-database-tools
```

### 🐧 Ubuntu / Debian

```bash
# For PostgreSQL
sudo apt-get update && sudo apt-get install -y postgresql-client

# For MySQL / MariaDB
sudo apt-get install -y mysql-client

# For MongoDB
sudo apt-get install -y mongodb-database-tools
```
