"""Test migrate table"""

import sqlite3
import csv
from io import StringIO
from unittest.mock import MagicMock

from open_webui_sqlite_migration import migrate


def test_migrate_table_copy_full_path(monkeypatch):
    # Force non-dry-run
    monkeypatch.setattr(migrate, "DRY_RUN", False)

    # SQLite setup
    sqlite_conn = sqlite3.connect(":memory:")
    sqlite_conn.execute("""
        CREATE TABLE test (
            id INTEGER,
            payload TEXT
        )
    """)
    sqlite_conn.execute(
        "INSERT INTO test VALUES (?, ?)",
        (1, '{"a": 1}')
    )
    sqlite_conn.commit()

    # Mock Postgres connection & cursor
    pg_conn = MagicMock()
    pg_cursor = MagicMock()
    pg_conn.cursor.return_value.__enter__.return_value = pg_cursor

    # Mock column types (jsonb handling)
    monkeypatch.setattr(
        migrate,
        "pg_column_types",
        lambda conn, table: {"payload": "jsonb"}
    )

    # Run migration
    migrate.migrate_table(sqlite_conn, pg_conn, "test")

    # Assertions
    pg_cursor.execute.assert_called_once_with(
        'TRUNCATE TABLE test CASCADE'
    )

    pg_cursor.copy_expert.assert_called_once()
    copy_sql, buffer = pg_cursor.copy_expert.call_args.args

    assert copy_sql == "COPY test (id, payload) FROM STDIN WITH CSV"
    assert isinstance(buffer, StringIO)

    buffer.seek(0)
    rows = list(csv.reader(buffer))
    assert rows == [["1", '{"a": 1}']]

    pg_conn.commit.assert_called_once()
