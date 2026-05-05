# =============================================================================
# Module 29 — Exercise 3: Time Resources
# =============================================================================
# Time-based resources for delays, offsets, and rotation schedules.
#
# Use cases:
# - Wait between resource creation steps
# - Calculate expiry dates
# - Trigger secret rotation on a schedule
# - Add timestamps to resource names
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "time" {}
provider "local" {}

# --- time_static: Captures a timestamp at creation ---
# Doesn't change on subsequent applies (unlike timestamp() function)
resource "time_static" "created_at" {}

# --- time_offset: Calculate future/past dates ---
resource "time_offset" "cert_expiry" {
  offset_days = 365 # 1 year from now
}

resource "time_offset" "trial_end" {
  offset_days = 30 # 30 days from now
}

resource "time_offset" "last_week" {
  offset_days = -7 # 7 days ago
}

# --- time_sleep: Wait between operations ---
# Useful when a resource needs time to become ready
resource "time_sleep" "wait_for_propagation" {
  create_duration = "5s" # Wait 5 seconds after creation

  triggers = {
    # Re-trigger when this value changes
    version = "1.0.0"
  }
}

# --- time_rotating: Triggers replacement on a schedule ---
# Use this to force secret rotation
resource "time_rotating" "rotation_30_days" {
  rotation_days = 30
}

resource "time_rotating" "rotation_90_days" {
  rotation_days = 90
}

# --- Practical example: Use rotation to trigger secret regeneration ---
# When time_rotating triggers, anything that depends on it gets recreated
resource "local_file" "time_report" {
  filename = "${path.module}/output/time-report.txt"
  content  = <<-EOT
    === Time Resources Report ===

    Created at:        ${time_static.created_at.rfc3339}
    Cert expires:      ${time_offset.cert_expiry.rfc3339}
    Trial ends:        ${time_offset.trial_end.rfc3339}
    Last week:         ${time_offset.last_week.rfc3339}

    30-day rotation:   ${time_rotating.rotation_30_days.rfc3339}
    90-day rotation:   ${time_rotating.rotation_90_days.rfc3339}

    Sleep duration:    5s (after creation)

    --- Use Cases ---
    time_static:    Immutable timestamp (resource creation date)
    time_offset:    Calculate expiry dates, schedule future events
    time_sleep:     Wait for DNS propagation, API readiness
    time_rotating:  Trigger secret rotation, cert renewal
  EOT
}

# --- Outputs ---
output "created_at" {
  value = time_static.created_at.rfc3339
}

output "cert_expiry" {
  value = time_offset.cert_expiry.rfc3339
}

output "next_30_day_rotation" {
  value = time_rotating.rotation_30_days.rotation_rfc3339
}

output "next_90_day_rotation" {
  value = time_rotating.rotation_90_days.rotation_rfc3339
}
