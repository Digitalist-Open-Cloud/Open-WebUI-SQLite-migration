from unittest.mock import MagicMock

from open_webui_sqlite_migration.migrate import pg_column_types


def test_pg_column_types_executes_query_and_returns_dict():
    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = [
        ("id", "integer"),
        ("payload", "jsonb"),
        ("created_at", "timestamp with time zone"),
    ]

    # Mock connection
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Call function
    result = pg_column_types(mock_conn, "test_table")

    # Assertions
    mock_cursor.execute.assert_called_once()

    sql, params = mock_cursor.execute.call_args.args
    assert "information_schema.columns" in sql
    assert params == ("test_table",)

    assert result == {
        "id": "integer",
        "payload": "jsonb",
        "created_at": "timestamp with time zone",
    }
