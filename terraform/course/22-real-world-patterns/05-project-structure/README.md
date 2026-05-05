# Pattern 5 — Project Structure

## Small Project (Single Environment)

```
project/
├── main.tf              # Resources
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── providers.tf         # Provider config + versions
├── locals.tf            # Local values
├── data.tf              # Data sources
├── terraform.tfvars     # Variable values (gitignored if sensitive)
└── README.md
```

## Medium Project (Multiple Environments)

```
project/
├── modules/
│   ├── networking/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── database/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf          # Calls modules with dev values
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── README.md
```

## Large Project (Terragrunt)

```
project/
├── modules/                    # Reusable Terraform modules
│   ├── networking/
│   ├── compute/
│   ├── database/
│   └── monitoring/
├── live/                       # Terragrunt live configs
│   ├── root.hcl               # Shared config (provider, backend)
│   ├── dev/
│   │   ├── env.hcl            # Dev-specific variables
│   │   ├── networking/
│   │   │   └── terragrunt.hcl
│   │   ├── compute/
│   │   │   └── terragrunt.hcl
│   │   └── database/
│   │       └── terragrunt.hcl
│   ├── staging/
│   │   ├── env.hcl
│   │   ├── networking/
│   │   │   └── terragrunt.hcl
│   │   └── ...
│   └── prod/
│       ├── env.hcl
│       ├── networking/
│       │   └── terragrunt.hcl
│       └── ...
├── .github/
│   └── workflows/
│       └── terraform.yml      # CI/CD pipeline
├── .gitignore
└── README.md
```

## Key Principles

1. **Modules are reusable** — no environment-specific logic inside modules
2. **Environments are separate** — each has its own state file
3. **DRY with Terragrunt** — shared config in `root.hcl`, env-specific in `env.hcl`
4. **State per component** — networking, compute, database each have separate state (blast radius control)
5. **CI/CD enforced** — no manual applies from laptops
6. **Secrets external** — never in the repo, always from env vars or secret stores

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Better Approach |
|-------------|-------------|-----------------|
| One giant `main.tf` | Unreadable, merge conflicts | Split into logical files |
| Shared state for everything | One bad apply breaks everything | Separate state per component |
| Copy-paste between environments | Drift, inconsistency | Modules + Terragrunt |
| Manual `terraform apply` | No audit trail, human error | CI/CD pipeline |
| `terraform.tfstate` in git | Secrets exposed, merge conflicts | Remote backend (S3, GCS) |
| `depends_on` everywhere | Hides real dependencies | Use implicit references |
