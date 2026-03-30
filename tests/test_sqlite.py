"""Test SQLite tables and schema"""

import sqlite3
from open_webui_sqlite_migration.migrate import (
    sqlite_tables,
    sqlite_schema,
    TABLE_ORDER,
    TABLE_DEPENDENCIES,
)


def test_sqlite_tables_and_schema():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
    conn.execute("CREATE TABLE alembic_version (x TEXT)")

    tables = sqlite_tables(conn)
    assert tables == ["test"]

    schema = sqlite_schema(conn, "test")
    assert len(schema) == 2
    assert schema[0][1] == "id"


def test_sqlite_tables_dependency_order():
    """Test that tables with dependencies are ordered correctly."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE knowledge_file (id TEXT, file_id TEXT, knowledge_id TEXT)")
    conn.execute("CREATE TABLE knowledge (id TEXT)")
    conn.execute("CREATE TABLE file (id TEXT)")
    conn.execute("CREATE TABLE user (id TEXT)")
    conn.execute("CREATE TABLE alembic_version (x TEXT)")

    tables = sqlite_tables(conn)

    knowledge_idx = tables.index("knowledge")
    file_idx = tables.index("file")
    knowledge_file_idx = tables.index("knowledge_file")

    assert knowledge_idx < knowledge_file_idx
    assert file_idx < knowledge_file_idx


def test_sqlite_tables_known_tables_ordered():
    """Test that known tables appear in expected order."""
    conn = sqlite3.connect(":memory:")
    for table in TABLE_ORDER[:10]:
        conn.execute(f"CREATE TABLE {table} (id TEXT)")

    tables = sqlite_tables(conn)

    for i in range(len(tables) - 1):
        current = tables[i]
        next_table = tables[i + 1]
        current_order = TABLE_ORDER.index(current) if current in TABLE_ORDER else 999
        next_order = TABLE_ORDER.index(next_table) if next_table in TABLE_ORDER else 999
        assert current_order <= next_order, f"{current} should come before {next_table}"


def test_sqlite_tables_unknown_tables_fallback():
    """Test that unknown tables are appended at the end."""
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE user (id TEXT)")
    conn.execute("CREATE TABLE unknown_table_1 (id TEXT)")
    conn.execute("CREATE TABLE unknown_table_2 (id TEXT)")
    conn.execute("CREATE TABLE alembic_version (x TEXT)")

    tables = sqlite_tables(conn)

    assert "user" in tables
    assert "unknown_table_1" in tables
    assert "unknown_table_2" in tables
    assert tables.index("user") < tables.index("unknown_table_1")
    assert tables.index("unknown_table_1") < tables.index("unknown_table_2")


def test_sqlite_tables_multiple_dependencies():
    """Test tables with multiple dependencies are ordered correctly."""
    conn = sqlite3.connect(":memory:")
    conn.execute('CREATE TABLE "group" (id TEXT)')
    conn.execute("CREATE TABLE user (id TEXT)")
    conn.execute("CREATE TABLE group_member (id TEXT, group_id TEXT, user_id TEXT)")
    conn.execute("CREATE TABLE alembic_version (x TEXT)")

    tables = sqlite_tables(conn)

    group_idx = tables.index("group")
    user_idx = tables.index("user")
    group_member_idx = tables.index("group_member")

    assert group_idx < group_member_idx
    assert user_idx < group_member_idx
