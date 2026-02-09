import sqlite3
from unittest.mock import MagicMock

from open_webui_sqlite_migration import migrate


def test_migrate_table_dry_run(monkeypatch):
    """Test dry-run argument."""
    # Force dry-run
    monkeypatch.setattr(migrate, "DRY_RUN", True)

    # SQLite setup
    sqlite_conn = sqlite3.connect(":memory:")
    sqlite_conn.execute("CREATE TABLE test (id INTEGER)")
    sqlite_conn.execute("INSERT INTO test VALUES (1)")
    sqlite_conn.commit()

    # Mock Postgres connection
    pg_conn = MagicMock()

    # Run
    migrate.migrate_table(sqlite_conn, pg_conn, "test")

    # Assert: nothing was written
    pg_conn.cursor.assert_not_called()
    pg_conn.commit.assert_not_called()
