# =============================================================================
# Module 27 — Exercise 1: Repository Management
# =============================================================================
# Create and configure GitHub repositories using Terraform.
#
# Prerequisites:
#   export GITHUB_TOKEN="ghp_your_token_here"
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
#   # Check your GitHub account — repos will be created!
#   terraform destroy    # removes the repos
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  # token is read from GITHUB_TOKEN env var
  # owner is read from GITHUB_OWNER env var (or defaults to authenticated user)
}

# --- Variables ---
variable "repos" {
  description = "Map of repositories to create"
  type = map(object({
    description = string
    visibility  = string
    topics      = list(string)
    has_issues  = bool
    has_wiki    = bool
    auto_init   = bool
  }))
  default = {
    terraform-demo-app = {
      description = "Demo application managed by Terraform"
      visibility  = "public"
      topics      = ["terraform", "demo", "iac"]
      has_issues  = true
      has_wiki    = false
      auto_init   = true
    }
    terraform-demo-infra = {
      description = "Infrastructure code managed by Terraform"
      visibility  = "public"
      topics      = ["terraform", "infrastructure", "devops"]
      has_issues  = true
      has_wiki    = false
      auto_init   = true
    }
    terraform-demo-docs = {
      description = "Documentation site managed by Terraform"
      visibility  = "public"
      topics      = ["terraform", "documentation"]
      has_issues  = false
      has_wiki    = true
      auto_init   = true
    }
  }
}

# --- Create repositories using for_each ---
resource "github_repository" "repos" {
  for_each = var.repos

  name        = each.key
  description = each.value.description
  visibility  = each.value.visibility
  topics      = each.value.topics

  has_issues   = each.value.has_issues
  has_wiki     = each.value.has_wiki
  auto_init    = each.value.auto_init
  has_projects = false

  # Security settings
  vulnerability_alerts             = true
  delete_branch_on_merge           = true
  allow_merge_commit               = false
  allow_squash_merge               = true
  allow_rebase_merge               = true
  squash_merge_commit_title        = "PR_TITLE"
  squash_merge_commit_message      = "PR_BODY"
}

# --- Set default branch ---
resource "github_branch_default" "repos" {
  for_each = github_repository.repos

  repository = each.value.name
  branch     = "main"
}

# --- Add a README file to one repo ---
resource "github_repository_file" "readme" {
  repository = github_repository.repos["terraform-demo-app"].name
  branch     = "main"
  file       = "README.md"
  content    = <<-EOT
    # Terraform Demo App

    This repository was created and is managed by Terraform.

    ## Managed Settings
    - Branch protection: enforced
    - Delete branch on merge: enabled
    - Squash merge: enabled
    - Vulnerability alerts: enabled
  EOT
  commit_message      = "docs: add README via Terraform"
  overwrite_on_create = true
}

# --- Outputs ---
output "repository_urls" {
  description = "URLs of created repositories"
  value = {
    for name, repo in github_repository.repos : name => repo.html_url
  }
}

output "repository_names" {
  value = [for repo in github_repository.repos : repo.name]
}
