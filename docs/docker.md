# Docker Container Deployment

LunarDump is available as an official multi-architecture Docker image (`linux/amd64` and `linux/arm64`) pre-packaged with Python 3.11 and native client tools (`pg_dump`, `mysqldump`, `mongodump`).

---

## 1. Official Image Registries

- **Docker Hub**: `indhifarhandika/lunardump:latest`
- **GitHub Container Registry**: `ghcr.io/indhifarhandika/lunardump:latest`

---

## 2. Quick Usage via `docker run`

Mount your local `config.yaml` and `.env` files into `/app/` inside the container:

```bash
# Execute automated backup pipeline
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/.env:/app/.env:ro \
  indhifarhandika/lunardump:latest run --config /app/config.yaml

# Perform health check
docker run --rm \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/.env:/app/.env:ro \
  indhifarhandika/lunardump:latest config check --config /app/config.yaml

# Generate an encryption key
docker run --rm indhifarhandika/lunardump:latest keygen
```

---

## 3. Running with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  lunardump:
    image: indhifarhandika/lunardump:latest
    container_name: lunardump
    restart: "no"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./.env:/app/.env:ro
      - ./backups:/app/backups:rw
    command: ["run", "--config", "/app/config.yaml"]
```

Execute with:

```bash
docker compose up
```

---

## 4. Crontab Automation via Docker

Automate daily backups using cron on your host server without installing Python or client tools natively:

```bash
0 2 * * * docker run --rm -v /opt/lunardump/config.yaml:/app/config.yaml:ro -v /opt/lunardump/.env:/app/.env:ro indhifarhandika/lunardump:latest run --config /app/config.yaml >> /var/log/lunardump.log 2>&1
```
