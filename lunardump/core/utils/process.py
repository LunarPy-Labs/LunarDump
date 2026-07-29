"""Subprocess execution runner with streaming support."""

import shutil
import subprocess
from typing import List, Generator, Optional, Dict, Tuple


def check_tool_installed(tool_name: str) -> bool:
    """Check if a CLI binary tool is available in system PATH."""
    return shutil.which(tool_name) is not None


def run_process_stream(
    cmd: List[str], env: Optional[Dict[str, str]] = None
) -> Generator[bytes, None, None]:
    """Execute a subprocess command and yield standard output chunks as stream.

    Args:
        cmd: List of command line arguments.
        env: Optional dictionary of environment variables.

    Yields:
        Bytes chunks of subprocess output.

    Raises:
        RuntimeError: If subprocess fails with a non-zero exit status.
    """
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        bufsize=64 * 1024,  # 64KB buffer
    )

    if process.stdout:
        while True:
            chunk = process.stdout.read(64 * 1024)
            if not chunk:
                break
            yield chunk

    _, stderr_data = process.communicate()
    return_code = process.poll()

    if return_code != 0:
        err_msg = stderr_data.decode("utf-8", errors="replace") if stderr_data else "Unknown error"
        raise RuntimeError(f"Subprocess '{cmd[0]}' failed (code {return_code}): {err_msg.strip()}")


def run_command(
    cmd: List[str], env: Optional[Dict[str, str]] = None
) -> Tuple[int, str, str]:
    """Execute command synchronously and return (code, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr
