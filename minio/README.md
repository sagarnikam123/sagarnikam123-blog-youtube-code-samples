# MinIO

S3-compatible object store — used as the storage backend for Loki (chunks, index, ruler).

## Quick Start (Docker)

```bash
cd install/docker
docker compose up -d
```

- **S3 API**: http://localhost:9000
- **Console UI**: http://localhost:9001 (login: `minioadmin` / `minioadmin`)

Buckets are created automatically by the `createbuckets` init service:
`loki-data`, `loki-chunks`, `loki-ruler`, `loki-admin`.

## Quick Start (Kubernetes)

```bash
kubectl create namespace minio --dry-run=client -o yaml | kubectl apply -f -
kubectl -n minio apply -f install/k8s/minio.yaml
kubectl -n minio rollout status deploy/minio

# access
kubectl -n minio port-forward svc/minio 9000:9000 &          # S3 API
kubectl -n minio port-forward svc/minio-console 9001:9001 &   # Console UI
```

## Credentials & buckets

| Setting | Value |
|---------|-------|
| Access key (root user) | `minioadmin` |
| Secret key (root password) | `minioadmin` |
| Buckets | `loki-data`, `loki-chunks`, `loki-ruler`, `loki-admin` |

These match the Loki S3 configs in `loki/configs/v3.x/v3.7.x/`:
- `loki-3.7.x-ui-minio-inmemory.yaml` / `-memberlist.yaml` → bucket `loki-data`
- `loki-3.7.x-ui-minio-thanos-*.yaml` → bucket `loki-chunks`

## Image note (important)

The **official MinIO images reject anonymous pulls** — `minio/minio` and `minio/mc` on
both Docker Hub and quay.io return `401 authorization failed`. Consequences:

- **Docker**: if `docker compose up` cannot pull `minio/minio`, either `docker login`, or
  edit `install/docker/docker-compose.yaml` to use `cgr.dev/chainguard/minio` (public).
- **Kubernetes**: the manifest already uses `cgr.dev/chainguard/minio:latest` (free, public,
  multi-arch), so it works on a stock cluster with no registry auth. Because that image
  bundles no `mc` client, buckets are created as directories by a root initContainer.

## Verify

Docker:
```bash
docker compose logs createbuckets   # should list the 4 buckets
```

Kubernetes:
```bash
kubectl -n minio exec deploy/minio -- sh -c \
  'wget -qO- http://localhost:9000/minio/health/ready >/dev/null && echo READY_OK; ls -1 /data'
# expect: READY_OK  then  loki-admin / loki-chunks / loki-data / loki-ruler
```

## Point Loki at this MinIO

Docker (Loki and MinIO on the same host/network): endpoint `http://minio:9000` (or
`http://127.0.0.1:9000`), path-style addressing, creds `minioadmin` / `minioadmin`.

Kubernetes: endpoint `minio.minio.svc.cluster.local:9000` (service `minio` in namespace
`minio`), `s3forcepathstyle: true`, `insecure: true` (HTTP in-cluster).

## Uninstall

Docker:
```bash
cd install/docker
docker compose down          # keep data volume
docker compose down -v       # also delete the minio-data volume
```

Kubernetes:
```bash
kubectl -n minio delete -f install/k8s/minio.yaml
kubectl -n minio delete pvc minio        # if it lingers
kubectl delete namespace minio
```
