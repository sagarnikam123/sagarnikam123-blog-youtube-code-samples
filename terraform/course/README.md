# Terraform Complete Course — Zero to Production Ready

> A hands-on Terraform course for DevOps / Platform / Infra engineers.
> **No cloud bills.** Every example runs locally using free providers: Docker, local, null, random, external, http, Kubernetes, and Helm.

### What makes this course different

- **23 modules** from absolute basics to production patterns
- **Every example is runnable** on your laptop — no cloud accounts needed
- **Challenges** in key modules — problem statements with no solutions, forcing you to build from scratch
- **Troubleshooting module** — intentionally broken configs to debug (the skill nobody teaches)
- **Real-world patterns** — tagging, secrets, CI/CD, code review checklists, project structure
- **Terragrunt + Kubernetes + Helm + Ollama AI** — not just toy examples
- **[CHEATSHEET.md](./CHEATSHEET.md)** — single-page quick reference you'll use daily

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Terraform CLI | 1.15.1 | [Install Guide](https://developer.hashicorp.com/terraform/install) |
| Terragrunt | 1.0.2 | [Install Guide](https://terragrunt.gruntwork.io/docs/getting-started/install/) |
| Docker | 29.4.0 | [Docker Install](https://docs.docker.com/get-docker/) |
| Ollama | >= 0.21 | [Ollama Install](https://ollama.com/download) (module 23) |
| Minikube | 1.38.1 | [Minikube Install](https://minikube.sigs.k8s.io/docs/start/) (modules 19-20) |
| kubectl | 1.35.4 | [kubectl Install](https://kubernetes.io/docs/tasks/tools/) (modules 19-20) |
| Helm CLI | 4.1.4 | [Helm Install](https://helm.sh/docs/intro/install/) (module 20) |
| Git | >= 2.x | Pre-installed on most systems |
| A code editor | Any | VS Code recommended with HashiCorp Terraform extension |

---

## Learning Path

```
Modules 01-13:  Docker + utility providers  → Learn Terraform language & core concepts
Modules 14-16:  Docker + utility providers  → Workspaces, CLI mastery, testing
Module  17:     Terragrunt + Docker         → DRY patterns, multi-env management
Module  18:     Docker project              → Tie it all together (capstone #1)
Modules 19-20:  Kubernetes + Helm           → Real-world infrastructure (Minikube)
Module  21:     Broken configs              → Debugging & troubleshooting skills
Module  22:     Patterns & checklists       → Production readiness
Module  23:     Ollama + Docker             → AI infrastructure as code
```

---

## Course Modules

| # | Module | Folder | What You'll Learn |
|---|--------|--------|-------------------|
| 01 | [Introduction & Setup](./01-introduction/) | `01-introduction/` | What is IaC, Terraform overview, installation, first `terraform init` |
| 02 | [HCL Basics & Configuration Syntax](./02-hcl-basics/) | `02-hcl-basics/` | Blocks, arguments, comments, file structure, `.tf` files |
| 03 | [Providers](./03-providers/) | `03-providers/` | Provider configuration, versioning, multiple providers, aliases |
| 04 | [Resources & Data Sources](./04-resources-and-data-sources/) | `04-resources-and-data-sources/` | Resource blocks, data sources, resource behavior, dependencies |
| 05 | [Variables & Outputs](./05-variables-and-outputs/) | `05-variables-and-outputs/` | Input variables, types, defaults, validation, outputs, sensitive values |
| 06 | [Expressions & Operators](./06-expressions/) | `06-expressions/` | Strings, numbers, bools, references, conditionals, `for`, splat |
| 07 | [Built-in Functions](./07-functions/) | `07-functions/` | String, numeric, collection, encoding, filesystem, date/time, type conversion |
| 08 | [State Management](./08-state-management/) | `08-state-management/` | Local state, remote backends, state commands, import, moved, removed |
| 09 | [Modules](./09-modules/) | `09-modules/` | Creating modules, inputs/outputs, local & registry modules, module composition |
| 10 | [Loops & Dynamic Blocks](./10-loops-and-dynamic-blocks/) | `10-loops-and-dynamic-blocks/` | count, for_each, for expressions, dynamic blocks |
| 11 | [Conditionals & Logic](./11-conditionals/) | `11-conditionals/` | Conditional expressions, conditional resources, feature flags |
| 12 | [Lifecycle & Meta-Arguments](./12-lifecycle-meta-arguments/) | `12-lifecycle-meta-arguments/` | lifecycle rules, depends_on, preconditions, postconditions, replace_triggered_by |
| 13 | [Provisioners](./13-provisioners/) | `13-provisioners/` | local-exec, null_resource, terraform_data |
| 14 | [Workspaces](./14-workspaces/) | `14-workspaces/` | CLI workspaces, workspace-based configs, environment separation |
| 15 | [Terraform CLI Deep Dive](./15-cli-deep-dive/) | `15-cli-deep-dive/` | plan, apply, destroy, fmt, validate, console, graph, -replace, output |
| 16 | [Testing & Validation](./16-testing/) | `16-testing/` | `terraform test`, variable validation, preconditions, postconditions, check blocks |
| 17 | [Terragrunt](./17-terragrunt/) | `17-terragrunt/` | DRY configs, remote state, dependency management, Terragrunt 1.0.2 |
| 18 | [Project — Multi-Container App](./18-project-multi-container/) | `18-project-multi-container/` | Full project: Docker network + multiple containers with modules |
| 19 | [Kubernetes with Minikube](./19-kubernetes/) | `19-kubernetes/` | Namespaces, deployments, services, configmaps, secrets on local K8s |
| 20 | [Helm Charts](./20-helm/) | `20-helm/` | Deploy and manage Helm charts via Terraform |
| 21 | [Troubleshooting](./21-troubleshooting/) | `21-troubleshooting/` | Debug intentionally broken configs — cycles, drift, version conflicts |
| 22 | [Real-World Patterns](./22-real-world-patterns/) | `22-real-world-patterns/` | Tagging, secrets, CI/CD, code review, project structure |
| 23 | [Terraform + Local AI](./23-terraform-and-ai/) | `23-terraform-and-ai/` | Query Ollama API, AI-generated configs, deploy Ollama with Docker |

---

## Free Providers Used in This Course

| Provider | Registry Source | What It Does |
|----------|----------------|--------------|
| **Docker** | `kreuzwerker/docker` | Manage Docker images, containers, networks, volumes |
| **local** | `hashicorp/local` | Create local files and read local data |
| **null** | `hashicorp/null` | Do-nothing resources for orchestration patterns |
| **random** | `hashicorp/random` | Generate random values (strings, IDs, passwords, integers) |
| **external** | `hashicorp/external` | Run external scripts and consume JSON output |
| **http** | `hashicorp/http` | Make HTTP requests as data sources |
| **terraform_data** | Built-in | Replacement for null_resource (Terraform 1.4+) |
| **Kubernetes** | `hashicorp/kubernetes` | Manage K8s namespaces, deployments, services, configmaps, secrets |
| **Helm** | `hashicorp/helm` | Deploy and manage Helm charts on Kubernetes |

---

## How to Use This Course

```bash
# Clone the repo
git clone <repo-url>
cd terraform

# Go to any module
cd 01-introduction/01-hello-terraform

# Standard workflow for every example
terraform init      # Download providers
terraform plan      # Preview changes
terraform apply     # Create resources
terraform destroy   # Clean up
```

Each module has its own `README.md` with theory, and sub-folders with runnable code examples.

Modules 05, 07, 09, 10, and 19 also have a `challenge/` folder with "build it yourself" problems — no solutions provided, just requirements and expected behavior.

---

## Quick Reference

- **[CHEATSHEET.md](./CHEATSHEET.md)** — Single-page reference for all commands, functions, and patterns
- [Terraform Docs](https://developer.hashicorp.com/terraform/docs)
- [Terraform Language Reference](https://developer.hashicorp.com/terraform/language)
- [Terraform Registry](https://registry.terraform.io/)
- [Docker Provider Docs](https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs)
- [Kubernetes Provider Docs](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs)
- [Helm Provider Docs](https://registry.terraform.io/providers/hashicorp/helm/latest/docs)
- [Terragrunt Docs](https://terragrunt.gruntwork.io/docs/)

---

**License:** MIT — use freely for learning and teaching.
