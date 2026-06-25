import os
import tempfile

import pytest

from app.db import init_db


@pytest.fixture
def temp_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        from app.config import Settings

        test_settings = Settings(database_path=db_path)
        monkeypatch.setattr("app.config.settings", test_settings)
        monkeypatch.setattr("app.db.settings", test_settings)
        init_db()
        yield db_path
