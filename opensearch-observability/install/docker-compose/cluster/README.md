# OpenSearch Observability — Docker Compose cluster

Run a multi-node OpenSearch cluster with Docker Compose for local replication and fault-tolerance testing. Add Data Prepper and Dashboards as sidecar services.

## Overview

A typical three-node Compose cluster extends the standalone benchmark by:

- Adding `opensearch-node2` and `opensearch-node3` services.
- Setting `discovery.seed_hosts` and `cluster.initial_cluster_manager_nodes` across all nodes.
- Removing `discovery.type=single-node`.

Follow the official multi-node Docker Compose documentation and adapt the benchmark Compose file's Data Prepper and Dashboards services:

- [OpenSearch Docker quickstart (multi-node)](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/)

For production distributed deployments, use the [Helm chart](../../helm/cluster/) or the [OpenSearch Kubernetes Operator](../../operator/cluster/).
