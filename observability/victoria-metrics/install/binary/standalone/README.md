# VictoriaMetrics — binary single-node (systemd)

VictoriaMetrics single-node is a self-contained binary that scales vertically and handles millions of metrics/s. No external dependencies required.

## Install (Linux amd64)

```bash
VERSION=1.150.0
wget "https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v${VERSION}/victoria-metrics-linux-amd64-v${VERSION}.tar.gz"
sudo tar -xvf victoria-metrics-linux-amd64-v${VERSION}.tar.gz -C /usr/local/bin

sudo useradd -s /usr/sbin/nologin victoriametrics
sudo mkdir -p /var/lib/victoria-metrics
sudo chown -R victoriametrics:victoriametrics /var/lib/victoria-metrics
```

## systemd service

```bash
sudo cat <<'EOF' > /etc/systemd/system/victoriametrics.service
[Unit]
Description=VictoriaMetrics service
After=network.target

[Service]
Type=simple
User=victoriametrics
Group=victoriametrics
ExecStart=/usr/local/bin/victoria-metrics-prod -storageDataPath=/var/lib/victoria-metrics -selfScrapeInterval=10s
Restart=always
PrivateTmp=yes
ProtectHome=yes
NoNewPrivileges=yes
ProtectSystem=full

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now victoriametrics.service
sudo systemctl status victoriametrics.service
```

Access vmui at `http://<host>:8428/vmui`.

## Notes

- Single binary, no JVM, no GC pauses.
- Listens on `:8428` for HTTP (configurable via `-httpListenAddr`).
- Built-in Prometheus scraper via `-promscrape.config`.
- For the full observability stack (VictoriaLogs + VictoriaTraces + Grafana), see the Docker Compose benchmark.

Official guide: [VictoriaMetrics Quick Start — Binary](https://docs.victoriametrics.com/victoriametrics/quick-start/#starting-victoriametrics-single-node-from-a-binary).
