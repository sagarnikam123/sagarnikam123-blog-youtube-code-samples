# Lesson 01-agent-gateway — 2-Tier Collector Architecture

This lesson implements the production-standard **Agent + Gateway** two-tier architecture:

1. **Tier 1 (Agent):** Applications send telemetry to `localhost:4317/4318`. The agent batches and immediately forwards to the centralized gateway.
2. **Tier 2 (Gateway):** Receives from all agents across the cluster, performs aggregation, and outputs to backends or debug logs.

---

## Running the Architecture

```bash
# Start both agent and gateway containers
docker compose up -d

# Verify both are running healthy
docker compose ps

# View gateway logs receiving forwarded telemetry
docker compose logs -f gateway

# Stop environment
docker compose down
```
