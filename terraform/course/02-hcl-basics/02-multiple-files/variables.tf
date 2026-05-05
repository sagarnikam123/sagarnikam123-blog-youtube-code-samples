# =============================================================================
# variables.tf — Input variable declarations
# =============================================================================

variable "author" {
  description = "Author name for the generated file"
  type        = string
  default     = "Terraform Learner"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "learning"
}
