#!/usr/bin/env python3
"""
SQLite to PostgreSQL migration for Open WebUI
"""

import os
import json
import sqlite3
import csv
import argparse
import time
from pathlib import Path
from typing import Dict, Iterable, List
from io import StringIO
import shutil
import tempfile


import psycopg2
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

__version__ = "0.1.13"
console = Console()


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="SQLite to PostgreSQL migration for Open WebUI",
        add_help=True,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview migration without writing to PostgreSQL",
    )
    parser.add_argument(
        "--sqlite-counts",
        action="store_true",
        help="Show row counts for all SQLite tables and exit",
    )
    parser.add_argument(
        "--postgres-counts",
        action="store_true",
        help="Show row counts for all PostgreSQL tables and exit",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate migrated data by comparing row counts",
    )
    args, _ = parser.parse_known_args()
    return args

DRY_RUN = False

def env(key: str, default=None, *, required=False, cast=str):
    """Get required environment variables."""
    value = os.getenv(key, default)
    if required and value is None:
        raise RuntimeError(f"Missing environment variable: {key}")
    try:
        return cast(value) if value is not None else value
    except Exception:
        raise RuntimeError(f"Invalid value for {key}: {value}")

SQLITE_PATH = Path(env("SQLITE_DB_PATH", required=True))
MIGRATE_DATABASE_URL = env("MIGRATE_DATABASE_URL", required=True)

def copy_sqlite_db(src: Path) -> Path:
    """
    Copy SQLite database (including WAL files if present) to a temp directory.
    Returns path to copied .db file.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="openwebui-sqlite-"))
    dst = tmp_dir / src.name

    shutil.copy2(src, dst)

    for suffix in ("-wal", "-shm"):
        wal_file = src.with_name(src.name + suffix)
        if wal_file.exists():
            shutil.copy2(wal_file, tmp_dir / wal_file.name)

    return dst

def validate_sqlite(path: Path) -> None:
    """Validate connection to SQLite."""
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA integrity_check")

def validate_postgres(db_url: str) -> None:
    """Validate connection to Postgres."""
    conn = psycopg2.connect(db_url)
    conn.close()

def sqlite_row_counts(conn: sqlite3.Connection, tables: List[str]) -> Dict[str, int]:
    """Get row counts for all tables."""
    counts = {}
    for table in tables:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            counts[table] = count
        except sqlite3.Error:
            counts[table] = -1
    return counts

def postgres_row_counts(conn, tables: List[str]) -> Dict[str, int]:
    """Get row counts for all tables."""
    counts = {}
    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f'SELECT COUNT(*) FROM {pg_ident(table)}')
                counts[table] = cur.fetchone()[0]
            except psycopg2.Error:
                counts[table] = -1
    return counts

def pg_ident(name: str) -> str:
    """Protected postgres names."""
    if name.lower() in {"user", "group", "order", "table", "select"}:
        return f'"{name}"'
    return name

TABLE_ORDER = [
    "user",
    "knowledge",
    "file",
    "auth",
    "memory",
    "tag",
    "folder",
    "chat",
    "chat_message",
    "chatidtag",
    "function",
    "tool",
    "model",
    "prompt",
    "prompt_history",
    "document",
    "channel",
    "message",
    "message_reaction",
    "channel_member",
    "channel_webhook",
    "oauth_session",
    "group",
    "group_member",
    "api_key",
    "feedback",
    "note",
    "skill",
    "access_grant",
    "chat_file",
    "channel_file",
    "knowledge_file",
]

TABLE_DEPENDENCIES = {
    "chat_file": ["chat", "file"],
    "channel_file": ["channel", "file"],
    "knowledge_file": ["knowledge", "file"],
    "api_key": ["user"],
    "oauth_session": ["user"],
    "group_member": ["group", "user"],
    "channel_webhook": ["channel"],
    "channel_member": ["channel"],
    "chat_message": ["chat"],
    "message_reaction": ["message"],
}

def sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    """Get SQLite tables in dependency order."""
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    available = {
        r[0] for r in cur.fetchall()
        if r[0] not in {"alembic_version", "migratehistory"}
    }

    ordered = []
    migrated = set()
    max_iterations = len(available) + 1
    for _ in range(max_iterations):
        remaining = available - migrated
        if not remaining:
            break
        progress_made = False
        for table in TABLE_ORDER:
            if table in remaining:
                deps = TABLE_DEPENDENCIES.get(table, [])
                if all(d in migrated for d in deps):
                    ordered.append(table)
                    migrated.add(table)
                    progress_made = True
        if not progress_made:
            ordered.extend(sorted(remaining))
            break
    return ordered

def sqlite_schema(conn: sqlite3.Connection, table: str):
    """Get SQLite schema."""
    return conn.execute(f'PRAGMA table_info("{table}")').fetchall()

def pg_column_types(conn, table: str) -> Dict[str, str]:
    """Postgres column types."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
        """, (table,))
        return dict(cur.fetchall())

def stream_sqlite_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: List[str],
) -> Iterable[tuple]:
    col_sql = ", ".join(f'"{c}"' for c in columns)
    cur = conn.execute(f'SELECT {col_sql} FROM "{table}"')

    while True:
        rows = cur.fetchmany(500)
        if not rows:
            break
        for row in rows:
            yield row

def normalize_row(row, columns, pg_types):
    """Normalize DB row in Postgres."""
    out = []
    for value, col in zip(row, columns):
        col_type = pg_types.get(col)
        if value is None:
            out.append(None)
        elif col_type == "jsonb":
            if isinstance(value, (dict, list)):
                out.append(json.dumps(value))
            else:
                try:
                    json.loads(value)
                    out.append(value)
                except Exception:
                    out.append("{}")
        else:
            out.append(value)
    return tuple(out)

class CopyStream:
    """Streaming file-like object for psycopg2 COPY."""

    def __init__(self, row_iter):
        self.row_iter = row_iter
        self._buffer = ""
        self._exhausted = False

    def _next_line(self):
        try:
            row = next(self.row_iter)
        except StopIteration:
            self._exhausted = True
            return ""

        output = StringIO()
        writer = csv.writer(
            output,
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writerow("" if v is None else v for v in row)
        return output.getvalue()

    def read(self, size=8192):
        if self._exhausted and not self._buffer:
            return ""

        # Fill buffer until we have enough data or exhausted
        while len(self._buffer) < size and not self._exhausted:
            self._buffer += self._next_line()

        # Return up to `size` bytes
        result = self._buffer[:size]
        self._buffer = self._buffer[size:]

        return result

def migrate_table(sqlite_conn: sqlite3.Connection, pg_conn, table: str):
    """Migrate a table."""
    start_time = time.time()
    sqlite_count = sqlite_conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]

    console.print(
        f"[cyan]Table:[/] {table} "
        f"[dim](rows: {sqlite_count})[/]"
    )

    if DRY_RUN:
        console.print(f"[yellow]DRY-RUN: for {table}[/]")
        return

    schema = sqlite_schema(sqlite_conn, table)
    columns = [c[1] for c in schema]
    pg_types = pg_column_types(pg_conn, table)
    with pg_conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {pg_ident(table)} CASCADE")
    pg_conn.commit()

    row_iter = (
        normalize_row(row, columns, pg_types)
        for row in stream_sqlite_rows(sqlite_conn, table, columns)
    )

    with pg_conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {pg_ident(table)} ({', '.join(columns)}) "
            f"FROM STDIN WITH CSV",
            CopyStream(row_iter),
        )
    elapsed = time.time() - start_time
    console.print(f"[green]Migrated {table} in {elapsed:.2f}s[/]")

def main():
    """ Run the script """
    global DRY_RUN
    args = parse_args()
    DRY_RUN = args.dry_run

    if args.sqlite_counts:
        sqlite_copy_path = copy_sqlite_db(SQLITE_PATH)
        validate_sqlite(sqlite_copy_path)
        sqlite_conn = sqlite3.connect(sqlite_copy_path, timeout=60)
        all_tables = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = sorted([r[0] for r in all_tables])
        counts = sqlite_row_counts(sqlite_conn, tables)
        total = sum(counts.values())

        table = Table(title="SQLite Row Counts")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", justify="right", style="green")
        for t in tables:
            table.add_row(t, f"{counts[t]:,}")
        table.add_row("[bold]Total[/]", f"[bold]{total:,}[/]")
        console.print(table)

        sqlite_conn.close()
        shutil.rmtree(sqlite_copy_path.parent, ignore_errors=True)
        return

    if args.postgres_counts:
        pg_conn = psycopg2.connect(MIGRATE_DATABASE_URL)
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            tables = sorted([r[0] for r in cur.fetchall()])
        counts = postgres_row_counts(pg_conn, tables)
        total = sum(c for c in counts.values() if c >= 0)

        table = Table(title="PostgreSQL Row Counts")
        table.add_column("Table", style="cyan")
        table.add_column("Rows", justify="right", style="green")
        for t in tables:
            table.add_row(t, f"{counts[t]:,}")
        table.add_row("[bold]Total[/]", f"[bold]{total:,}[/]")
        console.print(table)

        pg_conn.close()
        return

    if args.validate:
        console.print(Panel("Validate Migration", style="cyan"))

        sqlite_copy_path = copy_sqlite_db(SQLITE_PATH)
        validate_sqlite(sqlite_copy_path)
        sqlite_conn = sqlite3.connect(sqlite_copy_path, timeout=60)

        sqlite_tables_list = sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        sqlite_all = sorted([r[0] for r in sqlite_tables_list])
        sqlite_counts = sqlite_row_counts(sqlite_conn, sqlite_all)
        sqlite_conn.close()
        shutil.rmtree(sqlite_copy_path.parent, ignore_errors=True)

        pg_conn = psycopg2.connect(MIGRATE_DATABASE_URL)
        with pg_conn.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            pg_all = sorted([r[0] for r in cur.fetchall()])
        pg_counts = postgres_row_counts(pg_conn, pg_all)
        pg_conn.close()

        all_tables = sorted(set(sqlite_all) | set(pg_all))
        mismatches = []

        result_table = Table(title="Validation Results")
        result_table.add_column("Table", style="cyan")
        result_table.add_column("SQLite", justify="right", style="yellow")
        result_table.add_column("PostgreSQL", justify="right", style="green")
        result_table.add_column("Status", justify="center")

        for t in all_tables:
            sqlite_count = sqlite_counts.get(t, 0)
            pg_count = pg_counts.get(t, 0)
            if sqlite_count == pg_count:
                status = "[green]✓[/]"
            elif sqlite_count == -1 or pg_count == -1:
                status = "[yellow]N/A[/]"
            else:
                status = "[red]✗[/]"
                mismatches.append(t)
            result_table.add_row(t, f"{sqlite_count:,}", f"{pg_count:,}", status)

        console.print(result_table)

        if mismatches:
            console.print(f"[red]Mismatches found in:[/] {', '.join(mismatches)}")
        else:
            console.print("[green]All tables match![/]")
        return

    console.print(
        Panel(
            f"SQLite to PostgreSQL Migration "
            f"{'(DRY-RUN)' if DRY_RUN else ''}",
            style="cyan",
        )
    )

    console.print("[cyan]Creating temporary SQLite copy...[/]")
    sqlite_copy_path = copy_sqlite_db(SQLITE_PATH)
    console.print(f"[green]Using SQLite copy:[/] {sqlite_copy_path}")

    validate_sqlite(sqlite_copy_path)
    validate_postgres(MIGRATE_DATABASE_URL)

    sqlite_conn = sqlite3.connect(sqlite_copy_path, timeout=60)
    sqlite_conn.isolation_level = None
    sqlite_conn.text_factory = lambda b: b.decode("utf-8", errors="replace")

    pg_conn = psycopg2.connect(MIGRATE_DATABASE_URL)

    if DRY_RUN:
        with pg_conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
        console.print("[yellow]DRY-RUN: PostgreSQL session is read-only[/]")
    else:
        with pg_conn.cursor() as cur:
            cur.execute("SET session_replication_role = replica")
        pg_conn.commit()

    tables = sqlite_tables(sqlite_conn)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
    ) as progress:
        task = progress.add_task("Processing tables...", total=len(tables))
        for table in tables:
            migrate_table(sqlite_conn, pg_conn, table)
            progress.advance(task)

    sqlite_conn.close()
    shutil.rmtree(sqlite_copy_path.parent, ignore_errors=True)

    if not DRY_RUN:
        with pg_conn.cursor() as cur:
            cur.execute("SET session_replication_role = origin")
        pg_conn.commit()

    pg_conn.close()

    console.print(Panel("Done", style="green"))

if __name__ == "__main__":
    main()
