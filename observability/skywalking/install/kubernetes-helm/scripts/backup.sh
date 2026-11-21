#!/bin/bash
# =============================================================================
# BanyanDB Backup Script for AWS EKS
# =============================================================================
# Creates snapshots of BanyanDB PVCs using AWS EBS snapshots
#
# Usage:
#   ./scripts/backup.sh [environment] [options]
#
# Options:
#   --list        - List existing backups
#   --restore     - Restore from backup (interactive)
#   --retention   - Days to keep backups (default: 30)
#
# Prerequisites:
#   - AWS CLI configured with appropriate permissions
#   - kubectl access to the cluster
#   - EBS CSI driver with snapshot support
#
# Examples:
#   ./scripts/backup.sh production
#   ./scripts/backup.sh production --list
#   ./scripts/backup.sh production --restore
# =============================================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-production}"
RETENTION_DAYS=30
LIST_ONLY=false
RESTORE=false
BACKUP_PREFIX="skywalking-banyandb-backup"

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --list)
            LIST_ONLY=true
            shift
            ;;
        --restore)
            RESTORE=true
            shift
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

get_namespace() {
    case $ENVIRONMENT in
        dev) echo "skywalking-dev" ;;
        staging) echo "skywalking-staging" ;;
        production) echo "skywalking" ;;
    esac
}

# List existing backups
list_backups() {
    local namespace=$(get_namespace)

    log_info "Listing VolumeSnapshots in namespace: ${namespace}"
    echo ""

    kubectl get volumesnapshot -n "${namespace}" \
        -l app.kubernetes.io/name=skywalking \
        -o custom-columns=\
'NAME:.metadata.name,READY:.status.readyToUse,SIZE:.status.restoreSize,AGE:.metadata.creationTimestamp' \
        2>/dev/null || echo "No snapshots found"

    echo ""
    log_info "Listing AWS EBS Snapshots (tagged with skywalking):"
    aws ec2 describe-snapshots \
        --filters "Name=tag:Application,Values=skywalking" \
        --query 'Snapshots[*].[SnapshotId,VolumeSize,StartTime,State,Tags[?Key==`Name`].Value|[0]]' \
        --output table 2>/dev/null || echo "No AWS snapshots found or AWS CLI not configured"
}

# Create VolumeSnapshot
create_snapshot() {
    local namespace=$(get_namespace)
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local snapshot_name="${BACKUP_PREFIX}-${timestamp}"

    log_info "Creating backup for BanyanDB in namespace: ${namespace}"

    # Get BanyanDB PVCs
    local pvcs=$(kubectl get pvc -n "${namespace}" \
        -l app.kubernetes.io/name=banyandb \
        -o jsonpath='{.items[*].metadata.name}')

    if [[ -z "$pvcs" ]]; then
        log_error "No BanyanDB PVCs found in namespace: ${namespace}"
        exit 1
    fi

    log_info "Found PVCs: ${pvcs}"

    # Create VolumeSnapshot for each PVC
    for pvc in $pvcs; do
        local snap_name="${snapshot_name}-${pvc}"
        log_info "Creating snapshot: ${snap_name} for PVC: ${pvc}"

        cat <<EOF | kubectl apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: ${snap_name}
  namespace: ${namespace}
  labels:
    app.kubernetes.io/name: skywalking
    app.kubernetes.io/component: banyandb
    backup-timestamp: "${timestamp}"
spec:
  volumeSnapshotClassName: ebs-csi-snapclass
  source:
    persistentVolumeClaimName: ${pvc}
EOF
    done

    log_success "Backup initiated: ${snapshot_name}"
    log_info "Check status with: kubectl get volumesnapshot -n ${namespace}"
}

# Cleanup old backups
cleanup_old_backups() {
    local namespace=$(get_namespace)
    local cutoff_date=$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || \
                       date -v-${RETENTION_DAYS}d +%Y-%m-%dT%H:%M:%SZ)

    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

    # Get old snapshots
    local old_snapshots=$(kubectl get volumesnapshot -n "${namespace}" \
        -l app.kubernetes.io/name=skywalking \
        -o jsonpath="{.items[?(@.metadata.creationTimestamp<'${cutoff_date}')].metadata.name}" 2>/dev/null)

    if [[ -n "$old_snapshots" ]]; then
        for snap in $old_snapshots; do
            log_info "Deleting old snapshot: ${snap}"
            kubectl delete volumesnapshot "${snap}" -n "${namespace}"
        done
        log_success "Cleanup completed"
    else
        log_info "No old snapshots to clean up"
    fi
}

# Restore from backup
restore_backup() {
    local namespace=$(get_namespace)

    log_warn "RESTORE PROCEDURE"
    log_warn "This will create new PVCs from snapshots."
    log_warn "You will need to manually update the StatefulSet to use new PVCs."
    echo ""

    # List available snapshots
    list_backups

    echo ""
    read -p "Enter snapshot name prefix to restore from: " snapshot_prefix

    if [[ -z "$snapshot_prefix" ]]; then
        log_error "No snapshot prefix provided"
        exit 1
    fi

    # Find matching snapshots
    local snapshots=$(kubectl get volumesnapshot -n "${namespace}" \
        -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | grep "^${snapshot_prefix}")

    if [[ -z "$snapshots" ]]; then
        log_error "No snapshots found matching: ${snapshot_prefix}"
        exit 1
    fi

    log_info "Found snapshots:"
    echo "$snapshots"
    echo ""

    read -p "Proceed with restore? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    # Create PVCs from snapshots
    local timestamp=$(date +%Y%m%d-%H%M%S)
    for snap in $snapshots; do
        local pvc_name="restored-${timestamp}-${snap##*-}"
        log_info "Creating PVC: ${pvc_name} from snapshot: ${snap}"

        cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ${pvc_name}
  namespace: ${namespace}
  labels:
    app.kubernetes.io/name: skywalking
    app.kubernetes.io/component: banyandb
    restored-from: ${snap}
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3-skywalking
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: ${snap}
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
EOF
    done

    log_success "PVCs created from snapshots"
    log_warn "Next steps:"
    log_warn "1. Scale down BanyanDB: kubectl scale statefulset skywalking-banyandb -n ${namespace} --replicas=0"
    log_warn "2. Update StatefulSet to use new PVCs"
    log_warn "3. Scale up BanyanDB"
}

# Ensure VolumeSnapshotClass exists
ensure_snapshot_class() {
    if ! kubectl get volumesnapshotclass ebs-csi-snapclass &> /dev/null; then
        log_info "Creating VolumeSnapshotClass..."
        cat <<EOF | kubectl apply -f -
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: ebs-csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Retain
EOF
    fi
}

# Main
main() {
    echo ""
    echo "=============================================="
    echo "BanyanDB Backup Management"
    echo "=============================================="
    echo ""

    if [[ "$LIST_ONLY" == true ]]; then
        list_backups
        exit 0
    fi

    if [[ "$RESTORE" == true ]]; then
        restore_backup
        exit 0
    fi

    # Default: create backup
    ensure_snapshot_class
    create_snapshot
    cleanup_old_backups
}

main
