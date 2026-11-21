# PostgreSQL — RPM (RHEL/CentOS/Fedora/Amazon Linux)

Uses the official PGDG Yum repository.

## Install

```bash
# EL9 example — pick the RPM matching your distro/version
sudo dnf install -y "https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm"

# Disable the built-in module so PGDG's version wins
sudo dnf -qy module disable postgresql

sudo dnf install -y postgresql17-server postgresql17
```

## Start

```bash
# Initialize the data directory (PGDG packages don't auto-initdb)
sudo /usr/pgsql-17/bin/postgresql-17-setup initdb

sudo systemctl enable --now postgresql-17

sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'changeme';"
sudo -u postgres psql
```

## Verify

```sql
SELECT version();
```

## Notes

- Installs server + client.
- Config + data at `/var/lib/pgsql/17/data/` (`postgresql.conf`, `pg_hba.conf`).
- Logs at `/var/lib/pgsql/17/data/log/`.
- For EL8 use the `EL-8-x86_64` repo RPM; Amazon Linux 2023 uses the EL9 repo RPM.
- To allow remote connections, edit `listen_addresses` and `pg_hba.conf`, then restart.

Official guide: [PGDG Yum repository](https://www.postgresql.org/download/linux/redhat/).
