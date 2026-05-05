# Challenge — Loops & Dynamic Blocks

## Build It Yourself

Create a configuration that deploys a configurable set of Docker containers using loops.

### Requirements

1. Define a variable `applications` as a map of objects:
   ```hcl
   variable "applications" {
     type = map(object({
       image    = string
       ports    = list(object({ internal = number, external = number }))
       env_vars = map(string)
       enabled  = bool
     }))
   }
   ```

2. Default value should include at least 4 apps, with one `enabled = false`

3. Using `for_each`:
   - Create containers ONLY for enabled apps
   - Use `dynamic "ports"` blocks for each app's port list
   - Set environment variables from the `env_vars` map

4. Using `for` expressions in locals:
   - `enabled_apps` — filtered map of only enabled apps
   - `all_urls` — flat list of all external URLs across all apps
   - `app_summary` — map of app name → number of ports exposed

5. Create a `local_file` summary with:
   - Total enabled apps
   - Total ports exposed
   - List of all URLs

6. Outputs:
   - `enabled_app_names` — list of enabled app names
   - `all_urls` — all accessible URLs
   - `disabled_apps` — list of disabled app names

### Constraints
- Must use `for_each` (not `count`)
- Must use at least one `dynamic` block
- Must use at least 3 different `for` expression patterns
- Must filter out disabled apps

## Verify
```bash
terraform init
terraform plan     # should NOT create the disabled app
terraform apply
terraform output -json all_urls
terraform destroy
```
