# SigNoz — Docker Swarm

SigNoz supports deployment on Docker Swarm using Foundry with mode `docker-swarm`. This provisions the SigNoz stack as Swarm services.

## Install

```bash
# 1. Install Foundry CLI
curl -fsSL https://signoz.io/foundry.sh | bash

# 2. Create casting.yaml
cat <<'EOF' > casting.yaml
apiVersion: v1alpha1
kind: Installation
metadata:
  name: signoz
spec:
  deployment:
    flavor: compose
    mode: docker-swarm
EOF

# 3. Deploy
foundryctl cast -f casting.yaml
```

Foundry generates a Compose file and deploys it as a Docker Swarm stack.

Official guide: [Install SigNoz on Docker Swarm](https://signoz.io/docs/install/docker-swarm/).
