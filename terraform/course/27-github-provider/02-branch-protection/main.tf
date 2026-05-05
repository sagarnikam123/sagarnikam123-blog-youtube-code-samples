# =============================================================================
# Module 27 — Exercise 2: Branch Protection
# =============================================================================
# Enforce branch protection rules — PR reviews, status checks, etc.
#
# Note: Branch protection requires the repo to exist first.
# Run exercise 01 first, or this creates its own repo.
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

provider "github" {}

# --- Create a repo to protect ---
resource "github_repository" "protected" {
  name        = "terraform-protected-demo"
  description = "Demo repo with branch protection via Terraform"
  visibility  = "public"
  auto_init   = true

  has_issues             = true
  delete_branch_on_merge = true
  allow_squash_merge     = true
  allow_merge_commit     = false
  allow_rebase_merge     = false
}

# --- Branch Protection: main ---
resource "github_branch_protection" "main" {
  repository_id = github_repository.protected.node_id
  pattern       = "main"

  # Require PR reviews
  required_pull_request_reviews {
    required_approving_review_count = 1
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = false
  }

  # Require status checks to pass
  required_status_checks {
    strict   = true # Branch must be up-to-date before merging
    contexts = ["ci/terraform-plan", "ci/lint"]
  }

  # Enforce for admins too
  enforce_admins = true

  # Require signed commits
  require_signed_commits = false

  # Require linear history (no merge commits)
  required_linear_history = true

  # Allow force pushes? No!
  allows_force_pushes = false

  # Allow deletions? No!
  allows_deletions = false
}

# --- Branch Protection: release/* ---
resource "github_branch_protection" "release" {
  repository_id = github_repository.protected.node_id
  pattern       = "release/*"

  required_pull_request_reviews {
    required_approving_review_count = 2
    dismiss_stale_reviews           = true
  }

  enforce_admins      = true
  allows_force_pushes = false
  allows_deletions    = false
}

# --- Outputs ---
output "repository_url" {
  value = github_repository.protected.html_url
}

output "protected_branches" {
  value = ["main", "release/*"]
}

output "main_rules" {
  value = {
    required_reviews     = 1
    dismiss_stale        = true
    require_status       = ["ci/terraform-plan", "ci/lint"]
    enforce_admins       = true
    linear_history       = true
    allow_force_push     = false
  }
}
