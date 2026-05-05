# Challenge — Modules

## Build It Yourself

Create a reusable module called `web-service` and use it to deploy multiple services.

### Module Requirements (`modules/web-service/`)

The module should:
1. Accept variables: `service_name`, `image`, `external_port`, `environment`, `env_vars` (map)
2. Create a Docker container with the given image and port
3. Add standard labels: `managed_by=terraform`, `environment=<env>`, `service=<name>`
4. Output: `container_name`, `container_id`, `access_url`
5. Validate that `external_port` is between 1024-65535
6. Validate that `service_name` is lowercase alphanumeric with hyphens

### Root Module Requirements

1. Call the `web-service` module 3 times using `for_each` with this map:
   ```hcl
   services = {
     frontend = { image = "nginx:alpine",  port = 9600 }
     backend  = { image = "httpd:alpine",  port = 9601 }
     docs     = { image = "nginx:alpine",  port = 9602 }
   }
   ```

2. Output a map of service name → URL for all services

3. Output a list of all container names

### File Structure
```
challenge/
├── main.tf
├── variables.tf
├── outputs.tf
└── modules/
    └── web-service/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Verify
```bash
terraform init
terraform validate
terraform plan          # should show 3 images + 3 containers
terraform apply
curl http://localhost:9600
curl http://localhost:9601
curl http://localhost:9602
terraform destroy
```
