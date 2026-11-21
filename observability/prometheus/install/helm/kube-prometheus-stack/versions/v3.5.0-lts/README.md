# Prometheus v3.5.0 LTS

Long Term Support release (July 2025)

## Key Features

- Experimental type/unit metadata labels (`type-and-unit-labels` feature flag)
- New PromQL functions: `ts_of_(min|max|last)_over_time` (experimental)
- `always_scrape_classic_histograms` global option
- OTLP: `promote_all_resource_attributes` and `ignore_resource_attributes`
- STACKIT Cloud service discovery
- Hetzner SD: `label_selector` filtering

## When to Use

- Production environments requiring stability
- Long-term support and bug fixes
- Conservative upgrade strategy

## Installation

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n prometheus --create-namespace \
  -f ../../base/values.yaml \
  -f values.yaml \
  -f ../../environments/prod/values.yaml
```

## Chart Version Mapping

| Chart Version | Prometheus Version |
|--------------|-------------------|
| 77.10.0 | v3.5.0 |

## References

- [Release Notes](https://github.com/prometheus/prometheus/releases/tag/v3.5.0)
- [LTS Policy](https://prometheus.io/docs/introduction/release-cycle/)
