# Database Monitoring for SkyWalking

This directory contains configurations for monitoring databases in SkyWalking.

## Supported Databases

| Database | Exporter | SkyWalking Menu | Status |
|----------|----------|-----------------|--------|
| **MySQL/MariaDB** | mysqld_exporter | Database → MySQL/MariaDB | ✅ Ready |
| **PostgreSQL** | postgres_exporter | Database → PostgreSQL | ✅ Ready |
| **Redis** | redis_exporter | Database → Redis | ✅ Ready |
| **Elasticsearch** | elasticsearch_exporter | Database → Elasticsearch | ✅ Ready |
| **MongoDB** | mongodb_exporter | Database → MongoDB | ✅ Ready |
| **BookKeeper** | Built-in Prometheus | Database → BookKeeper | ✅ Ready |
| **ClickHouse** | clickhouse_exporter | Database → ClickHouse | ✅ Ready |
| **DynamoDB** | CloudWatch/YACE | Database → DynamoDB | 🔜 Production |

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATABASE LAYER                                  │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┤
│  MySQL   │PostgreSQL│  Redis   │  Mongo   │  Elastic │ BookKeeper/Click │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────┬─────────┘
     │          │          │          │          │              │
     ▼          ▼          ▼          ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         PROMETHEUS EXPORTERS                              │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────────┤
│ mysqld   │ postgres │  redis   │ mongodb  │ elastic  │ built-in/click   │
│ :9104    │ :9187    │ :9121    │ :9216    │ :9114    │ :8080/:9363      │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────┬─────────┘
     │          │          │          │          │              │
     └──────────┴──────────┴──────────┼──────────┴──────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     OTel Collector      │
                         │  (Prometheus Receiver)  │
                         └────────────┬────────────┘
                                      │ OTLP
                                      ▼
                         ┌─────────────────────────┐
                         │    SkyWalking OAP       │
                         │  (OC Rules enabled)     │
                         └─────────────────────────┘
```

## Quick Start

### 1. Enable Database Rules in OAP

Update your values.yaml:

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,mysql,mariadb,postgresql,redis,elasticsearch,mongodb,bookkeeper,clickhouse,..."
```

### 2. Deploy Database Exporters

```bash
# MySQL/MariaDB
kubectl apply -f mysql-exporter.yaml -n <database-namespace>

# PostgreSQL
kubectl apply -f postgresql-exporter.yaml -n <database-namespace>

# Redis
kubectl apply -f redis-exporter.yaml -n <database-namespace>

# Elasticsearch
kubectl apply -f elasticsearch-exporter.yaml -n <database-namespace>

# MongoDB
kubectl apply -f mongodb-exporter.yaml -n <database-namespace>

# ClickHouse
kubectl apply -f clickhouse-exporter.yaml -n <database-namespace>
```

### 3. Update OTel Collector

Add database scrape configs from `otel-collector-database.yaml` to your collector.

## Files

| File | Description |
|------|-------------|
| `mysql-exporter.yaml` | MySQL/MariaDB Prometheus Exporter |
| `postgresql-exporter.yaml` | PostgreSQL Prometheus Exporter |
| `redis-exporter.yaml` | Redis Prometheus Exporter |
| `elasticsearch-exporter.yaml` | Elasticsearch Prometheus Exporter |
| `mongodb-exporter.yaml` | MongoDB Prometheus Exporter |
| `bookkeeper-config.yaml` | BookKeeper Prometheus configuration |
| `clickhouse-exporter.yaml` | ClickHouse Prometheus Exporter |
| `otel-collector-database.yaml` | OTel Collector scrape configs |

## Exporter Ports Reference

| Exporter | Default Port | Metrics Path |
|----------|--------------|--------------|
| mysqld_exporter | 9104 | /metrics |
| postgres_exporter | 9187 | /metrics |
| redis_exporter | 9121 | /metrics |
| elasticsearch_exporter | 9114 | /metrics |
| mongodb_exporter | 9216 | /metrics |
| bookkeeper (built-in) | 8000 | /metrics |
| clickhouse_exporter | 9363 | /metrics |

## References

- [SkyWalking MySQL Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-mysql-monitoring/)
- [SkyWalking PostgreSQL Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-postgresql-monitoring/)
- [SkyWalking Redis Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-redis-monitoring/)
- [SkyWalking Elasticsearch Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-elasticsearch-monitoring/)
- [SkyWalking MongoDB Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-mongodb-monitoring/)
- [SkyWalking BookKeeper Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-bookkeeper-monitoring/)
- [SkyWalking ClickHouse Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-clickhouse-monitoring/)
