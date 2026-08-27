# Pixie Requirements

Source: https://docs.px.dev/installing-pixie/requirements/

Content rephrased for compliance with licensing restrictions.

## Kubernetes

- Version: v1.21+
- Uses Operator Lifecycle Manager (OLM) for Vizier operator management
- Requires PersistentVolume support

### Production environments

| K8s Environment | Support |
|:----------------|:--------|
| AKS | Supported |
| EKS | Supported (incl. Bottlerocket AMIs) |
| EKS Fargate | Not supported (no eBPF) |
| GKE | Supported |
| GKE Autopilot | Not supported (no eBPF) |
| OKE | Supported |
| OpenShift | Supported |
| kOps | Supported |
| Self-hosted | Supported (requires Linux kernel v4.14+) |

### Local development environments

Recommended: minikube with VM driver (kvm2 on Linux, hyperkit on Mac).
Container-based K8s environments are NOT supported.

| K8s Environment | Support |
|:----------------|:--------|
| Docker Desktop | Not supported |
| Rancher Desktop (containerd) | Supported |
| Rancher Desktop (dockerd) | Not supported |
| k0s | Supported |
| k3s | Supported |
| k3d | Not supported (runs inside Docker) |
| kind | Not supported (runs inside Docker) |
| minikube (kvm2) | Supported |
| minikube (hyperkit) | Supported |
| minikube (docker) | Not supported |
| minikube (none) | Not supported |

## Operating System

- Linux only (v4.14+ kernel)
- Windows not supported, not in roadmap
- Pixie can be configured to deploy to a subset of nodes

### Linux distributions

| Distribution | Version |
|:-------------|:--------|
| CentOS | 7.3+ |
| Debian | 10+ |
| RHEL | 8+ |
| Ubuntu | 18.04+ |

## CPU

| Architecture | Support |
|:-------------|:--------|
| x86-64 | Supported |
| ARM | Supported |

## Memory

- Minimum: 1 GiB per node
- Recommendation: PEM memory should not exceed 25% of node total
- Default PEM memory limit: 2 GiB (DaemonSet)
- Lowest recommended PEM limit: 1 GiB
- See [Tuning Memory Usage](https://docs.px.dev/reference/admin/tuning-mem-usage/) for configuration

## Network

- Outgoing HTTPS/2 on port 443 to Pixie Cloud
- Telemetry flows through Cloud via reverse proxy (encrypted, no persistence)
- End-to-end encryption for data in flight

## Pod Security

- `vizier-pem-*` pods require **privileged** access
- Needed to install BPF programs for telemetry collection
