# VictoriaLogs PoC — Local Mac Setup

## Quick Start

```bash
# 1. Start the webhook receiver (separate terminal)
python3 webhook-receiver.py

# 2. Start the stack
docker-compose up -d

# 3. Verify everything is running
docker-compose ps
```

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **VictoriaLogs VMUI** | http://localhost:9428/select/vmui/ | Built-in log explorer (dev-friendly) |
| **Grafana** | http://localhost:3000 (admin/admin) | Dashboards + log exploration |
| **AlertManager** | http://localhost:9093 | View active alerts |
| **vmalert** | http://localhost:8880 | View rule evaluation status |
| **VictoriaMetrics** | http://localhost:8428/vmui/ | Query recording rule metrics |

## Testing the Flow

### 1. Check logs are being ingested

Open VMUI at http://localhost:9428/select/vmui/ and run:

```logsql
*
```

You should see JSON logs from flog/fuzzy-train.

### 2. Query by cluster/region

```logsql
{cluster="local-mac-poc", region="us-east-1"}
```

### 3. Search for errors

```logsql
{service="fuzzy-train"} error OR "status":5*
```

### 4. Check alert status

- vmalert UI: http://localhost:8880/vmalert/groups
- AlertManager: http://localhost:9093/#/alerts
- Webhook receiver terminal (should print alerts)

## Using fuzzy-train Instead of flog

If you want to use your [fuzzy-train](https://github.com/sagarnikam123/fuzzy-train) tool:

1. Clone it locally:
   ```bash
   git clone https://github.com/sagarnikam123/fuzzy-train.git
   cd fuzzy-train
   docker build -t fuzzy-train:local .
   ```

2. Update `docker-compose.yaml` — replace the `fuzzy-train` service:
   ```yaml
   fuzzy-train:
     image: fuzzy-train:local
     container_name: fuzzy-train
     volumes:
       - app-logs:/var/log/app
     restart: unless-stopped
   ```

3. Ensure fuzzy-train writes logs to `/var/log/app/app.log` (or adjust the Fluent Bit input path).

## Simulating Multiple EKS Clusters

To test multi-cluster separation, run additional Fluent Bit instances with different labels:

```bash
# Create a second fluent-bit config for "cluster-b"
cp config/fluentbit/fluent-bit.conf config/fluentbit/fluent-bit-cluster-b.conf
# Edit: Change cluster=local-mac-poc to cluster=eks-us-east-1-prod
# Edit: Change region=us-east-1 to region=eu-west-1

# Add to docker-compose.yaml or run standalone:
docker run --rm --network=poc_default \
  -v $(pwd)/config/fluentbit/fluent-bit-cluster-b.conf:/fluent-bit/etc/fluent-bit.conf \
  -v $(pwd)/config/fluentbit/parsers.conf:/fluent-bit/etc/parsers.conf \
  fluent/fluent-bit:latest
```

Then query in VMUI:
```logsql
{cluster="eks-us-east-1-prod"}
```

## Cleanup

```bash
docker-compose down -v  # -v removes volumes (deletes all stored logs)
```
