#!/usr/bin/env python3
"""
name: SQLite → PostgreSQL migration for Open WebUI
description: Migrate Open WebUI from SQLite database to Postgres
version: 0.1.0
license: GPLv3
requirements: psycopg2-binary==2.9.11 rich==13.9.4
"""

from __future__ import annotations

import os
import json
import sqlite3
import csv
from pathlib import Path
from typing import Dict, Iterable, List
from io import StringIO

import psycopg2
from psycopg2.extras import execute_batch
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.panel import Panel

console = Console()

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
    if not path.exists():
        raise FileNotFoundError(f"SQLite DB not found: {path}")
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
    cur = conn.execute(f'PRAGMA table_info("{table}")')
    return cur.fetchall()

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
            try:
                json.loads(value)
                out.append(value)
            except Exception:
                out.append("{}")

        else:
            out.append(value)

    return tuple(out)

def migrate_table(
    sqlite_conn: sqlite3.Connection,
    pg_conn,
    table: str,
):
    console.print(f"[cyan]Migrating table:[/] {table}")

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
        delimiter=",",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    for row in rows:
        writer.writerow(
            "" if v is None else v
            for v in row
        )

    buffer.seek(0)

    with pg_conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {pg_ident(table)} CASCADE")
        copy_sql = f"""
          COPY {pg_ident(table)} ({", ".join(columns)})
          FROM STDIN WITH (FORMAT CSV, HEADER FALSE)
        """
        cur.copy_expert(copy_sql, buffer)

    pg_conn.commit()

def main():
    console.print(Panel("SQLite → PostgreSQL Migration", style="cyan"))

    validate_sqlite(SQLITE_PATH)
    validate_postgres(MIGRATE_DATABASE_URL)

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    pg_conn = psycopg2.connect(MIGRATE_DATABASE_URL)

    # Disable constraints for easy migration.
    # This make no need for table dependency at migration step.
    with pg_conn.cursor() as cur:
      cur.execute("SET session_replication_role = replica")
    pg_conn.commit()

    tables = sqlite_tables(sqlite_conn)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
    ) as progress:
        task = progress.add_task("Migrating tables...", total=len(tables))
        for table in tables:
            migrate_table(sqlite_conn, pg_conn, table)
            progress.advance(task)

    sqlite_conn.close()
    # Re-enable constraints.
    with pg_conn.cursor() as cur:
        cur.execute("SET session_replication_role = origin")
    # Check Postgres.
    with pg_conn.cursor() as cur:
        cur.execute("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN (
                    SELECT conrelid::regclass AS tbl, conname
                    FROM pg_constraint
                    WHERE contype = 'f'
                ) LOOP
                    EXECUTE format(
                        'ALTER TABLE %s VALIDATE CONSTRAINT %I',
                        r.tbl, r.conname
                    );
                END LOOP;
            END $$;
        """)
    pg_conn.commit()
    pg_conn.close()

    console.print(Panel("Migration complete", style="green"))

if __name__ == "__main__":
    main()
