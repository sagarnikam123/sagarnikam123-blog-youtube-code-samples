# =============================================================================
# Terraform Test File
# =============================================================================
# Run with: terraform test
# =============================================================================

# Test 1: Default values produce valid output
run "defaults" {
  command = plan

  assert {
    condition     = local_file.config.filename == "${path.module}/output/dev-config.txt"
    error_message = "Default environment should be 'dev'"
  }

  assert {
    condition     = output.environment == "dev"
    error_message = "Default environment output should be 'dev'"
  }
}

# Test 2: Production configuration
run "production" {
  command = plan

  variables {
    environment = "prod"
    app_name    = "myapp"
    port        = 8080
  }

  assert {
    condition     = output.environment == "prod"
    error_message = "Environment should be 'prod'"
  }

  assert {
    condition     = output.port == 8080
    error_message = "Port should be 8080"
  }
}

# Test 3: Invalid environment should fail validation
run "invalid_environment" {
  command = plan

  variables {
    environment = "invalid"
  }

  expect_failures = [
    var.environment,
  ]
}

# Test 4: Invalid port should fail validation
run "invalid_port" {
  command = plan

  variables {
    port = 80
  }

  expect_failures = [
    var.port,
  ]
}

# Test 5: Apply and verify (creates real resources)
run "apply_and_verify" {
  command = apply

  variables {
    environment = "dev"
    app_name    = "test-app"
    port        = 9999
  }

  assert {
    condition     = output.environment == "dev"
    error_message = "Applied environment should be 'dev'"
  }

  assert {
    condition     = output.config_file != ""
    error_message = "Config file path should not be empty"
  }
}
