# flog - Fake Log Generator

Uses [mingrammer/flog](https://github.com/mingrammer/flog) to generate fake log data for Loki testing.

## What is flog?

A fake log generator for common log formats:
- **Formats**: Apache Common, Apache Combined, Apache Error, RFC3164, RFC5424, JSON
- **Output**: stdout, file
- **Rate**: Configurable delay between logs
- **Volume**: Configurable number of logs

**Perfect for:**
- Load testing log ingestion
- Testing parsers
- Simulating realistic log patterns
- Stress testing with high volume

## Quick Start

### 1. Docker (Recommended)

```bash
# Generate JSON logs continuously
docker run -d --name flog \
  mingrammer/flog -f json -l -d 100ms

# Generate Apache logs to file
docker run -d --name flog \
  -v $(pwd)/logs:/logs \
  mingrammer/flog -f apache_combined -o /logs/access.log -l -d 50ms
```

### 2. Binary Installation

```bash
# macOS
brew install flog

# Linux
go install github.com/mingrammer/flog@latest

# Run
flog -f json -l -d 100ms
```

## Configuration Examples

### JSON Logs (100 lines/sec)

```bash
flog -f json -l -d 10ms
```

Output:
```json
{"host":"238.38.137.221","user":"-","method":"DELETE","path":"/innovate/e-commerce","code":503,"size":4924,"referer":"https://www.dynamicvisionary.io/synergize/e-commerce/synergize","agent":"Mozilla/5.0"}
```

### Apache Combined Logs

```bash
flog -f apache_combined -l -d 50ms
```

Output:
```
192.168.1.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /apache_pb.gif HTTP/1.0" 200 2326 "http://www.example.com/start.html" "Mozilla/4.08 [en] (Win98; I ;Nav)"
```

### RFC5424 Syslog

```bash
flog -f rfc5424 -l -d 100ms
```

Output:
```
<34>1 2024-01-06T12:00:00.000Z mymachine.example.com su - ID47 - 'su root' failed for lonvick on /dev/pts/8
```

### Write to File

```bash
# Generate 1 million logs to file
flog -f json -n 1000000 -o /tmp/test.log

# Continuous to file
flog -f json -l -o /tmp/continuous.log -d 10ms
```

### High Volume Testing

```bash
# 1000 logs/sec (1ms delay)
flog -f json -l -d 1ms

# 10000 logs/sec (0.1ms delay)
flog -f json -l -d 100us

# Burst: 100K logs as fast as possible
flog -f json -n 100000
```

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-f` | Log format | apache_combined |
| `-o` | Output file (default: stdout) | - |
| `-n` | Number of logs to generate | 1000 |
| `-l` | Loop forever | false |
| `-d` | Delay between logs | 0 |
| `-b` | Bytes per log line | 0 (random) |
| `-w` | Number of workers | 1 |

## Log Formats

| Format | Description |
|--------|-------------|
| `apache_common` | Apache Common Log Format |
| `apache_combined` | Apache Combined Log Format |
| `apache_error` | Apache Error Log Format |
| `rfc3164` | RFC3164 Syslog |
| `rfc5424` | RFC5424 Syslog |
| `json` | JSON format |

## Integration with Fluent Bit

```yaml
# fluent-bit-flog.yaml
pipeline:
  inputs:
    - name: tail
      path: /tmp/flog.log
      tag: flog
      parser: json
      db: /tmp/fb-flog.db

  outputs:
    - name: loki
      match: "*"
      host: localhost
      port: 3100
      labels: job=flog, format=json
```

Run:
```bash
# Start flog
flog -f json -l -o /tmp/flog.log -d 10ms &

# Start Fluent Bit
fluent-bit -c fluent-bit-flog.yaml
```

## Integration with Promtail

```yaml
# promtail-flog.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: flog
    static_configs:
      - targets:
          - localhost
        labels:
          job: flog
          __path__: /tmp/flog.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            method: method
            code: code
      - labels:
          level:
          method:
```

## Test Scenarios

### 1. Steady Load (100 logs/sec)
```bash
flog -f json -l -d 10ms -o /tmp/steady.log
```

### 2. High Volume (1000 logs/sec)
```bash
flog -f json -l -d 1ms -o /tmp/high.log
```

### 3. Burst Test (100K logs)
```bash
flog -f json -n 100000 -o /tmp/burst.log
```

### 4. Large Logs
```bash
# ~1KB per log
flog -f json -l -d 100ms -b 1024 -o /tmp/large.log
```

## Cleanup

```bash
# Stop Docker container
docker stop flog && docker rm flog

# Remove log files
rm -f /tmp/flog*.log
```

## Resources

- [flog GitHub](https://github.com/mingrammer/flog)
- [Docker Hub](https://hub.docker.com/r/mingrammer/flog)
