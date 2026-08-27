# ClickStack — ClickHouse-embedded mode

ClickStack UI is bundled directly into the ClickHouse server binary (since 26.2). No additional components required — navigate to `http://localhost:8123/clickstack` after starting the server.

Suitable for demos, evaluations, and exploring your own ClickHouse data with an observability UI.

> Source: [Embedded in ClickHouse docs](https://clickhouse.com/docs/clickstack/deployment/clickhouse-embedded) and [announcement blog](https://clickhouse.com/blog/clickstack-embedded-clickhouse)

## Limitations

- Not designed for production use
- No alerting
- No dashboard/search persistence across sessions
- No customizable query settings
- No event patterns (pyodide/WASM removed to keep binary small)

## Install ClickHouse binary

```bash
curl https://clickhouse.com/ | sh
```

## (Optional) Enable system log tables

Create a config snippet that enables internal query and metric logs so you can observe ClickHouse itself:

```bash
mkdir -p config.d && echo '<clickhouse>
  <query_log><database>system</database><table>query_log</table></query_log>
  <query_thread_log><database>system</database><table>query_thread_log</table></query_thread_log>
  <query_views_log><database>system</database><table>query_views_log</table></query_views_log>
  <metric_log><database>system</database><table>metric_log</table></metric_log>
  <asynchronous_metric_log><database>system</database><table>asynchronous_metric_log</table></asynchronous_metric_log>
</clickhouse>' > ./config.d/query_logs.xml
```

## Start the server

```bash
./clickhouse server
```

Open your browser at http://localhost:8123/clickstack

## Create a Log Source (query_log example)

A connection to the local instance is created automatically. On a fresh install you'll be prompted to create a source. Example for `system.query_log`:

| Setting | Value |
|---------|-------|
| Name | Query Logs |
| Database | system |
| Table | query_log |
| Timestamp Column | event_time |
| Default Select | event_time, query_kind, query, databases, tables, initial_user, projections, memory_usage, written_rows, read_rows, query_duration_ms |

Save the source — query logs will appear immediately in the search view.

## Next steps (production-ready options)

| Option | Description |
|--------|-------------|
| [All-in-One](https://clickhouse.com/docs/clickstack/deployment/oss) | Single container with all components, persistence, and auth |
| [Docker Compose](https://clickhouse.com/docs/clickstack/deployment/oss) | Individual components for more control |
| [Helm](https://clickhouse.com/docs/clickstack/deployment/oss) | Recommended for production Kubernetes deployments |
| [Managed ClickStack](https://clickhouse.com/cloud) | Fully managed on ClickHouse Cloud |

---

Content was rephrased for compliance with licensing restrictions.
