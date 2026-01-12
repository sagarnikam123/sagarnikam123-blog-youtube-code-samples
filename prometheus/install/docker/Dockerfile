# Dockerfile for Custom Prometheus Image
#
# Builds a custom Prometheus image with baked-in configuration
# Useful for immutable deployments where config is part of the image
#
# Usage:
#   docker build -t my-prometheus:latest .
#   docker build --build-arg PROMETHEUS_VERSION=v2.54.1 -t my-prometheus:v2.54.1 .
#
# Requirements: 2.5

ARG PROMETHEUS_VERSION=v2.54.1

# Use official Prometheus image as base
FROM prom/prometheus:${PROMETHEUS_VERSION}

# Labels for image metadata
LABEL maintainer="DevOps Team"
LABEL description="Custom Prometheus image with baked-in configuration"
LABEL version="${PROMETHEUS_VERSION}"

# Switch to root to copy files
USER root

# Copy custom configuration file
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Copy recording rules (if any)
COPY rules/ /etc/prometheus/rules/

# Copy alerting rules (if any)
COPY alerts/ /etc/prometheus/alerts/

# Set proper ownership
RUN chown -R nobody:nobody /etc/prometheus

# Switch back to nobody user for security
USER nobody

# Expose Prometheus port
EXPOSE 9090

# Default entrypoint from base image handles startup
# Override command to use our baked-in config
ENTRYPOINT [ "/bin/prometheus" ]
CMD [ "--config.file=/etc/prometheus/prometheus.yml", \
      "--storage.tsdb.path=/prometheus", \
      "--web.console.templates=/etc/prometheus/consoles", \
      "--web.console.libraries=/etc/prometheus/console_libraries", \
      "--web.enable-lifecycle" ]
