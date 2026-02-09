import sqlite3
from pathlib import Path
import pytest

from open_webui_sqlite_migration.migrate import validate_sqlite


def test_validate_sqlite_runs_integrity_check(tmp_path: Path):
    # Create a real SQLite database file
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test (id INTEGER)")
    conn.commit()
    conn.close()

    # Should not raise
    validate_sqlite(db_path)

def test_validate_sqlite_raises_on_invalid_db(tmp_path: Path):
    # Create an invalid SQLite file
    db_path = tmp_path / "not_sqlite.db"
    db_path.write_text("this is not a sqlite database")

    with pytest.raises(Exception):
        validate_sqlite(db_path)
