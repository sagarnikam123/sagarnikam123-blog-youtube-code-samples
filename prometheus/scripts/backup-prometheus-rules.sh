#!/bin/bash
#
# PrometheusRules Export/Import Script
# Exports or imports PrometheusRule CRDs from/to Kubernetes
#
# Usage:
#   Export: ./backup-prometheus-rules.sh export [BACKUP_FILE] [OPTIONS]
#   Import: ./backup-prometheus-rules.sh import <BACKUP_FILE> [OPTIONS]
#
# Options:
#   --exclude-namespaces "ns1,ns2"   Exclude specific namespaces
#   --include-namespaces "ns1,ns2"   Include only specific namespaces
#   --target-namespace "ns"          Import all rules to a specific namespace (import only)
#
# Examples:
#   ./backup-prometheus-rules.sh export
#   ./backup-prometheus-rules.sh export --exclude-namespaces "prometheus,kube-system"
#   ./backup-prometheus-rules.sh export ./backup.yaml --exclude-namespaces "prometheus,kube-system"
#   ./backup-prometheus-rules.sh export ./backup.yaml --include-namespaces "hunt,response,datascience"
#   ./backup-prometheus-rules.sh import ./backup.yaml
#   ./backup-prometheus-rules.sh import ./backup.yaml --target-namespace "monitoring"
#

set -e

ACTION="${1:-}"
BACKUP_FILE="prometheus-rules-backup.yaml"
EXCLUDE_NS=""
INCLUDE_NS=""
TARGET_NS=""

# Parse arguments after action
shift 1 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case "$1" in
        --exclude-namespaces)
            EXCLUDE_NS="$2"
            shift 2
            ;;
        --include-namespaces)
            INCLUDE_NS="$2"
            shift 2
            ;;
        --target-namespace)
            TARGET_NS="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            # Positional argument (backup file)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

usage() {
    echo "PrometheusRules Export/Import Script"
    echo ""
    echo "Usage:"
    echo "  Export: $0 export [BACKUP_FILE] [OPTIONS]"
    echo "  Import: $0 import <BACKUP_FILE> [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --exclude-namespaces \"ns1,ns2\"   Exclude specific namespaces"
    echo "  --include-namespaces \"ns1,ns2\"   Include only specific namespaces"
    echo "  --target-namespace \"ns\"          Import all rules to a specific namespace"
    echo ""
    echo "Examples:"
    echo "  $0 export"
    echo "  $0 export --exclude-namespaces \"prometheus,kube-system\""
    echo "  $0 export ./backup.yaml --exclude-namespaces \"prometheus,kube-system\""
    echo "  $0 export ./backup.yaml --include-namespaces \"hunt,response\""
    echo "  $0 import ./backup.yaml"
    echo "  $0 import ./backup.yaml --target-namespace \"monitoring\""
    exit 1
}

# Check if namespace should be skipped
should_skip_namespace() {
    local ns="$1"

    # If include list specified, skip if not in list
    if [[ -n "$INCLUDE_NS" ]]; then
        if ! echo ",$INCLUDE_NS," | grep -q ",$ns,"; then
            return 0  # Skip
        fi
    fi

    # If exclude list specified, skip if in list
    if [[ -n "$EXCLUDE_NS" ]]; then
        if echo ",$EXCLUDE_NS," | grep -q ",$ns,"; then
            return 0  # Skip
        fi
    fi

    return 1  # Don't skip
}

# Clean metadata from YAML (macOS and Linux compatible)
clean_metadata() {
    # Use grep -v for simple line removal, more portable than complex sed
    grep -v -E '^\s*(resourceVersion|uid|creationTimestamp|generation):\s' | \
    awk '
        # Skip kubectl.kubernetes.io/last-applied-configuration annotation (multi-line)
        /kubectl\.kubernetes\.io\/last-applied-configuration:/ { skip_annotation=1; next }
        # End of multi-line annotation when we see another annotation or label at same indent
        skip_annotation && /^    [a-zA-Z]/ { skip_annotation=0 }
        skip_annotation { next }

        # Skip managedFields section
        /^  managedFields:/ { skip=1; next }
        /^  [a-zA-Z]/ && skip { skip=0 }
        skip { next }

        # Skip status section
        /^status:/ { skip_status=1; next }
        /^[a-zA-Z]/ && skip_status { skip_status=0 }
        skip_status { next }

        { print }
    '
}

#######################################
# EXPORT FUNCTION
#######################################
do_export() {
    # Validate backup file is not a directory
    if [[ -d "$BACKUP_FILE" ]]; then
        echo "Error: '$BACKUP_FILE' is a directory. Please specify a file path."
        echo "Example: $0 export ./backup-rules/prometheus-rules.yaml --exclude-namespaces \"prometheus\""
        exit 1
    fi

    # Create parent directory if needed
    local backup_dir=$(dirname "$BACKUP_FILE")
    if [[ "$backup_dir" != "." ]] && [[ ! -d "$backup_dir" ]]; then
        mkdir -p "$backup_dir"
    fi

    echo "=== PrometheusRules Export ==="
    echo "Output file: $BACKUP_FILE"
    [[ -n "$EXCLUDE_NS" ]] && echo "Excluding namespaces: $EXCLUDE_NS"
    [[ -n "$INCLUDE_NS" ]] && echo "Including only namespaces: $INCLUDE_NS"
    echo ""

    # Check if prometheusrules CRD exists
    if ! kubectl get crd prometheusrules.monitoring.coreos.com &>/dev/null; then
        echo "Error: PrometheusRule CRD not found. Is Prometheus Operator installed?"
        exit 1
    fi

    # Get namespaces with prometheusrules
    local namespaces
    namespaces=$(kubectl get prometheusrules -A --no-headers 2>/dev/null | awk '{print $1}' | sort -u)

    local total=$(kubectl get prometheusrules -A --no-headers 2>/dev/null | wc -l | tr -d ' ')
    echo "Found $total PrometheusRules total"
    echo ""

    # Start the output file
    > "$BACKUP_FILE"
    local exported=0

    for ns in $namespaces; do
        if should_skip_namespace "$ns"; then
            local count=$(kubectl get prometheusrules -n "$ns" --no-headers 2>/dev/null | wc -l | tr -d ' ')
            echo "  ⊘ Skipping namespace: $ns ($count rules)"
            continue
        fi

        echo "  Processing namespace: $ns"

        # Get rules from this namespace
        local rules
        rules=$(kubectl get prometheusrules -n "$ns" --no-headers 2>/dev/null | awk '{print $1}')

        for rule in $rules; do
            echo "    ✓ $rule"

            # Export each rule, cleaning metadata
            kubectl get prometheusrule -n "$ns" "$rule" -o yaml | clean_metadata >> "$BACKUP_FILE"

            echo "---" >> "$BACKUP_FILE"
            ((exported++)) || true
        done
    done

    # Remove trailing ---
    if [[ "$(uname)" == "Darwin" ]]; then
        sed -i '' -e '$ { /^---$/d; }' "$BACKUP_FILE" 2>/dev/null || true
    else
        sed -i '$ { /^---$/d; }' "$BACKUP_FILE" 2>/dev/null || true
    fi

    echo ""
    echo "=== Export Complete ==="
    echo "Exported: $exported rules"
    echo "File: $BACKUP_FILE"
    echo ""
    echo "To import: $0 import $BACKUP_FILE"
}

#######################################
# IMPORT FUNCTION
#######################################
do_import() {
    if [[ ! -f "$BACKUP_FILE" ]]; then
        echo "Error: Backup file not found: $BACKUP_FILE"
        usage
    fi

    echo "=== PrometheusRules Import ==="
    echo "Source file: $BACKUP_FILE"
    [[ -n "$TARGET_NS" ]] && echo "Target namespace: $TARGET_NS"
    [[ -n "$EXCLUDE_NS" ]] && echo "Excluding namespaces: $EXCLUDE_NS"
    [[ -n "$INCLUDE_NS" ]] && echo "Including only namespaces: $INCLUDE_NS"
    echo ""

    # Check if prometheusrules CRD exists
    if ! kubectl get crd prometheusrules.monitoring.coreos.com &>/dev/null; then
        echo "Error: PrometheusRule CRD not found. Is Prometheus Operator installed?"
        exit 1
    fi

    local imported=0
    local skipped=0
    local failed=0

    # Process each document in the YAML file
    local doc_count=$(grep -c '^apiVersion: monitoring.coreos.com' "$BACKUP_FILE" 2>/dev/null || echo "0")
    echo "Found $doc_count PrometheusRules in backup"
    echo ""

    # Split YAML using awk (more portable than csplit)
    local temp_dir=$(mktemp -d)

    awk -v dir="$temp_dir" '
        /^---$/ {
            if (NR > 1) close(file)
            file_num++
            file = dir "/rule-" sprintf("%03d", file_num) ".yaml"
            next
        }
        /^apiVersion:/ && file_num == 0 {
            file_num = 1
            file = dir "/rule-" sprintf("%03d", file_num) ".yaml"
        }
        file { print > file }
    ' "$BACKUP_FILE"

    for file in "$temp_dir"/rule-*.yaml; do
        [[ -f "$file" ]] || continue

        # Skip empty files or files without apiVersion
        if ! grep -q 'apiVersion:' "$file" 2>/dev/null; then
            continue
        fi

        local ns=$(grep -E '^  namespace:' "$file" | head -1 | awk '{print $2}' | tr -d '"' | tr -d "'")
        local name=$(grep -E '^  name:' "$file" | head -1 | awk '{print $2}' | tr -d '"' | tr -d "'")

        # Skip if namespace should be filtered
        if [[ -n "$ns" ]] && should_skip_namespace "$ns"; then
            echo "  ⊘ $ns/$name (skipped by filter)"
            ((skipped++)) || true
            continue
        fi

        # Override namespace if target specified
        if [[ -n "$TARGET_NS" ]]; then
            if [[ "$(uname)" == "Darwin" ]]; then
                sed -i '' "s/^  namespace: .*/  namespace: $TARGET_NS/" "$file" 2>/dev/null
            else
                sed -i "s/^  namespace: .*/  namespace: $TARGET_NS/" "$file"
            fi
            ns="$TARGET_NS"
        fi

        # Apply the rule using server-side apply to avoid last-applied-configuration conflicts
        if kubectl apply --server-side --force-conflicts -f "$file" 2>/dev/null; then
            echo "  ✓ $ns/$name"
            ((imported++)) || true
        else
            echo "  ✗ $ns/$name (failed)"
            ((failed++)) || true
        fi
    done

    # Cleanup
    rm -rf "$temp_dir"

    echo ""
    echo "=== Import Complete ==="
    echo "Imported: $imported"
    echo "Skipped: $skipped"
    echo "Failed: $failed"
}

#######################################
# MAIN
#######################################
if [[ -z "$ACTION" ]]; then
    usage
fi

case "$ACTION" in
    export)
        do_export
        ;;
    import)
        do_import
        ;;
    *)
        echo "Error: Unknown action '$ACTION'"
        usage
        ;;
esac
