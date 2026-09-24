# sagarnikam123-blog-youtube-code-samples

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Blog](https://img.shields.io/badge/Blog-sagarnikam123.github.io-0075ca.svg?logo=rss&logoColor=white)](https://sagarnikam123.github.io/)
[![YouTube](https://img.shields.io/badge/YouTube-Sagar%20Nikam-FF0000.svg?logo=youtube&logoColor=white)](https://www.youtube.com/sagarnikam123)
[![Domain: DevOps & Observability](https://img.shields.io/badge/domain-DevOps%20%26%20Observability-7057ff.svg)](#-projects)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Installation Matrix](https://img.shields.io/badge/guide-Installation%20Matrix-0A9EDC.svg)](INSTALLATION-MATRIX.md)
[![Status: Maintained](https://img.shields.io/badge/status-actively%20maintained-success.svg)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/sagarnikam123/sagarnikam123-blog-youtube-code-samples/pulls)

A curated collection of production-ready code samples, automation frameworks, and DevOps projects shared through my blog and YouTube tutorials.

## 🔗 Links

- 📝 **Blog**: [https://sagarnikam123.github.io/](https://sagarnikam123.github.io/)
- 🎥 **YouTube**: [https://www.youtube.com/sagarnikam123](https://www.youtube.com/sagarnikam123)

## 📋 Projects

### 🔍 Observability
- **[loki/](loki/)** - Grafana Loki deployment configurations for log aggregation.
- **[mimir/](mimir/)** - Grafana Mimir deployment configurations for long-term metrics storage.
- **[prometheus/](prometheus/)** - Prometheus deployment and configuration.

### 🤖 Automation & Infrastructure
- **[grafana-automation/](grafana-automation/)** - Complete Ansible automation framework for managing Grafana resources with full CRUD operations, multienvironment support, and production-ready security practices.

### 📊 Analytics & Development Tools
- **[utilities/github-analysis/](utilities/github-analysis/)** - Comprehensive GitHub repository analysis tool with 7 analysis types (issues, commits, contributors, releases, pulls, compare, health) supporting 4 export formats (CSV, JSON, Excel, Markdown) for data-driven insights and repository management.

### 📦 Observability Installation Guide
- **[INSTALLATION-MATRIX.md](INSTALLATION-MATRIX.md)** - Installation modes, benchmark paths, and reusable platform coverage.
- **[benchmark/](benchmark/)** - Controlled benchmark deployments and OTLP validation.
- **[signoz/](signoz/)**, **[open-observe/](open-observe/)**, **[click-stack/](click-stack/)**, **[grafana-lgtm/](grafana-lgtm/)**, **[victoria-metrics/](victoria-metrics/)**, **[uptrace/](uptrace/)**, **[parseable/](parseable/)** - Phase 1 benchmark platforms.
- **[coroot/](coroot/)**, **[elastic-observability/](elastic-observability/)**, **[opensearch-observability/](opensearch-observability/)**, **[one-uptime/](one-uptime/)**, **[highlight-io/](highlight-io/)** - Phase 2 and extended platform deployments.

### ⏱️ Uptime Monitoring

Self-hosted uptime / status-page tools compared in the [open-source uptime monitoring guide](https://sagarnikam123.github.io/):

- **[uptime-kuma/](uptime-kuma/)** - UI-first monitor (Docker, Compose, Node.js binary, community Helm).
- **[gatus/](gatus/)** - Config-as-code probe engine (binary, Docker, Compose, K8s, official Helm).
- **[open-status/](open-status/)** - Monitoring-as-code + status pages (official Docker Compose full stack, status-page-only, private-location probe).
- **[one-uptime/](one-uptime/)** - Full reliability platform (uptime + incidents + on-call + OTel).
