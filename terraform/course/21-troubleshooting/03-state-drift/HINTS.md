# Hints — State Drift

## What's Happening
After you manually edit the file, Terraform's state says the content should be X, but the real file says Y. This is "drift."

## Hint 1
Run `terraform plan` after modifying the file. Terraform will show it wants to update the file back to the expected content.

## Hint 2
You have three options:
1. `terraform apply` — overwrite the manual change, restore Terraform's version
2. Update `var.content` to match the manual change, then `terraform apply`
3. `terraform refresh` — update state to match reality (but this doesn't change config)

## Hint 3
In production, drift usually means someone made a manual change. The right answer is almost always: update the Terraform config to reflect the desired state, then apply.
