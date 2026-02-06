# SkyWalking Docker Cluster Mode

High-availability deployment with multiple OAP nodes and load balancing.

## Architecture

```
                    ┌─────────────────┐
                    │   SkyWalking UI │
                    │    Port: 8080   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Nginx LB       │
                    │  gRPC: 11800    │
                    │  HTTP: 12800    │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │   OAP-1     │   │   OAP-2     │   │   OAP-3     │
    │  (Primary)  │   │  (Replica)  │   │  (Replica)  │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │    BanyanDB     │
                    │   Port: 17912   │
                    └─────────────────┘
```

## Quick Start

```bash
docker-compose up -d
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| UI | 8080 | Web interface |
| OAP LB (gRPC) | 11800 | Agent communication |
| OAP LB (HTTP) | 12800 | REST API |
| BanyanDB | 17912 | Storage backend |

## Scaling

Adjust the number of OAP nodes by adding/removing services in `docker-compose.yml` and updating `nginx.conf`.

## Health Check

```bash
# Check all services
docker-compose ps

# Check OAP health
curl http://localhost:12800/healthcheck
```
