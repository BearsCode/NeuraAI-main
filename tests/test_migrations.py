import subprocess
import unittest


class MigrationTests(unittest.TestCase):
    def test_alembic_upgrade_head(self) -> None:
        result = subprocess.run(
            ["./.venv/bin/alembic", "upgrade", "head"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
        )
