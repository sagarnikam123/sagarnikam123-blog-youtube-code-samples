# Module 27 — GitHub Provider

## Overview

Manage GitHub repositories, branch protection, teams, webhooks, and Actions secrets as code. This is one of the most practical Terraform skills — every DevOps team manages GitHub infrastructure.

## Prerequisites

```bash
# Create a Personal Access Token (PAT):
# GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
# Permissions needed: repo (all), admin:org (read), admin:repo_hook

# Set the token as an environment variable
export GITHUB_TOKEN="ghp_your_token_here"

# Or for organization-level resources:
export GITHUB_OWNER="your-org-or-username"
```

## Provider Configuration

```hcl
provider "github" {
  token = var.github_token  # or use GITHUB_TOKEN env var
  owner = var.github_owner  # your username or org
}
```

## Key Resources

| Resource | What It Does |
|----------|-------------|
| `github_repository` | Create/manage repos |
| `github_branch_protection` | Enforce PR reviews, status checks |
| `github_team` | Create teams (org only) |
| `github_team_repository` | Grant team access to repos |
| `github_repository_webhook` | Set up webhooks |
| `github_actions_secret` | Manage Actions secrets |
| `github_branch_default` | Set default branch |
| `github_repository_file` | Commit files to a repo |

## Official Docs

- [GitHub Provider](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [GitHub PAT Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Repository Management](./01-repositories/) | Create repos with settings, topics, visibility |
| 2 | [Branch Protection](./02-branch-protection/) | Enforce PR reviews, status checks, signed commits |
| 3 | [Actions Secrets & Webhooks](./03-actions-secrets/) | Manage CI/CD secrets and webhook integrations |
