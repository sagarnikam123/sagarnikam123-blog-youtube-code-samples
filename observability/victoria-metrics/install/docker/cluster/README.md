# VictoriaMetrics — Docker cluster

Run a VictoriaMetrics cluster (vmstorage + vminsert + vmselect + vmagent + Grafana) using the official Docker Compose from the VictoriaMetrics repository.

## Run

```bash
git clone https://github.com/VictoriaMetrics/VictoriaMetrics.git
cd VictoriaMetrics
make docker-vm-cluster-up
```

Access:
- Grafana: <http://localhost:3000> (admin/admin)
- vmui: <http://localhost:8427/select/0/vmui>

## Stop

```bash
make docker-vm-cluster-down
```

## Notes

- Starts vmstorage, vminsert, vmselect, vmagent, and Grafana.
- Customization via `deployment/docker/compose-vm-cluster.yml`.
- For Kubernetes cluster deployments, use the [Helm cluster chart](../../helm/cluster/) or [Operator](../../operator/cluster/).

Official guide: [VictoriaMetrics Quick Start — Cluster via Docker](https://docs.victoriametrics.com/victoriametrics/quick-start/#starting-victoriametrics-cluster-via-docker).
