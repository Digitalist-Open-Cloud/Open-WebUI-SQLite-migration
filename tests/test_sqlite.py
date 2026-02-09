import sqlite3
from open_webui_sqlite_migration.migrate import sqlite_tables, sqlite_schema

def test_sqlite_tables_and_schema():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE alembic_version (x TEXT)")

    tables = sqlite_tables(conn)
    assert tables == ["test"]

    schema = sqlite_schema(conn, "test")
    assert len(schema) == 2
    assert schema[0][1] == "id"
