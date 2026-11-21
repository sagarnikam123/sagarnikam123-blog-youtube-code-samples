# Elastic Observability — Terraform configuration management

The official `elastic/elasticstack` Terraform provider manages Elasticsearch and Kibana resources on any self-hosted deployment: index lifecycle policies, ingest pipelines, Kibana spaces, alerting rules, and more.

## What Terraform manages

- Elasticsearch index templates and ILM policies
- Ingest pipelines
- Kibana spaces and saved objects
- Alerting rules and connectors
- Security roles and API keys

Terraform does **not** provision Elasticsearch/Kibana/APM Server. Deploy first using Docker Compose, ECK, or binaries.

## Configure credentials

```bash
export ELASTICSEARCH_URL="http://localhost:9200"
export KIBANA_URL="http://localhost:5601"
export ELASTICSEARCH_USERNAME="elastic"
export ELASTICSEARCH_PASSWORD="your-password"
```

## Apply

```bash
terraform init
terraform plan
terraform apply
```

Official sources:
- [elasticstack provider](https://registry.terraform.io/providers/elastic/elasticstack/latest)
- [Elastic Terraform blog](https://www.elastic.co/blog/streamline-configuration-processes-with-official-elastic-stack-terraform-provider)
