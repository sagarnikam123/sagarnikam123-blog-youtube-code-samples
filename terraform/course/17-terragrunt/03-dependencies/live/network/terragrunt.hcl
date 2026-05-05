# =============================================================================
# Network module — no dependencies, runs first
# =============================================================================

include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "../../modules/network"
}

inputs = {
  network_name = "tg-dependency-net"
}
