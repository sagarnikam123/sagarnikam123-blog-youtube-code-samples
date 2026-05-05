# Hints — Provider Mismatch

## Hint 1
The Docker provider is NOT published by HashiCorp. Check the Terraform Registry for the correct source.

## Hint 2
The correct Docker provider source is `kreuzwerker/docker`.

## Hint 3
Every provider you use in resources must be declared in `required_providers`. The `random_pet` resource needs the `hashicorp/random` provider.
