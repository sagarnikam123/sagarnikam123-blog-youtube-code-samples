# File-based Service Discovery

This directory contains target files for Prometheus file-based service discovery (`file_sd_configs`).

## Requirements

- **Requirement 5.2**: Support file_sd_configs for file-based service discovery

## Usage

Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'file-sd-targets'
    file_sd_configs:
      - files:
          - '/etc/prometheus/file-sd/*.json'
        # How often to re-read the files
        refresh_interval: 30s
```

## File Format

Target files must be valid JSON arrays with the following structure:

```json
[
  {
    "targets": ["host1:port", "host2:port"],
    "labels": {
      "label_name": "label_value"
    }
  }
]
```

## Dynamic Updates

- Prometheus automatically detects changes to target files
- No restart required when targets are added/removed
- Use `refresh_interval` to control how often files are re-read

## Best Practices

1. Use separate files for different services or environments
2. Include meaningful labels for filtering and grouping
3. Use automation tools (Ansible, Terraform) to generate target files
4. Store target files in a shared location accessible by Prometheus
