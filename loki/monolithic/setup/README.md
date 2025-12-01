# Loki Monolithic

Monolithic Loki configurations for development, testing, and small production deployments.

## What is Monolithic Mode?

Monolithic mode runs all Loki components in a single process:
- **Distributor** - Receives log streams from clients
- **Ingester** - Writes log data and serves queries
- **Query Frontend** - Provides LogQL query interface
- **Querier** - Executes LogQL queries
- **Compactor** - Compacts and processes stored data
- **Ruler** - Evaluates recording and alerting rules

## When to Use Monolithic Mode

✅ **Recommended for:**
- Development and testing
- Small to medium deployments (<100GB/day)
- Proof of concepts
- Local development environments
- Single-node deployments

❌ **Not recommended for:**
- High-volume production (>100GB/day)
- High availability requirements
- Horizontal scaling needs
- Multi-tenant environments

## Structure

```
monolithic/
├── v2.x/          # Loki 2.x configurations
├── v3.x/          # Loki 3.x configurations
├── scripts/       # Start/Stop scripts
├── log-scrapers/  # Log shipper configurations
├── install.sh     # Installation script
└── README.md      # This file
```

## Versions

### Loki 2.x
- Stable, production-ready
- Well-documented features
- Backward compatibility
- Target: `all` (runs all components)

### Loki 3.x
- Latest features
- Performance improvements
- New storage backends
- Enhanced query engine
- Target: `all` (runs all components)

## Configuration Targets

Monolithic mode uses `target: all` which includes:
```yaml
target: all  # Runs: distributor,ingester,querier,query-frontend,compactor,ruler
```

## Storage Options

- **Filesystem** - Local disk storage (development)
- **S3** - Object storage (production-ready)
- **In-memory** - Components like memberlist, caching

## Usage

Choose the appropriate version directory based on your requirements:
- Use `v2.x/` for stable, production environments
- Use `v3.x/` for testing latest features and improvements

## Installation

### Full Stack Installation

Installs Loki, Grafana, Prometheus, MinIO, and related tools:

```bash
# Run the installation script
./install.sh

# Start services
~/loki-stack/scripts/start-loki.sh        # Loki at http://127.0.0.1:3100
~/loki-stack/scripts/start-grafana.sh     # Grafana at http://127.0.0.1:3000
~/loki-stack/scripts/start-prometheus.sh  # Prometheus at http://127.0.0.1:9090
~/loki-stack/scripts/start-minio.sh       # MinIO at http://127.0.0.1:9000

# Stop services
~/loki-stack/scripts/stop-all.sh          # Stop all services
```

### Quick Start (Loki Only)

For immediate testing:

```bash
# Quick Loki setup and start
./quick-start.sh

# Loki will be available at http://127.0.0.1:3100
```

### Manual Installation

```bash
# Download Loki binary
wget https://github.com/grafana/loki/releases/download/v3.5.7/loki-darwin-amd64.zip
unzip loki-darwin-amd64.zip

# Start Loki monolithic
./loki-darwin-amd64 -config.file=v3.x/loki-3.x-dev-local-storage.yaml
```

## Installation Documentation

| Tool | Download Page | Installation Guide | GitHub Releases |
|------|---------------|-------------------|------------------|
| **Loki** | [Loki Downloads](https://grafana.com/loki) | [Installation Guide](https://grafana.com/docs/loki/latest/setup/install/) | [GitHub Releases](https://github.com/grafana/loki/releases) |
| **Grafana** | [Grafana Downloads](https://grafana.com/grafana/download) | [Installation Guide](https://grafana.com/docs/grafana/latest/setup-grafana/installation/) | [GitHub Releases](https://github.com/grafana/grafana/releases) |
| **Prometheus** | [Prometheus Downloads](https://prometheus.io/download/) | [Installation Guide](https://prometheus.io/docs/prometheus/latest/installation/) | [GitHub Releases](https://github.com/prometheus/prometheus/releases) |
| **MinIO** | [MinIO Downloads](https://min.io/download) | [Installation Guide](https://min.io/docs/minio/linux/operations/installation.html) | [GitHub Releases](https://github.com/minio/minio/releases) |
| **Fluent Bit** | [Fluent Bit Downloads](https://fluentbit.io/download/) | [Installation Guide](https://docs.fluentbit.io/manual/installation/getting-started-with-fluent-bit) | [GitHub Releases](https://github.com/fluent/fluent-bit/releases) |
| **Vector** | [Vector Downloads](https://vector.dev/download/) | [Installation Guide](https://vector.dev/docs/setup/installation/) | [GitHub Releases](https://github.com/vectordotdev/vector/releases) |
| **Grafana Alloy** | [Alloy Downloads](https://grafana.com/docs/alloy/latest/get-started/install/) | [Installation Guide](https://grafana.com/docs/alloy/latest/get-started/install/) | [GitHub Releases](https://github.com/grafana/alloy/releases) |

📖 **For detailed configuration usage, see [USAGE.md](USAGE.md)**

**Note**: Log scraper installations are OS-dependent and highly customizable. Refer to official documentation for your specific platform and requirements.

## Resources

- [Loki Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
- [Monolithic Mode Documentation](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#monolithic-mode)
