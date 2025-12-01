# Fluent Bit Configurations

Fluent Bit configurations for different log collection scenarios.

## Installation

**📋 See [INSTALL.md](INSTALL.md) for detailed installation instructions**

Installation is OS-dependent and highly customizable. The installation guide covers all platforms and methods.

## Available Configurations

### 1. `fluent-bit-tail-logs-with-filesystem-storage.yaml`
**Purpose**: Basic log tailing with filesystem buffering
- **Input**: Tail log files from `/Users/sagar/data/log/logger/*.log`
- **Storage**: Filesystem buffering for reliability
- **Output**: Send to Loki with basic labels
- **Use Case**: Simple log collection with persistence

### 2. `fluent-bit-tail-json-logs-to-loki.yaml`
**Purpose**: JSON log parsing and forwarding
- **Input**: Tail JSON formatted log files
- **Parser**: JSON parser with timestamp handling
- **Output**: Send to Loki with detailed labels
- **Use Case**: Structured JSON log processing

### 3. `fluent-bit-tail-logs-filesystem-buffering.conf`
**Purpose**: Production-ready config with filesystem buffering
- **Input**: Tail logs with filesystem storage type
- **Features**:
  - Filesystem buffering for reliability
  - Storage metrics enabled
  - Retry logic with high retry limit
  - JSON parsing
- **Use Case**: Production log collection with high reliability

### 4. `fluent-bit-loki-canary-logs.conf`
**Purpose**: Loki Canary log collection
- **Input**: Tail Loki Canary generated logs
- **Path**: `/Users/sagar/data/loki-canary/*.log`
- **Features**:
  - Optimized for canary logs
  - Drops single key for clean output
  - Specific labels for canary identification
- **Use Case**: Monitoring Loki health with canary logs

## Usage

### Start Fluent Bit with a config:
```bash
# Basic log tailing
fluent-bit --config fluent-bit-tail-logs-with-filesystem-storage.yaml

# JSON log processing
fluent-bit --config fluent-bit-tail-json-logs-to-loki.yaml

# Production config
fluent-bit --config fluent-bit-tail-logs-filesystem-buffering.conf

# Loki canary monitoring
fluent-bit --config fluent-bit-loki-canary-logs.conf
```

### Configuration Notes:
- **Loki endpoint**: All configs point to `127.0.0.1:3100`
- **HTTP server**: Enabled on port `2020` for metrics
- **Storage paths**: Update paths according to your environment
- **Log paths**: Modify input paths to match your log locations

## Customization

Update the following in configs:
1. **Log paths**: Change `Path` in `[INPUT]` sections
2. **Storage paths**: Update `storage.Path` and `DB` paths
3. **Labels**: Modify Loki labels for your use case
4. **Parsers**: Adjust JSON parser settings for your log format
