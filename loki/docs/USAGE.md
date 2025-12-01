# Configuration Usage Guide

This guide explains which configuration files are used and how to select them.

## Loki Configurations

### Available Loki Configs:

**v2.x (Loki 2.x):**
- `loki-2.x-prod-local-storage.yaml` - Production with local filesystem storage
- `loki-2.x-prod-s3-memberlist.yaml` - Production with S3 storage and memberlist

**v3.x (Loki 3.x):**
- `loki-3.x-dev-local-storage.yaml` - Development with local filesystem storage (default)
- `loki-3.x-prod-s3-storage.yaml` - Production with S3 storage
- `loki-3.x-minimal-ui-only.yaml` - Minimal UI configuration

### Default Loki Configuration:

The install script sets **`loki-3.x-dev-local-storage.yaml`** as the default:

```bash
# Default startup
~/loki-stack/scripts/start-loki.sh

# Uses: ~/loki-stack/configs/loki.yaml -> loki-3.x-dev-local-storage.yaml
```

### Using Different Loki Configs:

```bash
# Use specific Loki configuration
~/loki-stack/scripts/start-loki.sh configs/loki-2.x-prod-local-storage.yaml
~/loki-stack/scripts/start-loki.sh configs/loki-3.x-prod-s3-storage.yaml
~/loki-stack/scripts/start-loki.sh configs/loki-3.x-minimal-ui-only.yaml

# Change default config
cd ~/loki-stack/configs
ln -sf loki-3.x-prod-s3-storage.yaml loki.yaml
```

## Fluent Bit Configurations

### Available Fluent Bit Configs:

Located in `~/loki-stack/log-scrapers/fluent-bit/`:

1. **`fluent-bit-tail-logs-with-filesystem-storage.yaml`**
   - Basic log tailing with filesystem buffering
   - **Use case**: Simple log collection with persistence

2. **`fluent-bit-tail-json-logs-to-loki.yaml`**
   - JSON log parsing and forwarding
   - **Use case**: Structured JSON log processing

3. **`fluent-bit-tail-logs-filesystem-buffering.conf`**
   - Production-ready with filesystem buffering
   - **Use case**: Production log collection with high reliability

4. **`fluent-bit-loki-canary-logs.conf`**
   - Loki Canary log collection
   - **Use case**: Monitoring Loki health with canary logs

### Using Fluent Bit Configs:

```bash
# Navigate to fluent-bit configs
cd ~/loki-stack/log-scrapers/fluent-bit/

# Start with specific config
fluent-bit --config fluent-bit-tail-json-logs-to-loki.yaml
fluent-bit --config fluent-bit-tail-logs-filesystem-buffering.conf
fluent-bit --config fluent-bit-loki-canary-logs.conf
```

## Configuration Selection Guide

### For Development:
```bash
# Loki: Use development config (default)
~/loki-stack/scripts/start-loki.sh

# Fluent Bit: Use basic JSON config
fluent-bit --config fluent-bit-tail-json-logs-to-loki.yaml
```

### For Production:
```bash
# Loki: Use production config
~/loki-stack/scripts/start-loki.sh configs/loki-2.x-prod-local-storage.yaml

# Fluent Bit: Use production config with buffering
fluent-bit --config fluent-bit-tail-logs-filesystem-buffering.conf
```

### For Testing/Monitoring:
```bash
# Loki: Use minimal config
~/loki-stack/scripts/start-loki.sh configs/loki-3.x-minimal-ui-only.yaml

# Fluent Bit: Use canary config
fluent-bit --config fluent-bit-loki-canary-logs.conf
```

## Configuration Customization

### Modify Paths in Configs:

Before using, update paths in configuration files:

**Fluent Bit configs:**
```yaml
# Update these paths to match your environment
path: /your/log/path/*.log
storage.path: /your/storage/path
db: /your/database/path
```

**Loki configs:**
```yaml
# Update storage paths
common:
  path_prefix: /your/loki/path
  storage:
    filesystem:
      chunks_directory: /your/chunks/path
```

## Quick Reference

| Use Case | Loki Config | Fluent Bit Config |
|----------|-------------|-------------------|
| **Development** | `loki-3.x-dev-local-storage.yaml` (default) | `fluent-bit-tail-json-logs-to-loki.yaml` |
| **Production** | `loki-2.x-prod-local-storage.yaml` | `fluent-bit-tail-logs-filesystem-buffering.conf` |
| **S3 Storage** | `loki-3.x-prod-s3-storage.yaml` | `fluent-bit-tail-logs-with-filesystem-storage.yaml` |
| **Monitoring** | `loki-3.x-minimal-ui-only.yaml` | `fluent-bit-loki-canary-logs.conf` |

## Configuration Locations

After installation:
```
~/loki-stack/
├── configs/                    # Loki configurations
│   ├── loki.yaml              # Default (symlink)
│   ├── loki-2.x-*.yaml       # Loki 2.x configs
│   └── loki-3.x-*.yaml       # Loki 3.x configs
├── scripts/                    # Start/Stop scripts
│   ├── start-loki.sh         # Start Loki
│   ├── start-grafana.sh      # Start Grafana
│   ├── start-prometheus.sh   # Start Prometheus
│   ├── start-minio.sh        # Start MinIO
│   └── stop-*.sh             # Stop scripts
└── log-scrapers/
    └── fluent-bit/            # Fluent Bit configurations
        ├── fluent-bit-*.yaml # YAML configs
        └── fluent-bit-*.conf # Conf format configs
```

#### Run Loki

##### Filesystem cleanup
rm -rf /tmp/loki
rm -rf $HOME/data/{loki,minio}
rm -rf $HOME/data/fluent-bit/{flb-storage,fluent_bit.log,fluent-bit-loki.db,fluent-bit-loki.db-shm,fluent-bit-loki.db-wal}
rm -rf $HOME/data/log/logger

mkdir -p /tmp/loki/{chunks,rules,compactor,wal,index,index_cache,bloom}
mkdir -p $HOME/data/{loki,minio}
mkdir -p $HOME/data/{fluent-bit/flb-storage,log/logger}
########################################################################################################################
# Loki
cd /Users/snikam/Documents/git/sagarnikam123-blog-youtube-code-samples/loki/monolithic/v3.x
loki-3.5.5 -config.file=loki-3.x-dev-local-storage.yaml -config.expand-env=true
