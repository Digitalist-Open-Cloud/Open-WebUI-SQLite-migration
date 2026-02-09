"""Test parse arguments"""

import sys
from open_webui_sqlite_migration.migrate import parse_args

def test_parse_args_default(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog"])
    args = parse_args()
    assert args.dry_run is False

def test_parse_args_dry_run(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--dry-run"])
    args = parse_args()
    assert args.dry_run is True

def test_parse_args_ignores_unknown_args(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["prog", "--cov", "--random-flag"])
    args = parse_args()
    assert args.dry_run is False
