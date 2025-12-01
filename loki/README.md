# Loki Deployment Modes

Complete collection of Loki deployment configurations covering all official Grafana deployment modes.

## 📁 Structure

```
loki/
├── install/                    # Installation methods
│   ├── docker/monolithic/     # Docker-based monolithic
│   ├── local/monolithic/      # Local binary installation
│   ├── k8s/microservices/     # Kubernetes microservices
│   ├── helm/simple-scalable/  # Helm simple-scalable
│   └── tanka/                 # Tanka deployments
├── configs/                    # Shared configurations
├── log-scrapers/              # Log collection tools
├── observability/             # Monitoring & metrics
├── storage/                   # Storage backends
├── scripts/                   # Operational scripts
├── docs/                      # Documentation
└── README.md                  # This file
```

## 🎯 Deployment Modes Comparison

| Mode | Use Case | Log Volume | Components | Scaling | Complexity |
|------|----------|------------|------------|---------|------------|
| **Monolithic** | Development, Testing | <100GB/day | All in one process | Vertical only | Low |
| **Simple Scalable** | Medium Production | 10GB-100GB/day | 3 services | Horizontal per group | Medium |
| **Microservices** | Large Production | >100GB/day | 8+ individual services | Full horizontal | High |

## 🚀 Quick Start

### Choose Your Deployment Mode

1. **Development/Testing** → Use `install/docker/monolithic/` or `install/local/monolithic/`
2. **Medium Production** → Use `install/helm/simple-scalable/`
3. **Large Production** → Use `install/k8s/microservices/`

### Version Selection

Each deployment mode supports:
- **v2.x** - Stable, production-ready
- **v3.x** - Latest features and improvements

## 📚 Documentation

### Deployment Modes
- [Loki Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
- [Monolithic Mode](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#monolithic-mode)
- [Simple Scalable Mode](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#simple-scalable)
- [Microservices Mode](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#microservices-mode)

### Configuration References
- [Loki 2.x Configuration](https://grafana.com/docs/loki/v2.9.x/configure/) - Complete configuration reference for v2.9.x
- [Loki 3.x Configuration](https://grafana.com/docs/loki/latest/configure/) - Latest configuration reference for v3.x

## 🔧 Configuration Targets

```yaml
# Monolithic
target: all

# Simple Scalable
target: read    # query-frontend, querier
target: write   # distributor, ingester
target: backend # compactor, ruler, index-gateway, query-scheduler

# Microservices
target: distributor
target: ingester
target: querier
# ... individual components
```