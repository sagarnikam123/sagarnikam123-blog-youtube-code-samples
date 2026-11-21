# SigNoz — binary/systemd standalone (Linux)

SigNoz supports bare-metal Linux installation using Foundry with systemd-managed services. The platform binary, OTel Collector, ClickHouse, and PostgreSQL run as systemd units on a single server.

## Prerequisites

- Linux host (amd64 or arm64)
- ClickHouse installed (single binary serves server + keeper)
- PostgreSQL installed
- `foundryctl` CLI

## Install

```bash
# 1. Install Foundry CLI
curl -fsSL https://signoz.io/foundry.sh | bash

# 2. Download SigNoz binaries
ARCH=$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')
sudo mkdir -p /opt/signoz /opt/ingester

curl -fsSL "https://github.com/SigNoz/signoz/releases/latest/download/signoz_linux_${ARCH}.tar.gz" \
  | sudo tar -xz --strip-components=1 -C /opt/signoz

curl -fsSL "https://github.com/SigNoz/signoz-otel-collector/releases/latest/download/signoz-otel-collector_linux_${ARCH}.tar.gz" \
  | sudo tar -xz --strip-components=1 -C /opt/ingester

# 3. Create casting.yaml
sudo mkdir -p /opt/signoz-foundry && cd /opt/signoz-foundry
cat <<'EOF' > casting.yaml
apiVersion: v1alpha1
kind: Installation
metadata:
  name: signoz
spec:
  deployment:
    flavor: binary
    mode: systemd
EOF

# 4. Deploy
sudo foundryctl cast -f casting.yaml

# 5. Verify
systemctl status signoz-signoz.service
systemctl status signoz-ingester.service
systemctl status signoz-telemetrystore-clickhouse-0-0.service
systemctl status signoz-metastore-postgres.service
```

Open `http://<server-ip>:8080/` for the SigNoz UI.

## Notes

- ClickHouse and PostgreSQL are external dependencies installed manually before running Foundry.
- Foundry generates systemd unit files, configs, and manages the service lifecycle.
- Pin binary versions by downloading specific releases instead of `latest`.
- For Docker-based installation, see [Docker standalone](../../docker/standalone/).

Official guide: [Install SigNoz on Linux with systemd](https://signoz.io/docs/install/linux/).
