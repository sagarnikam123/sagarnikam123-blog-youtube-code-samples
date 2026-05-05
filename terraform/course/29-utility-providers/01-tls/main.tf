# =============================================================================
# Module 29 — Exercise 1: TLS Certificates
# =============================================================================
# Generate private keys, self-signed certificates, and CA chains locally.
# Useful for: dev environments, mTLS between services, K8s secrets.
#
# No external dependencies — everything is generated in-memory.
# =============================================================================

terraform {
  required_version = ">= 1.15.0"

  required_providers {
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "tls" {}
provider "local" {}

# --- Generate a CA (Certificate Authority) ---
resource "tls_private_key" "ca" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "tls_self_signed_cert" "ca" {
  private_key_pem = tls_private_key.ca.private_key_pem

  subject {
    common_name  = "Terraform Course CA"
    organization = "Terraform Learning"
    country      = "IN"
  }

  validity_period_hours = 87600 # 10 years
  is_ca_certificate     = true

  allowed_uses = [
    "cert_signing",
    "crl_signing",
  ]
}

# --- Generate a server certificate signed by the CA ---
resource "tls_private_key" "server" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_cert_request" "server" {
  private_key_pem = tls_private_key.server.private_key_pem

  subject {
    common_name  = "localhost"
    organization = "Terraform Learning"
  }

  dns_names    = ["localhost", "*.local.dev", "api.local.dev"]
  ip_addresses = ["127.0.0.1"]
}

resource "tls_locally_signed_cert" "server" {
  cert_request_pem   = tls_cert_request.server.cert_request_pem
  ca_private_key_pem = tls_private_key.ca.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca.cert_pem

  validity_period_hours = 8760 # 1 year

  allowed_uses = [
    "digital_signature",
    "key_encipherment",
    "server_auth",
  ]
}

# --- Generate a client certificate (for mTLS) ---
resource "tls_private_key" "client" {
  algorithm = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_cert_request" "client" {
  private_key_pem = tls_private_key.client.private_key_pem

  subject {
    common_name  = "app-client"
    organization = "Terraform Learning"
  }
}

resource "tls_locally_signed_cert" "client" {
  cert_request_pem   = tls_cert_request.client.cert_request_pem
  ca_private_key_pem = tls_private_key.ca.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca.cert_pem

  validity_period_hours = 720 # 30 days

  allowed_uses = [
    "digital_signature",
    "client_auth",
  ]
}

# --- Write certificates to files ---
resource "local_file" "ca_cert" {
  filename = "${path.module}/output/ca.pem"
  content  = tls_self_signed_cert.ca.cert_pem
}

resource "local_file" "server_cert" {
  filename = "${path.module}/output/server.pem"
  content  = tls_locally_signed_cert.server.cert_pem
}

resource "local_file" "server_key" {
  filename        = "${path.module}/output/server-key.pem"
  content         = tls_private_key.server.private_key_pem
  file_permission = "0600"
}

# --- Outputs ---
output "ca_subject" {
  value = tls_self_signed_cert.ca.subject[0].common_name
}

output "server_dns_names" {
  value = tls_cert_request.server.dns_names
}

output "server_validity" {
  value = "${tls_locally_signed_cert.server.validity_period_hours} hours"
}

output "client_algorithm" {
  value = tls_private_key.client.algorithm
}

output "files_created" {
  value = [
    local_file.ca_cert.filename,
    local_file.server_cert.filename,
    local_file.server_key.filename,
  ]
}

output "verify_cert" {
  value = "openssl x509 -in output/server.pem -text -noout"
}
