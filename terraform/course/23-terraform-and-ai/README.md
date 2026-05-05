# Module 23 — Terraform + Local AI (Ollama)

## Overview

This module connects Terraform with a locally running AI model via Ollama. No cloud API keys, no billing — everything runs on your machine.

You'll learn two real patterns:
1. **Using the `http` data source** to call REST APIs from Terraform (applies to ANY API, not just AI)
2. **Using the `external` data source** to run scripts that interact with Ollama
3. **Deploying Ollama itself** as Docker infrastructure managed by Terraform

## Prerequisites

```bash
# Install Ollama
brew install ollama    # macOS
# or: https://ollama.com/download

# Start Ollama server
ollama serve

# Pull a small model (in a separate terminal)
ollama pull llama3.2:1b    # ~1.3 GB, runs on any machine
# or even smaller:
ollama pull tinyllama       # ~637 MB

# Verify it's running
curl http://localhost:11434/api/tags
```

## Ollama API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/tags` | List installed models |
| `POST` | `/api/generate` | Generate text (completion) |
| `POST` | `/api/chat` | Chat with a model |
| `POST` | `/api/embed` | Generate embeddings |
| `GET` | `/api/ps` | List running models |
| `POST` | `/api/show` | Show model details |
| `POST` | `/api/pull` | Pull a model |

## Why This Matters

The pattern of calling external APIs from Terraform is used everywhere in production:
- Fetching secrets from Vault
- Querying a CMDB for IP ranges
- Calling a compliance API before provisioning
- Registering resources in a service catalog

Ollama is just a fun, free way to learn the pattern.

## Official Docs

- [Ollama API Reference](https://docs.ollama.com/api/introduction)
- [Ollama Models Library](https://ollama.com/library)
- [Terraform HTTP Data Source](https://registry.terraform.io/providers/hashicorp/http/latest/docs/data-sources/http)
- [Terraform External Data Source](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external)
- [Docker Provider](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Query Ollama API](./01-query-ollama/) | Use http data source to list models and get AI responses |
| 2 | [AI-Generated Configs](./02-ai-generated-configs/) | Use external data source + script to generate configs with AI |
| 3 | [Deploy Ollama with Docker](./03-deploy-ollama-docker/) | Deploy Ollama + Open WebUI as Docker infrastructure |
