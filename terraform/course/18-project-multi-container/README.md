# Module 18 — Final Project: Multi-Container Application

## Overview

This project ties together everything from the course. You'll deploy a multi-container application stack using Docker, with:

- A shared Docker network
- An Nginx frontend (reverse proxy)
- An Apache backend (API server)
- A second Nginx instance (docs server)
- All connected on the same network
- Configuration driven by variables
- Reusable modules for network and app

## Architecture

```
┌─────────────────────────────────────────────┐
│              Docker Network                  │
│              (project-net)                    │
│                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ frontend │  │ backend  │  │   docs   │  │
│  │  :9300   │  │  :9301   │  │  :9302   │  │
│  │  nginx   │  │  httpd   │  │  nginx   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

## Usage

```bash
cd 18-project-multi-container

# Initialize
terraform init

# Preview
terraform plan

# Deploy the stack
terraform apply

# Access the services
curl http://localhost:9300   # frontend
curl http://localhost:9301   # backend
curl http://localhost:9302   # docs

# View all outputs
terraform output

# Tear down
terraform destroy
```

## Concepts Used

- Modules (network + app)
- Variables with validation
- for_each
- Dynamic blocks
- Outputs
- Local values
- String templates
- Collection functions
- Lifecycle rules
