# Challenge — Variables & Outputs

## Build It Yourself

Create a Terraform configuration that:

1. Accepts these input variables:
   - `project_name` (string, required, no default)
   - `environment` (string, must be one of: dev, staging, prod)
   - `services` (map of objects with `port` and `enabled` fields)
   - `admin_email` (string, must be a valid email format)

2. Uses `locals` to:
   - Build a full project name: `"<project_name>-<environment>"`
   - Filter `services` to only enabled ones
   - Generate a list of URLs for enabled services

3. Creates a `local_file` with a summary of all the above

4. Outputs:
   - The full project name
   - The list of enabled service names
   - The admin email (marked sensitive)

## Expected Behavior

```bash
terraform plan -var 'project_name=myapp' -var 'environment=prod'
# Should show: 1 local_file to create, 4 outputs

terraform plan -var 'project_name=myapp' -var 'environment=invalid'
# Should FAIL validation

terraform plan -var 'project_name=myapp' -var 'admin_email=not-an-email'
# Should FAIL validation
```

## Rules
- Use only the `local` provider
- All variables must have `description` and `type`
- Use variable validation for `environment` and `admin_email`
- Don't look at the solutions in other exercises until you've tried!

## Verify Your Solution
```bash
terraform init
terraform validate                    # must pass
terraform plan -var 'project_name=myapp'   # must succeed
terraform apply -var 'project_name=myapp'  # creates the file
```
