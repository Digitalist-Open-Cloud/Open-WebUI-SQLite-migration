import pytest

from open_webui_sqlite_migration.migrate import env


def test_env_missing_required_variable(monkeypatch):
    """Test to check for missing variable and fail."""
    # Ensure variable is not set
    monkeypatch.delenv("TEST_ENV", raising=False)

    with pytest.raises(RuntimeError) as exc:
        env("TEST_ENV", required=True)

    assert "Missing environment variable: TEST_ENV" in str(exc.value)


def test_env_invalid_cast_raises_runtime_error(monkeypatch):
    """Test to check for invalid value"""
    # Set variable to a value that can't be cast to int
    monkeypatch.setenv("TEST_ENV", "not_an_int")

    with pytest.raises(RuntimeError) as exc:
        env("TEST_ENV", cast=int)

    assert "Invalid value for TEST_ENV" in str(exc.value)

