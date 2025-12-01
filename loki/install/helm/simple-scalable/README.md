# Loki Simple Scalable

Simple scalable Loki configurations for medium-scale deployments with horizontal scaling capabilities.

## What is Simple Scalable Mode?

Simple scalable mode groups Loki components into three services for easier scaling:
- **Read** - Handles queries (query-frontend, querier)
- **Write** - Handles ingestion (distributor, ingester)  
- **Backend** - Handles processing (compactor, ruler, index-gateway, query-scheduler)

## When to Use Simple Scalable Mode

✅ **Recommended for:**
- Medium-scale deployments (10GB-100GB/day)
- Need for horizontal scaling
- Simplified operations vs full microservices
- Production environments with moderate complexity
- Teams wanting easier management than full microservices

❌ **Not recommended for:**
- Small deployments (<10GB/day) - use monolithic
- Very large deployments (>100GB/day) - use microservices
- Maximum performance requirements - use microservices

## Architecture

**3 Service Groups:**
```yaml
# Read path - handles queries
target: read
# Components: query-frontend, querier

# Write path - handles ingestion  
target: write
# Components: distributor, ingester

# Backend - handles processing
target: backend
# Components: compactor, ruler, index-gateway, query-scheduler
```

## Structure

```
simple-scalable/
├── v2.x/          # Loki 2.x configurations
├── v3.x/          # Loki 3.x configurations
└── README.md      # This file
```

## Scaling Benefits

- **Independent scaling** of read, write, and backend components
- **Simpler than microservices** - only 3 services to manage
- **Better than monolithic** - can scale based on workload patterns
- **Resource optimization** - scale components based on actual usage

## Configuration Targets

Simple scalable mode uses three targets:
```yaml
# Read service
target: read

# Write service  
target: write

# Backend service
target: backend
```

## Storage Options

- **Filesystem** - Local disk storage (development)
- **S3** - Object storage (production-ready)
- **In-memory** - Components like memberlist, caching

## Usage

Choose the appropriate version directory based on your requirements:
- Use `v2.x/` for stable, production environments
- Use `v3.x/` for testing latest features and improvements

## Quick Start

```bash
# Download Loki binary
wget https://github.com/grafana/loki/releases/download/v3.0.0/loki-linux-amd64.zip

# Start read service
./loki -config.file=v3.x/loki-3.x.x-read-config.yaml

# Start write service  
./loki -config.file=v3.x/loki-3.x.x-write-config.yaml

# Start backend service
./loki -config.file=v3.x/loki-3.x.x-backend-config.yaml
```

## Scaling Examples

```bash
# Scale read components for query performance
# Run multiple read instances behind load balancer

# Scale write components for ingestion throughput  
# Run multiple write instances with consistent hashing

# Scale backend components for processing
# Usually single instance sufficient for most workloads
```

## Resources

- [Simple Scalable Mode Documentation](https://grafana.com/docs/loki/latest/get-started/deployment-modes/#simple-scalable)
- [Loki Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)