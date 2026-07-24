from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


_TEST_RUN_ID = uuid4().hex
_TEST_ROOT = Path(tempfile.gettempdir()) / f"neura-pytest-{_TEST_RUN_ID}"
_TEST_DB_PATH = _TEST_ROOT / "neura-test-suite.db"
_TEST_STORAGE_PATH = _TEST_ROOT / "storage"

_TEST_ROOT.mkdir(parents=True, exist_ok=True)
_TEST_DB_PATH.unlink(missing_ok=True)
shutil.rmtree(_TEST_STORAGE_PATH, ignore_errors=True)

os.environ["APP__ENV"] = "local"
os.environ["DB__DSN"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
os.environ["DB__RUN_MIGRATIONS_ON_STARTUP"] = "true"
os.environ["REDIS__DSN"] = "redis://localhost:6379/0"
os.environ["S3__BACKEND"] = "local"
os.environ["S3__LOCAL_ROOT"] = str(_TEST_STORAGE_PATH)
os.environ["AI__PROVIDER"] = "mock"
os.environ["WEB__PUBLIC_BASE_URL"] = "http://127.0.0.1:8000"


def pytest_sessionfinish(session, exitstatus: int) -> None:  # type: ignore[no-untyped-def]
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)
