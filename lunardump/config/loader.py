"""Configuration loader module for LunarDump CLI."""

import os
from pathlib import Path
from typing import Union
import yaml

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

from lunardump.config.schema import LunarDumpConfig


def load_config(config_path: Union[str, Path]) -> LunarDumpConfig:
    """Load and validate LunarDump configuration from a YAML file.
    Automatically loads .env file if python-dotenv is available.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated LunarDumpConfig object.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If YAML parsing or validation fails.
    """
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    # Auto-load .env from config file directory or current working directory
    if HAS_DOTENV:
        config_env = path.parent / ".env"
        cwd_env = Path.cwd() / ".env"
        if config_env.exists():
            load_dotenv(dotenv_path=config_env, override=False)
        elif cwd_env.exists():
            load_dotenv(dotenv_path=cwd_env, override=False)
        else:
            load_dotenv(override=False)

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as err:
        raise ValueError(f"Failed to parse YAML configuration: {err}") from err

    if not isinstance(raw_data, dict):
        raise ValueError("Configuration file content must be a valid dictionary.")

    return LunarDumpConfig.model_validate(raw_data)
