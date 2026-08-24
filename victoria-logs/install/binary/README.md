# VictoriaLogs PoC — Binary (Local Mac)

The simplest way to run VictoriaLogs locally. Download binaries, run directly on your Mac.

## Prerequisites

- macOS (Apple Silicon or Intel)
- Homebrew (for AlertManager)
- Python 3 (for webhook receiver)

## Step 1: Download Binaries

```bash
# Create a bin directory
mkdir -p bin && cd bin

# --- VictoriaLogs ---
# For Apple Silicon (M1/M2/M3):
curl -L -o victoria-logs.tar.gz \
  https://github.com/VictoriaMetrics/VictoriaLogs/releases/latest/download/victoria-logs-darwin-arm64.tar.gz

# For Intel Mac:
# curl -L -o victoria-logs.tar.gz \
#   https://github.com/VictoriaMetrics/VictoriaLogs/releases/latest/download/victoria-logs-darwin-amd64.tar.gz

tar -xzf victoria-logs.tar.gz
rm victoria-logs.tar.gz

# --- VictoriaMetrics (for recording rule state) ---
curl -L -o victoria-metrics.tar.gz \
  https://github.com/VictoriaMetrics/VictoriaMetrics/releases/latest/download/victoria-metrics-darwin-arm64.tar.gz
tar -xzf victoria-metrics.tar.gz
rm victoria-metrics.tar.gz

# --- vmalert ---
curl -L -o vmalert.tar.gz \
  https://github.com/VictoriaMetrics/VictoriaMetrics/releases/latest/download/vmutils-darwin-arm64.tar.gz
tar -xzf vmalert.tar.gz
rm vmalert.tar.gz
# vmutils contains: vmalert, vmauth, vmbackup, vmrestore, etc.

# --- AlertManager ---
brew install alertmanager

# --- Fluent Bit ---
brew install fluent-bit

# --- flog (fake log generator) ---
brew install flog
# OR use fuzzy-train: git clone https://github.com/sagarnikam123/fuzzy-train.git

cd ..
```

## Step 2: Start All Services

Open separate terminal tabs for each service:

### Terminal 1: VictoriaLogs

```bash
./bin/victoria-logs-prod \
  -storageDataPath=./data/vlogs \
  -retentionPeriod=7d \
  -httpListenAddr=:9428
```

VMUI available at: http://localhost:9428/select/vmui/

### Terminal 2: VictoriaMetrics

```bash
./bin/victoria-metrics-prod \
  -storageDataPath=./data/vm \
  -retentionPeriod=7d \
  -httpListenAddr=:8428
```

### Terminal 3: AlertManager

```bash
alertmanager --config.file=./config/alertmanager.yaml --storage.path=./data/alertmanager
```

AlertManager UI at: http://localhost:9093

### Terminal 4: vmalert

```bash
./bin/vmalert-prod \
  -rule=./config/alert-rules.yaml \
  -datasource.url=http://localhost:9428 \
  -notifier.url=http://localhost:9093 \
  -remoteWrite.url=http://localhost:8428 \
  -remoteRead.url=http://localhost:8428 \
  -rule.defaultRuleType=vlogs \
  -evaluationInterval=30s \
  -httpListenAddr=:8880
```

vmalert UI at: http://localhost:8880

### Terminal 5: Fake Log Generator (flog)

```bash
# Generate JSON logs continuously to a file
mkdir -p ./data/logs
flog -f json -d 2s -l -w -o ./data/logs/app.log
```

OR with fuzzy-train:
```bash
cd fuzzy-train
# Follow fuzzy-train's README to generate logs to ../data/logs/app.log
```

### Terminal 6: Fluent Bit

```bash
fluent-bit -c ./config/fluent-bit.conf
```

### Terminal 7: Webhook Receiver (simulates Teams/OpsGenie)

```bash
python3 ./webhook-receiver.py
```

## Step 3: Verify

1. Open http://localhost:9428/select/vmui/
2. Run query: `*` — should see logs flowing
3. Run query: `{cluster="local-mac-poc"} error` — filter for errors
4. Check http://localhost:8880 — vmalert should show rule evaluations
5. Check webhook receiver terminal — alerts should appear when thresholds are crossed

## Directory Structure After Running

```
binary/
├── bin/                          # Downloaded binaries
│   ├── victoria-logs-prod
│   ├── victoria-metrics-prod
│   └── vmalert-prod
├── config/
│   ├── fluent-bit.conf
│   ├── parsers.conf
│   ├── alert-rules.yaml
│   └── alertmanager.yaml
├── data/                         # Created at runtime
│   ├── vlogs/                    # VictoriaLogs storage
│   ├── vm/                       # VictoriaMetrics storage
│   ├── alertmanager/             # AlertManager state
│   └── logs/                     # Fake logs (flog/fuzzy-train output)
├── webhook-receiver.py
├── start-all.sh                  # Convenience script
└── README.md
```

## Cleanup

```bash
rm -rf ./data    # Remove all stored data
```
