# Pixie installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| CLI (recommended) | Available | [`cli/`](cli/) | Fastest install via `px` CLI |
| Helm | Available | [`helm/`](helm/) | Operator-managed via Helm chart |
| YAML | Available | [`yaml/`](yaml/) | Extract manifests, apply with kubectl |
| Minikube (local dev) | Available | [`minikube/`](minikube/) | Local cluster setup with hyperkit/kvm2 |

## Requirements

- Kubernetes v1.21+
- Linux kernel v4.14+ (eBPF required)
- x86-64 or ARM architecture
- 1 GiB minimum memory per node (2 GiB recommended per PEM)
- Privileged pod access (BPF programs)
- PersistentVolume support

## Supported environments

| Environment | Support |
|:------------|:--------|
| EKS | Supported (incl. Bottlerocket) |
| AKS | Supported |
| GKE | Supported |
| OKE | Supported |
| OpenShift | Supported |
| kOps | Supported |
| Self-hosted | Supported (kernel v4.14+) |
| minikube (kvm2/hyperkit) | Supported |
| k0s / k3s | Supported |
| Rancher Desktop (containerd) | Supported |

### Not supported

- EKS Fargate, GKE Autopilot (no eBPF)
- Docker Desktop, kind, k3d (container-based "nodes")
- minikube with docker/none driver

Official docs: https://docs.px.dev/installing-pixie/
