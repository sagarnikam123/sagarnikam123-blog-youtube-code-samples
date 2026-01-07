# Loki Configuration Files

Centralized Loki configuration files for all deployment methods.

## Structure

```
configs/
├── reference/              # Official docs config snippets (read-only)
│   ├── server.yaml
│   ├── ingester.yaml
│   ├── limits_config.yaml
│   └── ...
├── v3.x/
│   ├── v3.6.x/            # Current version
│   │   ├── loki-3.6.x-local-filesystem.yaml
│   │   ├── loki-3.6.x-docker-filesystem.yaml
│   │   ├── loki-3.6.x-k8s-exported.yaml
│   │   ├── loki-3.6.x-minimal-official-github.yaml
│   │   ├── loki-3.6.x-minimal-ui-only.yaml
│   │   ├── loki-3.6.x-ui-filesystem-inmemory.yaml
│   │   ├── loki-3.6.x-ui-minio-memberlist.yaml
│   │   └── loki-3.6.x-ui-minio-thanos-memberlist.yaml
│   └── v3.5.x/            # Previous version
│       └── ...
└── v2.x/                  # Legacy
    └── v2.9.x/
```

## Current Version (v3.6.x)

### Basic Configs

| Config | Use Case | Storage | Ring |
|--------|----------|---------|------|
| `loki-3.6.x-local-filesystem.yaml` | Local binary | `/tmp/loki` filesystem | inmemory |
| `loki-3.6.x-docker-filesystem.yaml` | Docker container | `/loki` filesystem | inmemory |
| `loki-3.6.x-k8s-exported.yaml` | Reference (full K8s config) | `/var/loki` | memberlist |

### Minimal Configs

| Config | Use Case | Storage | Ring |
|--------|----------|---------|------|
| `loki-3.6.x-minimal-official-github.yaml` | Official minimal example | `/tmp/loki` filesystem | inmemory |
| `loki-3.6.x-minimal-ui-only.yaml` | Minimal with UI enabled | `/tmp/loki` filesystem | inmemory |

### Feature Configs

| Config | Use Case | Storage | Ring |
|--------|----------|---------|------|
| `loki-3.6.x-ui-filesystem-inmemory.yaml` | UI + filesystem + caching | `/tmp/loki` filesystem | inmemory |
| `loki-3.6.x-ui-minio-memberlist.yaml` | UI + MinIO S3 + clustering | MinIO S3 | memberlist |
| `loki-3.6.x-ui-minio-thanos-memberlist.yaml` | UI + MinIO (Thanos objstore) | MinIO S3 (Thanos) | memberlist |

### Config Comparison

| Feature | minimal | ui-only | filesystem-inmemory | minio-memberlist | minio-thanos |
|---------|---------|---------|---------------------|------------------|--------------|
| UI | ❌ | ✅ | ✅ | ✅ | ✅ |
| Caching | ❌ | ❌ | ✅ | ✅ | ✅ |
| S3/MinIO | ❌ | ❌ | ❌ | ✅ | ✅ |
| Memberlist | ❌ | ❌ | ❌ | ✅ | ✅ |
| Thanos objstore | ❌ | ❌ | ❌ | ❌ | ✅ |

## Usage

### With Binary

```bash
loki -config.file=configs/v3.x/v3.6.x/loki-local-filesystem.yaml
```

### With Docker

```bash
docker run -d --name loki \
  -p 3100:3100 \
  -v $(pwd)/configs/v3.x/v3.6.x/loki-local-filesystem.yaml:/etc/loki/config.yaml:ro \
  -v loki-data:/loki \
  grafana/loki:3.6.3 \
  -config.file=/etc/loki/config.yaml
```

### With Docker Compose

See `install/local/docker-compose.yaml` or `install/docker/monolithic/docker-compose.yml`

### With Helm

Helm uses values files in `install/helm/v3.6.x/` which generate configs at deploy time.

## Reference Configs

The `reference/` directory contains config snippets from official Grafana docs.
Use these as reference when customizing your config.

## Official Documentation

- [Loki Configuration](https://grafana.com/docs/loki/latest/configure/)
- [Configuration Examples](https://grafana.com/docs/loki/latest/configure/examples/)
