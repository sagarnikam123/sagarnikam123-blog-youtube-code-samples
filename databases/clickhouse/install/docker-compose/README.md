# ClickHouse — Docker Compose cluster

Two ClickHouse server shards coordinated by a ClickHouse Keeper instance.

## Start

```bash
docker compose up -d
```

## Access

```bash
# Node 1 (primary)
clickhouse-client --host localhost --port 9000

# Node 2
clickhouse-client --host localhost --port 9001

# HTTP
curl http://localhost:8123/ -d "SELECT * FROM system.clusters"
```

## Create distributed table

```sql
CREATE TABLE events ON CLUSTER 'default' (
    timestamp DateTime,
    message String
) ENGINE = MergeTree()
ORDER BY timestamp;

CREATE TABLE events_dist AS events
ENGINE = Distributed('default', currentDatabase(), events, rand());
```

## Notes

- Keeper handles distributed DDL and replication coordination.
- For production, run 3+ Keeper instances.
- Scale by adding more shard services to `docker-compose.yml`.

Official guide: [ClickHouse cluster setup](https://clickhouse.com/docs/architecture/cluster-deployment).
