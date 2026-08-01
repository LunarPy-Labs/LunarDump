# Use official lightweight Python 3.11 Debian Bookworm base image
FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory inside container
WORKDIR /app

# Install system prerequisites: PostgreSQL client, MariaDB/MySQL client, curl, gnupg, and ca-certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    mariadb-client \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install MongoDB Database Tools (mongodump / mongorestore) for multi-arch (amd64 / arm64)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then \
        URL="https://fastdl.mongodb.org/tools/db/mongodb-database-tools-debian12-x86_64-100.11.0.tgz"; \
    elif [ "$ARCH" = "arm64" ]; then \
        URL="https://fastdl.mongodb.org/tools/db/mongodb-database-tools-ubuntu2204-arm64-100.11.0.tgz"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    curl -fsSL "$URL" | tar -xz --strip-components=2 -C /usr/local/bin */bin/

# Copy package files into container
COPY pyproject.toml README.md config.example.yaml ./
COPY lunardump/ ./lunardump/

# Install LunarDump CLI with GCS cloud storage support
RUN pip install --no-cache-dir ".[gcs]"

# Expose default CLI entrypoint
ENTRYPOINT ["lunardump"]

# Default command if no arguments are passed
CMD ["run", "--config", "/app/config.yaml"]
