# Elastic Observability — Docker Compose cluster

Elastic publishes an official three-node Elasticsearch cluster deployment using Docker Compose. This mode demonstrates Elasticsearch replication, node discovery, and cross-cluster features in a local environment.

Follow the upstream guide and official Compose file:

- [Start a multi-node cluster with Docker Compose](https://www.elastic.co/docs/deploy-manage/deploy/self-managed/install-elasticsearch-docker-compose)
- [Official Compose file](https://github.com/elastic/elasticsearch/blob/main/docs/reference/setup/install/docker/docker-compose.yml)

Add Kibana and APM Server as in the standalone mode. The key difference is `discovery.seed_hosts` and `cluster.initial_master_nodes` across three `es0x` services.

For production fault tolerance on Kubernetes, use the [ECK operator](../../operator/cluster/) or [Helm/ECK stack chart](../../helm/cluster/) instead.
