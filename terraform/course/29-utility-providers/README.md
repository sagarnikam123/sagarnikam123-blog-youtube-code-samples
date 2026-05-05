# Module 29 — Utility Providers (TLS, Archive, Time, DNS)

## Overview

These are small but useful providers that solve specific problems. They're often combined with other providers in real-world configs.

## Providers in This Module

| Provider | Source | What It Does |
|----------|--------|-------------|
| **TLS** | `hashicorp/tls` | Generate private keys, self-signed certs, CSRs locally |
| **Archive** | `hashicorp/archive` | Create zip/tar files from source code (used with Lambda, Cloud Functions) |
| **Time** | `hashicorp/time` | Time-based resources — delays, offsets, rotation triggers |
| **DNS** | `hashicorp/dns` | Read-only DNS lookups as data sources |

## Official Docs

- [TLS Provider](https://registry.terraform.io/providers/hashicorp/tls/latest/docs)
- [Archive Provider](https://registry.terraform.io/providers/hashicorp/archive/latest/docs)
- [Time Provider](https://registry.terraform.io/providers/hashicorp/time/latest/docs)
- [DNS Provider](https://registry.terraform.io/providers/hashicorp/dns/latest/docs)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [TLS Certificates](./01-tls/) | Generate keys, self-signed certs, CA chains |
| 2 | [Archive Files](./02-archive/) | Create zip packages from source directories |
| 3 | [Time Resources](./03-time/) | Delays, offsets, rotation schedules |
| 4 | [DNS Lookups](./04-dns/) | Query DNS records as data sources |
