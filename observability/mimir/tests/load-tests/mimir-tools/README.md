# Mimir Tools - Official Binaries

All official tools shipped with Mimir for operations, testing, and debugging.

## Tools Overview

| Tool | Purpose | Use Case |
|------|---------|----------|
| **mimir** | Main Mimir binary | Run Mimir components |
| **mimirtool** | CLI for operations | Rules, alertmanager, load testing |
| **query-tee** | Query comparison | Compare query results between systems |
| **metaconvert** | Metadata conversion | Convert Thanos/Cortex metadata to Mimir |
| **mark-blocks** | Block marking | Mark blocks for deletion/no-compact |

## Quick Links

- [mimirtool.md](./mimirtool.md) - Complete mimirtool documentation
- Sections below cover other utilities

---

## 1. mimir (Main Binary)

Run any Mimir component:

```bash
# Run all-in-one (monolithic)
./mimir -config.file=mimir.yaml -target=all

# Run specific component
./mimir -config.file=mimir.yaml -target=ingester
./mimir -config.file=mimir.yaml -target=distributor
./mimir -config.file=mimir.yaml -target=querier

# List available targets
./mimir -help | grep target
```

## 2. mimirtool (CLI Tool)

See [mimirtool.md](./mimirtool.md) for complete documentation.

**Quick reference:**
```bash
# Rules management
mimirtool rules list
mimirtool rules load rules.yaml

# Alertmanager
mimirtool alertmanager get
mimirtool alertmanager load config.yaml

# Load testing
mimirtool analyze grafana --address=http://localhost:8080
```

## 3. query-tee

Compare query results between two Prometheus/Mimir instances.

### Use Cases
- **Migration validation**: Compare old vs new Mimir cluster
- **Version upgrades**: Verify query compatibility
- **A/B testing**: Compare different configurations

### Basic Usage

```bash
# Compare two Mimir instances
./query-tee \
  -backend.endpoints=http://mimir-old:8080 \
  -backend.endpoints=http://mimir-new:8080 \
  -server.http-listen-port=9900
```

### Configuration

```yaml
# query-tee.yaml
server:
  http_listen_port: 9900

backend:
  endpoints:
    - http://mimir-old:8080
    - http://mimir-new:8080

  # Preferred backend (used for responses)
  preferred: 0

  # Compare results
  compare_responses: true

  # Log differences
  log_slow_query_response_threshold: 1s
```

### Run with Config

```bash
./query-tee -config.file=query-tee.yaml
```

### Send Queries Through Tee

```bash
# Query through tee (port 9900)
curl "http://localhost:9900/prometheus/api/v1/query?query=up" \
  -H "X-Scope-OrgID: demo"

# Tee compares results from both backends
# Returns response from preferred backend
# Logs any differences
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: query-tee
spec:
  replicas: 1
  selector:
    matchLabels:
      app: query-tee
  template:
    metadata:
      labels:
        app: query-tee
    spec:
      containers:
      - name: query-tee
        image: grafana/mimir:latest
        command: ["/bin/query-tee"]
        args:
          - -backend.endpoints=http://mimir-old:8080
          - -backend.endpoints=http://mimir-new:8080
          - -server.http-listen-port=9900
        ports:
        - containerPort: 9900
```

## 4. metaconvert

Convert block metadata from Thanos/Cortex format to Mimir format.

### Use Cases
- **Migration from Thanos**: Convert Thanos blocks to Mimir
- **Migration from Cortex**: Convert Cortex blocks to Mimir
- **Block format updates**: Update metadata format

### Basic Usage

```bash
# Convert single block
./metaconvert \
  -tenant-id=demo \
  -block-id=01ABCDEF123456789 \
  /path/to/blocks

# Convert all blocks for tenant
./metaconvert \
  -tenant-id=demo \
  /path/to/blocks

# Dry run (don't modify)
./metaconvert \
  -tenant-id=demo \
  -dry-run \
  /path/to/blocks
```

### S3 Bucket Conversion

```bash
# Convert blocks in S3
./metaconvert \
  -backend=s3 \
  -s3.endpoint=s3.amazonaws.com \
  -s3.bucket-name=mimir-blocks \
  -s3.access-key-id=$AWS_ACCESS_KEY_ID \
  -s3.secret-access-key=$AWS_SECRET_ACCESS_KEY \
  -tenant-id=demo
```

### Migration Workflow

```bash
# 1. Backup blocks
aws s3 sync s3://old-bucket s3://backup-bucket

# 2. Dry run conversion
./metaconvert -dry-run -tenant-id=demo /path/to/blocks

# 3. Convert blocks
./metaconvert -tenant-id=demo /path/to/blocks

# 4. Verify conversion
ls -la /path/to/blocks/demo/
```

## 5. mark-blocks

Mark blocks for deletion or no-compaction.

### Use Cases
- **Block deletion**: Mark corrupted blocks for deletion
- **Skip compaction**: Prevent specific blocks from compaction
- **Troubleshooting**: Isolate problematic blocks

### Mark for Deletion

```bash
# Mark single block for deletion
./mark-blocks \
  -tenant-id=demo \
  -block-id=01ABCDEF123456789 \
  -details="Corrupted block" \
  -mark=deletion \
  /path/to/blocks

# Mark multiple blocks
./mark-blocks \
  -tenant-id=demo \
  -block-id=01ABCDEF123456789,01GHIJKL987654321 \
  -mark=deletion \
  /path/to/blocks
```

### Mark for No-Compact

```bash
# Prevent block from compaction
./mark-blocks \
  -tenant-id=demo \
  -block-id=01ABCDEF123456789 \
  -mark=no-compact \
  -details="Testing block" \
  /path/to/blocks
```

### S3 Bucket Operations

```bash
# Mark blocks in S3
./mark-blocks \
  -backend=s3 \
  -s3.endpoint=s3.amazonaws.com \
  -s3.bucket-name=mimir-blocks \
  -tenant-id=demo \
  -block-id=01ABCDEF123456789 \
  -mark=deletion
```

### List Marked Blocks

```bash
# Find deletion markers
find /path/to/blocks/demo/ -name "deletion-mark.json"

# Find no-compact markers
find /path/to/blocks/demo/ -name "no-compact-mark.json"

# View marker content
cat /path/to/blocks/demo/01ABCDEF123456789/deletion-mark.json
```

## Testing Workflows

### Migration Testing with query-tee

```bash
# 1. Deploy query-tee between old and new clusters
./query-tee \
  -backend.endpoints=http://old-mimir:8080 \
  -backend.endpoints=http://new-mimir:8080 \
  -backend.compare-responses=true

# 2. Route production queries through tee
# Update clients to point to query-tee:9900

# 3. Monitor logs for differences
tail -f query-tee.log | grep "response mismatch"

# 4. Investigate differences
# Fix issues in new cluster

# 5. Switch to new cluster
# Update clients to point directly to new-mimir:8080
```

### Block Cleanup Workflow

```bash
# 1. Identify problematic blocks
# Check compactor logs or use mimirtool

# 2. Mark for deletion
./mark-blocks \
  -tenant-id=demo \
  -block-id=<block-id> \
  -mark=deletion \
  -details="Corrupted data"

# 3. Compactor will delete marked blocks
# Check compactor logs for deletion
```

## Resources

- [Mimir Documentation](https://grafana.com/docs/mimir/latest/)
- [Migration Guide](https://grafana.com/docs/mimir/latest/migration-guide/)
- [Block Format](https://grafana.com/docs/mimir/latest/references/architecture/binary-index-header/)
