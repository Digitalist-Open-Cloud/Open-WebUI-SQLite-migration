"""Test parse arguments"""

import sys
from open_webui_sqlite_migration.migrate import parse_args

def test_parse_args_default(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    args = parse_args()
    assert args.dry_run is False
    assert args.sqlite_counts is False
    assert args.postgres_counts is False
    assert args.validate is False

def test_parse_args_dry_run(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--dry-run"])
    args = parse_args()
    assert args.dry_run is True

def test_parse_args_sqlite_counts(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--sqlite-counts"])
    args = parse_args()
    assert args.sqlite_counts is True

def test_parse_args_postgres_counts(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--postgres-counts"])
    args = parse_args()
    assert args.postgres_counts is True

def test_parse_args_validate(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--validate"])
    args = parse_args()
    assert args.validate is True

def test_parse_args_ignores_unknown_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--cov", "--random-flag"])
    args = parse_args()
    assert args.dry_run is False
