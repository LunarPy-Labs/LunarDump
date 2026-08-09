"""PostgreSQL dumper plugin implementation using pg_dump / pg_restore or psql."""

import os
import subprocess
from typing import Generator, List, Optional
from lunardump.core.dumpers.base import BaseDumper
from lunardump.core.utils.process import check_tool_installed, run_process_stream, run_command


class PostgreSQLDumper(BaseDumper):
    """PostgreSQL database dumper using pg_dump."""

    def check_tool(self) -> bool:
        return check_tool_installed("pg_dump")

    def _build_env(self) -> dict:
        env = os.environ.copy()
        if self.config.password:
            env["PGPASSWORD"] = self.config.password
        return env

    def dump_stream(self) -> Generator[bytes, None, None]:
        if not self.check_tool():
            raise RuntimeError("pg_dump binary tool is not installed or not in PATH")

        cmd = [
            "pg_dump",
            "-h", self.config.host,
            "-p", str(self.config.port or 5432),
            "-U", self.config.user,
            "-d", self.config.name,
            "-F", "c",  # Custom format (compressed and suitable for pg_restore)
        ]

        yield from run_process_stream(cmd, env=self._build_env())

    def restore_stream(self, stream: Generator[bytes, None, None]) -> None:
        if not check_tool_installed("pg_restore"):
            raise RuntimeError("pg_restore binary tool is not installed or not in PATH")

        cmd = [
            "pg_restore",
            "-h", self.config.host,
            "-p", str(self.config.port or 5432),
            "-U", self.config.user,
            "-d", self.config.name,
            "--clean",
            "--if-exists",
        ]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._build_env(),
        )

        for chunk in stream:
            if process.stdin:
                process.stdin.write(chunk)

        if process.stdin:
            process.stdin.close()

        _, stderr_data = process.communicate()
        if process.returncode != 0:
            err_msg = stderr_data.decode("utf-8", errors="replace") if stderr_data else "Unknown error"
            raise RuntimeError(f"pg_restore failed (code {process.returncode}): {err_msg.strip()}")

    def check_connection(self) -> bool:
        if not check_tool_installed("pg_isready"):
            # Fallback to checking via psql if pg_isready is missing
            return self.check_tool()

        cmd = [
            "pg_isready",
            "-h", self.config.host,
            "-p", str(self.config.port or 5432),
            "-d", self.config.name,
            "-U", self.config.user,
        ]
        try:
            code, _, _ = run_command(cmd, env=self._build_env())
            return code == 0
        except Exception:
            return False
