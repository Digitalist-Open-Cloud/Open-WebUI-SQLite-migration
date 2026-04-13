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
    pg_types = {"data": "jsonb"}  # type shouldn't matter for None

    assert normalize_row(row, columns, pg_types) == (None,)

def test_normalize_row_none_mixed_with_other_values():
    row = (None, '{"a": 1}')
    columns = ["meta", "data"]
    pg_types = {"meta": "jsonb", "data": "jsonb"}

    assert normalize_row(row, columns, pg_types) == (None, '{"a": 1}')

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

def test_normalize_row_date_not_null_stays_none():
    row = (None,)
    columns = ["date_of_birth"]
    pg_types = {"date_of_birth": "date"}
    result = normalize_row(row, columns, pg_types, table_name="user")
    assert result == (None,)
