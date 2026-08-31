# OpenSearch Observability — Homebrew (macOS)

Native macOS install of OpenSearch + OpenSearch Dashboards via Homebrew formulae, managed by `brew services` (launchd). Simplest local-dev path on a Mac; the macOS equivalent of the DEB/RPM package mode.

## Install

```bash
brew install opensearch
brew install opensearch-dashboards
```

## Start OpenSearch

```bash
# Background service (starts now + at login)
brew services start opensearch

# Or run in the foreground (no auto-start)
/opt/homebrew/opt/opensearch/bin/opensearch
```

## Start OpenSearch Dashboards

```bash
# Background service
brew services start opensearch-dashboards

# Or run in the foreground
/opt/homebrew/opt/opensearch-dashboards/bin/opensearch-dashboards
```

## Verify

```bash
# OpenSearch REST API
curl http://localhost:9200

# Cluster health
curl http://localhost:9200/_cluster/health?pretty

# Dashboards UI
open http://localhost:5601
```

The Homebrew formula ships with the **Security plugin disabled** by default, so OpenSearch answers on plain HTTP (`http://localhost:9200`) with no login — fine for local dev. Do not expose this beyond localhost without enabling security.

## Manage

```bash
brew services list
brew services restart opensearch
brew services stop opensearch-dashboards
```

## Notes

- OpenSearch config: `/opt/homebrew/etc/opensearch/opensearch.yml`
- Dashboards config: `/opt/homebrew/etc/opensearch-dashboards/opensearch_dashboards.yml`
- Data: `/opt/homebrew/var/lib/opensearch/`; logs: `/opt/homebrew/var/log/opensearch/`
- Ports: `9200` REST, `9300` transport, `5601` Dashboards.
- If Dashboards can't connect, confirm `opensearch.hosts: ["http://localhost:9200"]` in its config and that OpenSearch is up first.
- Homebrew tracks the latest OpenSearch (3.x). For a pinned version or Data Prepper, use the native tarball guide at [`../../binary/standalone/`](../../binary/standalone/).

Official sources:
- [Homebrew formula: opensearch](https://formulae.brew.sh/formula/opensearch)
- [Homebrew formula: opensearch-dashboards](https://formulae.brew.sh/formula/opensearch-dashboards)
