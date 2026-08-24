terraform {
  required_version = ">= 1.5.0"

  required_providers {
    signoz = {
      source  = "SigNoz/signoz"
      version = "~> 0.1"
    }
  }
}
