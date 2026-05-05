# Hints — Sensitive Output

## Hint 1
`random_password` marks its `result` attribute as sensitive. Any output that references it must also be marked `sensitive = true`.

## Hint 2
Add `sensitive = true` to both outputs. This hides them from `terraform output` display but they're still accessible via `terraform output -json`.

## Hint 3
If you intentionally want to display a sensitive value (e.g., for debugging), you can use `nonsensitive()` — but never do this in production code.
