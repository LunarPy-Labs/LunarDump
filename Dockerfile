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

# Install MongoDB Database Tools (mongodump / mongorestore)
RUN curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg \
    && echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends mongodb-database-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy package files into container
COPY pyproject.toml README.md config.example.yaml ./
COPY lunardump/ ./lunardump/

# Install LunarDump CLI with GCS cloud storage support
RUN pip install --no-cache-dir ".[gcs]"

# Expose default CLI entrypoint
ENTRYPOINT ["lunardump"]

# Default command if no arguments are passed
CMD ["run", "--config", "/app/config.yaml"]
