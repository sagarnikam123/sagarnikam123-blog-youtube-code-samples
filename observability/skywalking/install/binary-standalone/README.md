# SkyWalking + BanyanDB — Binary Standalone Installation

Install Apache SkyWalking OAP, UI, and BanyanDB on a single machine using binary tarballs. No Docker or Kubernetes required.

## Versions

| Component | Version | Port |
|-----------|---------|------|
| SkyWalking OAP | 10.3.0 | gRPC: 11800, HTTP: 12800 |
| SkyWalking UI | 10.3.0 | 8080 |
| BanyanDB | 0.9.0 | gRPC: 17912, HTTP: 17913 |

## Prerequisites

- Java 11+ (Java 17 recommended)
- 4 GB+ RAM
- 20 GB+ disk space
- Linux (amd64/arm64) — BanyanDB server binaries are Linux-only
- macOS users: use Docker for BanyanDB, binary install for SkyWalking OAP/UI

Run the prerequisites script to check and install Java:

```bash
chmod +x install/binary-standalone/install-prerequisites.sh
./install/binary-standalone/install-prerequisites.sh
```

This will:
- Check Java version (installs Java 17 if missing — supports apt, yum, dnf, brew)
- Verify RAM and disk space
- Create the directory structure: `data/`, `logs/`, `downloads/`

## Directory Structure (after install)

```
install/binary-standalone/
├── install-prerequisites.sh
├── install-banyandb.sh
├── install-skywalking.sh
├── README.md
├── conf/                          # Custom configs (bydb.yaml)
│   └── bydb.yaml
├── banyandb/                      # BanyanDB binary + bin/
├── skywalking-oap/                # OAP + UI (bin/, config/, webapp/)
├── downloads/                     # Downloaded tarballs
├── data/
│   └── banyandb/                  # BanyanDB data files
└── logs/                          # Runtime logs
```

---

## Step 1: Install BanyanDB

> **Linux only:** The official BanyanDB tarball contains Linux binaries only (amd64/arm64). macOS users should use Docker instead:
> ```bash
> docker run -d -p 17912:17912 -p 17913:17913 apache/skywalking-banyandb:0.9.0 standalone
> ```

```bash
chmod +x install/binary-standalone/install-banyandb.sh
./install/binary-standalone/install-banyandb.sh
```

Downloads from:
```
https://dlcdn.apache.org/skywalking/banyandb/0.9.0/skywalking-banyandb-0.9.0-banyand.tgz
```

This is a single universal tarball containing multi-platform binaries:
```
bin/
├── banyand-server-slim-linux-amd64
├── banyand-server-slim-linux-arm64
├── banyand-server-static-linux-amd64
└── banyand-server-static-linux-arm64
```

The script auto-detects your architecture and symlinks the correct `banyand-server-static-linux-*` binary to `banyandb/banyand`.

Override the version with:
```bash
# Via argument
./install/binary-standalone/install-banyandb.sh 0.10.0

# Via environment variable
BANYANDB_VERSION=0.10.0 ./install/binary-standalone/install-banyandb.sh
```

After install, the binary is at `banyandb/banyand`.

## Step 2: Install SkyWalking OAP + UI

```bash
chmod +x install/binary-standalone/install-skywalking.sh
./install/binary-standalone/install-skywalking.sh
```

Downloads from:
```
https://dlcdn.apache.org/skywalking/10.3.0/apache-skywalking-apm-10.3.0-bin.tar.gz
```

Override the version with:
```bash
# Via argument
./install/binary-standalone/install-skywalking.sh 10.4.0

# Via environment variable
SKYWALKING_VERSION=10.4.0 ./install/binary-standalone/install-skywalking.sh
```


The install script automatically:
1. Backs up the default `config/application.yml`
2. Changes the storage selector from `h2` (default) to `banyandb`
3. Copies `conf/bydb.yaml` → `skywalking-oap/config/bydb.yaml` (if it exists)
4. Copies `conf/application.yml` → `skywalking-oap/config/application.yml` (if it exists)

---

## Step 3: Configure BanyanDB Storage

The custom BanyanDB config is at `conf/bydb.yaml`. Key settings:

```yaml
global:
  targets: 127.0.0.1:17912        # BanyanDB gRPC address
  maxBulkSize: 10000               # Max records per bulk write
  flushInterval: 15                # Flush interval (seconds)
  concurrentWriteThreads: 15      # Parallel write threads

groups:
  trace:
    shardNum: 2
    ttl: 3                         # Days to keep traces
  recordsLog:
    shardNum: 2
    ttl: 3                         # Days to keep logs
  metricsMinute:
    shardNum: 2
    ttl: 7                         # Days to keep minute metrics
  metricsHour:
    ttl: 15                        # Days to keep hour metrics
  metricsDay:
    ttl: 15                        # Days to keep day metrics
```

All values support environment variable overrides (e.g., `SW_STORAGE_BANYANDB_TRACE_TTL_DAYS`).

---

## Step 4: Start Everything

```bash
chmod +x scripts/start-all.sh
./scripts/start-all.sh
```

Startup order: BanyanDB → OAP → UI. The script waits for each service to be healthy before starting the next.

Environment variables set automatically:
```bash
SW_STORAGE=banyandb
SW_STORAGE_BANYANDB_TARGETS=127.0.0.1:17912
```

## Check Status

```bash
./scripts/status.sh
```

## Stop Everything

```bash
./scripts/stop-all.sh
```

Shutdown order: UI → OAP → BanyanDB (reverse of startup). Sends SIGTERM first, SIGKILL after 10s if the process doesn't exit.

---

## Start Services Individually

If you prefer to start each service manually:

### BanyanDB

```bash
./banyandb/banyand standalone --data-path=./data/banyandb
```

Health check: `curl http://localhost:17913/api/healthz`

### SkyWalking OAP

```bash
export SW_STORAGE=banyandb
export SW_STORAGE_BANYANDB_TARGETS=127.0.0.1:17912
./skywalking-oap/bin/oapService.sh
```

Health check: `curl http://localhost:12800/healthcheck`

### SkyWalking UI

```bash
./skywalking-oap/bin/webappService.sh
```

Open: http://localhost:8080

---

## Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| SkyWalking UI | http://localhost:8080 | Dashboard, topology, traces |
| OAP HTTP API | http://localhost:12800 | GraphQL API, health check |
| OAP gRPC | localhost:11800 | Agent reporting endpoint |
| BanyanDB HTTP | http://localhost:17913 | Health check, web UI |
| BanyanDB gRPC | localhost:17912 | Storage protocol |

## Logs

All logs are written to the `logs/` directory:

| File | Service |
|------|---------|
| `logs/banyandb.log` | BanyanDB |
| `logs/oap.log` | SkyWalking OAP |
| `logs/ui.log` | SkyWalking UI |

---

## Connecting a Java Agent

To send traces from a Java application to this SkyWalking instance:

```bash
java -javaagent:/path/to/skywalking-agent.jar \
  -Dskywalking.agent.service_name=my-service \
  -Dskywalking.collector.backend_service=127.0.0.1:11800 \
  -jar my-app.jar
```

Download the Java agent from:
```
https://dlcdn.apache.org/skywalking/java-agent/9.3.0/apache-skywalking-java-agent-9.3.0.tgz
```

---

## Troubleshooting

### OAP fails to start with "storage not found"
The storage selector in `config/application.yml` is still set to `h2`. Re-run `install-skywalking.sh` or manually change:
```yaml
storage:
  selector: ${SW_STORAGE:banyandb}
```

### OAP can't connect to BanyanDB
Make sure BanyanDB is running and healthy before starting OAP:
```bash
curl http://localhost:17913/api/healthz
```

### Port already in use
Check what's using the port:
```bash
lsof -i :17912   # BanyanDB gRPC
lsof -i :11800   # OAP gRPC
lsof -i :8080    # UI
```

### BanyanDB data corruption
Stop all services, clear data, and restart:
```bash
./scripts/stop-all.sh
rm -rf data/banyandb/*
./scripts/start-all.sh
```

---

## Reference Links

| Topic | URL |
|-------|-----|
| SkyWalking Downloads | https://skywalking.apache.org/downloads/ |
| BanyanDB Downloads | https://skywalking.apache.org/downloads/#BanyanDB |
| SkyWalking Quick Start | https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-setup/ |
| BanyanDB Standalone Setup | https://skywalking.apache.org/docs/skywalking-banyandb/latest/installation/standalone/ |
| BanyanDB Storage Config | https://skywalking.apache.org/docs/main/latest/en/setup/backend/storages/banyandb/ |
| Java Agent Setup | https://skywalking.apache.org/docs/skywalking-java/latest/en/setup/service-agent/java-agent/readme/ |
