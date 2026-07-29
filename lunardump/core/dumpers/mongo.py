"""MongoDB dumper plugin implementation using mongodump."""

import os
import subprocess
from typing import Generator
from lunardump.core.dumpers.base import BaseDumper
from lunardump.core.utils.process import check_tool_installed, run_process_stream, run_command


class MongoDBDumper(BaseDumper):
    """MongoDB database dumper using mongodump."""

    def check_tool(self) -> bool:
        return check_tool_installed("mongodump")

    def dump_stream(self) -> Generator[bytes, None, None]:
        if not self.check_tool():
            raise RuntimeError("mongodump binary tool is not installed or not in PATH")

        cmd = [
            "mongodump",
            "--host", self.config.host,
            "--port", str(self.config.port or 27017),
            "--db", self.config.name,
            "--archive",  # Stream directly to stdout archive
            "--gzip",     # Enable gzip compression inside archive stream
        ]

        if self.config.user:
            cmd.extend(["--username", self.config.user])
        if self.config.password:
            cmd.extend(["--password", self.config.password])

        yield from run_process_stream(cmd)

    def restore_stream(self, stream: Generator[bytes, None, None]) -> None:
        if not check_tool_installed("mongorestore"):
            raise RuntimeError("mongorestore binary tool is not installed or not in PATH")

        cmd = [
            "mongorestore",
            "--host", self.config.host,
            "--port", str(self.config.port or 27017),
            "--db", self.config.name,
            "--archive",
            "--gzip",
            "--drop",
        ]

        if self.config.user:
            cmd.extend(["--username", self.config.user])
        if self.config.password:
            cmd.extend(["--password", self.config.password])

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        for chunk in stream:
            if process.stdin:
                process.stdin.write(chunk)

        if process.stdin:
            process.stdin.close()

        _, stderr_data = process.communicate()
        if process.returncode != 0:
            err_msg = stderr_data.decode("utf-8", errors="replace") if stderr_data else "Unknown error"
            raise RuntimeError(f"mongorestore failed (code {process.returncode}): {err_msg.strip()}")

    def check_connection(self) -> bool:
        if not check_tool_installed("mongosh"):
            return self.check_tool()

        cmd = [
            "mongosh",
            "--host", self.config.host,
            "--port", str(self.config.port or 27017),
            "--eval", "db.runCommand({ping:1})",
        ]
        code, _, _ = run_command(cmd)
        return code == 0
