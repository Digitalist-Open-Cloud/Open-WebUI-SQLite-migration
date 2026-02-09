#!/usr/bin/env python3
"""
SQLite to PostgreSQL migration for Open WebUI
"""

import os
import json
import sqlite3
import csv
import argparse
from pathlib import Path
from typing import Dict, Iterable, List
from io import StringIO

import psycopg2
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel

__version__ = "0.1.1"
console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="SQLite → PostgreSQL migration for Open WebUI",
        add_help=True,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview migration without writing to PostgreSQL",
    )
    args, _ = parser.parse_known_args()
    return args

DRY_RUN = False

def env(key: str, default=None, *, required=False, cast=str):
    value = os.getenv(key, default)
    if required and value is None:
        raise RuntimeError(f"Missing environment variable: {key}")
    try:
        return cast(value) if value is not None else value
    except Exception:
        raise RuntimeError(f"Invalid value for {key}: {value}")

SQLITE_PATH = Path(env("SQLITE_DB_PATH", required=True))
MIGRATE_DATABASE_URL = env("MIGRATE_DATABASE_URL", required=True)
BATCH_SIZE = env("BATCH_SIZE", 5000, cast=int)

def validate_sqlite(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA integrity_check")

def validate_postgres(db_url: str) -> None:
    conn = psycopg2.connect(db_url)
    conn.close()

def pg_ident(name: str) -> str:
    if name.lower() in {"user", "group", "order", "table", "select"}:
        return f'"{name}"'
    return name

def sqlite_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
    return [
        r[0] for r in cur.fetchall()
        if r[0] not in {"alembic_version", "migratehistory"}
    ]

def sqlite_schema(conn: sqlite3.Connection, table: str):
    return conn.execute(f'PRAGMA table_info("{table}")').fetchall()

def pg_column_types(conn, table: str) -> Dict[str, str]:
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
        rows = cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        for row in rows:
            yield row

def normalize_row(row, columns, pg_types):
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

def migrate_table(sqlite_conn: sqlite3.Connection, pg_conn, table: str):
    sqlite_count = sqlite_conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]

    console.print(
        f"[cyan]Table:[/] {table} "
        f"[dim](rows: {sqlite_count})[/]"
    )

    if DRY_RUN:
        console.print(f"[yellow]DRY‑RUN: for {table}[/]")
        return

    schema = sqlite_schema(sqlite_conn, table)
    columns = [c[1] for c in schema]
    pg_types = pg_column_types(pg_conn, table)

    rows = (
        normalize_row(row, columns, pg_types)
        for row in stream_sqlite_rows(sqlite_conn, table, columns)
    )

    buffer = StringIO()
    writer = csv.writer(
        buffer,
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )

    for row in rows:
        writer.writerow("" if v is None else v for v in row)

    buffer.seek(0)

    with pg_conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {pg_ident(table)} CASCADE")
        cur.copy_expert(
            f"COPY {pg_ident(table)} ({', '.join(columns)}) FROM STDIN WITH CSV",
            buffer,
        )

    pg_conn.commit()

def main():
    global DRY_RUN
    args = parse_args()
    DRY_RUN = args.dry_run
    console.print(
        Panel(
            f"SQLite → PostgreSQL Migration "
            f"{'(DRY‑RUN)' if DRY_RUN else ''}",
            style="cyan",
        )
    )

    validate_sqlite(SQLITE_PATH)
    validate_postgres(MIGRATE_DATABASE_URL)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.text_factory = lambda b: b.decode("utf-8", errors="replace")

    pg_conn = psycopg2.connect(MIGRATE_DATABASE_URL)

    if DRY_RUN:
        with pg_conn.cursor() as cur:
            cur.execute("SET default_transaction_read_only = on")
        console.print("[yellow]DRY‑RUN: PostgreSQL session is read‑only[/]")
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

    if not DRY_RUN:
        with pg_conn.cursor() as cur:
            cur.execute("SET session_replication_role = origin")
        pg_conn.commit()

    pg_conn.close()

    console.print(Panel("Done", style="green"))

if __name__ == "__main__":
    main()
