# Module 25 — Secrets Management with HashiCorp Vault

## Overview

Vault is the industry standard for secrets management. Running it locally in dev mode gives you a free, zero-config way to practice the `hashicorp/vault` provider and learn patterns you'll use in production.

## Prerequisites

```bash
# Option 1: Install Vault CLI
brew install vault    # macOS

# Start in dev mode (in-memory, auto-unsealed, root token = "root")
vault server -dev -dev-root-token-id="root"

# Option 2: Run via Docker (no install needed)
docker run -d --name vault \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=root \
  -e VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200 \
  hashicorp/vault:latest

# Verify
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="root"
vault status
```

## Vault Provider Configuration

```hcl
provider "vault" {
  address = "http://127.0.0.1:8200"
  token   = "root"  # dev mode only — never hardcode in production!
}
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Secrets Engine** | Backend that stores/generates secrets (KV, database, PKI, AWS) |
| **KV v2** | Key-value store with versioning — most common for static secrets |
| **Dynamic Secrets** | Generated on-demand with a TTL (database creds, AWS keys) |
| **Policies** | Define who can access what paths |
| **Auth Methods** | How clients authenticate (token, AppRole, Kubernetes, OIDC) |

## Why Vault + Terraform?

- **No secrets in state** — Terraform reads from Vault at apply time
- **Rotation** — Vault rotates secrets automatically; Terraform picks up new values
- **Audit** — every secret access is logged
- **Dynamic creds** — Vault generates unique DB passwords per application

## Official Docs

- [Vault Provider](https://registry.terraform.io/providers/hashicorp/vault/latest/docs)
- [Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Vault KV Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/kv/kv-v2)
- [Vault Dev Server](https://developer.hashicorp.com/vault/docs/concepts/dev-server)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [KV Secrets](./01-kv-secrets/) | Write and read key-value secrets |
| 2 | [Policies & Auth](./02-policies-auth/) | Create policies and AppRole authentication |
| 3 | [Dynamic Secrets](./03-dynamic-secrets/) | Generate database credentials on-demand |
