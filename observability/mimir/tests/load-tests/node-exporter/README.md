# Node Exporter - System Metrics Generator

Prometheus exporter for hardware and OS metrics - generates realistic system metrics for testing.

## Installation

### Kubernetes
```bash
kubectl apply -f kubernetes/node-exporter-daemonset.yaml -n mimir-test
```

### Docker
```bash
docker run -d --name node-exporter \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  quay.io/prometheus/node-exporter:latest \
  --path.rootfs=/host
```

### Binary
```bash
# Download
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-*.tar.gz
cd node_exporter-*/

# Run
./node_exporter
```

## Metrics Exposed

Node Exporter provides 100+ metrics including:

| Category | Metrics | Examples |
|----------|---------|----------|
| **CPU** | Usage, frequency, temperature | `node_cpu_seconds_total` |
| **Memory** | RAM, swap, buffers | `node_memory_MemAvailable_bytes` |
| **Disk** | I/O, space, inodes | `node_disk_io_time_seconds_total` |
| **Network** | Traffic, errors, drops | `node_network_receive_bytes_total` |
| **Filesystem** | Mount points, usage | `node_filesystem_avail_bytes` |
| **Load** | System load averages | `node_load1`, `node_load5`, `node_load15` |

## Scrape Configuration

### Prometheus Config
```yaml
scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
```

### Grafana Alloy Config
```river
prometheus.scrape "node_exporter" {
  targets = [
    {"__address__" = "node-exporter:9100"},
  ]
  forward_to = [prometheus.remote_write.mimir.receiver]
}

prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir-gateway/api/v1/push"
    headers = {
      "X-Scope-OrgID" = "demo",
    }
  }
}
```

## Load Testing with Multiple Instances

### Deploy Multiple Node Exporters
```bash
# Deploy 10 node-exporter instances
for i in {1..10}; do
  docker run -d --name node-exporter-$i \
    -p $((9100+i)):9100 \
    quay.io/prometheus/node-exporter:latest
done
```

### Kubernetes DaemonSet
Automatically deploys one pod per node:
```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: quay.io/prometheus/node-exporter:latest
        args:
          - --path.rootfs=/host
        ports:
        - containerPort: 9100
        volumeMounts:
        - name: root
          mountPath: /host
          readOnly: true
      volumes:
      - name: root
        hostPath:
          path: /
```

## Useful Queries

```promql
# CPU usage per core
rate(node_cpu_seconds_total{mode!="idle"}[5m])

# Memory usage percentage
100 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100)

# Disk I/O rate
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])

# Network traffic
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Filesystem usage
100 - (node_filesystem_avail_bytes / node_filesystem_size_bytes * 100)

# System load
node_load1
node_load5
node_load15
```

## Load Testing Scenarios

### Scenario 1: Basic Load (10 nodes)
```bash
# Deploy 10 node-exporters
docker-compose -f docker-compose-10-nodes.yaml up -d

# Scrape every 15s
# Expected: ~1000 samples/sec
```

### Scenario 2: High Cardinality (100 nodes)
```bash
# Deploy 100 node-exporters
for i in {1..100}; do
  docker run -d --name node-exporter-$i \
    quay.io/prometheus/node-exporter:latest
done

# Expected: ~10,000 samples/sec
```

### Scenario 3: Realistic Production
```bash
# DaemonSet on 50-node cluster
kubectl apply -f kubernetes/node-exporter-daemonset.yaml

# Expected: ~5,000 samples/sec
```

## Monitoring Node Exporter

```bash
# Check metrics endpoint
curl http://localhost:9100/metrics

# Count metrics
curl -s http://localhost:9100/metrics | grep -c "^node_"

# Check specific metric
curl -s http://localhost:9100/metrics | grep node_cpu_seconds_total
```

## Resources

- [Node Exporter Documentation](https://github.com/prometheus/node_exporter)
- [Available Collectors](https://github.com/prometheus/node_exporter#collectors)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/1860)
