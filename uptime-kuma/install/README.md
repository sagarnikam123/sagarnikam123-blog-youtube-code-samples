# Uptime Kuma installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available (Node.js + PM2) | [`binary/standalone/`](binary/standalone/) | Clone + `npm run setup`; run under PM2. No prebuilt binary is published |
| Docker standalone | Available | [`docker/standalone/`](docker/standalone/) | Single `docker run`, SQLite in `/app/data` |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Official `compose.yaml` pattern |
| Docker Compose cluster | N/A | — | SQLite single-writer; not a supported cluster mode |
| Kubernetes standalone | Community (via Helm) | [`helm/standalone/`](helm/standalone/) | No official raw manifests |
| Helm standalone | Community | [`helm/standalone/`](helm/standalone/) | No official chart; HelmForge / dirsigler charts are community-maintained |
| Operator | N/A | — | No official operator |

Uptime Kuma is a single-container application. The only officially documented installs are Docker, Docker Compose, and the non-Docker Node.js path. Kubernetes/Helm charts are community-provided and used at your own risk.

Official sources:
- [How to Install (wiki)](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%94%A7-How-to-Install)
- [Docker tags](https://github.com/louislam/uptime-kuma/wiki/Migration-From-v1-To-v2#docker-tags)
- [Reverse proxy (WebSocket)](https://github.com/louislam/uptime-kuma/wiki/Reverse-Proxy)
