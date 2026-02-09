# Migrate tool for OpenWebUI SQLite

Migrate from using SQLite database in Open WebUI to use Postgres.

Inspiration from: <https://github.com/taylorwilsdon/open-webui-postgres-migration>,
one of the big differences is that the migration require no input, with environment
variables set, you just run the script, no input.

This so you can automate the process, instead of manual input.

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

## License

MIT
Copyright (c) Digitalist Open Cloud.
