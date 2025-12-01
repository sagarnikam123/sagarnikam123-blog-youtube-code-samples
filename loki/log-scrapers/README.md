# Log Scrapers Configuration

Configuration files for various log scrapers that send logs to Loki.

## Directory Structure

```
log-scrapers/
├── fluent-bit/     # Fluent Bit configurations
├── vector/         # Vector.dev configurations
├── alloy/          # Grafana Alloy configurations
└── README.md       # This file
```

## Supported Log Scrapers

### Fluent Bit
- **Purpose**: Lightweight log processor and forwarder
- **Config Location**: `fluent-bit/`
- **File Format**: `.conf` or `.yaml`
- **Installation**: OS-dependent - [Getting Started Guide](https://docs.fluentbit.io/manual/installation/getting-started-with-fluent-bit)
- **GitHub**: [Releases](https://github.com/fluent/fluent-bit/releases)
- **Documentation**: https://docs.fluentbit.io/

### Vector.dev
- **Purpose**: High-performance observability data pipeline
- **Config Location**: `vector/`
- **File Format**: `.yaml` or `.toml`
- **Installation**: OS-dependent - [Installation Guide](https://vector.dev/docs/setup/installation/)
- **GitHub**: [Releases](https://github.com/vectordotdev/vector/releases)
- **Documentation**: https://vector.dev/docs/

### Grafana Alloy
- **Purpose**: OpenTelemetry collector distribution
- **Config Location**: `alloy/`
- **File Format**: `.alloy` or `.yaml`
- **Installation**: OS-dependent - [Installation Guide](https://grafana.com/docs/alloy/latest/set-up/install/)
- **GitHub**: [Releases](https://github.com/grafana/alloy/releases)
- **Documentation**: https://grafana.com/docs/alloy/

## Usage

After running `./install.sh`, configurations will be copied to:
```
~/loki-stack/log-scrapers/
├── fluent-bit/
├── vector/
└── alloy/
```

## Example Configurations

Each subdirectory should contain:
- Configuration files for the respective log scraper
- Example configurations for common use cases
- Documentation specific to that scraper

## Integration with Loki

All configurations should be set up to send logs to:
- **Loki URL**: `http://127.0.0.1:3100/loki/api/v1/push`
- **Format**: JSON or Protobuf
- **Labels**: Appropriate labels for log identification
