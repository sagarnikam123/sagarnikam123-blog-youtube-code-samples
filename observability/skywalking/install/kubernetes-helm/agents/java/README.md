# SkyWalking Java Agent for Kubernetes

This directory contains configurations for deploying SkyWalking Java agent to instrument Java applications in Kubernetes.

## Methods

### 1. Init Container Method (Recommended)
Uses an init container to copy the agent to a shared volume, then adds JVM args to the application.

### 2. Sidecar Injection (via Webhook)
Automatic injection using a mutating webhook - requires additional setup.

## Quick Start

### For hunt namespace (spotter-* services):

```bash
# Apply the ConfigMap with agent config
kubectl apply -f agents/java/hunt-namespace/agent-config.yaml

# Patch a single deployment to test
kubectl patch deployment spotter-api-service -n hunt --patch-file agents/java/hunt-namespace/patch-template.yaml

# Or apply to all spotter services
./agents/java/hunt-namespace/enable-agent.sh
```

## Agent Configuration

The agent connects to SkyWalking via:
- **Satellite** (recommended): `skywalking-satellite.skywalking.svc:11800`
- **Direct to OAP**: `skywalking-oap.skywalking.svc:11800`

## Files

- `hunt-namespace/` - Configurations for hunt namespace services
  - `agent-config.yaml` - ConfigMap with agent.config
  - `patch-template.yaml` - Deployment patch template
  - `enable-agent.sh` - Script to enable agent on all services
  - `disable-agent.sh` - Script to remove agent from all services
