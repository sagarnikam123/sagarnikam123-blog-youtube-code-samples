# Lesson 01-pipeline-components — Standalone Collector Pipeline

This lesson demonstrates running a standalone OpenTelemetry Collector configured with:

- **Receivers**: OTLP gRPC (`4317`) and OTLP HTTP (`4318`).
- **Processors**: `memory_limiter` followed by `batch`.
- **Exporters**: `debug` with detailed console verbosity.
- **Extensions**: `health_check` (`13133`) and `zpages` (`55679`).

---

## Running the Collector

```bash
# Start container
docker compose up -d

# Verify health check
curl http://localhost:13133/
# Output: {"status":"Server available"}

# View debug logs as telemetry arrives
docker compose logs -f collector

# Stop container
docker compose down
```
