# ClickHouse — RPM (RHEL/CentOS/Fedora)

## Install

```bash
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://packages.clickhouse.com/rpm/clickhouse.repo
sudo yum install -y clickhouse-server clickhouse-client
```

## Start

```bash
sudo systemctl enable --now clickhouse-server
clickhouse-client
```

## Verify

```sql
SELECT version();
```

## Notes

- Installs server + client + Keeper.
- Config at `/etc/clickhouse-server/`.
- Data at `/var/lib/clickhouse/`.
- Supports RHEL 7+, CentOS 7+, Fedora, Amazon Linux.

Official guide: [Install on RHEL](https://clickhouse.com/docs/get-started/setup/self-managed/redhat).
