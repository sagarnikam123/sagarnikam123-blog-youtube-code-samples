# Module 01 — Introduction & Setup

## What is Infrastructure as Code (IaC)?

Infrastructure as Code means managing and provisioning infrastructure through machine-readable configuration files rather than manual processes or interactive tools.

**Benefits:**
- **Version control** — track every change in Git
- **Reproducibility** — same config = same infrastructure, every time
- **Automation** — no manual clicking in consoles
- **Collaboration** — review infra changes in PRs like application code
- **Documentation** — the code IS the documentation

## What is Terraform?

Terraform is an open-source IaC tool by HashiCorp that uses a declarative language (HCL) to define infrastructure. You describe the **desired state**, and Terraform figures out how to get there.

### Core Workflow

```
Write → Plan → Apply
```

1. **Write** — Define resources in `.tf` files
2. **Plan** — `terraform plan` shows what will change
3. **Apply** — `terraform apply` makes it happen

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Provider** | Plugin that talks to an API (Docker, AWS, GCP, etc.) |
| **Resource** | A single piece of infrastructure (a container, a file, a network) |
| **State** | Terraform's record of what it manages (stored in `terraform.tfstate`) |
| **Plan** | A preview of changes Terraform will make |
| **Module** | A reusable package of Terraform configuration |

## Installation

### macOS
```bash
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

### Linux (Ubuntu/Debian)
```bash
wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

### Verify
```bash
terraform -version
```

## Official Docs

- [What is Terraform?](https://developer.hashicorp.com/terraform/intro)
- [Core Workflow](https://developer.hashicorp.com/terraform/intro/core-workflow)
- [Install Terraform](https://developer.hashicorp.com/terraform/install)
- [Get Started — Docker Tutorial](https://developer.hashicorp.com/terraform/tutorials/docker-get-started)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Hello Terraform](./01-hello-terraform/) | First `init`, `plan`, `apply` with a local file |
| 2 | [Hello Docker](./02-hello-docker/) | Run your first Docker container via Terraform |
