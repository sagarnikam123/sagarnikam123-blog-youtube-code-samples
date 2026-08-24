# Elastic Observability — native components

Elastic publishes native packages and archives for Elasticsearch and Kibana. A complete observability installation still consists of separate Elasticsearch, Kibana, and APM/Elastic Agent components, so this mode is documented as component installation rather than one binary.

Use the official platform-specific package/archive instructions:

- [Install Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/install-elasticsearch.html)
- [Install Kibana](https://www.elastic.co/guide/en/kibana/current/install.html)
- [APM Server and Elastic Agent](https://www.elastic.co/guide/en/observability/current/ingest-logs-metrics-and-traces.html)

Configure TLS, authentication, and service management before production use. The repository's Compose stack remains the reproducible single-node benchmark path.
