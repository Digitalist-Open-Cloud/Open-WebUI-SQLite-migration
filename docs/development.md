# Development

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

### Linting

```shell
poetry run pylint $(git ls-files '*.py')
```
