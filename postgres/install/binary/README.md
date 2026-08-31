# PostgreSQL — quick install (pgenv)

PostgreSQL doesn't publish a generic run-from-anywhere tarball the way ClickHouse does. For a no-root, local, multi-version install, [`pgenv`](https://github.com/theory/pgenv) builds and manages Postgres versions in your home directory. (For a graphical all-in-one on any OS, the [EDB installers](https://www.postgresql.org/download/) are the alternative.)

## Install pgenv

```bash
git clone https://github.com/theory/pgenv.git ~/.pgenv
export PATH="$HOME/.pgenv/bin:$PATH"      # add to ~/.bashrc / ~/.zshrc
```

> Building from source needs a compiler + `readline`/`zlib` dev headers
> (Debian: `build-essential libreadline-dev zlib1g-dev`; RHEL: `gcc readline-devel zlib-devel`).

## Build & start

```bash
pgenv build 17.2        # download + compile
pgenv use 17.2          # initdb + start on port 5432
```

## Verify

```bash
psql -h localhost -U postgres -c "SELECT version();"
```

## Notes

- Everything lives under `~/.pgenv/` — no root, no system packages.
- `pgenv versions` lists installed versions; `pgenv use <v>` switches the running server.
- Data dir: `~/.pgenv/pgsql/data`. Stop with `pgenv stop`.
- For production, prefer the PGDG DEB/RPM packages with systemd.

Official sources:
- [pgenv](https://github.com/theory/pgenv)
- [Download overview](https://www.postgresql.org/download/)
