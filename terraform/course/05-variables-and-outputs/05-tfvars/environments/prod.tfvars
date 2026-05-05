environment   = "prod"
app_name      = "myapp"
replica_count = 5
enable_debug  = false

tags = {
  managed_by  = "terraform"
  environment = "production"
  cost_center = "operations"
  compliance  = "soc2"
}
