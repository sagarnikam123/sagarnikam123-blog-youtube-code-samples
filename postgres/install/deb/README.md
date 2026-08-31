# PostgreSQL — DEB/APT (Debian/Ubuntu)

Uses the official PostgreSQL Global Development Group (PGDG) APT repository, which tracks the latest major versions (newer than distro defaults).

## Install

```bash
sudo apt-get install -y curl ca-certificates
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
  --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc

echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | \
  sudo tee /etc/apt/sources.list.d/pgdg.list

sudo apt-get update
sudo apt-get install -y postgresql-17
```

## Start

```bash
sudo systemctl enable --now postgresql

# Set a password for the default superuser
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'changeme';"
sudo -u postgres psql
```

## Verify

```sql
SELECT version();
```

## Notes

- Installs server + client + contrib.
- Config at `/etc/postgresql/17/main/` (`postgresql.conf`, `pg_hba.conf`).
- Data at `/var/lib/postgresql/17/main/`.
- Logs at `/var/log/postgresql/`.
- Ubuntu also ships Postgres in default repos (`apt-get install postgresql`) — PGDG just tracks newer versions.
- To allow remote connections, set `listen_addresses = '*'` in `postgresql.conf` and add a `pg_hba.conf` rule.

Official guide: [PGDG APT repository](https://www.postgresql.org/download/linux/ubuntu/).
