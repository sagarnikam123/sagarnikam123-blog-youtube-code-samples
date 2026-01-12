# Prometheus v3.9.0 Latest

Latest release (January 2026)

## Key Features

- **Native Histograms GA** - No longer experimental!
  - `native-histogram` feature flag is now a no-op
  - Use `scrape_native_histograms` config option instead
- `/api/v1/features` endpoint for feature discovery
- `--storage.tsdb.delay-compact-file.path` flag (Thanos interop)
- UI: Duplicate query panel, Y-axis zero start option
- Promtool: `start_timestamp` for unit tests

## Breaking Changes

Native Histograms configuration changed:
```yaml
# OLD (no longer works)
prometheus:
  prometheusSpec:
    enableFeatures:
      - native-histograms

# NEW
# Use scrape_native_histograms in scrape configs
```

## When to Use

- Development/staging environments
- Need Native Histograms in production
- Want latest features and improvements

## Installation

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f ../../base/values.yaml \
  -f values.yaml \
  -f ../../environments/dev/values.yaml
```

## Chart Version Mapping

| Chart Version | Prometheus Version |
|--------------|-------------------|
| 80.13.0 | v3.9.0 |

## References

- [Release Notes](https://github.com/prometheus/prometheus/releases/tag/v3.9.0)
