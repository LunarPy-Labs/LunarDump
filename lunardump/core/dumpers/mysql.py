"""MySQL / MariaDB dumper plugin implementation using mysqldump."""

import os
import subprocess
from typing import Generator
from lunardump.core.dumpers.base import BaseDumper
from lunardump.core.utils.process import check_tool_installed, run_process_stream, run_command


class MySQLDumper(BaseDumper):
    """MySQL/MariaDB database dumper using mysqldump."""

    def check_tool(self) -> bool:
        return check_tool_installed("mysqldump")

    def _build_env(self) -> dict:
        env = os.environ.copy()
        if self.config.password:
            env["MYSQL_PWD"] = self.config.password
        return env

    def dump_stream(self) -> Generator[bytes, None, None]:
        if not self.check_tool():
            raise RuntimeError("mysqldump binary tool is not installed or not in PATH")

        cmd = [
            "mysqldump",
            "-h", self.config.host,
            "-P", str(self.config.port or 3306),
            "-u", self.config.user,
            "--single-transaction",
            "--quick",
            "--routines",
            "--triggers",
            self.config.name,
        ]

        yield from run_process_stream(cmd, env=self._build_env())

    def restore_stream(self, stream: Generator[bytes, None, None]) -> None:
        if not check_tool_installed("mysql"):
            raise RuntimeError("mysql binary tool is not installed or not in PATH")

        cmd = [
            "mysql",
            "-h", self.config.host,
            "-P", str(self.config.port or 3306),
            "-u", self.config.user,
            self.config.name,
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
            raise RuntimeError(f"mysql restore failed (code {process.returncode}): {err_msg.strip()}")

    def check_connection(self) -> bool:
        if not check_tool_installed("mysqladmin"):
            return self.check_tool()

        cmd = [
            "mysqladmin",
            "-h", self.config.host,
            "-P", str(self.config.port or 3306),
            "-u", self.config.user,
            "ping",
        ]
        code, _, _ = run_command(cmd, env=self._build_env())
        return code == 0
