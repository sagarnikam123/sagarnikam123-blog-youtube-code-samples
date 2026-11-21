# ClickStack — Install via Homebrew (macOS)

Install ClickHouse as a macOS cask. Since ClickStack UI is embedded in the binary (26.2+), this gives you ClickStack with a single `brew install`.

> Source: [formulae.brew.sh/cask/clickhouse](https://formulae.brew.sh/cask/clickhouse)

## 1. Install ClickHouse

```bash
brew install --cask clickhouse
```

Supports both Apple Silicon and Intel Macs (macOS Big Sur+).

## 2. Start the server

```bash
clickhouse server
```

## 3. Open ClickStack

Navigate to http://localhost:8123/clickstack

## (Optional) Enable system log tables

```bash
mkdir -p config.d && echo '<clickhouse>
  <query_log><database>system</database><table>query_log</table></query_log>
  <query_thread_log><database>system</database><table>query_thread_log</table></query_thread_log>
  <query_views_log><database>system</database><table>query_views_log</table></query_views_log>
  <metric_log><database>system</database><table>metric_log</table></metric_log>
  <asynchronous_metric_log><database>system</database><table>asynchronous_metric_log</table></asynchronous_metric_log>
</clickhouse>' > ./config.d/query_logs.xml
```

Restart the server and create a Log Source for `system.query_log` (see [binary/standalone README](../standalone/README.md) for the source config table).

---

Content was rephrased for compliance with licensing restrictions.
