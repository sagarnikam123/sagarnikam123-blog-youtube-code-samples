#!/bin/bash

# Function to clean a single YAML file
clean_yaml() {
    local file="$1"
    echo "Cleaning: $file"

    # Create backup
    cp "$file" "${file}.bak"

    # Remove Helm annotations and labels
    sed -i '' '/meta.helm.sh\/release-name:/d' "$file"
    sed -i '' '/meta.helm.sh\/release-namespace:/d' "$file"
    sed -i '' '/helm.sh\/chart:/d' "$file"
    sed -i '' '/app.kubernetes.io\/managed-by: Helm/d' "$file"
    sed -i '' '/app.kubernetes.io\/version:/d' "$file"
    sed -i '' '/chart: mimir-distributed-/d' "$file"
    sed -i '' '/chart: minio-/d' "$file"
    sed -i '' '/heritage: Helm/d' "$file"
    sed -i '' '/release: mimir/d' "$file"
    sed -i '' '/checksum\//d' "$file"

    # Remove kubectl annotations
    sed -i '' '/kubectl.kubernetes.io\/last-applied-configuration:/d' "$file"

    # Remove runtime annotations
    sed -i '' '/pv.kubernetes.io\/bind-completed:/d' "$file"
    sed -i '' '/pv.kubernetes.io\/bound-by-controller:/d' "$file"
    sed -i '' '/volume.beta.kubernetes.io\/storage-provisioner:/d' "$file"
    sed -i '' '/volume.kubernetes.io\/storage-provisioner:/d' "$file"

    # Remove volumeName (runtime PV binding)
    sed -i '' '/volumeName: pvc-/d' "$file"

    # Remove finalizers
    sed -i '' '/finalizers:/d' "$file"
    sed -i '' '/- kubernetes.io\/pvc-protection/d' "$file"

    # Remove metadata fields
    sed -i '' '/creationTimestamp:/d' "$file"
    sed -i '' '/resourceVersion:/d' "$file"
    sed -i '' '/uid:/d' "$file"
    sed -i '' '/generation:/d' "$file"
    sed -i '' '/selfLink:/d' "$file"

    # Remove empty annotations/labels sections
    sed -i '' '/^  annotations: {}$/d' "$file"
    sed -i '' '/^  labels: {}$/d' "$file"
    sed -i '' '/^      annotations:$/d' "$file"
    sed -i '' '/^    annotations:$/d' "$file"
    sed -i '' '/^  annotations:$/d' "$file"

    # Remove runtime Service fields
    sed -i '' '/^  clusterIP:/d' "$file"
    sed -i '' '/^  clusterIPs:/d' "$file"
    sed -i '' '/^  ipFamilies:/d' "$file"
    sed -i '' '/^  ipFamilyPolicy:/d' "$file"

    # Remove managedFields section (multi-line)
    sed -i '' '/managedFields:/,/^[^ ]/{ /managedFields:/d; /^[^ ]/!d; }' "$file"

    # Remove status section (multi-line)
    sed -i '' '/^status:/,/^[^ ]/{ /^status:/d; /^[^ ]/!d; }' "$file"
    sed -i '' '/^    status:$/,/^      phase: Pending$/d' "$file"
}

# Clean all YAML files in subdirectories
for dir in deployments statefulsets services configmaps pvcs jobs serviceaccounts; do
    if [ -d "$dir" ]; then
        echo "Processing $dir..."
        for file in "$dir"/*.yaml; do
            if [ -f "$file" ]; then
                clean_yaml "$file"
            fi
        done
    fi
done

echo ""
echo "Cleanup complete! Backups saved with .bak extension"
echo "To remove backups: find . -name '*.bak' -delete"
