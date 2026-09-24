#!/usr/bin/env bash
# OpenStatus setup script for self-hosting / benchmarking.
# OpenStatus has its own large, frequently-changing docker-compose project
# (many services). This script clones the official repo and prepares config.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
INSTALL_DIR="${PLATFORM_DIR}/install/docker-compose/standalone/openstatus-install"

echo "=== OpenStatus Setup ==="

if [ -d "$INSTALL_DIR" ]; then
  echo "Installation directory already exists: $INSTALL_DIR"
  echo "To re-install: rm -rf $INSTALL_DIR && ./scripts/setup.sh"
  exit 0
fi

echo "Cloning OpenStatus repository..."
git clone --depth 1 --single-branch --branch main \
  https://github.com/openstatusHQ/openstatus.git "$INSTALL_DIR"

cd "$INSTALL_DIR"

# Prepare config from the example
if [ -f config.example.env ]; then
  cp config.example.env .env.docker
elif [ -f .env.docker.example ]; then
  cp .env.docker.example .env.docker
else
  echo "WARNING: no env example found; create .env.docker manually."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. cd $INSTALL_DIR"
echo "  2. Edit .env.docker and set the REQUIRED values:"
echo "       AUTH_SECRET, RESEND_API_KEY, SELF_HOST, NEXT_PUBLIC_URL"
echo "       TINYBIRD_URL=http://tinybird-local:7181"
echo "       CRON_SECRET=<random-string>"
echo "  3. export DOCKER_BUILDKIT=1 && docker compose up -d"
echo "     (or: docker compose -f docker-compose.github-packages.yaml up -d  for prebuilt images)"
echo "  4. Deploy Tinybird analytics:"
echo "       cd packages/tinybird && tb --local deploy && tb --local deployment promote"
echo "       tb --local info   # copy token into TINY_BIRD_API_KEY and TINYBIRD_TOKEN"
echo ""
echo "Access:"
echo "  Dashboard:    http://localhost:3002"
echo "  Status pages: http://localhost:3003"
echo "  API server:   http://localhost:3001"
echo ""
echo "Then deploy a private-location probe (see install/docker-compose/probe/)."
