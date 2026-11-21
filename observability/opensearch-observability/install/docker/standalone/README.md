# OpenSearch Observability — Docker standalone

Run OpenSearch as a single-node Docker container for quick evaluation. Data Prepper and Dashboards can be added as separate containers on the same Docker network.

## Run OpenSearch (single-node)

```bash
docker network create opensearch-net

docker run -d --name opensearch --net opensearch-net \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:2.19.1
```

## Run OpenSearch Dashboards

```bash
docker run -d --name dashboards --net opensearch-net \
  -p 5601:5601 \
  -e "OPENSEARCH_HOSTS=http://opensearch:9200" \
  -e "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true" \
  opensearchproject/opensearch-dashboards:2.19.1
```

## Run Data Prepper (OTLP → OpenSearch)

```bash
docker run -d --name data-prepper --net opensearch-net \
  -p 4317:21890 -p 4318:21891 -p 4900:4900 \
  -v $PWD/pipelines.yaml:/usr/share/data-prepper/pipelines/pipelines.yaml \
  opensearchproject/data-prepper:2.11.0
```

A `pipelines.yaml` must define the OTLP sources and OpenSearch sinks. Use the benchmark Compose config as a reference.

Official sources:
- [Install OpenSearch with Docker](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/)
- [Data Prepper](https://opensearch.org/docs/latest/data-prepper/)
