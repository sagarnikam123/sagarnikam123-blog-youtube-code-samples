# Loki Configuration Deep Dive


## Configuration

### Loki Targets

You can see the complete list of targets for your version of Loki by running Loki with the flag `-list-targets`, for example:

```bash
docker run docker.io/grafana/loki:3.5.7 -config.file=/etc/loki/local-config.yaml -list-targets
```

```commandline
# target 3.5.7
all
  compactor
  distributor
  ingester
  pattern-ingester
  querier
  query-frontend
  query-scheduler
  ruler
  ui
backend
  bloom-builder
  bloom-gateway
  bloom-gateway-client
  bloom-planner
  compactor
  index-gateway
  query-scheduler
  ruler
  ui
block-builder
  ui
block-scheduler
  ui
bloom-builder
  bloom-gateway-client
  ui
bloom-gateway
  bloom-gateway-client
  ui
bloom-gateway-client
bloom-planner
  bloom-gateway-client
  ui
compactor
  ui
dataobj-consumer
  ui
dataobj-explorer
  ui
distributor
  ui
index-gateway
  bloom-gateway-client
  ui
ingest-limits
ingest-limits-frontend
ingester
  ui
overrides-exporter
  ui
pattern-ingester
  ui
querier
  query-scheduler
  ui
query-frontend
  query-scheduler
  ui
query-scheduler
  ui
read
  querier
  query-frontend
  query-scheduler
  ui
ruler
  ui
table-manager
  ui
ui
write
  distributor
  ingester
  pattern-ingester
  ui
```


### blocks/targets/components with ring structure
- distributor
- query_scheduler
- ruler
- ingester
- pattern_ingester
- index_gateway
- compactor
- ingest_limits
- ingest_limits_frontend
- common

### non ring targets
- server
- internal_server (only visible in <loki-url>/config)
- ui
- querier
- ingester_client
- block_builder
- block_scheduler
- bloom_build (experimental)
- bloom_gateway (experimental)
- bloom_shipper (experimental)
- storage_config
- chunk_store_config
- schema_config
- limits_config
- table_manager
- memberlist
- kafka_config
- dataobj
- runtime_config
- operational_config
- tracing
- analytics


### grpc_client_config
- frontend
- ruler
- ingester_client
- block_builder
- pattern_ingester
- bloom_build (experimental)
- bloom_gateway (experimental)
- compactor_grpc_client
- frontend_worker
- ingest_limits_frontend
- ingest_limits_frontend_client

### cache
- query_range - results_cache, index_stats_results_cache, volume_results_cache, instant_metric_results_cache, series_results_cache
- 