#!/bin/bash
# =============================================================================
# External data source script
# MUST output valid JSON to stdout. No other output allowed.
# =============================================================================

HOSTNAME=$(hostname)
OS=$(uname -s)
ARCH=$(uname -m)
DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat <<EOF
{
  "hostname": "${HOSTNAME}",
  "os": "${OS}",
  "arch": "${ARCH}",
  "date": "${DATE}"
}
EOF
