"""Test migrate table"""
import sqlite3
import csv
from unittest.mock import MagicMock
from open_webui_sqlite_migration import migrate


def test_migrate_table_copy_full_path(monkeypatch):
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

    pg_conn = MagicMock()
    pg_cursor = MagicMock()
    pg_conn.cursor.return_value.__enter__.return_value = pg_cursor

    # Capture streamed data like psycopg2 would
    captured_data = []

    def fake_copy_expert(sql, stream):
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            captured_data.append(chunk)

    pg_cursor.copy_expert.side_effect = fake_copy_expert

    monkeypatch.setattr(
        migrate,
        "pg_column_types",
        lambda conn, table: {"payload": "jsonb"}
    )

    migrate.migrate_table(sqlite_conn, pg_conn, "test")

    # TRUNCATE
    pg_cursor.execute.assert_called_once_with(
        'TRUNCATE TABLE test CASCADE'
    )

    # COPY SQL
    copy_sql = pg_cursor.copy_expert.call_args.args[0]
    assert copy_sql == "COPY test (id, payload) FROM STDIN WITH CSV"

    # Verify streamed CSV content
    streamed_data = "".join(captured_data)
    rows = list(csv.reader(streamed_data.splitlines()))
    assert rows == [["1", '{"a": 1}']]

    # Commit once after truncate + once after copy
    assert pg_conn.commit.call_count == 1