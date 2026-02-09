# Migrate tool for OpenWebUI SQLite to Postgres

![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue) [![Tests & Coverage](https://github.com/Digitalist-Open-Cloud/Open-WebUI-SQLite-migration/actions/workflows/tests.yaml/badge.svg)](https://github.com/Digitalist-Open-Cloud/Open-WebUI-SQLite-migration/actions/workflows/tests.yaml)

Migrate from using SQLite database in Open WebUI to use Postgres.

Inspiration from: <https://github.com/taylorwilsdon/open-webui-postgres-migration>,
one of the big differences is that the migration require no input, with environment
variables set, you just run the script, no input.

This so you can automate the process, instead of manual input.

## Install

You can copy the script to you environment and run it, or you could install it:

```shell
pip install open-webui-sqlite-migration
```

## Configuration

Before anything else, backup you SQLite database and keep it in a safe place.

Needed environment variables:

- `SQLITE_DB_PATH` - exact path to your open webui db, like: `/app/backend/data/webui.db`.
- `MIGRATE_DATABASE_URL` - normally the same you should use for `DATABASE_URL`, like `postgresql://user:pass@postgres:5432/openwebui`

Also you need to start Open WebUI with `DATABASE_URL`, so needed tables are created. After that,
you remove that variable so you go back to use SQLite. When using SQLite, you run the migration script,
then you stop Open WebUI, and then again set `DATABASE_URL`. If everything now runs smoothly, you can remove the
SQLite database. Keep a backup of the database until you are really sure that all things are working as they
should.

## Migration

- Again - make sure you backup your SQLite database, before doing anything.
- Start Open WebUI with SQLite if it's not running (info logs should say: `Context impl SQLiteImpl`).
- Stop Open WebUI.
- Start Open WebUI with `DATABASE_URL` set. Needed tables should be created.
- Stop Open WebUI.
- Remove ENV variable `DATABASE_URL`,  start Open WebUI.
- Run `open-webui-migrate-sqlite --dry-run`
- Check output, if what is you expected, go to next step.
- Have you really done a backup of your SQLite database?
- Run `open-webui-migrate-sqlite`
- If all succeeds, restart Open WebUI with `DATABASE_URL` set.
- You should now be running Open WebUI with Postgres (if you have info logs from Open WebUI, you should see `Context impl PostgresqlImpl`).

## Development

Poetry is used.

```shell
poetry install
```

Release:

Make sure to change version, then:

```shell
poetry build
poetry publish
```

## Tests

```shell
export SQLITE_DB_PATH="/web.db"
export MIGRATE_DATABASE_URL=postgresql://user:pass@postgres:5432/openwebui
poetry run pytest
```

### Coverage

```shell
poetry run pytest --cov
```

## License

MIT

Copyright (c) Digitalist Open Cloud.
