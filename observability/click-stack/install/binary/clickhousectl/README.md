# ClickStack — Install via clickhousectl

The ClickHouse CLI (`clickhousectl`) manages local ClickHouse versions, launches servers, and runs queries. Since ClickStack UI is embedded in the ClickHouse binary (26.2+), installing via `clickhousectl` gives you ClickStack out of the box.

> Source: [Install with the ClickHouse CLI](https://clickhouse.com/docs/get-started/setup/self-managed/clickhousectl)

## 1. Install the ClickHouse CLI

```bash
curl https://clickhouse.com/cli | sh
```

A `chctl` alias is created automatically.

## 2. Install ClickHouse

```bash
clickhousectl local use latest
```

This installs the latest version, sets it as default, and creates a `clickhouse` symlink in `~/.local/bin`.

Specific version:

```bash
clickhousectl local use 26.5            # Latest 26.5.x.x
clickhousectl local use 26.5.2.39       # Exact version
```

> `local use` installs + sets default. Use `local install <version>` to download without changing your default.

## 3. Start the server

```bash
clickhousectl local server start
```

Verify it's running:

```bash
clickhousectl local server list
```

## 4. Open ClickStack

Navigate to http://localhost:8123/clickstack

## 5. (Optional) Start the client

```bash
clickhousectl local client
```

## (Optional) Enable system log tables

To observe ClickHouse internals via ClickStack, create a config snippet before starting:

```bash
mkdir -p config.d && echo '<clickhouse>
  <query_log><database>system</database><table>query_log</table></query_log>
  <query_thread_log><database>system</database><table>query_thread_log</table></query_thread_log>
  <query_views_log><database>system</database><table>query_views_log</table></query_views_log>
  <metric_log><database>system</database><table>metric_log</table></metric_log>
  <asynchronous_metric_log><database>system</database><table>asynchronous_metric_log</table></asynchronous_metric_log>
</clickhouse>' > ./config.d/query_logs.xml
```

Then restart the server and create a Log Source for `system.query_log` (see [binary/standalone README](../standalone/README.md) for the source config table).

---

Content was rephrased for compliance with licensing restrictions.
