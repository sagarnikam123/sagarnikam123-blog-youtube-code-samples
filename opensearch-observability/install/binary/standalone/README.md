# OpenSearch Observability — native install (tarball / package)

Native single-node install of the three components on Linux. Latest version at time of writing: **OpenSearch 3.8.0** (bundles Java 25; needs Java 21/25/26 if using your own JDK).

- **OpenSearch** — search/analytics engine (REST API on `9200`)
- **OpenSearch Dashboards** — UI (`5601`)
- **Data Prepper** — OTLP ingest + pipelines (`4317`/`4318`)

Config files in this folder are for **local single-node dev with the Security plugin disabled**. Enable security before any shared/production use (see [Notes](#notes)).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Option A: Tarball](#option-a-tarball)
- [Option B: Debian/APT package](#option-b-debianapt-package)
- [Option C: RPM package](#option-c-rpm-package)
- [OpenSearch Dashboards](#opensearch-dashboards)
- [Data Prepper](#data-prepper)
- [Verify](#verify)
- [Config files](#config-files)
- [Notes](#notes)

---

## Prerequisites

OpenSearch needs one host-level setting on Linux (applies to every install method):

```bash
# Increase mmap count (required — OpenSearch won't start reliably below this)
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf

# Disable swap for performance/stability
sudo swapoff -a
```

The Linux tarball/packages bundle a compatible JDK, so no separate Java install is required.

---

## Option A: Tarball

Self-contained directory, no root, full control over paths.

```bash
OPENSEARCH_VERSION="3.8.0"
ARCH="x64"        # or arm64

# x64
wget "https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VERSION}/opensearch-${OPENSEARCH_VERSION}-linux-${ARCH}.tar.gz"
tar -xzf "opensearch-${OPENSEARCH_VERSION}-linux-${ARCH}.tar.gz"
cd "opensearch-${OPENSEARCH_VERSION}"
```

Apply the local-dev config from this folder (security disabled), then start:

```bash
cp /path/to/config/opensearch.yml config/opensearch.yml
cp /path/to/config/jvm.options.d-heap.options config/jvm.options.d/heap.options   # optional heap override

./opensearch-tar-install.sh        # runs in the foreground; Ctrl-C to stop
```

> `opensearch-tar-install.sh` normally applies a demo security config. With `plugins.security.disabled: true` in `opensearch.yml` (as shipped here), it starts on plain HTTP for local testing.

---

## Option B: Debian/APT package

systemd-managed, config under `/etc/opensearch/`. For OpenSearch 3.7+ you can skip the demo security setup at install time.

```bash
OPENSEARCH_VERSION="3.8.0"
curl -SLO "https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VERSION}/opensearch-${OPENSEARCH_VERSION}-linux-x64.deb"

# Local dev — skip demo security config entirely:
sudo env DISABLE_INSTALL_DEMO_CONFIG=true dpkg -i "opensearch-${OPENSEARCH_VERSION}-linux-x64.deb"

# Production with demo TLS — set an admin password instead:
# sudo env OPENSEARCH_INITIAL_ADMIN_PASSWORD='<Strong-Passw0rd!>' dpkg -i opensearch-${OPENSEARCH_VERSION}-linux-x64.deb
```

Apply local-dev config and start:

```bash
sudo cp config/opensearch.yml /etc/opensearch/opensearch.yml
sudo systemctl enable --now opensearch
sudo systemctl status opensearch
```

---

## Option C: RPM package

```bash
OPENSEARCH_VERSION="3.8.0"
sudo curl -SLO "https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VERSION}/opensearch-${OPENSEARCH_VERSION}-linux-x64.rpm"

sudo env DISABLE_INSTALL_DEMO_CONFIG=true rpm -ivh "opensearch-${OPENSEARCH_VERSION}-linux-x64.rpm"

sudo cp config/opensearch.yml /etc/opensearch/opensearch.yml
sudo systemctl enable --now opensearch
```

---

## OpenSearch Dashboards

The web UI for OpenSearch — Discover, visualizations, Query Workbench, Dev Tools, and the observability plugins. Install the version matching your OpenSearch node (**3.8.0** here). Distribution packages bundle a compatible Node.js runtime (3.5+ ships Node.js 22), so no separate Node install is needed.

### Tarball

```bash
OPENSEARCH_VERSION="3.8.0"
ARCH="x64"        # or arm64
wget "https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/${OPENSEARCH_VERSION}/opensearch-dashboards-${OPENSEARCH_VERSION}-linux-${ARCH}.tar.gz"
tar -xzf "opensearch-dashboards-${OPENSEARCH_VERSION}-linux-${ARCH}.tar.gz"
cd "opensearch-dashboards-${OPENSEARCH_VERSION}"

cp /path/to/config/opensearch_dashboards.yml config/opensearch_dashboards.yml
./bin/opensearch-dashboards        # foreground; Ctrl-C to stop
```

### Debian/APT package

```bash
OPENSEARCH_VERSION="3.8.0"
curl -SLO "https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/${OPENSEARCH_VERSION}/opensearch-dashboards-${OPENSEARCH_VERSION}-linux-x64.deb"
sudo dpkg -i "opensearch-dashboards-${OPENSEARCH_VERSION}-linux-x64.deb"

sudo cp config/opensearch_dashboards.yml /etc/opensearch-dashboards/opensearch_dashboards.yml
sudo systemctl enable --now opensearch-dashboards
sudo systemctl status opensearch-dashboards
```

### RPM package

```bash
OPENSEARCH_VERSION="3.8.0"
sudo curl -SLO "https://artifacts.opensearch.org/releases/bundle/opensearch-dashboards/${OPENSEARCH_VERSION}/opensearch-dashboards-${OPENSEARCH_VERSION}-linux-x64.rpm"
sudo rpm -ivh "opensearch-dashboards-${OPENSEARCH_VERSION}-linux-x64.rpm"

sudo cp config/opensearch_dashboards.yml /etc/opensearch-dashboards/opensearch_dashboards.yml
sudo systemctl enable --now opensearch-dashboards
```

### Docker

```bash
docker run -d --name dashboards \
  -p 5601:5601 \
  -e "OPENSEARCH_HOSTS=http://host.docker.internal:9200" \
  -e "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" \
  opensearchproject/opensearch-dashboards:3.8.0
```

### Access & verify

Open `http://localhost:5601`. Then confirm it connected to the backend:

```bash
# Dashboards server status API (reports "green"/"yellow" and the OpenSearch link)
curl -s http://localhost:5601/api/status | grep -o '"state":"[a-z]*"' | head -1
```

With security disabled (local dev), no login prompt appears. With security enabled, log in with your admin credentials.

> **Node.js:** the packages bundle Node.js 22 (OpenSearch Dashboards 3.5+). To use your own runtime instead, install Node.js `>=14.20.1 <23` and set `NODE_OSD_HOME` (or `NODE_HOME`) to its install path before running `bin/opensearch-dashboards`.

> **Version match:** run the same major.minor as your OpenSearch node. A Dashboards version newer/older than the cluster can fail to connect or hide features.

---

## Data Prepper

OTLP receiver + pipeline component. Install matching-era distribution:

```bash
DATA_PREPPER_VERSION="2.12.0"
wget "https://artifacts.opensearch.org/data-prepper/${DATA_PREPPER_VERSION}/opensearch-data-prepper-${DATA_PREPPER_VERSION}-linux-x64.tar.gz"
tar -xzf "opensearch-data-prepper-${DATA_PREPPER_VERSION}-linux-x64.tar.gz"
cd "opensearch-data-prepper-${DATA_PREPPER_VERSION}"

cp /path/to/config/data-prepper-config.yaml config/data-prepper-config.yaml
cp /path/to/config/pipelines.yaml pipelines/pipelines.yaml
bin/data-prepper
```

> The Compose stack at [`../../docker-compose/standalone/config/`](../../docker-compose/standalone/config/) has ready-made `data-prepper-config.yaml` and `data-prepper-pipelines.yaml` you can reuse.

---

## Verify

```bash
# OpenSearch (security disabled → plain HTTP)
curl http://localhost:9200

# Cluster health
curl http://localhost:9200/_cluster/health?pretty

# Version
curl -s http://localhost:9200 | grep number
```

Expected: JSON with `"number" : "3.8.0"` and cluster status `green` (single node).

---

## Config files

| File | Applies to | Purpose |
|:-----|:-----------|:--------|
| [`config/opensearch.yml`](config/opensearch.yml) | OpenSearch | single-node, bind address, security disabled (local dev) |
| [`config/jvm.options.d-heap.options`](config/jvm.options.d-heap.options) | OpenSearch | heap override (drop into `config/jvm.options.d/`) |
| [`config/opensearch_dashboards.yml`](config/opensearch_dashboards.yml) | Dashboards | points at OpenSearch, security plugin disabled |

---

## Notes

- **Security is disabled** in these configs for frictionless local dev. For anything shared: remove `plugins.security.disabled: true`, install with demo TLS (`OPENSEARCH_INITIAL_ADMIN_PASSWORD`), then replace demo certs with real ones. See [Security configuration](https://docs.opensearch.org/latest/security/configuration/index/).
- **Ports:** `9200` REST, `9300` transport/node, `9600` Performance Analyzer, `5601` Dashboards, `4317`/`4318` Data Prepper OTLP.
- **Java heap:** default `-Xms1g -Xmx1g`. Set to ~50% of host RAM via `config/jvm.options.d/`. Don't set heap in both `jvm.options` and `OPENSEARCH_JAVA_OPTS`.
- Pin the version (`3.8.0`) for reproducibility; check the [downloads page](https://opensearch.org/downloads.html) for newer releases.

Official sources:
- [Install OpenSearch](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/index/)
- [Tarball](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/tar/)
- [Debian](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/debian/) · [RPM](https://docs.opensearch.org/latest/install-and-configure/install-opensearch/rpm/)
- [Install Dashboards](https://docs.opensearch.org/latest/install-and-configure/install-dashboards/index/)
- [Data Prepper](https://docs.opensearch.org/latest/data-prepper/)
