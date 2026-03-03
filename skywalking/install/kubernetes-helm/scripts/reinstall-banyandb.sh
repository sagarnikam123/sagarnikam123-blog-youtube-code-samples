#!/bin/bash

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Quick script to delete and reinstall BanyanDB

set -e

NAMESPACE="${NAMESPACE:-sw}"
RELEASE_NAME="${RELEASE_NAME:-banyandb}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

print_warn "This will delete the BanyanDB deployment in namespace '$NAMESPACE'"
read -p "Are you sure? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
  print_info "Cancelled"
  exit 0
fi

print_info "Deleting Helm release..."
helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" 2>/dev/null || print_warn "Release not found or already deleted"

print_info "Waiting for pods to terminate..."
sleep 5

print_info "Deleting PVCs..."
kubectl delete pvc -n "$NAMESPACE" --all 2>/dev/null || print_warn "No PVCs found"

print_info "Waiting for cleanup..."
sleep 3

print_info "Reinstalling BanyanDB..."
./install-banyandb-cluster-mode.sh "$@"

print_info "Done! Check status with: kubectl get pods -n $NAMESPACE"
