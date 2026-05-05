# =============================================================================
# Tests for the final project
# =============================================================================
# Run: terraform test
# =============================================================================

# Test default configuration
run "default_config" {
  command = plan

  assert {
    condition     = output.project_name == "final-project-dev"
    error_message = "Default project name should be 'final-project-dev'"
  }
}

# Test custom environment
run "staging_config" {
  command = plan

  variables {
    environment = "staging"
  }

  assert {
    condition     = output.project_name == "final-project-staging"
    error_message = "Staging project name should be 'final-project-staging'"
  }
}

# Test invalid environment
run "invalid_environment" {
  command = plan

  variables {
    environment = "invalid"
  }

  expect_failures = [
    var.environment,
  ]
}
