# Module 26 — Terraform Ecosystem & What's Next

## Overview

This module is a reference guide — no exercises, just awareness of the broader Terraform ecosystem. These are tools and alternatives you'll encounter on the job.

---

## OpenTofu — The Open-Source Fork

In August 2023, HashiCorp changed Terraform's license from MPL 2.0 to BSL 1.1 (Business Source License). The community responded by forking Terraform into **OpenTofu** under the Linux Foundation.

| Aspect | Terraform | OpenTofu |
|--------|-----------|----------|
| License | BSL 1.1 (source-available) | MPL 2.0 (truly open-source) |
| CLI command | `terraform` | `tofu` |
| Compatibility | — | Drop-in replacement (same HCL, same providers) |
| Registry | registry.terraform.io | registry.opentofu.org (mirrors Terraform registry) |
| Maintained by | HashiCorp | Linux Foundation + community |

**For learning:** Everything in this course works identically with OpenTofu. Just replace `terraform` with `tofu`.

```bash
# Install OpenTofu
brew install opentofu

# Use it exactly like Terraform
tofu init
tofu plan
tofu apply
```

**Links:**
- [OpenTofu Website](https://opentofu.org/)
- [OpenTofu Documentation](https://opentofu.org/docs/)
- [Migration Guide](https://opentofu.org/docs/intro/migration/)

---

## CDKTF — Cloud Development Kit for Terraform

CDKTF lets you write Terraform configurations in TypeScript, Python, Go, Java, or C# instead of HCL. It generates standard Terraform JSON under the hood.

**TypeScript example:**

```typescript
import { App, TerraformStack } from "cdktf";
import { DockerProvider } from "@cdktf/provider-docker";
import { Container } from "@cdktf/provider-docker/lib/container";

class MyStack extends TerraformStack {
  constructor(scope: App, id: string) {
    super(scope, id);
    new DockerProvider(this, "docker", {});
    new Container(this, "nginx", {
      name: "cdktf-nginx",
      image: "nginx:alpine",
      ports: [{ internal: 80, external: 8080 }],
    });
  }
}
```

**Python example:**

```python
from cdktf import App, TerraformStack
from cdktf_cdktf_provider_docker.provider import DockerProvider
from cdktf_cdktf_provider_docker.container import Container
from cdktf_cdktf_provider_docker.image import Image

class MyStack(TerraformStack):
    def __init__(self, scope, id):
        super().__init__(scope, id)

        DockerProvider(self, "docker")

        nginx_image = Image(self, "nginx_image",
            name="nginx:alpine",
            keep_locally=True,
        )

        Container(self, "nginx",
            name="cdktf-nginx",
            image=nginx_image.image_id,
            ports=[{"internal": 80, "external": 8080}],
        )

app = App()
MyStack(app, "docker-stack")
app.synth()
```

**When to use CDKTF:**
- Your team is stronger in TypeScript/Python than HCL
- You need complex logic that's awkward in HCL (loops over APIs, conditional module composition)
- You want IDE autocomplete and type safety

**When NOT to use CDKTF:**
- Learning Terraform (learn HCL first — it's what 95% of the industry uses)
- Simple infrastructure (HCL is more readable for straightforward configs)
- Team collaboration (most DevOps engineers know HCL, not CDKTF)

**Links:**
- [CDKTF Documentation](https://developer.hashicorp.com/terraform/cdktf)
- [CDKTF Examples](https://github.com/hashicorp/terraform-cdk/tree/main/examples)

---

## CI/CD Automation Tools

### Running Terraform in Pipelines

| Tool | How It Works |
|------|-------------|
| **GitHub Actions** | `.github/workflows/terraform.yml` — see module 22 |
| **GitLab CI** | `.gitlab-ci.yml` with terraform image |
| **`act`** | Run GitHub Actions locally for testing |
| **Atlantis** | Self-hosted, auto-runs `plan` on PRs, `apply` on merge |
| **Spacelift** | SaaS platform for Terraform automation |
| **Terraform Cloud** | HashiCorp's hosted CI/CD for Terraform |
| **env0** | SaaS with cost estimation and policy enforcement |

### `act` — Run GitHub Actions Locally

```bash
# Install
brew install act

# Run your workflow locally
act -W .github/workflows/terraform.yml

# Run a specific job
act -j plan
```

**Links:**
- [act — Run GitHub Actions Locally](https://github.com/nektos/act)
- [Atlantis](https://www.runatlantis.io/)
- [Spacelift](https://spacelift.io/)

---

## Policy as Code

| Tool | Description |
|------|-------------|
| **OPA (Open Policy Agent)** | General-purpose policy engine, works with Terraform plan JSON |
| **Sentinel** | HashiCorp's policy-as-code framework (Terraform Cloud/Enterprise only) |
| **Checkov** | Static analysis for Terraform — security and compliance scanning |
| **tfsec** | Security scanner for Terraform (now part of Trivy) |
| **Trivy** | Comprehensive security scanner including IaC |

```bash
# Scan your Terraform code with Checkov
pip install checkov
checkov -d .

# Scan with Trivy
brew install trivy
trivy config .
```

---

## Terraform Ecosystem Tools

| Tool | Purpose |
|------|---------|
| **Terragrunt** | DRY wrapper (covered in module 17) |
| **Terratest** | Go-based integration testing for Terraform |
| **terraform-docs** | Auto-generate documentation from modules |
| **Infracost** | Cost estimation for Terraform changes |
| **tflint** | Linter for Terraform (catches errors before plan) |
| **pre-commit-terraform** | Git hooks for fmt, validate, docs, tflint |
| **Rover** | Visualize Terraform state and plan |

```bash
# Generate module docs
brew install terraform-docs
terraform-docs markdown table . > README.md

# Lint your code
brew install tflint
tflint --init
tflint

# Estimate costs
brew install infracost
infracost breakdown --path .
```

---

## What to Learn Next

After completing this course, here's the recommended progression:

1. **AWS/GCP/Azure with real accounts** — apply everything you learned to a cloud provider (free tier)
2. **Terratest** — write Go tests that actually provision and verify infrastructure
3. **Policy as Code** — add Checkov/OPA to your CI/CD pipeline
4. **Terraform Cloud/Spacelift** — team collaboration, remote state, policy enforcement
5. **Multi-account/multi-region** — the real complexity of production infrastructure
