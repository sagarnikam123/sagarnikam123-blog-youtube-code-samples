# Uptime Kuma — Helm (community)

There is **no official Helm chart**. The charts below are community-maintained and, per the upstream wiki, are not officially tested and may break on future releases. Use at your own risk.

## HelmForge chart (community)

```bash
helm repo add helmforge https://repo.helmforge.dev
helm repo update
helm install uptime-kuma helmforge/uptime-kuma
```

Or via OCI:

```bash
helm install uptime-kuma oci://ghcr.io/helmforgedev/helm/uptime-kuma
```

Features: SQLite or MariaDB backends, built-in S3-compatible backup workflows.

- Chart source: <https://github.com/helmforgedev/charts/tree/main/charts/uptime-kuma>
- Artifact Hub: <https://artifacthub.io/packages/helm/helmforge/uptime-kuma>

## Notes

- Uptime Kuma is a single-writer SQLite app: run **one replica**. Scaling out requires an external MariaDB backend (supported by some community charts) and is not the default design.
- Persist `/app/data` (or the MariaDB it points at) via a PVC.
- Other community charts exist (dirsigler, johanneskastl, fmjstudios); evaluate maintenance cadence before adopting.

Official reference: [How to Install → Deployment Tools (unofficial)](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install).
