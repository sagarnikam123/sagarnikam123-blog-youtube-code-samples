# VictoriaMetrics — binary cluster (systemd)

VictoriaMetrics cluster consists of three components running on separate or colocated hosts:
- **vmstorage** — stores time-series data
- **vminsert** — accepts ingested data and distributes it across vmstorage nodes
- **vmselect** — executes queries across all vmstorage nodes

## Install

Download the cluster archive (contains `vmstorage-prod`, `vminsert-prod`, `vmselect-prod`):

```bash
VERSION=1.150.0
wget "https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v${VERSION}/victoria-metrics-linux-amd64-v${VERSION}-cluster.tar.gz"
sudo tar -xvf victoria-metrics-linux-amd64-v${VERSION}-cluster.tar.gz -C /usr/local/bin
sudo useradd -s /usr/sbin/nologin victoriametrics
```

## systemd services

Create a service for each component. Key ports:
- vmstorage: `:8400` (vminsert), `:8401` (vmselect), `:8482` (HTTP)
- vminsert: `:8480` (HTTP)
- vmselect: `:8481` (HTTP)

Set `-storageNode=<vmstorage1>,<vmstorage2>,...` on vminsert and vmselect.

See the full systemd unit examples in the [VictoriaMetrics Quick Start](https://docs.victoriametrics.com/victoriametrics/quick-start/#starting-victoriametrics-cluster-from-binaries).

## Notes

- Run components in the same private network for security.
- For horizontal scaling, add more vmstorage nodes and update `-storageNode` lists.
- For Kubernetes cluster deployments, use the [Helm cluster chart](../../helm/cluster/) or [Operator](../../operator/cluster/).

Official guide: [VictoriaMetrics Quick Start — Cluster from Binaries](https://docs.victoriametrics.com/victoriametrics/quick-start/#starting-victoriametrics-cluster-from-binaries).
