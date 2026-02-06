# Message Queue Monitoring for SkyWalking

This directory contains configurations for monitoring message queues in SkyWalking.

## Supported Message Queues

| Message Queue | Exporter | Port | SkyWalking Menu | Status |
|---------------|----------|------|-----------------|--------|
| **Kafka** | kafka_exporter | 9308 | MQ → Kafka | ✅ Ready |
| **RabbitMQ** | Built-in Prometheus | 15692 | MQ → RabbitMQ | ✅ Ready |
| **Pulsar** | Built-in Prometheus | 8080 | MQ → Pulsar | ✅ Ready |
| **ActiveMQ** | activemq_exporter | 8161 | MQ → ActiveMQ | ✅ Ready |
| **RocketMQ** | rocketmq_exporter | 5557 | MQ → RocketMQ | ✅ Ready |

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        MESSAGE QUEUE LAYER                                │
├──────────┬──────────┬──────────┬──────────┬──────────────────────────────┤
│  Kafka   │ RabbitMQ │  Pulsar  │ ActiveMQ │        RocketMQ              │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────────┬─────────────────┘
     │          │          │          │                  │
     ▼          ▼          ▼          ▼                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         PROMETHEUS EXPORTERS                              │
├──────────┬──────────┬──────────┬──────────┬──────────────────────────────┤
│ kafka    │ built-in │ built-in │ activemq │      rocketmq                │
│ :9308    │ :15692   │ :8080    │ :8161    │      :5557                   │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────────────┬─────────────────┘
     │          │          │          │                  │
     └──────────┴──────────┴──────────┼──────────────────┘
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
                         └─────────────────────────┘
```

## Quick Start

### 1. Enable MQ Rules in OAP

```yaml
oap:
  env:
    SW_OTEL_RECEIVER_ENABLED_OC_RULES: "oap,kafka,rabbitmq,pulsar,activemq,rocketmq,..."
```

### 2. Deploy Exporter

```bash
# Kafka
kubectl apply -f kafka-exporter.yaml -n <mq-namespace>

# RabbitMQ (built-in, enable plugin)
kubectl apply -f rabbitmq-config.yaml -n <mq-namespace>

# Pulsar (built-in)
kubectl apply -f pulsar-config.yaml -n <mq-namespace>

# ActiveMQ
kubectl apply -f activemq-exporter.yaml -n <mq-namespace>

# RocketMQ
kubectl apply -f rocketmq-exporter.yaml -n <mq-namespace>
```

### 3. Update OTel Collector

Add MQ scrape configs from `otel-collector-mq.yaml`.

## Files

| File | Description |
|------|-------------|
| `kafka-exporter.yaml` | Kafka Prometheus Exporter |
| `rabbitmq-config.yaml` | RabbitMQ Prometheus plugin config |
| `pulsar-config.yaml` | Pulsar Prometheus configuration |
| `activemq-exporter.yaml` | ActiveMQ Prometheus Exporter |
| `rocketmq-exporter.yaml` | RocketMQ Prometheus Exporter |
| `otel-collector-mq.yaml` | OTel Collector scrape configs |

## References

- [SkyWalking Kafka Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-kafka-monitoring/)
- [SkyWalking RabbitMQ Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-rabbitmq-monitoring/)
- [SkyWalking Pulsar Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-pulsar-monitoring/)
- [SkyWalking ActiveMQ Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-activemq-monitoring/)
- [SkyWalking RocketMQ Monitoring](https://skywalking.apache.org/docs/main/latest/en/setup/backend/backend-rocketmq-monitoring/)
