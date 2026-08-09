"""PostgreSQL restorer implementation using psql."""

import os
import shutil
import subprocess
from typing import Generator
from lunardump.core.restorers.base import BaseRestorer
from lunardump.core.utils.logger import logger


class PostgreSQLRestorer(BaseRestorer):
    """PostgreSQL Restorer streaming input bytes into psql."""

    def check_tool(self) -> bool:
        return shutil.which("psql") is not None

    def check_connection(self) -> bool:
        if not self.check_tool():
            return False

        env = os.environ.copy()
        if self.config.password:
            env["PGPASSWORD"] = self.config.password

        cmd = [
            "psql",
            "-h", self.config.host,
            "-p", str(self.config.port),
            "-U", self.config.user,
            "-d", self.config.name,
            "-c", "SELECT 1;",
        ]
        try:
            res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return res.returncode == 0
        except Exception as err:
            logger.debug(f"psql connection check failed: {err}")
            return False

    def restore_stream(self, stream: Generator[bytes, None, None]) -> bool:
        if not self.check_tool():
            raise RuntimeError("PostgreSQL client tool 'psql' is not installed in PATH.")

        env = os.environ.copy()
        if self.config.password:
            env["PGPASSWORD"] = self.config.password

        cmd = [
            "psql",
            "-h", self.config.host,
            "-p", str(self.config.port),
            "-U", self.config.user,
            "-d", self.config.name,
            "-v", "ON_ERROR_STOP=1",
        ]

        logger.debug(f"Executing PostgreSQL restorer: {' '.join(cmd)}")
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
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
                raise RuntimeError(f"psql restore failed (exit code {proc.returncode}): {err_text}")

            return True

        except Exception as err:
            proc.kill()
            raise err
