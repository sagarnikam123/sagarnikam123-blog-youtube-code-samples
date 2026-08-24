# Tempo — binary standalone (monolithic)

Download and run Tempo as a single binary in monolithic mode.

## Install

```bash
VERSION=2.7.2
curl -L -o tempo \
  "https://github.com/grafana/tempo/releases/download/v${VERSION}/tempo_${VERSION}_linux_amd64"
chmod +x tempo
```

## Run

```bash
./tempo -config.file=tempo.yaml
```

## Verify

```bash
curl http://localhost:3200/ready
curl http://localhost:3200/status
```

## Notes

- Monolithic mode: all components (distributor, ingester, querier, compactor) in one process.
- Local filesystem backend for dev/testing; use object storage for production.
- Accepts OTLP on `:4317` (gRPC) and `:4318` (HTTP) by default.
- Jaeger on `:14268` (HTTP) and `:6831` (UDP compact thrift).

Official guide: [Deploy Tempo](https://grafana.com/docs/tempo/latest/set-up-for-tracing/setup-tempo/deploy/).
