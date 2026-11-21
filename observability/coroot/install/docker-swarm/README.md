# Coroot — Docker Swarm

Coroot supports deployment on Docker Swarm. Since Swarm doesn't support privileged containers, the node-agent must be deployed manually on each node.

## Deploy

```bash
# Deploy the main stack as a Swarm stack
curl -fsS https://raw.githubusercontent.com/coroot/coroot/main/deploy/docker-compose.yaml | \
  docker stack deploy -c - coroot

# On each node, deploy node-agent manually (replace NODE_IP with any Swarm node IP)
docker run -d --name coroot-node-agent \
  --privileged --pid=host --network=host \
  -v /sys/kernel/tracing:/sys/kernel/tracing:rw \
  -v /sys/kernel/debug:/sys/kernel/debug:rw \
  -v /sys/fs/cgroup:/host/sys/fs/cgroup:ro \
  ghcr.io/coroot/coroot-node-agent \
  --collector-endpoint=http://NODE_IP:8080
```

## Notes

- node-agent requires Linux kernel 5.8+ and privileged access.
- Swarm doesn't support `privileged` in stack deployments, so node-agent runs outside the stack.
- For full orchestrated deployment, use the [Kubernetes Operator](../../operator/cluster/).

Official guide: [Coroot Docker Swarm](https://docs.coroot.com/installation/docker-swarm).
