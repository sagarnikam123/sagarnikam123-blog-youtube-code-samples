# Coroot — binary/systemd standalone (Linux)

Coroot supports bare-metal/VM installation on Ubuntu, Debian, and RHEL using official install scripts. The server, ClickHouse, Prometheus, and node-agent all run as systemd services.

## Prerequisites

- Linux host (kernel 5.8+ for eBPF node-agent)
- Ubuntu/Debian or RHEL

## Install (Ubuntu/Debian)

```bash
# Step 1: Install ClickHouse
sudo apt install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL 'https://packages.clickhouse.com/rpm/lts/repodata/repomd.xml.key' | \
  sudo gpg --dearmor -o /usr/share/keyrings/clickhouse-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/clickhouse-keyring.gpg] https://packages.clickhouse.com/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/clickhouse.list
sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y clickhouse-server clickhouse-client
sudo service clickhouse-server start

# Step 2: Install Prometheus (with remote-write-receiver)
sudo apt install -y prometheus
echo 'ARGS="--enable-feature=remote-write-receiver"' | sudo tee /etc/default/prometheus
sudo service prometheus restart

# Step 3: Install Coroot server
curl -sfL https://raw.githubusercontent.com/coroot/coroot/main/deploy/install.sh | \
  BOOTSTRAP_PROMETHEUS_URL="http://127.0.0.1:9090" \
  BOOTSTRAP_REFRESH_INTERVAL=15s \
  BOOTSTRAP_CLICKHOUSE_ADDRESS=127.0.0.1:9000 \
  sh -

# Step 4: Install coroot-node-agent (eBPF)
curl -sfL https://raw.githubusercontent.com/coroot/coroot-node-agent/main/install.sh | \
  COLLECTOR_ENDPOINT=http://127.0.0.1:8080 \
  SCRAPE_INTERVAL=15s \
  sh -
```

Access Coroot at `http://<NODE_IP>:8080`.

## Upgrade

Re-run the install script from Step 3 — it downloads the latest version and restarts the service.

## Uninstall

```bash
/usr/local/bin/coroot-uninstall.sh
```

## Notes

- eBPF node-agent requires Linux kernel 5.8+.
- Prometheus must have `--enable-feature=remote-write-receiver`.
- ClickHouse and Prometheus are external dependencies managed separately.
- For Docker-based deployments, see [`../../docker-compose/standalone/`](../../docker-compose/standalone/).

Official guide: [Ubuntu & Debian installation](https://docs.coroot.com/installation/ubuntu/).
