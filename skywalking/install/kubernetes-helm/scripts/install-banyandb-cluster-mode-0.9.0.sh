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

# Script to install BanyanDB in cluster mode using Helm
# Reference: https://skywalking.apache.org/docs/skywalking-banyandb/next/installation/kubernetes/

set -e

# Configuration
NAMESPACE="${NAMESPACE:-sw}"
RELEASE_NAME="${RELEASE_NAME:-banyandb}"
CHART_VERSION="${CHART_VERSION:-0.6.0-rc3}"
IMAGE_TAG="${IMAGE_TAG:-0.9.0}"
LIAISON_REPLICAS="${LIAISON_REPLICAS:-2}"
DATA_REPLICAS="${DATA_REPLICAS:-2}"
ETCD_REPLICAS="${ETCD_REPLICAS:-1}"
STORAGE_SIZE="${STORAGE_SIZE:-10Gi}"
STORAGE_CLASS="${STORAGE_CLASS:-standard}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
  print_info "Checking prerequisites..."

  # Check if kubectl is installed
  if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
  fi

  # Check if helm is installed
  if ! command -v helm &> /dev/null; then
    print_error "helm is not installed. Please install Helm 3 first."
    exit 1
  fi

  # Check Helm version (should be v3+)
  HELM_VERSION=$(helm version --short | grep -oE 'v[0-9]+' | head -1)
  if [[ ! "$HELM_VERSION" =~ ^v3 ]]; then
    print_error "Helm version 3 is required. Current version: $HELM_VERSION"
    exit 1
  fi

  # Check cluster connectivity
  if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
  fi

  print_info "Prerequisites check passed."
}

# Function to create namespace
create_namespace() {
  print_info "Creating namespace '$NAMESPACE' if it doesn't exist..."

  if kubectl get namespace "$NAMESPACE" &> /dev/null; then
    print_info "Namespace '$NAMESPACE' already exists."
  else
    kubectl create namespace "$NAMESPACE"
    print_info "Namespace '$NAMESPACE' created."
  fi
}

# Function to configure Helm for OCI
configure_helm_oci() {
  print_info "Configuring Helm for OCI registry..."
  print_warn "You may be prompted to login to Docker Hub registry."

  # Check if already logged in by trying to pull chart info
  if helm show chart oci://registry-1.docker.io/apache/skywalking-banyandb-helm --version "$CHART_VERSION" &> /dev/null; then
    print_info "Already authenticated to Docker Hub OCI registry."
  else
    print_warn "Please login to Docker Hub registry (press Enter to skip if already logged in):"
    helm registry login registry-1.docker.io || true
  fi
}

# Function to install BanyanDB in cluster mode
install_banyandb() {
  print_info "Installing BanyanDB in cluster mode..."
  print_info "Configuration:"
  print_info "  - Namespace: $NAMESPACE"
  print_info "  - Release Name: $RELEASE_NAME"
  print_info "  - Chart Version: $CHART_VERSION"
  print_info "  - Image Tag: $IMAGE_TAG"
  print_info "  - Liaison Replicas: $LIAISON_REPLICAS"
  print_info "  - Data Replicas: $DATA_REPLICAS"
  print_info "  - Etcd Replicas: $ETCD_REPLICAS"
  print_info "  - Storage Size: $STORAGE_SIZE"
  print_info "  - Storage Class: $STORAGE_CLASS"

  helm upgrade --install "$RELEASE_NAME" \
    oci://registry-1.docker.io/apache/skywalking-banyandb-helm \
    --version "$CHART_VERSION" \
    --set image.tag="$IMAGE_TAG" \
    --set standalone.enabled=false \
    --set cluster.enabled=true \
    --set cluster.liaison.replicas="$LIAISON_REPLICAS" \
    --set cluster.data.nodeTemplate.replicas="$DATA_REPLICAS" \
    --set etcd.enabled=true \
    --set etcd.replicaCount="$ETCD_REPLICAS" \
    --set etcd.auth.rbac.create=false \
    --set etcd.auth.rbac.enabled=false \
    --set etcd.auth.client.secureTransport=false \
    --set etcd.auth.peer.secureTransport=false \
    --set etcd.auth.client.enableAuthentication=false \
    --set etcd.auth.peer.enableAuthentication=false \
    --set-string etcd.extraEnvVars[0].name=ALLOW_NONE_AUTHENTICATION \
    --set-string etcd.extraEnvVars[0].value=yes \
    --set cluster.fodc.enabled=false \
    --set core.setupJob.enabled=false \
    --set etcd.volumePermissions.enabled=true \
    --set global.security.allowInsecureImages=true \
    --set etcd.volumePermissions.image.registry=docker.io \
    --set etcd.volumePermissions.image.repository=bitnami/minideb \
    --set etcd.volumePermissions.image.tag=bookworm \
    --set etcd.volumePermissions.image.pullPolicy=IfNotPresent \
    --set etcd.readinessProbe.initialDelaySeconds=30 \
    --set etcd.readinessProbe.periodSeconds=10 \
    --set etcd.readinessProbe.timeoutSeconds=5 \
    --set etcd.readinessProbe.failureThreshold=10 \
    --set etcd.livenessProbe.initialDelaySeconds=30 \
    --set etcd.livenessProbe.periodSeconds=30 \
    --set etcd.livenessProbe.timeoutSeconds=5 \
    --set etcd.livenessProbe.failureThreshold=10 \
    --set etcd.startupProbe.enabled=true \
    --set etcd.startupProbe.initialDelaySeconds=0 \
    --set etcd.startupProbe.periodSeconds=10 \
    --set etcd.startupProbe.timeoutSeconds=5 \
    --set etcd.startupProbe.failureThreshold=30 \
    --set etcd.startupProbe.successThreshold=1 \
    --set storage.data.enabled=true \
    --set storage.data.persistentVolumeClaims[0].mountTargets[0]=measure \
    --set storage.data.persistentVolumeClaims[0].claimName=measure-data \
    --set storage.data.persistentVolumeClaims[0].size="$STORAGE_SIZE" \
    --set storage.data.persistentVolumeClaims[0].accessModes[0]=ReadWriteOnce \
    --set storage.data.persistentVolumeClaims[0].volumeMode=Filesystem \
    --set storage.data.persistentVolumeClaims[0].storageClass="$STORAGE_CLASS" \
    --set storage.data.persistentVolumeClaims[1].mountTargets[0]=stream \
    --set storage.data.persistentVolumeClaims[1].claimName=stream-data \
    --set storage.data.persistentVolumeClaims[1].size="$STORAGE_SIZE" \
    --set storage.data.persistentVolumeClaims[1].accessModes[0]=ReadWriteOnce \
    --set storage.data.persistentVolumeClaims[1].volumeMode=Filesystem \
    --set storage.data.persistentVolumeClaims[1].storageClass="$STORAGE_CLASS" \
    --set storage.liaison.enabled=false \
    -n "$NAMESPACE"

  print_info "BanyanDB installation initiated."
}

# Function to wait for pods to be ready
wait_for_pods() {
  print_info "Waiting for BanyanDB pods to be ready (timeout: 5 minutes)..."

  # Wait for liaison pods
  if ! kubectl wait --for=condition=ready pod \
    -l "app.kubernetes.io/name=banyandb,app.kubernetes.io/component=liaison" \
    -n "$NAMESPACE" \
    --timeout=300s 2>/dev/null; then
    print_warn "Liaison pods are not ready yet. Checking status..."
  fi

  # Wait for data pods
  if ! kubectl wait --for=condition=ready pod \
    -l "app.kubernetes.io/name=banyandb,app.kubernetes.io/component=data" \
    -n "$NAMESPACE" \
    --timeout=300s 2>/dev/null; then
    print_warn "Data pods are not ready yet. Checking status..."
  fi

  # Wait for etcd pods
  if ! kubectl wait --for=condition=ready pod \
    -l "app.kubernetes.io/name=etcd" \
    -n "$NAMESPACE" \
    --timeout=300s 2>/dev/null; then
    print_warn "Etcd pods are not ready yet. Checking status..."
  fi
}

# Function to display deployment status
display_status() {
  print_info "Deployment Status:"
  echo ""

  print_info "Pods:"
  kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"
  echo ""

  print_info "Services:"
  kubectl get svc -n "$NAMESPACE" -l "app.kubernetes.io/instance=$RELEASE_NAME"
  echo ""

  print_info "Persistent Volume Claims:"
  kubectl get pvc -n "$NAMESPACE"
  echo ""

  print_info "BanyanDB Cluster Information:"
  print_info "  - GRPC Service: $RELEASE_NAME-grpc.$NAMESPACE.svc.cluster.local:17912"
  print_info "  - HTTP Service: $RELEASE_NAME-http.$NAMESPACE.svc.cluster.local:17913"
  print_info "  - Etcd Service: $RELEASE_NAME-etcd.$NAMESPACE.svc.cluster.local:2379"
  echo ""

  print_info "To access BanyanDB HTTP UI, run:"
  print_info "  kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-http 17913:17913"
  print_info "  Then open: http://localhost:17913"
}

# Function to display usage
usage() {
  cat << EOF
Usage: $0 [OPTIONS]

Install BanyanDB in cluster mode using Helm.

OPTIONS:
  -n, --namespace NAMESPACE       Kubernetes namespace (default: sw)
  -r, --release RELEASE_NAME      Helm release name (default: banyandb)
  -v, --chart-version VERSION     Helm chart version (default: 0.3.0)
  -t, --image-tag TAG             BanyanDB image tag (default: 0.7.0)
  -l, --liaison-replicas COUNT    Number of liaison replicas (default: 2)
  -d, --data-replicas COUNT       Number of data replicas (default: 2)
  -e, --etcd-replicas COUNT       Number of etcd replicas (default: 1)
  -s, --storage-size SIZE         Storage size for PVCs (default: 10Gi)
  -c, --storage-class CLASS       Storage class name (default: standard)
  -h, --help                      Display this help message

EXAMPLES:
  # Install with default settings
  $0

  # Install with custom namespace and replicas
  $0 -n skywalking -l 3 -d 3 -e 3

  # Install with custom storage
  $0 -s 50Gi -c gp3

ENVIRONMENT VARIABLES:
  NAMESPACE, RELEASE_NAME, CHART_VERSION, IMAGE_TAG, LIAISON_REPLICAS,
  DATA_REPLICAS, ETCD_REPLICAS, STORAGE_SIZE, STORAGE_CLASS

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    -r|--release)
      RELEASE_NAME="$2"
      shift 2
      ;;
    -v|--chart-version)
      CHART_VERSION="$2"
      shift 2
      ;;
    -t|--image-tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    -l|--liaison-replicas)
      LIAISON_REPLICAS="$2"
      shift 2
      ;;
    -d|--data-replicas)
      DATA_REPLICAS="$2"
      shift 2
      ;;
    -e|--etcd-replicas)
      ETCD_REPLICAS="$2"
      shift 2
      ;;
    -s|--storage-size)
      STORAGE_SIZE="$2"
      shift 2
      ;;
    -c|--storage-class)
      STORAGE_CLASS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      print_error "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# Main execution
main() {
  print_info "Starting BanyanDB cluster mode installation..."
  echo ""

  check_prerequisites
  create_namespace
  configure_helm_oci
  install_banyandb
  wait_for_pods
  display_status

  print_info "BanyanDB cluster mode installation completed!"
  print_info "Check the status above and verify all pods are running."
}

# Run main function
main
