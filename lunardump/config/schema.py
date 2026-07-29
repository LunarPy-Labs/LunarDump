"""Pydantic v2 configuration schema for LunarDump CLI."""

import os
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, SecretStr, model_validator


class DatabaseConfig(BaseModel):
    type: Literal["postgres", "mysql", "mongo"] = Field(
        ..., description="Database engine type: postgres, mysql, or mongo"
    )
    host: str = Field(default="localhost", description="Database host address")
    port: Optional[int] = Field(default=None, description="Database port number")
    name: str = Field(..., description="Database name to backup")
    user: str = Field(..., description="Database user name")
    password_env: Optional[str] = Field(
        default=None, description="Environment variable holding database password"
    )
    password: Optional[str] = Field(
        default=None, description="Direct password string (not recommended for production)"
    )
    uri: Optional[str] = Field(
        default=None, description="Direct URI connection string"
    )

    @model_validator(mode="after")
    def resolve_password(self) -> "DatabaseConfig":
        if not self.port:
            if self.type == "postgres":
                self.port = 5432
            elif self.type == "mysql":
                self.port = 3306
            elif self.type == "mongo":
                self.port = 27017

        if not self.password and self.password_env:
            env_val = os.getenv(self.password_env)
            self.password = env_val if env_val is not None else self.password_env
        return self


class SecurityConfig(BaseModel):
    encrypt: bool = Field(default=True, description="Enable AES-256-GCM encryption")
    algorithm: Literal["aes-256-gcm"] = Field(
        default="aes-256-gcm", description="Encryption algorithm"
    )
    key_env: Optional[str] = Field(
        default="LUNARDUMP_ENCRYPTION_KEY",
        description="Environment variable holding secret encryption key",
    )
    key_path: Optional[str] = Field(
        default=None, description="File path to key file"
    )
    key: Optional[str] = Field(
        default=None, description="Raw key hex or base64 string"
    )

    @model_validator(mode="after")
    def resolve_key(self) -> "SecurityConfig":
        if self.key:
            return self

        if self.key_env:
            val = os.getenv(self.key_env)
            if val:
                self.key = val
            elif os.path.exists(self.key_env):
                with open(self.key_env, "r", encoding="utf-8") as f:
                    self.key = f.read().strip()
            elif len(self.key_env) >= 32:
                self.key = self.key_env

        if not self.key and self.key_path and os.path.exists(self.key_path):
            with open(self.key_path, "r", encoding="utf-8") as f:
                self.key = f.read().strip()
        return self


class StorageConfig(BaseModel):
    provider: Literal["s3", "gcs", "local"] = Field(
        default="s3", description="Storage provider target"
    )
    bucket: str = Field(..., description="Target cloud storage bucket name or directory path")
    region: Optional[str] = Field(default="ap-southeast-1", description="Cloud storage region")
    path: str = Field(default="backups/", description="Remote directory prefix path")
    retention_days: int = Field(
        default=30, ge=1, description="Number of days to keep backups before purging"
    )
    endpoint_url: Optional[str] = Field(
        default=None, description="Custom S3 endpoint URL for MinIO or Cloudflare R2"
    )


class NotificationChannelConfig(BaseModel):
    type: Literal["telegram", "slack"] = Field(..., description="Notification service type")
    bot_token_env: Optional[str] = Field(
        default=None, description="Env var holding Telegram bot token"
    )
    bot_token: Optional[str] = Field(
        default=None, description="Direct Telegram bot token string"
    )
    chat_id: Optional[str] = Field(
        default=None, description="Telegram chat ID or channel ID"
    )
    webhook_url_env: Optional[str] = Field(
        default=None, description="Env var holding Slack webhook URL"
    )
    webhook_url: Optional[str] = Field(
        default=None, description="Direct Slack webhook URL"
    )

    @model_validator(mode="after")
    def resolve_envs(self) -> "NotificationChannelConfig":
        if not self.bot_token and self.bot_token_env:
            env_val = os.getenv(self.bot_token_env)
            self.bot_token = env_val if env_val is not None else self.bot_token_env

        if not self.webhook_url and self.webhook_url_env:
            env_val = os.getenv(self.webhook_url_env)
            self.webhook_url = env_val if env_val is not None else self.webhook_url_env
        return self


class NotificationConfig(BaseModel):
    on_success: bool = Field(default=True, description="Send notification on backup success")
    on_failure: bool = Field(default=True, description="Send notification on backup failure")
    channels: List[NotificationChannelConfig] = Field(default_factory=list)


class BackupProfile(BaseModel):
    name: str = Field(..., description="Backup job profile name")
    database: DatabaseConfig
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    storage: StorageConfig
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)


class LunarDumpConfig(BaseModel):
    version: str = Field(default="1.0", description="Configuration schema version")
    backup: BackupProfile
