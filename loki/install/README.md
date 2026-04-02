# Loki Installation Methods

Choose an installation method based on your environment and requirements.

## Methods

| Method | Best For | Complexity | Production Ready |
|--------|----------|------------|------------------|
| [Helm](helm/) | Most Kubernetes clusters | Medium | ✅ Yes |
| [Operator](operator/) | OpenShift, GitOps workflows | High | ✅ Yes |
| [Local](local/) | Development, learning | Low | ❌ No |
| [Docker](docker/) | Quick testing | Low | ❌ No |
| [Tanka](tanka/) | Jsonnet-based deployments | High | ✅ Yes |
| [K8s](k8s/) | Raw Kubernetes manifests | Medium | ⚠️ Manual |

## When to Use What

### Development & Learning

| Method | When to Use |
|--------|-------------|
| **Local** | Learning Loki basics, testing configs locally |
| **Docker** | Quick experiments, CI pipelines |
| **Helm (Single Binary)** | Learning Kubernetes deployment, Minikube/Docker Desktop |

### Production

| Method | When to Use |
|--------|-------------|
| **Helm** | EKS, GKE, AKS, vanilla K8s - most flexible, widely adopted |
| **Operator** | OpenShift environments, teams using OLM/operator patterns |
| **Tanka** | Teams already using Jsonnet, Grafana Labs' internal tooling |

### Helm vs Operator (Production)

| Factor | Helm | Operator |
|--------|------|----------|
| Version control | Full - you choose exact version | Limited - operator decides |
| Flexibility | High | Opinionated |
| Community support | Large, more examples | Smaller, OpenShift-focused |
| Upgrade control | Manual, predictable | Automated |
| Best for | EKS/GKE/AKS/vanilla K8s | OpenShift, GitOps |

**Recommendation:** Use **Helm** for most production Kubernetes clusters.

## Quick Decision Guide

```
Development/Learning?
  ├── Local machine → local/ or docker/
  └── Kubernetes (Minikube) → helm/ (single-binary)

Production?
  ├── OpenShift → operator/
  ├── EKS/GKE/AKS/vanilla K8s → helm/ (recommended)
  ├── Using Jsonnet/Tanka → tanka/
  └── Need raw manifests → k8s/
```

## Deployment Modes

All Kubernetes methods support these deployment modes:

| Mode | Scale | Use Case |
|------|-------|----------|
| Single Binary | <100GB/day | Dev/test |
| Simple Scalable | 100GB-1TB/day | Medium production |
| Distributed | >1TB/day | Large production |

## Getting Started

### Helm (Recommended for K8s)

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki -n loki --create-namespace \
  -f helm/v3.6.x/single-binary/values-base.yaml \
  -f helm/v3.6.x/single-binary/values-minikube.yaml
```

### Operator (OpenShift/GitOps)

```bash
# Install operator, then apply LokiStack CR
kubectl apply -f operator/lokistack/lokistack-demo.yaml
```

### Local

```bash
./local/install.sh
```

## Checking for Config Changes Between Versions

When upgrading Loki, it's important to check for configuration changes between versions. You can use Docker to compare the full configuration output between two versions.

For more details, see the [official Grafana documentation on checking for config changes](https://grafana.com/docs/loki/latest/setup/upgrade/#checking-for-config-changes).

### Comparing Loki 3.6.8 with 3.7.1

**Prerequisites:**
- Docker installed and running
- Your Loki config file in the current directory

**Step 1: Set version variables and config file**

```bash
export OLD_LOKI=3.6.8
export NEW_LOKI=3.7.1
export CONFIG_FILE=your-loki-config.yaml  # Replace with your actual config filename
```

**Step 2: Run the comparison**

```bash
diff --color=always --side-by-side \
  <(docker run --rm -t -v "${PWD}":/config grafana/loki:${OLD_LOKI} \
    -config.file=/etc/loki/${CONFIG_FILE} -print-config-stderr 2>&1 | \
    sed '/Starting Loki/q' | tr -d '\r') \
  <(docker run --rm -t -v "${PWD}":/config grafana/loki:${NEW_LOKI} \
    -config.file=/etc/loki/${CONFIG_FILE} -print-config-stderr 2>&1 | \
    sed '/Starting Loki/q' | tr -d '\r') | less -R
```

### Understanding the Command

- `OLD_LOKI` and `NEW_LOKI`: Specify the versions to compare (e.g., 3.6.8 vs 3.7.1)
- `CONFIG_FILE`: Your Loki configuration file (must exist in current directory)
- `-v "${PWD}":/config`: Mounts current directory to /config in container
- `-config.file=/etc/loki/${CONFIG_FILE}`: Path to config inside container
- `-print-config-stderr`: Prints the entire internal config struct used by Loki
- `sed '/Starting Loki/q'`: Stops output before Loki starts
- `tr -d '\r'`: Removes Windows newline characters (useful for WSL2 users)
- `--side-by-side`: Shows differences side-by-side for easier comparison
- `less -R`: Allows scrolling through the output with color support

### Troubleshooting

**No output or "----" only:**
- Ensure your config file exists in the current directory
- Check that `CONFIG_FILE` variable matches your actual filename
- Verify Docker is running: `docker ps`

**Config file not found error:**
- Make sure you're in the directory containing the config file
- The file will be mounted from your current directory to the container

**No differences shown:**
- This is normal if your config produces identical runtime configurations
- The versions might have no breaking changes affecting your specific config

### Notes

- The output is very verbose as it shows the entire internal config struct (1000+ lines)
- This comparison helps identify deprecated configs, new defaults, and breaking changes
- Always review the [official upgrade guide](https://grafana.com/docs/loki/latest/setup/upgrade/) before upgrading
- If no differences appear, your config is likely compatible with both versions

## Resources

- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Loki Upgrade Guide](https://grafana.com/docs/loki/latest/setup/upgrade/)
- [Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
- [Loki Operator](https://loki-operator.dev/)
