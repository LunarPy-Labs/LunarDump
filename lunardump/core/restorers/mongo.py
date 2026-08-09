"""MongoDB restorer implementation using mongorestore."""

import os
import shutil
import subprocess
from typing import Generator
from lunardump.core.restorers.base import BaseRestorer
from lunardump.core.utils.logger import logger


class MongoRestorer(BaseRestorer):
    """MongoDB Restorer streaming BSON archive bytes into mongorestore."""

    def check_tool(self) -> bool:
        return shutil.which("mongorestore") is not None

    def check_connection(self) -> bool:
        if not self.check_tool():
            return False

        if self.config.uri:
            cmd = ["mongosh", self.config.uri, "--eval", "db.runCommand({ping: 1})"]
            if not shutil.which("mongosh"):
                return True
        else:
            cmd = ["mongorestore", f"--host={self.config.host}:{self.config.port}", "--drop", "--archive"]
            return True

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            return res.returncode == 0
        except Exception:
            return True

    def restore_stream(self, stream: Generator[bytes, None, None]) -> bool:
        if not self.check_tool():
            raise RuntimeError("MongoDB client tool 'mongorestore' is not installed in PATH.")

        if self.config.uri:
            cmd = ["mongorestore", f"--uri={self.config.uri}", "--archive", "--drop"]
        else:
            cmd = [
                "mongorestore",
                f"--host={self.config.host}:{self.config.port}",
                f"--db={self.config.name}",
                "--archive",
                "--drop",
            ]
            if self.config.user:
                cmd.append(f"--username={self.config.user}")
            if self.config.password:
                cmd.append(f"--password={self.config.password}")

        logger.debug(f"Executing Mongo restorer: {' '.join(cmd)}")
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
                raise RuntimeError(f"mongorestore failed (exit code {proc.returncode}): {err_text}")

            return True

        except Exception as err:
            proc.kill()
            raise err
