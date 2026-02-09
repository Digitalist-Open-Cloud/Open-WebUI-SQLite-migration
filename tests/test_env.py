"""Test env variables"""

import pytest
from open_webui_sqlite_migration.migrate import env

def test_env_required_missing(monkeypatch):
    """Test to check for required env."""
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(RuntimeError):
        env("FOO", required=True)

def test_env_default(monkeypatch):
    """Test to check for required env."""
    monkeypatch.delenv("FOO", raising=False)
    assert env("FOO", "bar") == "bar"

def test_env_cast(monkeypatch):
    """Test to check for required env."""
    monkeypatch.setenv("FOO", "123")
    assert env("FOO", cast=int) == 123

def test_env_valid_cast(monkeypatch):
    """Test to check for valid value"""
    monkeypatch.setenv("TEST_ENV", "123")
    assert env("TEST_ENV", cast=int) == 123
