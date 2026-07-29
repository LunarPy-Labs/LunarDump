"""Configuration loader module for LunarDump CLI."""

import os
from pathlib import Path
from typing import Union
import yaml

from lunardump.config.schema import LunarDumpConfig


def load_config(config_path: Union[str, Path]) -> LunarDumpConfig:
    """Load and validate LunarDump configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated LunarDumpConfig object.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If YAML parsing or validation fails.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
    except yaml.YAMLError as err:
        raise ValueError(f"Failed to parse YAML configuration: {err}") from err

    if not isinstance(raw_data, dict):
        raise ValueError("Configuration file content must be a valid dictionary.")

    return LunarDumpConfig.model_validate(raw_data)
