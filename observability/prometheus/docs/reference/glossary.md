# Glossary

This glossary defines key terms and concepts used throughout the Prometheus Installation and Testing Framework documentation.

## A

### Active Series
The number of unique time series currently stored in Prometheus's head block. Each unique combination of metric name and label set constitutes one active series.

### AKS (Azure Kubernetes Service)
Microsoft Azure's managed Kubernetes service. One of the supported platforms for deploying and testing Prometheus.

### Alertmanager
A component that handles alerts sent by Prometheus. It manages deduplication, grouping, routing, and notification delivery.

## B

### Binary Installation
Installing Prometheus from pre-compiled binaries directly on a host operating system without containerization.

### Breaking Point
The threshold at which Prometheus fails or experiences significant performance degradation. Identified through stress testing.

## C

### cAdvisor (Container Advisor)
A tool that provides container resource usage and performance metrics. Commonly scraped by Prometheus for container monitoring.

### Cardinality
The number of unique time series in Prometheus. High cardinality (many unique label combinations) can impact performance.

### Chaos Mesh
A cloud-native chaos engineering platform for Kubernetes. Used by the testing framework for chaos tests.

### Chaos Test
Tests that verify Prometheus handles unexpected failures gracefully, such as pod kills, network partitions, and resource pressure.

### Compaction
The process of merging smaller TSDB blocks into larger ones to optimize storage and query performance.

## D

### Deployment Mode
The architecture pattern for Prometheus deployment:
- **Monolithic**: Single Prometheus instance
- **Distributed**: Multiple replicas with federation or Thanos/Mimir integration

### Distributed Prometheus
A Prometheus deployment with multiple replicas, federation, or Thanos/Mimir integration for horizontal scaling and high availability.

### Docker Installation
Running Prometheus as a Docker container, typically using docker-compose for orchestration.

## E

### EKS (Elastic Kubernetes Service)
Amazon Web Services' managed Kubernetes service. One of the supported platforms for deploying and testing Prometheus.

### Endurance Test
Tests that verify Prometheus stability over extended periods (also known as soak tests). Typically run for 24+ hours.

### Exporter
A component that exposes metrics in Prometheus format. Examples include Node Exporter, MySQL Exporter, and Blackbox Exporter.

## F

### Federation
A Prometheus feature that allows one Prometheus server to scrape selected time series from another Prometheus server.

### File-based Service Discovery (file_sd)
A service discovery mechanism where targets are defined in JSON or YAML files that Prometheus watches for changes.

## G

### GKE (Google Kubernetes Engine)
Google Cloud's managed Kubernetes service. One of the supported platforms for deploying and testing Prometheus.

### Grafana
An open-source visualization and analytics platform commonly used with Prometheus for dashboards and alerting.

## H

### Head Block
The in-memory portion of the TSDB where recent samples are stored before being persisted to disk.

### Healthcheck Endpoint
HTTP endpoints (`/-/healthy`, `/-/ready`) that indicate Prometheus's operational status.

### Helm
A package manager for Kubernetes. The framework uses the kube-prometheus-stack Helm chart for Kubernetes deployments.

### Helm Installation
Deploying Prometheus on Kubernetes using the kube-prometheus-stack Helm chart.

## I

### Ingestion Rate
The number of samples Prometheus receives per second from all scrape targets.

### Integration Test
Tests that verify Prometheus works correctly with other components like Alertmanager, Grafana, and exporters.

## K

### k6
A modern load testing tool by Grafana Labs. The primary tool used by the testing framework for HTTP load generation.

### k6 Virtual Users (VUs)
Simulated users in k6 that execute test scripts concurrently.

### kube-prometheus-stack
A Helm chart that deploys a complete monitoring stack including Prometheus, Alertmanager, Grafana, and various exporters.

### kube-state-metrics
A service that generates metrics about the state of Kubernetes objects (deployments, pods, nodes, etc.).

### Kubernetes Service Discovery
Prometheus's ability to automatically discover and scrape targets in a Kubernetes cluster using the kubernetes_sd_config.

## L

### Label
A key-value pair attached to a time series that provides dimensional data for filtering and aggregation.

### Launchd
macOS's service management framework. Used for running Prometheus as a service on macOS.

### Litmus
A cloud-native chaos engineering framework. An alternative to Chaos Mesh for chaos tests.

### Load Test
Tests that simulate realistic production workloads to measure Prometheus performance under load.

### Loki
Grafana's log aggregation system. One of the observability components that can be scraped by Prometheus.

## M

### Metric
A measurement collected by Prometheus, consisting of a metric name, labels, and a value.

### Mimir
Grafana's horizontally scalable, highly available metrics backend. Can be used with Prometheus for long-term storage.

### Minikube
A tool that runs a single-node Kubernetes cluster locally. Used for local development and testing.

### Monolithic Prometheus
A single Prometheus server instance running standalone (binary, Docker, or single-pod Kubernetes deployment).

## N

### Node Exporter
A Prometheus exporter that exposes hardware and OS metrics from *NIX systems.

## O

### OLM (Operator Lifecycle Manager)
A component of the Operator Framework that manages the lifecycle of operators in Kubernetes.

### Operator Installation
Deploying Prometheus using the Prometheus Operator and Custom Resource Definitions (CRDs).

### OpenShift
Red Hat's enterprise Kubernetes platform. Supports Prometheus deployment via OperatorHub.

## P

### PodMonitor
A Kubernetes Custom Resource Definition (CRD) used by the Prometheus Operator to configure direct pod scraping.

### Prometheus API
The HTTP API exposed by Prometheus at `/api/v1/*` endpoints for queries, healthchecks, and management.

### Prometheus Instance
A deployed Prometheus server instance on any supported platform.

### Prometheus Operator
A Kubernetes operator that manages Prometheus deployments using Custom Resource Definitions.

### PromQL
Prometheus Query Language. A functional query language for selecting and aggregating time series data.

### Property-Based Test
A testing approach that verifies properties hold for all valid inputs, using random input generation.

## R

### Recording Rule
A PromQL expression that is evaluated at regular intervals and stored as a new time series.

### Regression Test
Tests that verify Prometheus upgrades don't break existing functionality by comparing behavior across versions.

### Relabel Config
Configuration that modifies labels on targets or metrics during scraping.

### Reliability Test
Tests that verify Prometheus behavior during failures and recoveries, such as restarts and network partitions.

### Remote Write
A Prometheus feature that sends samples to a remote storage backend in real-time.

### Retention
The duration for which Prometheus keeps data before deletion.

## S

### Sample
A single data point in a time series, consisting of a timestamp and a value.

### Sanity Test
Quick validation tests to verify basic Prometheus functionality after deployment.

### Scalability Test
Tests that measure how Prometheus scales with increasing workloads across various dimensions.

### Scrape
The process of Prometheus collecting metrics from a target endpoint.

### Scrape Interval
The frequency at which Prometheus scrapes metrics from targets.

### Scrape Target
An endpoint that Prometheus collects metrics from.

### Security Test
Tests that verify Prometheus security configuration including TLS, authentication, and RBAC.

### ServiceMonitor
A Kubernetes CRD used by the Prometheus Operator to configure service scraping.

### Soak Test
See Endurance Test.

### Static Config
A scrape configuration where targets are explicitly defined rather than discovered dynamically.

### Stress Test
Tests that push Prometheus beyond normal limits to find breaking points and understand failure modes.

### Systemd
Linux's system and service manager. Used for running Prometheus as a service on Linux.

## T

### Tempo
Grafana's distributed tracing backend. One of the observability components that can be scraped by Prometheus.

### Test Framework
The testing infrastructure that executes various test types against Prometheus deployments.

### Test Runner Host
The local laptop/workstation from which all tests are executed, targeting local or remote Prometheus deployments.

### Thanos
A highly available Prometheus setup with long-term storage capabilities. Can be used for distributed Prometheus deployments.

### Time Series
A stream of timestamped values belonging to the same metric and set of labels.

### TSDB (Time Series Database)
Prometheus's built-in storage engine optimized for time series data.

## V

### Vector
A high-performance observability data pipeline. One of the components that can be scraped by Prometheus.

## W

### WAL (Write-Ahead Log)
A log of all incoming samples that haven't been compacted into blocks yet. Used for crash recovery.

### WAL Replay
The process of recovering data from the WAL after a Prometheus restart or crash.

## See Also

- [Architecture](architecture.md) - System architecture overview
- [Metrics Reference](metrics-reference.md) - Prometheus metrics reference
- [Test Types](../testing/test-types.md) - Description of each test type
