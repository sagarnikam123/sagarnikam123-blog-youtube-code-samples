# Fluent Bit - Helm - v5.x

## Versions
- **App version**: v5.0.1
- **Chart version**: ~0.57.x (latest)
- **Docs**: https://docs.fluentbit.io/manual

---

## Files

| File | Purpose |
|------|---------|
| `fluent-bit.yaml` | Fluent Bit pipeline config — edit this file for any config changes |
| `configmap.yaml` | Instructions to generate ConfigMap from `fluent-bit.yaml` |
| `values.yaml` | Helm values — image, volumes, resources, hot reload |

---

## Features

### 1. Multiline Parsing

Two layers handle logs that span multiple lines:

**Layer 1 — Built-in parsers (tail input)** — reassembles lines split by container runtime:
```yaml
multiline.parser: docker, cri
```
- `docker` — Docker JSON log lines split due to size limits
- `cri` — CRI-O/containerd partial log lines

**Layer 2 — Multiline filter** — reassembles application stack traces:
```yaml
- name: multiline
  multiline.key_content: log
  multiline.parser: java, python, go
```
- `java` — `Exception in thread...` + `at com.example...` lines
- `python` — `Traceback (most recent call last):` blocks
- `go` — `goroutine ... [running]:` panic blocks

> The multiline filter must be the **first filter** in the pipeline. It re-emits records to the head of the pipeline — placing other filters before it causes them to run twice.

### 2. Namespace Exclusions

Logs from system/infra namespaces are excluded at the **input level** via `exclude_path` — before any parsing or enrichment, saving CPU and memory.

**Excluded categories:**

| Category | Namespaces |
|----------|-----------|
| Kubernetes system | `kube-system`, `kube-public`, `kube-node-lease` |
| Dashboard | `kubernetes-dashboard` |
| Default | `default` |
| Monitoring | `monitoring`, `monitoring-testing`, `prometheus`, `datadog`, `cloudability`, `kubecost` |
| Networking | `ingress-nginx`, `nginx`, `nginx-external`, `cert-manager`, `external-dns` |
| Observability | `otel`, `otel-log`, `ot-operators`, `opentelemetry-operator-system`, `tracing` |
| Cloud | `amazon-cloudwatch`, `aws-observability` |
| Infrastructure | `karpenter`, `keda`, `castai-agent`, `castai-live` |
| Data | `argo`, `redis`, `kafka-lag-exporter`, `warpstream` |
| Utilities | `housekeeping` |

To add/remove exclusions, edit `exclude_path` in `fluent-bit.yaml`.

### 3. Long Line Handling

By default Fluent Bit drops lines exceeding `buffer_max_size`. This config accepts them:

```yaml
skip_long_lines: false    # accept instead of drop
buffer_chunk_size: 256k   # initial read buffer per file (default: 32k)
buffer_max_size: 512k     # lines up to 512KB accepted
```

- `buffer_chunk_size: 256k` → fewer `read()` syscalls → lower CPU
- To accept larger lines increase `buffer_max_size` (e.g. `1M`, `2M`) but monitor memory

### 4. Filesystem Buffering

When memory fills up, logs spill to disk instead of being dropped.

**How it works:**
1. Logs buffer in memory first (fast path)
2. When `mem_buf_limit` (20MB) is reached → new chunks go to filesystem only
3. When memory frees up → filesystem chunks load back to memory
4. If Loki is down → logs queue on disk up to `storage.total_limit_size` (10M)
5. No data loss unless disk quota is also exhausted

**Config summary:**

| Setting | Value | Purpose |
|---------|-------|---------|
| `storage.path` | `/var/log/flb-storage/` | Where chunks are stored on disk |
| `storage.sync` | `normal` | Balance between safety and performance |
| `storage.max_chunks_up` | `128` | Max chunks loaded in memory at once |
| `storage.backlog.mem_limit` | `10M` | Max memory for backlog chunks |
| `storage.type` | `filesystem` | Hybrid: memory + filesystem per input |
| `storage.pause_on_chunks_overlimit` | `off` | Don't pause input, spill to disk |
| `mem_buf_limit` | `20MB` | Memory limit before spilling |
| `storage.total_limit_size` | `10M` | Max disk queue per output |

**Required volume mounts** (already in `values.yaml`):
```yaml
- name: flb-storage
  hostPath:
    path: /var/log/flb-storage/
    type: DirectoryOrCreate
  mountPath: /var/log/flb-storage/
- name: flb-db
  hostPath:
    path: /var/log/flb_kube.db
    type: FileOrCreate
  mountPath: /var/log/flb_kube.db
```

### 5. Backpressure Handling

Backpressure occurs when logs are ingested faster than they can be flushed to Loki.

**Config levers:**

| Setting | Value | Effect |
|---------|-------|--------|
| `mem_buf_limit` | `20MB` | Memory limit per input before spilling to disk |
| `storage.type` | `filesystem` | Spill to disk instead of pausing/dropping |
| `storage.pause_on_chunks_overlimit` | `off` | Keep ingesting even when memory full |
| `storage.backlog.mem_limit` | `10M` | Max memory for backlog (disk→memory loading) |
| `storage.total_limit_size` | `10M` | Max disk queue per output |
| `retry_limit` | `3` | Retry failed Loki sends 3 times before dropping |
| `buffer_chunk_size` | `256k` | Larger chunks = fewer syscalls = less CPU |
| `threaded` | `true` | Run tail input in separate thread for better CPU utilization |

**What happens under backpressure:**
1. Memory fills up → input spills to filesystem (no pause, no drop)
2. Loki is down → output retries 3 times, then queues to disk (up to 10M)
3. Disk queue full → oldest chunks dropped (data loss only at this point)
4. Loki recovers → backlog drains from disk automatically

**Monitor backpressure:**
```bash
# Check storage metrics
curl http://localhost:2020/api/v1/storage

# Watch for pause/resume messages
kubectl logs -n fluent-bit -l app.kubernetes.io/name=fluent-bit | grep -E "paused|resume|overlimit"
```

### 6. Hot Reload

Hot reload allows config changes without restarting pods — no log gaps.

**Enabled in `fluent-bit.yaml`:**
```yaml
service:
  hot_reload: on
  http_server: on
  http_port: 2020
```

**Enabled in `values.yaml`:**
```yaml
hotReload:
  enabled: true   # deploys a sidecar that sends SIGHUP on ConfigMap change
```

See [Hot Reload](#hot-reload-1) under Operations for how to trigger it.

---

## Prerequisites
- Kubernetes cluster
- Helm 3.x
- kubectl configured
- Loki running at `loki-gateway.loki.svc.cluster.local` (port 80)

### RBAC

The Helm chart (`fluent/fluent-bit`) automatically creates all required RBAC resources:

| Resource | Name | Scope |
|----------|------|-------|
| ServiceAccount | `fluent-bit` | namespace: `fluent-bit` |
| ClusterRole | `fluent-bit` | cluster-wide |
| ClusterRoleBinding | `fluent-bit` | binds SA → ClusterRole |

**ClusterRole permissions granted:**

| API Group | Resources | Verbs | Why |
|-----------|-----------|-------|-----|
| `""` (core) | `namespaces`, `pods`, `pods/logs`, `nodes`, `nodes/proxy` | `get`, `list`, `watch` | Kubernetes filter enriches logs with pod/namespace/node metadata from across all namespaces |

> ClusterRole (not Role) is required because Fluent Bit runs as a DaemonSet and reads logs from pods across **all namespaces**.

---

## Install

```bash
# 1. Add Helm repo
helm repo add fluent https://fluent.github.io/helm-charts
helm repo update

# 2. Create namespace
kubectl create namespace fluent-bit

# 3. Apply ConfigMap from fluent-bit.yaml
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit

# 4. Install chart
helm install fluent-bit fluent/fluent-bit \
  -f values.yaml \
  -n fluent-bit
```

## Verify

```bash
helm status fluent-bit -n fluent-bit
kubectl get pods -n fluent-bit
kubectl logs -n fluent-bit -l app.kubernetes.io/name=fluent-bit
```

---

## Operations

### Update Config (without helm upgrade)

Edit `fluent-bit.yaml`, then apply and restart:
```bash
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart daemonset/fluent-bit -n fluent-bit
```

### Hot Reload

Reload config without restarting pods (requires `hot_reload: on` in `fluent-bit.yaml`).

#### Method 1 — HTTP API (recommended)
```bash
kubectl port-forward -n fluent-bit <pod-name> 2020:2020 &
curl -X POST -d '{}' http://localhost:2020/api/v2/reload

# Confirm reload count increased
curl http://localhost:2020/api/v2/reload
# returns: {"hot_reload_count": 1}
```

#### Method 2 — SIGHUP signal
```bash
kubectl exec -n fluent-bit <pod-name> -- kill -SIGHUP 1
```

#### Method 3 — Automatic via Helm sidecar
When `hotReload.enabled: true` in `values.yaml`, a sidecar watches the ConfigMap
and automatically sends SIGHUP when it changes — no manual step needed:
```bash
kubectl create configmap fluent-bit-config \
  --from-file=fluent-bit.yaml=fluent-bit.yaml \
  -n fluent-bit --dry-run=client -o yaml | kubectl apply -f -
# sidecar detects change and reloads automatically
```

**Verify reload:**
```bash
kubectl logs -n fluent-bit <pod-name> | grep -i reload
# [info] [reload] reloading configuration
# [info] [reload] configuration reloaded successfully
```

### Upgrade Helm Chart

```bash
helm repo update
helm search repo fluent/fluent-bit --versions   # check available versions
helm upgrade fluent-bit fluent/fluent-bit \
  -f values.yaml \
  -n fluent-bit
```

### Uninstall

```bash
helm uninstall fluent-bit -n fluent-bit
kubectl delete namespace fluent-bit
```

---

## Loki Output

Logs are shipped to Loki via the gateway at `loki-gateway.loki.svc.cluster.local:80`.

**Loki index labels sent by Fluent Bit:**

| Label | Value | Purpose |
|-------|-------|---------|
| `job` | `fluent-bit` | Identifies the collector |
| `namespace` | pod namespace | Log stream grouping |
| `container` | container name | Log stream grouping |
| `pod` | pod name | Log stream grouping |
| `pod_id` | pod UUID | Unique pod identification |
| `node` | node name | Node-level filtering |

**Test Loki connectivity from inside the cluster:**
```bash
kubectl exec -n loki loki-canary-clrnb -- \
  wget -q -O- http://loki-gateway.loki.svc.cluster.local/ready
# Expected: ready
```

**Query logs in Loki (LogQL):**
```logql
# All logs collected by fluent-bit
{job="fluent-bit"}

# By namespace
{namespace="fuzzy-train"}

# By pod
{pod=~"fuzzy-train.*"}

# Filter by log level (JSON logs)
{namespace="fuzzy-train"} | json | level="ERROR"

# By pod_id
{pod_id="1e22b803-1ccf-4269-8688-b904a00e95b9"}

# Log rate per second
rate({namespace="fuzzy-train"}[1m])
```

---

## References

- [Tail Input](https://docs.fluentbit.io/manual/data-pipeline/inputs/tail)
- [Multiline Parsing](https://docs.fluentbit.io/manual/data-pipeline/parsers/multiline-parsing)
- [Multiline Filter](https://docs.fluentbit.io/manual/data-pipeline/filters/multiline-stacktrace)
- [Kubernetes Filter](https://docs.fluentbit.io/manual/data-pipeline/filters/kubernetes)
- [Record Modifier Filter](https://docs.fluentbit.io/manual/data-pipeline/filters/record-modifier)
- [Grep Filter](https://docs.fluentbit.io/manual/data-pipeline/filters/grep)
- [Lua Filter](https://docs.fluentbit.io/manual/data-pipeline/filters/lua)
- [Buffering](https://docs.fluentbit.io/manual/data-pipeline/buffering)
- [Backpressure](https://docs.fluentbit.io/manual/administration/backpressure)
- [Hot Reload](https://docs.fluentbit.io/manual/administration/hot-reload)
- [Performance Tips](https://docs.fluentbit.io/manual/administration/performance)
- [Loki Output](https://docs.fluentbit.io/manual/data-pipeline/outputs/loki)
