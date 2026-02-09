from unittest.mock import MagicMock

import psycopg2

from open_webui_sqlite_migration.migrate import validate_postgres


def test_validate_postgres_connects_and_closes(monkeypatch):
    mock_conn = MagicMock()

    # Mock psycopg2.connect to return our mock connection
    monkeypatch.setattr(psycopg2, "connect", lambda url: mock_conn)

    # Call function
    validate_postgres("postgresql://example")

    # Assertions
    mock_conn.close.assert_called_once()
