"""MySQL / MariaDB restorer implementation using mysql client."""

import os
import shutil
import subprocess
from typing import Generator
from lunardump.core.restorers.base import BaseRestorer
from lunardump.core.utils.logger import logger


class MySQLRestorer(BaseRestorer):
    """MySQL / MariaDB Restorer streaming SQL bytes into mysql client."""

    def check_tool(self) -> bool:
        return shutil.which("mysql") is not None or shutil.which("mariadb") is not None

    def get_binary(self) -> str:
        if shutil.which("mysql"):
            return "mysql"
        if shutil.which("mariadb"):
            return "mariadb"
        return "mysql"

    def check_connection(self) -> bool:
        if not self.check_tool():
            return False

        bin_name = self.get_binary()
        cmd = [
            bin_name,
            f"-h{self.config.host}",
            f"-P{self.config.port}",
            f"-u{self.config.user}",
            "-e", "SELECT 1;",
            self.config.name,
        ]
        if self.config.password:
            cmd.insert(4, f"-p{self.config.password}")

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return res.returncode == 0
        except Exception as err:
            logger.debug(f"mysql connection check failed: {err}")
            return False

    def restore_stream(self, stream: Generator[bytes, None, None]) -> bool:
        if not self.check_tool():
            raise RuntimeError("MySQL client tool 'mysql' is not installed in PATH.")

        bin_name = self.get_binary()
        cmd = [
            bin_name,
            f"-h{self.config.host}",
            f"-P{self.config.port}",
            f"-u{self.config.user}",
            self.config.name,
        ]
        if self.config.password:
            cmd.insert(4, f"-p{self.config.password}")

        logger.debug(f"Executing MySQL restorer: {bin_name} -h{self.config.host} -u{self.config.user} {self.config.name}")
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            for chunk in stream:
                if chunk and proc.stdin:
                    proc.stdin.write(chunk)
            if proc.stdin:
                proc.stdin.close()

            _, stderr = proc.communicate()
            if proc.returncode != 0:
                err_text = stderr.decode("utf-8", errors="replace")
                raise RuntimeError(f"mysql restore failed (exit code {proc.returncode}): {err_text}")

            return True

        except Exception as err:
            proc.kill()
            raise err
