"""Test copy of SQLite database files"""
from pathlib import Path

from open_webui_sqlite_migration.migrate import copy_sqlite_db


def test_copy_sqlite_db_without_wal(tmp_path: Path):
    # Create fake SQLite DB
    src = tmp_path / "test.db"
    src.write_text("sqlite-data")

    # Run copy
    dst = copy_sqlite_db(src)

    # Assertions
    assert dst.exists()
    assert dst.read_text() == "sqlite-data"

    # WAL/SHM should not exist
    assert not (dst.parent / "test.db-wal").exists()
    assert not (dst.parent / "test.db-shm").exists()


def test_copy_sqlite_db_with_wal_and_shm(tmp_path: Path):
    # Create fake SQLite DB + WAL files
    src = tmp_path / "test.db"
    wal = tmp_path / "test.db-wal"
    shm = tmp_path / "test.db-shm"

    src.write_text("sqlite-data")
    wal.write_text("wal-data")
    shm.write_text("shm-data")

    # Run copy
    dst = copy_sqlite_db(src)

    # Assertions
    copied_dir = dst.parent

    assert dst.exists()
    assert dst.read_text() == "sqlite-data"

    assert (copied_dir / "test.db-wal").exists()
    assert (copied_dir / "test.db-shm").exists()

    assert (copied_dir / "test.db-wal").read_text() == "wal-data"
    assert (copied_dir / "test.db-shm").read_text() == "shm-data"