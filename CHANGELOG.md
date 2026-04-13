# Changelog

## [0.1.20] - 2026-04-1

### Fixed

- Issue with `date_of_birth` in `users` if empty.

## [0.1.19] - 2026-04-1

### Fixed

- Issue with `date_of_birth` in `users` if empty.

## [0.1.18] - 2026-04-13

### Fixed

- Only allow text/varchar for empty strings.

## [0.1.17] - 2026-04-13

### Added

- Handle NULL values also for groups description, which will be converted to strings.

## [0.1.16] - 2026-04-13

### Added

- Handle NULL values, and make sure empty strings are properly quoted.

## [0.1.15] - 2026-03-31

### Security

- Bumbed version of `pygments`, because of [CVE-2026-4539](https://nvd.nist.gov/vuln/detail/CVE-2026-4539)

## [0.1.14] - 2026-03-31

### Added

- SBOM generation on new release.

## [0.1.13] - 2026-03-30

### Added

- Security policy
- Simple validation of migration

```shell
# Validate migration (compare SQLite to PostgreSQL counts)
open-webui-migrate-sqlite --validate
```

## [0.1.12] - 2026-03-30

### Added

- List tables alphabetic and nice table output.

## [0.1.11] - 2026-03-30

### Added

- Options to list number of rows in Postgres and SQLite.

```shell
# Show row counts in SQLite (before migration)
open-webui-migrate-sqlite --sqlite-counts

# Show row counts in PostgreSQL (after migration)
open-webui-migrate-sqlite --postgres-counts
```

## [0.1.10] - 2026-03-30

### Changed

- Improved migration with setting table order.

## [0.1.9] - 2026-02-26

### Changed

- Improved logging.

## [0.1.8] - 2026-02-26

### Changed

- Fixed bug for streaming copy.

## [0.1.7] - 2026-02-25

### Changed

- Removing batches, created class for handling the data stream.

## [0.1.6] - 2026-02-25

### Changed

- Smaller batches, fix memory usage.

## [0.1.5] - 2026-02-10

### Changed

- Changelog URL.

## [0.1.4] - 2026-02-10

### Updated

- Handle big databases better, do not use all the memory.

### Changed

- Copy SQLite database to `/tmp` before running migration.

## [0.1.3] - 2026-02-09

### Added

- Picky cleanup.

## [0.1.2] - 2026-02-09

### Added

- Tests and code coverage (mostly AI-generated)

## [0.1.1] - 2026-02-09

### Added

- Dry run option

## [0.1.0] - 2026-02-09

### Added

- Simple migration script
