# Grafana - Helm - v12.x

## Versions
- **App version**: 12.3.1
- **Chart version**: 10.5.15
- **Docs**: https://grafana.com/docs/grafana/latest/

## Prerequisites
- Kubernetes cluster
- Helm 3.x
- kubectl configured
- Loki running at `loki-gateway.loki.svc.cluster.local` (port 80)

## Add Helm Repo

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

## Search Chart Versions

```bash
helm search repo grafana/grafana --versions
```

## Install

```bash
helm install grafana grafana/grafana \
  -f values.yaml \
  -n grafana --create-namespace
```

## Access Grafana

### 1. Port-forward Grafana service

```bash
kubectl port-forward -n grafana svc/grafana 3000:80 &
```

#### Troubleshooting: port 3000 already in use

If you see this error:
```
E socat[xxxx] E connect(5, AF=2 127.0.0.1:3000, 16): Connection refused
error: lost connection to pod
```

It means a previous port-forward is still holding port 3000. Fix it:

```bash
# Option 1 — Kill the stale process on port 3000 and retry
lsof -ti:3000 | xargs kill -9 2>/dev/null
kubectl port-forward -n grafana svc/grafana 3000:80 &
```

```bash
# Option 2 — Use a different local port (no kill needed)
kubectl port-forward -n grafana svc/grafana 3001:80 &
# Then open http://localhost:3001 instead
```

### 2. Get admin password

```bash
kubectl get secret -n grafana grafana -o jsonpath="{.data.admin-password}" | base64 --decode; echo
```

### 3. Open in browser

```
http://localhost:3000
```

### 4. Login
- **Username**: `admin`
- **Password**: output from step 2 above

## Loki Datasource

Loki runs in the `loki` namespace. Grafana accesses it via Kubernetes cluster DNS.
The URL format is: `http://<service-name>.<namespace>.svc.cluster.local:<port>`

### URL by environment

| Environment | Loki URL |
|-------------|----------|
| Minikube | `http://loki-gateway.loki.svc.cluster.local` |
| EKS (same cluster) | `http://loki-gateway.loki.svc.cluster.local` |
| EKS (cross-cluster) | `http://<loki-gateway-loadbalancer-dns>` |

> Cluster DNS (`svc.cluster.local`) works as long as Grafana and Loki are in the **same cluster**, regardless of namespace. Namespace isolation does not block service-to-service communication by default.

### Option A — Pre-configured via values.yaml (recommended)

Loki datasource is already defined in `values.yaml` under `datasources:` and is automatically provisioned on install. No manual steps needed.

To verify after login:
1. Go to **Connections → Data sources**
2. Confirm `Loki` is listed with URL `http://loki-gateway.loki.svc.cluster.local`
3. Click **Save & test** → should show `Data source connected and labels found`

### Option B — Add manually via Grafana UI

1. Login to Grafana at http://localhost:3000
2. Go to **Connections → Data sources → Add new data source**
3. Search and select **Loki**
4. Set the URL based on your environment:

   **Minikube / EKS (same cluster):**
   ```
   http://loki-gateway.loki.svc.cluster.local
   ```

   **EKS (Loki exposed via LoadBalancer):**
   ```bash
   # Get the external DNS of loki-gateway
   kubectl get svc -n loki loki-gateway
   # Use EXTERNAL-IP or hostname as the URL
   ```

5. Click **Save & test**

### Option C — Add via Helm values (declarative)

Edit `values.yaml` and update the datasource URL if needed:

```yaml
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
      - name: Loki
        type: loki
        access: proxy
        url: http://loki-gateway.loki.svc.cluster.local  # same cluster (minikube/EKS)
        isDefault: true
        jsonData:
          maxLines: 1000
```

Then upgrade:
```bash
helm upgrade grafana grafana/grafana \
  -f values.yaml \
  -n grafana
```

### Verify Loki connectivity from inside the cluster

```bash
# Exec into Grafana pod and test Loki gateway
kubectl exec -n grafana deploy/grafana -- \
  wget -q -O- http://loki-gateway.loki.svc.cluster.local/ready
```

Expected output: `ready`

## Query Fluent Bit Logs in Grafana

1. Go to **Explore** (compass icon in left sidebar)
2. Select `Loki` datasource
3. Use **Label filters** or switch to **Code** mode and run LogQL:

```logql
# All logs from fluent-bit
{job="fluent-bit"}

# Logs from a specific namespace
{namespace="kube-system"}

# Logs from a specific pod
{pod=~"fluent-bit.*"}

# Filter by log level
{namespace="loki"} |= "error"

# Logs from all namespaces with container label
{job="fluent-bit", namespace="cert-manager"}
```

4. Set time range (top right) to **Last 15 minutes** or **Last 1 hour**
5. Click **Run query**

## Upgrade

```bash
helm repo update

helm upgrade grafana grafana/grafana \
  -f values.yaml \
  -n grafana
```

## Uninstall

```bash
helm uninstall grafana -n grafana
kubectl delete namespace grafana
```

## Verify

```bash
helm status grafana -n grafana
kubectl get pods -n grafana
kubectl logs -n grafana -l app.kubernetes.io/name=grafana
```
