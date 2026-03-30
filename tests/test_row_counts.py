"""Test row counts functions"""

import sqlite3
from unittest.mock import MagicMock

from open_webui_sqlite_migration.migrate import (
    sqlite_row_counts,
    postgres_row_counts,
)


def test_sqlite_row_counts():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE posts (id INTEGER, content TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'Alice'), (2, 'Bob')")
    conn.execute("INSERT INTO posts VALUES (1, 'Hello'), (2, 'World'), (3, 'Test')")

    counts = sqlite_row_counts(conn, ["users", "posts"])

    assert counts["users"] == 2
    assert counts["posts"] == 3


def test_sqlite_row_counts_handles_error():
    conn = sqlite3.connect(":memory:")

    counts = sqlite_row_counts(conn, ["nonexistent_table"])

    assert counts["nonexistent_table"] == -1


def test_postgres_row_counts():
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (42,)

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    counts = postgres_row_counts(mock_conn, ["users", "posts"])

    assert counts["users"] == 42
    assert counts["posts"] == 42
    assert mock_cursor.execute.call_count == 2


def test_postgres_row_counts_handles_error():
    import psycopg2

    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = psycopg2.Error("test error")

    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    counts = postgres_row_counts(mock_conn, ["users"])

    assert counts["users"] == -1
