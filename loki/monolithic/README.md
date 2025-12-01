# Loki Monolithic Setup

Complete Loki monolithic deployment with comprehensive tooling for local development and testing.

## 📁 Directory Structure

```
loki/monolithic/
├── setup/                          # Installation & Setup
│   ├── install.sh                  # Main installation script
│   ├── quick-start.sh             # Quick setup script
│   └── README.md                  # Setup documentation
├── configs/                        # Loki Configurations
│   ├── v2.x/                      # Loki 2.x configs
│   ├── v3.x/                      # Loki 3.x configs
│   │   ├── minimal/               # Basic configurations
│   │   ├── production/            # Production-ready configs
│   │   └── development/           # Development configs
│   └── official-docs/             # Official config examples
├── log-scrapers/                   # Log Collection Tools
│   ├── fluent-bit/                # Fluent Bit configurations
│   ├── alloy/                     # Grafana Alloy configs
│   └── vector/                    # Vector configurations
├── observability/                  # Monitoring & Metrics
│   ├── prometheus/                # Prometheus configs
│   ├── grafana/                   # Grafana configs & dashboards
│   └── metrics/                   # Metrics collection tools
├── storage/                        # Storage Backends
│   └── minio/                     # MinIO configuration
├── scripts/                        # Operational Scripts
│   ├── stack/                     # Start/stop services
│   ├── logs/                      # Log generation
│   └── utils/                     # Utility scripts
└── docs/                          # Documentation
    └── USAGE.md                   # Usage guide
```

## 🚀 Quick Start

```bash
# 1. Install components
./setup/install.sh

# 2. Start Loki stack
./scripts/stack/start-loki.sh
./scripts/stack/start-prometheus.sh
./scripts/stack/start-grafana.sh

# 3. Generate logs
./scripts/logs/generate-logs.sh

# 4. Collect metrics
./observability/metrics/collect-all-metrics.sh
```

## 📖 Documentation

- **Setup Guide**: [setup/README.md](setup/README.md)
- **Usage Guide**: [docs/USAGE.md](docs/USAGE.md)
- **Configuration Guide**: [configs/v3.x/README.md](configs/v3.x/README.md)

## 🔧 Configuration Categories

### Minimal Configs
- Basic Loki setup with essential components
- Perfect for learning and testing

### Production Configs
- Full ring configuration with all components
- Optimized for production workloads

### Development Configs
- Development-focused configurations
- Debugging and troubleshooting enabled

## 📊 Monitoring

Access the observability stack:
- **Loki**: http://localhost:3100
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 🛠️ Scripts

All operational scripts organized by function:
- **Stack Management**: Start/stop services
- **Log Generation**: Create test data
- **Utilities**: Cleanup and maintenance
