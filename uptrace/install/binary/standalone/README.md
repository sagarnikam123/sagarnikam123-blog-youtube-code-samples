# Uptrace — binary standalone

Uptrace publishes DEB/RPM packages and precompiled binaries for Linux, macOS, and Windows. The binary requires ClickHouse, PostgreSQL, and Redis; those dependencies are not bundled in this mode.

## Linux binary example

```bash
VERSION=2.0.3
curl -L -o uptrace "https://github.com/uptrace/uptrace/releases/download/v${VERSION}/uptrace_linux_amd64"
chmod +x uptrace
./uptrace --config=/path/to/uptrace.yml config create
./uptrace --config=/path/to/uptrace.yml pg init
./uptrace --config=/path/to/uptrace.yml ch init
./uptrace --config=/path/to/uptrace.yml db seed
./uptrace --config=/path/to/uptrace.yml serve
```

Use the matching release artifact for macOS or Windows and configure database addresses for the host environment. For clustered ClickHouse, run `ch dist` after initialization.

Official guide: [Installing Uptrace](https://uptrace.dev/get/hosted/install).
