"""Key generation and management utilities for LunarDump."""

import secrets
from pathlib import Path
from typing import Union


def generate_key_hex() -> str:
    """Generate a cryptographically secure 256-bit (32 bytes) hex string key."""
    return secrets.token_hex(32)


def generate_key_file(output_path: Union[str, Path]) -> str:
    """Generate and write a secure 256-bit encryption key to a file.

    Args:
        output_path: Path where key file will be written.

    Returns:
        The generated hex key string.
    """
    key = generate_key_hex()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{key}\n")
    # Restrict file permissions to read-write for owner only (0600)
    try:
        path.chmod(0o600)
    except Exception:
        pass
    return key
