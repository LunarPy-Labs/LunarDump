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

## 🌐 Pre-installed OS Distributions

<img width="400" height="100" alt="mini-logotype-hacktrack" src="https://github.com/user-attachments/assets/e5a189ec-7f94-457e-9556-98603d273ac1" />

- **HackTrack OS**: Pre-installed natively out-of-the-box. You can run `lunardump` directly from any terminal window or launch it from the system application menu under **Extra Tools**.

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
sudo apt-get install -y gnupg curl
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```
