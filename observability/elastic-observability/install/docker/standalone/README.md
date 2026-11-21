# Elastic Observability — Docker standalone

Run individual Elastic components as Docker containers. This is not a single all-in-one image; you manage Elasticsearch, Kibana, and APM Server as separate containers.

## Run Elasticsearch

```bash
docker network create elastic

docker run -d --name elasticsearch --net elastic \
  -p 9200:9200 \
  -e discovery.type=single-node \
  -e xpack.security.enabled=false \
  -e "ES_JAVA_OPTS=-Xms2g -Xmx2g" \
  docker.elastic.co/elasticsearch/elasticsearch:8.17.0
```

## Run Kibana

```bash
docker run -d --name kibana --net elastic \
  -p 5601:5601 \
  -e ELASTICSEARCH_HOSTS=http://elasticsearch:9200 \
  docker.elastic.co/kibana/kibana:8.17.0
```

## Run APM Server (OTLP ingestion)

```bash
docker run -d --name apm-server --net elastic \
  -p 8200:8200 -p 4317:4317 -p 4318:4318 \
  docker.elastic.co/apm/apm-server:8.17.0 \
  apm-server -e \
    -E apm-server.host=0.0.0.0:8200 \
    -E output.elasticsearch.hosts=["http://elasticsearch:9200"] \
    -E apm-server.auth.anonymous.enabled=true
```

APM Server natively accepts OTLP on ports 4317 (gRPC) and 4318 (HTTP).

Official sources:
- [Install Elasticsearch with Docker](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-with-docker)
- [Install Kibana with Docker](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-kibana-with-docker)
