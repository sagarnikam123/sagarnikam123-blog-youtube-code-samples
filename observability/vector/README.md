# Vector — observability data pipeline

Vector is a high-performance, end-to-end observability data pipeline built in Rust. It collects, transforms, and routes logs, metrics, and traces to any backend.

## Installation modes

| Mode | Guide |
|:-----|:------|
| Binary / install script | [`install/binary/`](install/binary/) |
| Docker / Docker Compose | [`install/docker/`](install/docker/) |
| Helm (Kubernetes) | [`install/helm/`](install/helm/) |
| Kubernetes DaemonSet (raw YAML) | [`install/k8s/`](install/k8s/) |

## Pipeline examples

| # | Example | Pattern | Source → Sink |
|:--|:--------|:--------|:--------------|
| 1 | [logs-to-elasticsearch](examples/logs-to-elasticsearch/) | source → transform → sink | file → VRL parse → Elasticsearch |
| 2 | [logs-to-opensearch](examples/logs-to-opensearch/) | source → transform → sink | file → VRL parse → OpenSearch |
| 3 | [logs-to-loki](examples/logs-to-loki/) | source → transform → sink | file + docker_logs → VRL → Loki |
| 4 | [logs-to-clickhouse](examples/logs-to-clickhouse/) | source → transform → sink | file → VRL parse → ClickHouse |
| 5 | [logs-to-s3](examples/logs-to-s3/) | source → transform → sink | file → enrich → S3 (gzip/ndjson) |
| 6 | [metrics-to-prometheus](examples/metrics-to-prometheus/) | source → sink | host_metrics → Prometheus exporter |
| 7 | [metrics-to-victoriametrics](examples/metrics-to-victoriametrics/) | source → sink | host_metrics → Prometheus remote_write → VM |
| 8 | [k8s-logs-to-loki](examples/k8s-logs-to-loki/) | source → transform → sink | kubernetes_logs → VRL enrich → Loki |
| 9 | [syslog-to-elasticsearch](examples/syslog-to-elasticsearch/) | source → transform → sink | syslog UDP/TCP → enrich → Elasticsearch |
| 10 | [kafka-to-clickhouse](examples/kafka-to-clickhouse/) | source → transform → sink | Kafka → VRL parse → ClickHouse |
| 11 | [route-by-level](examples/route-by-level/) | source → transform → route → multi-sink | file → parse → route → Loki (errors) + S3 (all) |
| 12 | [log-to-metric](examples/log-to-metric/) | source → transform → transform → sink | file → parse → log_to_metric → Prometheus exporter |
| 13 | [journald-to-loki](examples/journald-to-loki/) | source → transform → sink | journald → VRL enrich → Loki |
| 14 | [docker-logs-to-clickhouse](examples/docker-logs-to-clickhouse/) | source → transform → sink | docker_logs → VRL parse → ClickHouse |
| 15 | [fluent-to-opensearch](examples/fluent-to-opensearch/) | source → transform → sink | Fluent Bit/Fluentd → VRL enrich → OpenSearch |
| 16 | [splunk-hec-to-elasticsearch](examples/splunk-hec-to-elasticsearch/) | source → transform → sink | Splunk HEC → normalize → Elasticsearch |
| 17 | [exec-command-to-loki](examples/exec-command-to-loki/) | source → transform → sink | exec (df -h) → VRL → Loki |
| 18 | [redis-to-elasticsearch](examples/redis-to-elasticsearch/) | source → transform → sink | Redis pub/sub → VRL parse → Elasticsearch |
| 19 | [aws-s3-source-to-clickhouse](examples/aws-s3-source-to-clickhouse/) | source → transform → sink | S3 (via SQS) → VRL parse → ClickHouse |
| 20 | [postgres-metrics-to-prometheus](examples/postgres-metrics-to-prometheus/) | source → sink | postgresql_metrics → Prometheus exporter |
| 21 | [nginx-metrics-to-prometheus](examples/nginx-metrics-to-prometheus/) | source → sink | nginx_metrics → Prometheus exporter |
| 22 | [statsd-to-prometheus](examples/statsd-to-prometheus/) | source → transform → sink | StatsD → incremental_to_absolute → Prometheus |
| 23 | [host-metrics-aggregate-to-influxdb](examples/host-metrics-aggregate-to-influxdb/) | source → transform → sink | host_metrics → aggregate → InfluxDB |
| 24 | [file-filter-dedupe-to-elasticsearch](examples/file-filter-dedupe-to-elasticsearch/) | source → transform chain → sink | file → parse → filter → dedupe → Elasticsearch |
| 25 | [file-sample-throttle-to-s3](examples/file-sample-throttle-to-s3/) | source → transform chain → sink | file → parse → sample → throttle → S3 |
| 26 | [prometheus-scrape-to-remote-write](examples/prometheus-scrape-to-remote-write/) | source → transform → sink | prometheus_scrape → tag_cardinality_limit → remote_write (Mimir) |
| 27 | [http-server-to-kafka](examples/http-server-to-kafka/) | source → transform → sink | HTTP webhooks → VRL enrich → Kafka |
| 28 | [otlp-to-loki-and-tempo](examples/otlp-to-loki-and-tempo/) | source → route → multi-sink | OpenTelemetry (OTLP) → route logs/traces → Loki + Tempo |
| 29 | [demo-logs-to-console](examples/demo-logs-to-console/) | source → transform → sink | demo_logs → VRL parse → console (zero-dep) |
| 30 | [multi-source-to-multi-sink](examples/multi-source-to-multi-sink/) | multi-source → transform → route → multi-sink | file + journald + host_metrics → parse → route → Loki + Elasticsearch + ClickHouse + VictoriaMetrics |

## Key facts

- Single Rust binary, no runtime dependencies
- Roles: Agent (DaemonSet), Aggregator (StatefulSet), Sidecar
- Config: YAML, TOML, or JSON
- Transform language: VRL (Vector Remap Language)
- License: MPL-2.0
- Maintained by Datadog
- Docker image: `timberio/vector`

Official site: [vector.dev](https://vector.dev/)
