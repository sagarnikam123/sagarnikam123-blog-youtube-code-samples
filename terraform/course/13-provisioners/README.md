# Module 13 — Provisioners

## What are Provisioners?

Provisioners execute scripts or commands on local or remote machines during resource creation or destruction. They are a **last resort** — prefer native provider features when possible.

## Types

| Provisioner | Runs On | Use Case |
|-------------|---------|----------|
| `local-exec` | Your machine (where Terraform runs) | Run local scripts, CLI commands |
| `remote-exec` | The created resource | SSH into a server and run commands |
| `file` | The created resource | Copy files to a remote server |

## local-exec

```hcl
resource "null_resource" "example" {
  provisioner "local-exec" {
    command = "echo 'Hello from local-exec'"
  }
}
```

## terraform_data (Terraform 1.4+)

Replaces `null_resource` — built-in, no provider needed:

```hcl
resource "terraform_data" "example" {
  triggers_replace = [timestamp()]

  provisioner "local-exec" {
    command = "echo 'Hello from terraform_data'"
  }
}
```

## When to Use Provisioners

- Running database migrations after infrastructure is created
- Triggering external CI/CD pipelines
- Generating local files from templates
- Running health checks

## When NOT to Use Provisioners

- Installing software → use cloud-init, user_data, or Packer
- Configuration management → use Ansible, Chef, Puppet
- Anything the provider can do natively

## Official Docs

- [Provisioners Overview](https://developer.hashicorp.com/terraform/language/resources/provisioners/syntax)
- [local-exec Provisioner](https://developer.hashicorp.com/terraform/language/resources/provisioners/local-exec)
- [remote-exec Provisioner](https://developer.hashicorp.com/terraform/language/resources/provisioners/remote-exec)
- [file Provisioner](https://developer.hashicorp.com/terraform/language/resources/provisioners/file)
- [terraform_data Resource](https://developer.hashicorp.com/terraform/language/resources/terraform-data)
- [null_resource](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource)

## Exercises

| # | Exercise | Folder |
|---|----------|--------|
| 1 | [Local Exec](./01-local-exec/) | Run local commands during apply |
| 2 | [Terraform Data](./02-terraform-data/) | Modern replacement for null_resource |
