# Test Deployments for SkyWalking Monitoring

Minimal test deployments to verify each monitoring feature in SkyWalking.

Each deployment includes the service + Prometheus exporter as sidecar.

## Quick Start

```bash
# 1. Deploy test service (e.g., MySQL)
kubectl apply -f demo-mysql.yaml -n skywalking

# 2. Deploy OTel Collector for test scraping
kubectl apply -f otel-collector-demo.yaml -n skywalking

# 3. Wait for pods
kubectl get pods -n skywalking -l app=demo-mysql

# 4. Check SkyWalking UI → Database → MySQL
```

## Available Tests

| File | Service | Exporter Port | SkyWalking Menu |
|------|---------|---------------|-----------------|
| `demo-nginx.yaml` | Nginx | 9113 | Gateway → NGINX |
| `demo-mysql.yaml` | MySQL 8.0 | 9104 | Database → MySQL |
| `demo-postgresql.yaml` | PostgreSQL 16 | 9187 | Database → PostgreSQL |
| `demo-redis.yaml` | Redis 7 | 9121 | Database → Redis |
| `demo-mongodb.yaml` | MongoDB 7 | 9216 | Database → MongoDB |
| `demo-elasticsearch.yaml` | Elasticsearch 8 | 9114 | Database → Elasticsearch |
| `demo-kafka.yaml` | Kafka 3.8 (KRaft) | 9308 | MQ → Kafka |
| `demo-rabbitmq.yaml` | RabbitMQ 3.13 | 15692 | MQ → RabbitMQ |
| `demo-pulsar.yaml` | Pulsar 3.3 | 8080 | MQ → Pulsar |
| `demo-activemq.yaml` | ActiveMQ 6.1 | 9404 | MQ → ActiveMQ |
| `demo-rocketmq.yaml` | RocketMQ 5.2 | 5557 | MQ → RocketMQ |
| `demo-flink.yaml` | Flink 1.19 | 9249 | Flink |

## Usage Examples

### Test Single Feature

```bash
# Deploy MySQL test
kubectl apply -f demo-mysql.yaml -n skywalking
kubectl apply -f otel-collector-demo.yaml -n skywalking

# Connect to MySQL
kubectl exec -it deploy/demo-mysql -c mysql -n skywalking -- mysql -uroot -ptest123

# Check metrics
kubectl port-forward svc/demo-mysql 9104:9104 -n skywalking
curl http://localhost:9104/metrics
```

### Test All Features

```bash
# Deploy everything
kubectl apply -f . -n skywalking

# Check all test pods
kubectl get pods -n skywalking | grep demo-

# Clean up
kubectl delete -f . -n skywalking
```

### Verify Metrics Flow

```bash
# Check OTel Collector logs
kubectl logs deploy/otel-collector-demo -n skywalking

# Check OAP is receiving metrics
kubectl logs deploy/skywalking-oap -n skywalking | grep -i "mysql\|redis\|kafka"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Deployments                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │demo-mysql│ │demo-redis│ │demo-kafka│ │demo-nginx│  ...      │
│  │ +exporter│ │ +exporter│ │ +exporter│ │ +exporter│           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                   │
│       └────────────┴─────┬──────┴────────────┘                   │
│                          ▼                                       │
│              ┌─────────────────────────┐                         │
│              │  otel-collector-demo    │                         │
│              │  (scrapes all tests)    │                         │
│              └───────────┬─────────────┘                         │
│                          │ OTLP                                  │
│                          ▼                                       │
│              ┌─────────────────────────┐                         │
│              │    SkyWalking OAP       │                         │
│              └─────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

## Resource Requirements

| Deployment | CPU Request | Memory Request |
|------------|-------------|----------------|
| demo-mysql | 150m | 288Mi |
| demo-postgresql | 150m | 288Mi |
| demo-redis | 100m | 96Mi |
| demo-mongodb | 150m | 288Mi |
| demo-elasticsearch | 250m | 544Mi |
| demo-kafka | 250m | 544Mi |
| demo-rabbitmq | 100m | 256Mi |
| demo-nginx | 100m | 96Mi |
| otel-collector-demo | 100m | 128Mi |
| **Total (all)** | **~1.4 CPU** | **~2.5 GB** |

## Credentials

| Service | Username | Password |
|---------|----------|----------|
| MySQL | root | test123 |
| PostgreSQL | postgres | test123 |
| MongoDB | admin | test123 |
| RabbitMQ | guest | guest |
| Redis | - | - |
| Elasticsearch | - | - |
| Kafka | - | - |

## Troubleshooting

```bash
# Check if exporter is working
kubectl exec -it deploy/demo-mysql -c mysql-exporter -n skywalking -- wget -qO- http://localhost:9104/metrics | head

# Check service connectivity
kubectl exec -it deploy/otel-collector-demo -n skywalking -- wget -qO- http://demo-mysql:9104/metrics | head

# Check OTel Collector config
kubectl describe cm otel-collector-demo-config -n skywalking
```
