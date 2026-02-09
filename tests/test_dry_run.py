import sqlite3
import psycopg2
from unittest.mock import MagicMock
from open_webui_sqlite_migration import migrate

def test_migrate_table_dry_run(monkeypatch):
    # Force dry-run
    migrate.DRY_RUN = True

    sqlite_conn = sqlite3.connect(":memory:")
    sqlite_conn.execute("CREATE TABLE test (id INTEGER)")
    sqlite_conn.execute("INSERT INTO test VALUES (1)")

    pg_conn = MagicMock()

    migrate.migrate_table(sqlite_conn, pg_conn, "test")

    # Ensure no cursor actions were called
    pg_conn.cursor.assert_not_called()
