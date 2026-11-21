# Uptrace installation modes

| Mode | Status | Path | Notes |
|:-----|:-------|:-----|:------|
| Binary standalone | Available | [`binary/standalone/`](binary/standalone/) | Linux/macOS/Windows executable; external databases required |
| Docker Compose standalone | Available | [`docker-compose/standalone/`](docker-compose/standalone/) | Phase 1 benchmark |
| Ansible (bare-metal/VM) | Available | [`ansible/`](ansible/) | Official playbooks for ClickHouse + PostgreSQL + Redis + Uptrace |
| Helm standalone | Available | [`helm/standalone/`](helm/standalone/) | Kubernetes chart |
| Helm cluster | Available | [`helm/cluster/`](helm/cluster/) | Use clustered dependencies for production |
| Raw Kubernetes | Not maintained separately | — | Helm is the upstream Kubernetes path |
| Operator | Not documented upstream | — | Do not invent one |
