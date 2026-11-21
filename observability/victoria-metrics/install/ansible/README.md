# VictoriaMetrics — Ansible Roles

VictoriaMetrics publishes official Ansible roles for automating deployment of all components on bare-metal servers and VMs.

## Available roles

| Role | Purpose |
|:-----|:--------|
| `victoriametrics.cluster.vmauth` | vmauth proxy |
| `victoriametrics.cluster.vminsert` | vminsert ingestion |
| `victoriametrics.cluster.vmselect` | vmselect query |
| `victoriametrics.cluster.vmstorage` | vmstorage data |
| `victoriametrics.single` | Single-node VictoriaMetrics |
| `victoriametrics.vmagent` | vmagent metrics collector |
| `victoriametrics.vmalert` | vmalert alerting |

## Install roles

```bash
ansible-galaxy collection install victoriametrics.cluster
```

## Notes

- Roles are published on Ansible Galaxy under the `victoriametrics` namespace.
- Use for bare-metal/VM deployments where Kubernetes is not available.
- For Kubernetes, use the [Helm charts](../helm/) or [Operator](../operator/).

Official source: [VictoriaMetrics Quick Start](https://docs.victoriametrics.com/victoriametrics/quick-start/) mentions Ansible Roles as an installation method.
