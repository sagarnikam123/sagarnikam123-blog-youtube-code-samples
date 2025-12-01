# Loki 3.x Configurations

Latest Loki 3.x monolithic configurations with new features.

## Available Configurations

- `loki-3.x.x-filesystem-inmemory-config.yaml` - Filesystem storage with in-memory components
- `loki-3.x.x-s3-inmemory-config.yaml` - S3 storage with in-memory components  
- `loki-3.x.x-ui-minimal-config.yaml` - Minimal UI configuration

## New Features

- Enhanced performance
- Improved query engine
- Better caching mechanisms
- Pattern ingester support
- Block builder optimizations

## Usage

```bash
# Start Loki with specific config
loki -config.file=loki-3.x.x-s3-inmemory-config.yaml
```

## Configuration Reference

- [Loki 3.x Configuration Documentation](https://grafana.com/docs/loki/latest/configure/)
- [Configuration Examples](https://grafana.com/docs/loki/latest/configure/examples/)
- [Storage Configuration](https://grafana.com/docs/loki/latest/configure/storage/)
- [Migration from 2.x](https://grafana.com/docs/loki/latest/setup/upgrade/)

## Notes

- Some features may be experimental
- Check compatibility with your log shippers
- Review breaking changes from 2.x