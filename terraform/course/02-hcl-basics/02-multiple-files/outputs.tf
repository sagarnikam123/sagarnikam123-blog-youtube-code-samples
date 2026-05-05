# =============================================================================
# outputs.tf — Output value declarations
# =============================================================================

output "random_hex" {
  description = "The generated random hex ID"
  value       = random_id.example.hex
}

output "file_path" {
  description = "Path to the generated config file"
  value       = local_file.config.filename
}
