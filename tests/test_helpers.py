from open_webui_sqlite_migration.migrate import pg_ident, normalize_row

def test_pg_ident_reserved():
    assert pg_ident("user") == '"user"'

def test_pg_ident_normal():
    assert pg_ident("chat") == "chat"

def test_normalize_row_json_string():
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