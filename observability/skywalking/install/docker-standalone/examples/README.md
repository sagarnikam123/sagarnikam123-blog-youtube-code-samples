# Sample Services for Testing SkyWalking Monitoring

This directory contains sample service configurations for testing SkyWalking monitoring features.

## Quick Start

### 1. Start SkyWalking Core

```bash
cd ..
docker compose up -d
```

### 2. Start Sample Services

```bash
# MySQL
docker compose -f examples/mysql/docker-compose.yml up -d

# Redis
docker compose -f examples/redis/docker-compose.yml up -d

# Nginx
docker compose -f examples/nginx/docker-compose.yml up -d
```

### 3. Enable Monitoring

```bash
# Update .env with sample service credentials
cp .env.example .env

# For MySQL example, use these settings:
# MYSQL_HOST=sample-mysql
# MYSQL_USER=exporter
# MYSQL_EXPORTER_PASSWORD=exporterpassword

# For Redis example:
# REDIS_HOST=sample-redis

# For Nginx example:
# NGINX_HOST=sample-nginx

# Enable monitoring
docker compose --profile mysql --profile redis --profile nginx up -d
```

### 4. View Dashboards

Open http://localhost:8080 and navigate to:
- MySQL menu for MySQL metrics
- Redis menu for Redis metrics
- Nginx menu for Nginx metrics

## Available Examples

| Directory | Service | Default Port |
|-----------|---------|--------------|
| `mysql/` | MySQL 8.0 | 3306 |
| `redis/` | Redis 7 | 6379 |
| `nginx/` | Nginx | 8081 |

## Cleanup

```bash
# Stop sample services
docker compose -f examples/mysql/docker-compose.yml down -v
docker compose -f examples/redis/docker-compose.yml down -v
docker compose -f examples/nginx/docker-compose.yml down -v

# Stop SkyWalking
cd ..
docker compose --profile monitoring down -v
```
