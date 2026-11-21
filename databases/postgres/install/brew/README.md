# PostgreSQL — Homebrew (macOS)

The simplest native install on macOS. Two routes: the `postgresql` formula (CLI + `brew services`) or Postgres.app (menu-bar GUI). The macOS equivalent of the DEB/RPM package modes.

## Option A: Homebrew formula (CLI)

```bash
brew install postgresql@18
```

> `postgresql@18` is keg-only and versioned. The unversioned `postgresql` alias tracks the latest major. If `psql`/`pg_config` don't appear on PATH, link it:
> ```bash
> brew link postgresql@18
> ```
> If a `libpq`-only install conflicts on link, `brew unlink libpq` first — `postgresql` supersedes it.

### Start

```bash
# Background service (starts now + at login)
brew services start postgresql@18

# Or run in the foreground (no auto-start)
LC_ALL="en_US.UTF-8" /opt/homebrew/opt/postgresql@18/bin/postgres -D /opt/homebrew/var/postgresql@18
```

### Connect

```bash
# Default superuser = your macOS username, no password
psql -d postgres
```

### Verify

```sql
SELECT version();
```

## Option B: Postgres.app (GUI)

```bash
brew install --cask postgres-app
```

Launch **Postgres** from Applications, click **Initialize** to create a server (listens on `127.0.0.1:5432`). To use its CLI tools, add them to PATH:

```bash
echo '/Applications/Postgres.app/Contents/Versions/latest/bin' | sudo tee /etc/paths.d/postgresapp
```

## Manage (formula)

```bash
brew services list
brew services restart postgresql@18
brew services stop postgresql@18
```

## Create a database

```bash
createdb kiro
psql -d kiro -c "CREATE ROLE app LOGIN PASSWORD 'app'; GRANT ALL ON SCHEMA public TO app;"
```

## Notes

- Formula data dir: `/opt/homebrew/var/postgresql@18/` (initialized by the formula's post-install).
- Config: `postgresql.conf` / `pg_hba.conf` in that data dir.
- Postgres.app keeps its data under `~/Library/Application Support/Postgres/`.
- Both listen on `127.0.0.1:5432`; run only one at a time to avoid a port clash.

Official sources:
- [Homebrew formula: postgresql@18](https://formulae.brew.sh/formula/postgresql@18)
- [Postgres.app](https://postgresapp.com/)
