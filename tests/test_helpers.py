"""Test helper functions"""

from open_webui_sqlite_migration.migrate import pg_ident, normalize_row

def test_pg_ident_reserved():
    """Test to check Postgres reserved"""
    assert pg_ident("user") == '"user"'

def test_pg_ident_normal():
    """Test to check Open WebUI table name"""
    assert pg_ident("chat") == "chat"

def test_normalize_row_json_string():
    """Test to check that JSON is normalized"""
    row = ('{"a":1}',)
    columns = ["data"]
    pg_types = {"data": "jsonb"}
    assert normalize_row(row, columns, pg_types) == ('{"a":1}',)

def test_normalize_row_invalid_json():
    row = ('{bad}',)
    columns = ["data"]
    pg_types = {"data": "jsonb"}
    assert normalize_row(row, columns, pg_types) == ("{}",)

def test_normalize_row_dict():
    row = ({"a": 1},)
    columns = ["data"]
    pg_types = {"data": "jsonb"}
    assert normalize_row(row, columns, pg_types) == ('{"a": 1}',)

def test_normalize_row_none_value():
    row = (None,)
    columns = ["data"]
    pg_types = {"data": "jsonb"}
    result = normalize_row(row, columns, pg_types)
    assert "__NULL__" in result[0]

def test_normalize_row_none_mixed_with_other_values():
    row = (None, '{"a": 1}')
    columns = ["meta", "data"]
    pg_types = {"meta": "jsonb", "data": "jsonb"}
    result = normalize_row(row, columns, pg_types)
    assert "__NULL__" in result[0]
    assert result[1] == '{"a": 1}'

def test_normalize_row_not_null_column():
    row = (None,)
    columns = ["content"]
    pg_types = {"content": "text"}
    result = normalize_row(row, columns, pg_types, table_name="prompt")
    assert result == ("",)

def test_normalize_row_not_null_column_with_value():
    row = ("test prompt content",)
    columns = ["content"]
    pg_types = {"content": "text"}
    result = normalize_row(row, columns, pg_types, table_name="prompt")
    assert result == ("test prompt content",)

def test_normalize_row_group_description():
    row = (None,)
    columns = ["description"]
    pg_types = {"description": "text"}
    result = normalize_row(row, columns, pg_types, table_name="group")
    assert result == ("",)

def test_normalize_row_date_returns_null_marker():
    row = (None,)
    columns = ["date_of_birth"]
    pg_types = {"date_of_birth": "date"}
    result = normalize_row(row, columns, pg_types, table_name="user")
    assert result == ("__NULL__",)

def test_normalize_row_user_date_of_birth_not_null():
    row = (None,)
    columns = ["date_of_birth"]
    pg_types = {"date_of_birth": "date"}
    result = normalize_row(row, columns, pg_types, table_name="user")
    assert result == ("__NULL__",)

def test_normalize_row_user_name_returns_null_marker():
    row = (None,)
    columns = ["name"]
    pg_types = {"name": "text"}
    result = normalize_row(row, columns, pg_types, table_name="user")
    assert result == ("__NULL__",)

def test_copy_stream_handles_none():
    from open_webui_sqlite_migration.migrate import CopyStream
    row_iter = iter([(None, "test"), ("value", None)])
    stream = CopyStream(row_iter)
    first_line = stream.read(1024)
    print(f"First line: {repr(first_line)}")

def test_copy_stream_handles_not_null_text():
    from open_webui_sqlite_migration.migrate import CopyStream
    row_iter = iter([("", "test")])
    stream = CopyStream(row_iter)
    first_line = stream.read(1024)
    print(f"Not null text: {repr(first_line)}")
