import pytest
from open_webui_sqlite_migration.migrate import env

def test_env_required_missing(monkeypatch):
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(RuntimeError):
        env("FOO", required=True)

def test_env_default(monkeypatch):
    monkeypatch.delenv("FOO", raising=False)
    assert env("FOO", "bar") == "bar"

def test_env_cast(monkeypatch):
    monkeypatch.setenv("FOO", "123")
    assert env("FOO", cast=int) == 123