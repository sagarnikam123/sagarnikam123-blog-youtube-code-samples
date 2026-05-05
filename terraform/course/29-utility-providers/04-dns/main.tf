# =============================================================================
# Module 29 — Exercise 4: DNS Lookups
# =============================================================================
# Use the DNS provider to query DNS records as data sources.
# Read-only — doesn't create DNS records, just queries them.
#
# Use cases:
# - Validate DNS is configured before deploying
# - Look up service endpoints dynamically
# - Check MX records, TXT records for verification
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    dns = {
      source  = "hashicorp/dns"
      version = "~> 3.4"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "dns" {}
provider "local" {}

# --- Look up A records ---
data "dns_a_record_set" "google" {
  host = "google.com"
}

data "dns_a_record_set" "github" {
  host = "github.com"
}

# --- Look up AAAA records (IPv6) ---
data "dns_aaaa_record_set" "google_ipv6" {
  host = "google.com"
}

# --- Look up MX records ---
data "dns_mx_record_set" "google_mx" {
  domain = "google.com."
}

# --- Look up TXT records ---
data "dns_txt_record_set" "google_txt" {
  host = "google.com"
}

# --- Look up NS records ---
data "dns_ns_record_set" "google_ns" {
  host = "google.com"
}

# --- Write DNS report ---
resource "local_file" "dns_report" {
  filename = "${path.module}/output/dns-report.txt"
  content  = <<-EOT
    === DNS Lookup Report ===

    google.com A records:
    ${join("\n    ", data.dns_a_record_set.google.addrs)}

    github.com A records:
    ${join("\n    ", data.dns_a_record_set.github.addrs)}

    google.com IPv6 (AAAA):
    ${join("\n    ", data.dns_aaaa_record_set.google_ipv6.addrs)}

    google.com MX records:
    ${join("\n    ", [for mx in data.dns_mx_record_set.google_mx.mx : "${mx.preference} ${mx.exchange}"])}

    google.com NS records:
    ${join("\n    ", data.dns_ns_record_set.google_ns.nameservers)}

    --- Use Cases ---
    - Validate DNS before deploying (precondition)
    - Discover service IPs dynamically
    - Verify domain ownership (TXT records)
    - Check mail configuration (MX records)
  EOT
}

# --- Outputs ---
output "google_ips" {
  description = "Google.com A records"
  value       = data.dns_a_record_set.google.addrs
}

output "github_ips" {
  description = "GitHub.com A records"
  value       = data.dns_a_record_set.github.addrs
}

output "google_nameservers" {
  description = "Google.com NS records"
  value       = data.dns_ns_record_set.google_ns.nameservers
}

output "google_mx" {
  description = "Google.com MX records"
  value       = [for mx in data.dns_mx_record_set.google_mx.mx : "${mx.preference} ${mx.exchange}"]
}
