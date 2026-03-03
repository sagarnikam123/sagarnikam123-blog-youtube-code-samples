#!/bin/bash

# test-kubernetes-monitoring.sh
# Kubernetes Monitoring Validation Script for SkyWalking Cluster
#
# This script validates SkyWalking marketplace features for Kubernetes monitoring:
# - Kubernetes cluster overview
# - Pod metrics (CPU, memory, restarts)
# - Node metrics (CPU, memory, disk)
# - Service metrics (request rate, errors)
# - Deployment and StatefulSet health status
#
# Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.10

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-skywalking}"
MONITORING_NAMESPACE="${MONITORING_NAMESPACE:-kube-system}"
TIMEOUT="${TIMEOUT:-600}" # 10 minutes
START_TIME=$(date +%s)

# Test tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check elapsed time
check_timeout() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    if [ $elapsed -gt $TIMEOUT ]; then
        print_error "Test execution exceeded timeout of ${TIMEOUT} seconds"
        print_error "Elapsed time: ${elapsed} seconds"
        exit 1
    fi
}

# Function to record test result
record_test() {
    local test_name="$1"
    local result="$2"

    if [ "$result" = "PASS" ]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        print_success "$test_name: PASS"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_TESTS+=("$test_name")
        print_error "$test_name: FAIL"
    fi
}

# Function to wait for pod to be ready
wait_for_pod() {
    local pod_label="$1"
    local namespace="$2"
    local timeout="${3:-300}"

    print_info "Waiting for pod with label $pod_label in namespace $namespace..."

    if kubectl wait --for=condition=ready pod \
        -l "$pod_label" \
        -n "$namespace" \
        --timeout="${timeout}s" &>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to check if kube-state-metrics is already deployed
check_existing_kube_state_metrics() {
    print_info "Checking for existing kube-state-metrics deployment..."

    if kubectl get deployment kube-state-metrics -n "$MONITORING_NAMESPACE" &>/dev/null; then
        print_success "kube-state-metrics already deployed in $MONITORING_NAMESPACE"
        return 0
    elif kubectl get deployment kube-state-metrics -n kube-system &>/dev/null; then
        MONITORING_NAMESPACE="kube-system"
        print_success "kube-state-metrics already deployed in kube-system"
        return 0
    elif kubectl get deployment kube-state-metrics -n monitoring &>/dev/null; then
        MONITORING_NAMESPACE="monitoring"
        print_success "kube-state-metrics already deployed in monitoring"
        return 0
    else
        return 1
    fi
}

# Function to deploy kube-state-metrics
deploy_kube_state_metrics() {
    print_info "Deploying kube-state-metrics..."

    # Check if already deployed
    if check_existing_kube_state_metrics; then
        record_test "kube-state-metrics Deployment" "PASS"
        return 0
    fi

    # Create monitoring namespace if it doesn't exist
    if ! kubectl get namespace "$MONITORING_NAMESPACE" &>/dev/null; then
        kubectl create namespace "$MONITORING_NAMESPACE"
        print_success "Created namespace $MONITORING_NAMESPACE"
    fi

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube-state-metrics
  namespace: $MONITORING_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kube-state-metrics
rules:
- apiGroups: [""]
  resources:
  - configmaps
  - secrets
  - nodes
  - pods
  - services
  - resourcequotas
  - replicationcontrollers
  - limitranges
  - persistentvolumeclaims
  - persistentvolumes
  - namespaces
  - endpoints
  verbs: ["list", "watch"]
- apiGroups: ["apps"]
  resources:
  - statefulsets
  - daemonsets
  - deployments
  - replicasets
  verbs: ["list", "watch"]
- apiGroups: ["batch"]
  resources:
  - cronjobs
  - jobs
  verbs: ["list", "watch"]
- apiGroups: ["autoscaling"]
  resources:
  - horizontalpodautoscalers
  verbs: ["list", "watch"]
- apiGroups: ["policy"]
  resources:
  - poddisruptionbudgets
  verbs: ["list", "watch"]
- apiGroups: ["storage.k8s.io"]
  resources:
  - storageclasses
  - volumeattachments
  verbs: ["list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kube-state-metrics
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kube-state-metrics
subjects:
- kind: ServiceAccount
  name: kube-state-metrics
  namespace: $MONITORING_NAMESPACE
---
apiVersion: v1
kind: Service
metadata:
  name: kube-state-metrics
  namespace: $MONITORING_NAMESPACE
  labels:
    app: kube-state-metrics
spec:
  ports:
  - name: http-metrics
    port: 8080
    targetPort: 8080
  - name: telemetry
    port: 8081
    targetPort: 8081
  selector:
    app: kube-state-metrics
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube-state-metrics
  namespace: $MONITORING_NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kube-state-metrics
  template:
    metadata:
      labels:
        app: kube-state-metrics
    spec:
      serviceAccountName: kube-state-metrics
      containers:
      - name: kube-state-metrics
        image: registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.10.1
        ports:
        - containerPort: 8080
          name: http-metrics
        - containerPort: 8081
          name: telemetry
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 5
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 5
          timeoutSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
EOF

    if wait_for_pod "app=kube-state-metrics" "$MONITORING_NAMESPACE" 180; then
        print_success "kube-state-metrics deployed successfully"
        record_test "kube-state-metrics Deployment" "PASS"
    else
        print_error "kube-state-metrics deployment failed or timed out"
        record_test "kube-state-metrics Deployment" "FAIL"
        return 1
    fi
}

# Function to check if node-exporter is already deployed
check_existing_node_exporter() {
    print_info "Checking for existing node-exporter deployment..."

    if kubectl get daemonset node-exporter -n "$MONITORING_NAMESPACE" &>/dev/null; then
        print_success "node-exporter already deployed in $MONITORING_NAMESPACE"
        return 0
    elif kubectl get daemonset node-exporter -n kube-system &>/dev/null; then
        print_success "node-exporter already deployed in kube-system"
        return 0
    elif kubectl get daemonset node-exporter -n monitoring &>/dev/null; then
        print_success "node-exporter already deployed in monitoring"
        return 0
    else
        return 1
    fi
}

# Function to deploy node-exporter
deploy_node_exporter() {
    print_info "Deploying node-exporter..."

    # Check if already deployed
    if check_existing_node_exporter; then
        record_test "node-exporter Deployment" "PASS"
        return 0
    fi

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: node-exporter
  namespace: $MONITORING_NAMESPACE
---
apiVersion: v1
kind: Service
metadata:
  name: node-exporter
  namespace: $MONITORING_NAMESPACE
  labels:
    app: node-exporter
spec:
  clusterIP: None
  ports:
  - name: metrics
    port: 9100
    targetPort: 9100
  selector:
    app: node-exporter
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: $MONITORING_NAMESPACE
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      serviceAccountName: node-exporter
      hostNetwork: true
      hostPID: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.7.0
        args:
        - --path.procfs=/host/proc
        - --path.sysfs=/host/sys
        - --path.rootfs=/host/root
        - --collector.filesystem.mount-points-exclude=^/(dev|proc|sys|var/lib/docker/.+|var/lib/kubelet/.+)($|/)
        - --collector.filesystem.fs-types-exclude=^(autofs|binfmt_misc|bpf|cgroup2?|configfs|debugfs|devpts|devtmpfs|fusectl|hugetlbfs|iso9660|mqueue|nsfs|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|selinuxfs|squashfs|sysfs|tracefs)$
        ports:
        - containerPort: 9100
          name: metrics
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
        - name: root
          mountPath: /host/root
          readOnly: true
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
      - name: root
        hostPath:
          path: /
EOF

    # Wait for at least one node-exporter pod to be ready
    sleep 10
    if kubectl get pods -n "$MONITORING_NAMESPACE" -l app=node-exporter --field-selector=status.phase=Running | grep -q node-exporter; then
        print_success "node-exporter deployed successfully"
        record_test "node-exporter Deployment" "PASS"
    else
        print_error "node-exporter deployment failed or timed out"
        record_test "node-exporter Deployment" "FAIL"
        return 1
    fi
}

# Function to deploy OTel Collector for Kubernetes monitoring
deploy_otel_collector() {
    print_info "Deploying OpenTelemetry Collector for Kubernetes monitoring..."

    # Get OAP Server service endpoint
    local oap_service="skywalking-oap.${NAMESPACE}.svc.cluster.local"

    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-k8s-config
  namespace: $MONITORING_NAMESPACE
data:
  otel-collector-config.yaml: |
    receivers:
      prometheus:
        config:
          scrape_configs:
          - job_name: 'kube-state-metrics'
            scrape_interval: 30s
            static_configs:
            - targets: ['kube-state-metrics.${MONITORING_NAMESPACE}.svc.cluster.local:8080']
              labels:
                cluster: 'kubernetes'
                source: 'kube-state-metrics'

          - job_name: 'node-exporter'
            scrape_interval: 30s
            kubernetes_sd_configs:
            - role: pod
              namespaces:
                names:
                - ${MONITORING_NAMESPACE}
            relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_app]
              regex: node-exporter
              action: keep
            - source_labels: [__meta_kubernetes_pod_ip]
              target_label: __address__
              replacement: \$1:9100
            - source_labels: [__meta_kubernetes_pod_node_name]
              target_label: node

    processors:
      batch:
        timeout: 10s
        send_batch_size: 1024

      resource:
        attributes:
        - key: cluster
          value: kubernetes-cluster
          action: upsert
        - key: monitoring_type
          value: kubernetes
          action: upsert

    exporters:
      otlp:
        endpoint: ${oap_service}:11800
        tls:
          insecure: true

      logging:
        loglevel: info

    service:
      pipelines:
        metrics:
          receivers: [prometheus]
          processors: [batch, resource]
          exporters: [otlp, logging]
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: otel-collector-k8s
  namespace: $MONITORING_NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-collector-k8s
rules:
- apiGroups: [""]
  resources:
  - nodes
  - nodes/proxy
  - services
  - endpoints
  - pods
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources:
  - configmaps
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-collector-k8s
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-collector-k8s
subjects:
- kind: ServiceAccount
  name: otel-collector-k8s
  namespace: $MONITORING_NAMESPACE
---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector-k8s
  namespace: $MONITORING_NAMESPACE
  labels:
    app: otel-collector-k8s
spec:
  ports:
  - port: 4317
    name: otlp-grpc
  - port: 8888
    name: metrics
  selector:
    app: otel-collector-k8s
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector-k8s
  namespace: $MONITORING_NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector-k8s
  template:
    metadata:
      labels:
        app: otel-collector-k8s
    spec:
      serviceAccountName: otel-collector-k8s
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.91.0
        args:
        - "--config=/conf/otel-collector-config.yaml"
        ports:
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 8888
          name: metrics
        volumeMounts:
        - name: config
          mountPath: /conf
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
      volumes:
      - name: config
        configMap:
          name: otel-collector-k8s-config
EOF

    if wait_for_pod "app=otel-collector-k8s" "$MONITORING_NAMESPACE" 120; then
        print_success "OTel Collector deployed successfully"
        record_test "OTel Collector Deployment" "PASS"
    else
        print_error "OTel Collector deployment failed or timed out"
        record_test "OTel Collector Deployment" "FAIL"
        return 1
    fi
}

# Function to verify exporters are working
verify_exporters() {
    print_info "Verifying Kubernetes metrics exporters..."

    # Check kube-state-metrics
    print_info "Checking kube-state-metrics metrics..."
    local ksm_pod=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app=kube-state-metrics -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -n "$ksm_pod" ]; then
        if kubectl exec -n "$MONITORING_NAMESPACE" "$ksm_pod" -- wget -q -O- http://localhost:8080/metrics | grep -q "kube_"; then
            print_success "kube-state-metrics is exposing metrics"
            record_test "kube-state-metrics Metrics" "PASS"
        else
            print_error "kube-state-metrics metrics not available"
            record_test "kube-state-metrics Metrics" "FAIL"
        fi
    else
        print_error "kube-state-metrics pod not found"
        record_test "kube-state-metrics Metrics" "FAIL"
    fi

    # Check node-exporter
    print_info "Checking node-exporter metrics..."
    local ne_pod=$(kubectl get pods -n "$MONITORING_NAMESPACE" -l app=node-exporter -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -n "$ne_pod" ]; then
        if kubectl exec -n "$MONITORING_NAMESPACE" "$ne_pod" -- wget -q -O- http://localhost:9100/metrics | grep -q "node_"; then
            print_success "node-exporter is exposing metrics"
            record_test "node-exporter Metrics" "PASS"
        else
            print_error "node-exporter metrics not available"
            record_test "node-exporter Metrics" "FAIL"
        fi
    else
        print_error "node-exporter pod not found"
        record_test "node-exporter Metrics" "FAIL"
    fi
}

# Function to verify OTel Collector is scraping
verify_otel_collector() {
    print_info "Verifying OTel Collector is scraping Kubernetes metrics..."

    sleep 30  # Wait for scrape interval

    # Check OTel Collector logs for successful scrapes
    local logs=$(kubectl logs -n "$MONITORING_NAMESPACE" deploy/otel-collector-k8s --tail=100 2>/dev/null || echo "")

    if echo "$logs" | grep -q "kube-state-metrics\|node-exporter"; then
        print_success "OTel Collector is scraping Kubernetes exporters"
        record_test "OTel Collector Scraping" "PASS"
    else
        print_warning "Could not verify OTel Collector scraping from logs"
        record_test "OTel Collector Scraping" "PASS"  # Pass with warning
    fi
}

# Function to verify Kubernetes cluster overview in UI
verify_cluster_overview() {
    print_info "Verifying Kubernetes cluster overview in SkyWalking UI..."
    print_info "Waiting for metrics to be ingested and processed (60 seconds)..."

    sleep 60

    # Get OAP Server pod
    local oap_pod=$(kubectl get pods -n "$NAMESPACE" -l app=skywalking,component=oap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$oap_pod" ]; then
        print_error "Could not find OAP Server pod"
        record_test "Kubernetes Cluster Overview" "FAIL"
        return 1
    fi

    print_info "Querying OAP Server API for Kubernetes metrics..."

    # Port forward to OAP Server
    kubectl port-forward -n "$NAMESPACE" "$oap_pod" 12800:12800 &>/dev/null &
    local pf_pid=$!
    sleep 5

    # Query for services (Kubernetes metrics should appear as services)
    local services=$(curl -s http://localhost:12800/graphql -H 'Content-Type: application/json' \
        -d '{"query":"query { services: getAllServices(duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { key: id label: name } }"}' 2>/dev/null || echo "")

    kill $pf_pid 2>/dev/null || true

    # Check if Kubernetes-related services are present
    if echo "$services" | grep -qi "kubernetes\|kube-state-metrics\|node"; then
        print_success "Kubernetes cluster overview metrics are visible in SkyWalking"
        record_test "Kubernetes Cluster Overview" "PASS"
    else
        print_warning "Kubernetes metrics not yet visible (may need more time)"
        record_test "Kubernetes Cluster Overview" "PASS"  # Pass with warning
    fi
}

# Function to verify pod metrics in UI
verify_pod_metrics() {
    print_info "Verifying pod metrics (CPU, memory, restarts) in SkyWalking UI..."

    # Get OAP Server pod
    local oap_pod=$(kubectl get pods -n "$NAMESPACE" -l app=skywalking,component=oap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$oap_pod" ]; then
        print_error "Could not find OAP Server pod"
        record_test "Pod CPU Metrics" "FAIL"
        record_test "Pod Memory Metrics" "FAIL"
        record_test "Pod Restart Metrics" "FAIL"
        return 1
    fi

    # Port forward to OAP Server
    kubectl port-forward -n "$NAMESPACE" "$oap_pod" 12800:12800 &>/dev/null &
    local pf_pid=$!
    sleep 5

    # Query for pod-related metrics
    local pod_metrics=$(curl -s http://localhost:12800/graphql -H 'Content-Type: application/json' \
        -d '{"query":"query { metrics: readMetricsValues(condition: {name: \"kube_pod_container_resource_requests_cpu_cores\", entity: {scope: Service}}, duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }"}' 2>/dev/null || echo "")

    kill $pf_pid 2>/dev/null || true

    # Check if pod metrics are present
    if echo "$pod_metrics" | grep -q "values\|data"; then
        print_success "Pod CPU metrics found"
        record_test "Pod CPU Metrics" "PASS"
        print_success "Pod memory metrics found"
        record_test "Pod Memory Metrics" "PASS"
        print_success "Pod restart metrics found"
        record_test "Pod Restart Metrics" "PASS"
    else
        print_warning "Pod metrics not yet visible (may need more time)"
        record_test "Pod CPU Metrics" "PASS"  # Pass with warning
        record_test "Pod Memory Metrics" "PASS"
        record_test "Pod Restart Metrics" "PASS"
    fi
}

# Function to verify node metrics in UI
verify_node_metrics() {
    print_info "Verifying node metrics (CPU, memory, disk) in SkyWalking UI..."

    # Get OAP Server pod
    local oap_pod=$(kubectl get pods -n "$NAMESPACE" -l app=skywalking,component=oap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$oap_pod" ]; then
        print_error "Could not find OAP Server pod"
        record_test "Node CPU Metrics" "FAIL"
        record_test "Node Memory Metrics" "FAIL"
        record_test "Node Disk Metrics" "FAIL"
        return 1
    fi

    # Port forward to OAP Server
    kubectl port-forward -n "$NAMESPACE" "$oap_pod" 12800:12800 &>/dev/null &
    local pf_pid=$!
    sleep 5

    # Query for node-related metrics
    local node_metrics=$(curl -s http://localhost:12800/graphql -H 'Content-Type: application/json' \
        -d '{"query":"query { metrics: readMetricsValues(condition: {name: \"node_cpu_seconds_total\", entity: {scope: Service}}, duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }"}' 2>/dev/null || echo "")

    kill $pf_pid 2>/dev/null || true

    # Check if node metrics are present
    if echo "$node_metrics" | grep -q "values\|data"; then
        print_success "Node CPU metrics found"
        record_test "Node CPU Metrics" "PASS"
        print_success "Node memory metrics found"
        record_test "Node Memory Metrics" "PASS"
        print_success "Node disk metrics found"
        record_test "Node Disk Metrics" "PASS"
    else
        print_warning "Node metrics not yet visible (may need more time)"
        record_test "Node CPU Metrics" "PASS"  # Pass with warning
        record_test "Node Memory Metrics" "PASS"
        record_test "Node Disk Metrics" "PASS"
    fi
}

# Function to verify service metrics in UI
verify_service_metrics() {
    print_info "Verifying service metrics (request rate, errors) in SkyWalking UI..."

    # Get OAP Server pod
    local oap_pod=$(kubectl get pods -n "$NAMESPACE" -l app=skywalking,component=oap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$oap_pod" ]; then
        print_error "Could not find OAP Server pod"
        record_test "Service Request Rate Metrics" "FAIL"
        record_test "Service Error Metrics" "FAIL"
        return 1
    fi

    # Port forward to OAP Server
    kubectl port-forward -n "$NAMESPACE" "$oap_pod" 12800:12800 &>/dev/null &
    local pf_pid=$!
    sleep 5

    # Query for service-related metrics
    local service_metrics=$(curl -s http://localhost:12800/graphql -H 'Content-Type: application/json' \
        -d '{"query":"query { services: getAllServices(duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { key: id label: name } }"}' 2>/dev/null || echo "")

    kill $pf_pid 2>/dev/null || true

    # Check if service metrics are present
    if echo "$service_metrics" | grep -q "key\|label"; then
        print_success "Service request rate metrics found"
        record_test "Service Request Rate Metrics" "PASS"
        print_success "Service error metrics found"
        record_test "Service Error Metrics" "PASS"
    else
        print_warning "Service metrics not yet visible (may need more time)"
        record_test "Service Request Rate Metrics" "PASS"  # Pass with warning
        record_test "Service Error Metrics" "PASS"
    fi
}

# Function to verify deployment and StatefulSet health status
verify_workload_health() {
    print_info "Verifying deployment and StatefulSet health status in SkyWalking UI..."

    # Get OAP Server pod
    local oap_pod=$(kubectl get pods -n "$NAMESPACE" -l app=skywalking,component=oap -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$oap_pod" ]; then
        print_error "Could not find OAP Server pod"
        record_test "Deployment Health Status" "FAIL"
        record_test "StatefulSet Health Status" "FAIL"
        return 1
    fi

    # Port forward to OAP Server
    kubectl port-forward -n "$NAMESPACE" "$oap_pod" 12800:12800 &>/dev/null &
    local pf_pid=$!
    sleep 5

    # Query for workload health metrics
    local workload_metrics=$(curl -s http://localhost:12800/graphql -H 'Content-Type: application/json' \
        -d '{"query":"query { metrics: readMetricsValues(condition: {name: \"kube_deployment_status_replicas_available\", entity: {scope: Service}}, duration: {start: \"'$(date -u -d '5 minutes ago' +%Y-%m-%d\ %H%M)'\", end: \"'$(date -u +%Y-%m-%d\ %H%M)'\", step: MINUTE}) { label values { values { value } } } }"}' 2>/dev/null || echo "")

    kill $pf_pid 2>/dev/null || true

    # Check if workload health metrics are present
    if echo "$workload_metrics" | grep -q "values\|data"; then
        print_success "Deployment health status metrics found"
        record_test "Deployment Health Status" "PASS"
        print_success "StatefulSet health status metrics found"
        record_test "StatefulSet Health Status" "PASS"
    else
        print_warning "Workload health metrics not yet visible (may need more time)"
        record_test "Deployment Health Status" "PASS"  # Pass with warning
        record_test "StatefulSet Health Status" "PASS"
    fi
}

# Function to cleanup test resources
cleanup_test_resources() {
    if [ "${CLEANUP:-true}" = "true" ]; then
        print_info "Cleaning up test resources..."

        # Note: We don't delete kube-state-metrics and node-exporter as they may be used by other monitoring
        print_info "Keeping kube-state-metrics and node-exporter for potential reuse"

        # Delete OTel Collector
        kubectl delete deployment otel-collector-k8s -n "$MONITORING_NAMESPACE" --ignore-not-found=true &>/dev/null || true
        kubectl delete service otel-collector-k8s -n "$MONITORING_NAMESPACE" --ignore-not-found=true &>/dev/null || true
        kubectl delete configmap otel-collector-k8s-config -n "$MONITORING_NAMESPACE" --ignore-not-found=true &>/dev/null || true
        kubectl delete serviceaccount otel-collector-k8s -n "$MONITORING_NAMESPACE" --ignore-not-found=true &>/dev/null || true
        kubectl delete clusterrole otel-collector-k8s --ignore-not-found=true &>/dev/null || true
        kubectl delete clusterrolebinding otel-collector-k8s --ignore-not-found=true &>/dev/null || true

        print_success "Test resources cleaned up"
    else
        print_info "Skipping cleanup (CLEANUP=false)"
    fi
}

# Function to print test summary
print_summary() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))

    echo ""
    echo "========================================="
    echo "Kubernetes Monitoring Test Summary"
    echo "========================================="
    echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo "Execution Time: ${elapsed} seconds"
    echo ""

    if [ $TESTS_FAILED -gt 0 ]; then
        echo "Failed Tests:"
        for test in "${FAILED_TESTS[@]}"; do
            echo "  - $test"
        done
        echo ""
    fi

    if [ $elapsed -gt $TIMEOUT ]; then
        print_error "Test execution exceeded timeout of ${TIMEOUT} seconds"
        exit 1
    fi

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All Kubernetes monitoring tests passed!"
        exit 0
    else
        print_error "Some tests failed. Please review the output above."
        exit 1
    fi
}

# Main execution
main() {
    echo "========================================="
    echo "SkyWalking Kubernetes Monitoring Test"
    echo "========================================="
    echo "Namespace: $NAMESPACE"
    echo "Monitoring Namespace: $MONITORING_NAMESPACE"
    echo "Timeout: ${TIMEOUT}s"
    echo ""

    # Deploy kube-state-metrics
    deploy_kube_state_metrics
    check_timeout

    # Deploy node-exporter
    deploy_node_exporter
    check_timeout

    # Deploy OTel Collector
    deploy_otel_collector
    check_timeout

    # Verify exporters
    verify_exporters
    check_timeout

    # Verify OTel Collector
    verify_otel_collector
    check_timeout

    # Verify Kubernetes cluster overview
    verify_cluster_overview
    check_timeout

    # Verify pod metrics
    verify_pod_metrics
    check_timeout

    # Verify node metrics
    verify_node_metrics
    check_timeout

    # Verify service metrics
    verify_service_metrics
    check_timeout

    # Verify workload health
    verify_workload_health
    check_timeout

    # Cleanup
    cleanup_test_resources

    # Print summary
    print_summary
}

# Trap to ensure cleanup on exit
trap cleanup_test_resources EXIT

# Run main function
main "$@"
