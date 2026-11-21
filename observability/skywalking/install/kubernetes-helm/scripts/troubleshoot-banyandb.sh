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

# Script to troubleshoot BanyanDB cluster deployment

set -e

NAMESPACE="${NAMESPACE:-sw}"
RELEASE_NAME="${RELEASE_NAME:-banyandb}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
  echo -e "\n${BLUE}========================================${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}========================================${NC}\n"
}

print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Check pod status
check_pods() {
  print_header "Pod Status"
  kubectl get pods -n "$NAMESPACE" -o wide

  echo ""
  print_info "Checking individual pod readiness..."

  # Check etcd
  ETCD_READY=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=etcd" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}')
  if [[ "$ETCD_READY" == "True" ]]; then
    print_info "✓ Etcd is ready"
  else
    print_warn "✗ Etcd is not ready"
  fi

  # Check liaison
  LIAISON_READY=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=liaison" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}')
  if [[ "$LIAISON_READY" == *"True"* ]]; then
    print_info "✓ Liaison pods are ready"
  else
    print_warn "✗ Liaison pods are not ready"
  fi

  # Check data
  DATA_READY=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/component=data" -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}')
  if [[ "$DATA_READY" == *"True"* ]]; then
    print_info "✓ Data pods are ready"
  else
    print_warn "✗ Data pods are not ready"
  fi
}

# Check etcd logs
check_etcd_logs() {
  print_header "Etcd Logs (last 20 lines)"
  kubectl logs -n "$NAMESPACE" -l "app.kubernetes.io/name=etcd" --tail=20 || print_error "Failed to get etcd logs"
}

# Check liaison logs
check_liaison_logs() {
  print_header "Liaison Logs (last 30 lines)"
  kubectl logs -n "$NAMESPACE" -l "app.kubernetes.io/component=liaison" --tail=30 --all-containers || print_error "Failed to get liaison logs"
}

# Check data logs
check_data_logs() {
  print_header "Data Logs (last 30 lines)"
  kubectl logs -n "$NAMESPACE" -l "app.kubernetes.io/component=data" --tail=30 --all-containers || print_error "Failed to get data logs"
}

# Check services
check_services() {
  print_header "Services"
  kubectl get svc -n "$NAMESPACE"
}

# Check PVCs
check_pvcs() {
  print_header "Persistent Volume Claims"
  kubectl get pvc -n "$NAMESPACE"
}

# Check events
check_events() {
  print_header "Recent Events"
  kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -20
}

# Test etcd connectivity
test_etcd_connectivity() {
  print_header "Testing Etcd Connectivity"

  ETCD_POD=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=etcd" -o jsonpath='{.items[0].metadata.name}')

  if [[ -z "$ETCD_POD" ]]; then
    print_error "No etcd pod found"
    return
  fi

  print_info "Testing etcd endpoint health..."
  kubectl exec -n "$NAMESPACE" "$ETCD_POD" -- etcdctl endpoint health || print_warn "Etcd health check failed"

  print_info "Testing etcd member list..."
  kubectl exec -n "$NAMESPACE" "$ETCD_POD" -- etcdctl member list || print_warn "Etcd member list failed"
}

# Check resource usage
check_resources() {
  print_header "Resource Usage"
  kubectl top pods -n "$NAMESPACE" 2>/dev/null || print_warn "Metrics server not available"
}

# Main menu
show_menu() {
  echo ""
  echo "BanyanDB Troubleshooting Menu"
  echo "=============================="
  echo "1. Check all (recommended)"
  echo "2. Check pod status"
  echo "3. Check etcd logs"
  echo "4. Check liaison logs"
  echo "5. Check data logs"
  echo "6. Check services"
  echo "7. Check PVCs"
  echo "8. Check events"
  echo "9. Test etcd connectivity"
  echo "10. Check resource usage"
  echo "11. Delete and reinstall"
  echo "0. Exit"
  echo ""
}

# Delete deployment
delete_deployment() {
  print_warn "This will delete the BanyanDB deployment in namespace '$NAMESPACE'"
  read -p "Are you sure? (yes/no): " confirm

  if [[ "$confirm" == "yes" ]]; then
    print_info "Deleting Helm release..."
    helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || print_error "Failed to uninstall"

    print_info "Deleting PVCs..."
    kubectl delete pvc -n "$NAMESPACE" --all || print_warn "Failed to delete PVCs"

    print_info "Deployment deleted. You can now reinstall."
  else
    print_info "Deletion cancelled"
  fi
}

# Interactive mode
if [[ "$1" == "--interactive" ]] || [[ "$1" == "-i" ]]; then
  while true; do
    show_menu
    read -p "Select option: " choice

    case $choice in
      1)
        check_pods
        check_services
        check_pvcs
        check_events
        check_etcd_logs
        check_liaison_logs
        check_data_logs
        test_etcd_connectivity
        check_resources
        ;;
      2) check_pods ;;
      3) check_etcd_logs ;;
      4) check_liaison_logs ;;
      5) check_data_logs ;;
      6) check_services ;;
      7) check_pvcs ;;
      8) check_events ;;
      9) test_etcd_connectivity ;;
      10) check_resources ;;
      11) delete_deployment ;;
      0) exit 0 ;;
      *) print_error "Invalid option" ;;
    esac

    read -p "Press Enter to continue..."
  done
else
  # Run all checks
  check_pods
  check_services
  check_pvcs
  check_events
  check_etcd_logs
  check_liaison_logs
  check_data_logs
  test_etcd_connectivity
  check_resources

  echo ""
  print_info "Troubleshooting complete. Run with --interactive for menu mode."
fi
