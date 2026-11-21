# ClickHouse — DEB/APT (Debian/Ubuntu)

## Install

```bash
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | \
  sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/clickhouse.list

sudo apt-get update
sudo apt-get install -y clickhouse-server clickhouse-client
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

- Installs server + client + Keeper (bundled in server).
- Config at `/etc/clickhouse-server/`.
- Data at `/var/lib/clickhouse/`.
- Logs at `/var/log/clickhouse-server/`.

Official guide: [Install on Debian/Ubuntu](https://clickhouse.com/docs/get-started/setup/self-managed/debian-ubuntu).
