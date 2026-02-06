# SkyWalking Satellite Usage Guide

## Overview

Satellite is deployed as a proxy between agents and OAP for:
- Load balancing across OAP instances
- Buffering during OAP restarts/upgrades
- Reducing direct connections to OAP

## Agent Configuration

### Connect Agents to Satellite (Recommended for Production)

Instead of connecting directly to OAP, configure agents to connect to Satellite:

#### Java Agent
```properties
# agent.config or environment variable
collector.backend_service=skywalking-satellite.skywalking:11800
# Or via env var:
# SW_AGENT_COLLECTOR_BACKEND_SERVICES=skywalking-satellite.skywalking:11800
```

#### Python Agent
```python
from skywalking import agent, config

config.init(
    agent_collector_backend_services='skywalking-satellite.skywalking:11800',
    agent_name='my-python-service'
)
agent.start()
```

#### Go Agent
```go
import "github.com/apache/skywalking-go/reporter"

reporter.NewGRPCReporter("skywalking-satellite.skywalking:11800")
```

#### Node.js Agent
```javascript
require('skywalking-backend-js').start({
  serviceName: 'my-nodejs-service',
  collectorAddress: 'skywalking-satellite.skywalking:11800'
});
```

### Connect Agents Directly to OAP (Dev/Testing)

For simple setups or development:
```
collector.backend_service=skywalking-oap.skywalking:11800
```

## Architecture

```
With Satellite (Production):
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agent 1   │────▶│             │────▶│   OAP 1     │
└─────────────┘     │             │     └─────────────┘
┌─────────────┐     │  Satellite  │     ┌─────────────┐
│   Agent 2   │────▶│   (proxy)   │────▶│   OAP 2     │
└─────────────┘     │             │     └─────────────┘
┌─────────────┐     │             │     ┌─────────────┐
│   Agent 3   │────▶│             │────▶│   OAP 3     │
└─────────────┘     └─────────────┘     └─────────────┘

Without Satellite (Dev):
┌─────────────┐     ┌─────────────┐
│   Agent     │────▶│     OAP     │
└─────────────┘     └─────────────┘
```

## Service Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Satellite | `skywalking-satellite.skywalking:11800` | Agent connection (via proxy) |
| OAP Direct | `skywalking-oap.skywalking:11800` | Direct agent connection |
| OAP REST | `skywalking-oap.skywalking:12800` | GraphQL API |
| UI | `skywalking-ui.skywalking:80` | Web interface |

## Important Notes

1. **Satellite does NOT scrape Prometheus metrics** - Use OTel Collector for infrastructure monitoring
2. **Satellite is optional** - For small deployments, agents can connect directly to OAP
3. **Use Satellite when**:
   - You have >100 agent instances
   - You need buffering during OAP maintenance
   - You want to reduce connections to OAP
