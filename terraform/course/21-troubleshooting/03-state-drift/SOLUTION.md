# Solution — State Drift

## What Happened
After `terraform apply`, the file content in state is "This file is managed by Terraform. Do not edit manually." When you manually edited the file, the real file no longer matches state.

## How Terraform Detects It
`terraform plan` reads the real file and compares it to state. It shows:
```
~ content = "MODIFIED OUTSIDE TERRAFORM" -> "This file is managed by Terraform. Do not edit manually."
```

## Three Options

### Option 1: Restore Terraform's version (most common)
```bash
terraform apply
```
This overwrites the manual change with what's in your config. This is the standard approach — Terraform is the source of truth.

### Option 2: Accept the manual change
Update your variable to match reality:
```bash
terraform apply -var 'content=MODIFIED OUTSIDE TERRAFORM'
```
Or update the default in your config. Now config matches reality — no changes needed.

### Option 3: Refresh state only (rarely used)
```bash
terraform apply -refresh-only
```
This updates state to match reality WITHOUT changing the config. Dangerous — your config and state now disagree.

## The Lesson
- Terraform detects drift on every `plan`/`apply` by comparing state to reality
- The fix depends on intent: was the manual change correct or accidental?
- In production, drift usually means someone bypassed Terraform — investigate before blindly applying
- Use `ignore_changes` in lifecycle blocks for attributes that are expected to change outside Terraform
